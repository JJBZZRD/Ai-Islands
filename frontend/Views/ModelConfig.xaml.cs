using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.Text.Json;
using frontend.Services;
using System.Diagnostics;
using System.Linq;
using Microsoft.Maui.Graphics;
using System.Reflection;

namespace frontend.Views
{
    public partial class ModelConfig : ContentView
    {
        private Model _model;
        private Dictionary<string, object> _configValues = new Dictionary<string, object>();
        private ModelService _modelService;

        public ModelConfig(Model model)
        {
            InitializeComponent();
            _model = model;
            _modelService = new ModelService();
            ModelIdLabel.Text = $"Model: {_model.ModelId}";
            CreateConfigUI();
        }

        private void CreateConfigUI()
        {
            if (_model.Config == null) return;

            // Handle the config as a dictionary, which should work for all models
            if (_model.Config is IDictionary<string, object> configDict)
            {
                foreach (var kvp in configDict)
                {
                    AddConfigSection(kvp.Key, kvp.Value);
                }
            }
            else
            {
                // Fallback for non-dictionary configs
                var properties = _model.Config.GetType().GetProperties();
                foreach (var property in properties)
                {
                    var value = property.GetValue(_model.Config);
                    if (value != null)
                    {
                        AddConfigSection(property.Name, value);
                    }
                }
            }
        }

        private void AddConfigSection(string sectionName, object sectionConfig)
        {
            if (sectionConfig == null) return;

            var displayName = FormatNameForDisplay(sectionName);
            var sectionLabel = new Label
            {
                Text = displayName,
                FontSize = 18,
                FontAttributes = FontAttributes.Bold,
                TextColor = Color.FromHex("#5D5D5D"),
                Margin = new Thickness(0, 10, 0, 5)
            };
            ConfigContainer.Children.Add(sectionLabel);

            if (sectionConfig is IDictionary<string, object> dict)
            {
                foreach (var kvp in dict)
                {
                    AddConfigItemToUI(sectionName, kvp.Key, kvp.Value);
                }
            }
            else if (sectionConfig is IList<object> list)
            {
                for (int i = 0; i < list.Count; i++)
                {
                    AddConfigItemToUI(sectionName, $"[{i}]", list[i]);
                }
            }
            else if (sectionConfig.GetType().IsPrimitive || sectionConfig is string)
            {
                AddConfigItemToUI(sectionName, sectionName, sectionConfig);
            }
            else
            {
                var properties = sectionConfig.GetType().GetProperties();
                foreach (var property in properties)
                {
                    var value = property.GetValue(sectionConfig);
                    if (value != null)
                    {
                        AddConfigItemToUI(sectionName, property.Name, value);
                    }
                }
            }
        }

        private void AddConfigItemToUI(string sectionName, string key, object value)
        {
            var displayKey = FormatNameForDisplay(key);
            var label = new Label
            {
                Text = displayKey,
                FontSize = 14,
                TextColor = Color.FromHex("#333333")
            };

            View inputView;
            string dictionaryKey = $"{sectionName}.{key}";

            if (value is bool boolValue)
            {
                var switchControl = new Microsoft.Maui.Controls.Switch { IsToggled = boolValue };
                switchControl.Toggled += (s, e) => _configValues[dictionaryKey] = switchControl.IsToggled;
                inputView = switchControl;
            }
            else if (value is int || value is double || value is float)
            {
                var entry = new Entry { Text = value.ToString(), Keyboard = Keyboard.Numeric };
                entry.TextChanged += (s, e) => _configValues[dictionaryKey] = entry.Text;
                inputView = entry;
            }
            else if (value is string stringValue)
            {
                var entry = new Entry { Text = stringValue };
                entry.TextChanged += (s, e) => _configValues[dictionaryKey] = entry.Text;
                inputView = entry;
            }
            else if (value is Dictionary<string, object> dictValue)
            {
                var stackLayout = new VerticalStackLayout();
                foreach (var kvp in dictValue)
                {
                    AddConfigItemToUI($"{sectionName}.{key}", kvp.Key, kvp.Value);
                }
                inputView = stackLayout;
            }
            else
            {
                // For other types, display as read-only text
                inputView = new Label { Text = value.ToString() };
            }

            _configValues[dictionaryKey] = value;

            var itemLayout = new VerticalStackLayout
            {
                Children = { label, inputView },
                Margin = new Thickness(0, 0, 0, 10)
            };

            ConfigContainer.Children.Add(itemLayout);
        }

        private string FormatNameForDisplay(string name)
        {
            // Insert a space before each capital letter, except for the first one
            return System.Text.RegularExpressions.Regex.Replace(name, @"((?<=\p{Ll})\p{Lu}|\p{Lu}(?=\p{Ll}))", " $1");
        }

        private async void OnSaveConfigClicked(object sender, EventArgs e)
        {
            Debug.WriteLine("OnSaveConfigClicked started");
            try
            {
                Debug.WriteLine("Updating model config");
                UpdateModelConfig();

                Debug.WriteLine($"Sending request to configure model. ModelId: {_model.ModelId}");
                Debug.WriteLine($"Config data: {JsonSerializer.Serialize(_model.Config)}");

                var result = await _modelService.ConfigureModel(_model.ModelId, _model.Config);

                Debug.WriteLine("Configuration saved successfully");
                await Application.Current.MainPage.DisplayAlert("Success", "Configuration saved successfully", "OK");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error saving configuration: {ex.Message}");
                Debug.WriteLine($"Stack trace: {ex.StackTrace}");
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save configuration: {ex.Message}", "OK");
            }
        }

        private void UpdateModelConfig()
        {
            Debug.WriteLine("UpdateModelConfig started");
            Debug.WriteLine($"Number of config values to update: {_configValues.Count}");

            foreach (var item in _configValues)
            {
                Debug.WriteLine($"Updating config item: {item.Key} = {item.Value}");

                var keys = item.Key.Split('.');
                Debug.WriteLine($"Keys: [{string.Join(", ", keys)}]");
                if (keys.Distinct().ToArray().Length == 1)
                {
                    // Handle top-level attributes
                    SetTopLevelPropertyValue(_model.Config, keys[0], item.Value);
                }
                else
                {
                    // Handle nested attributes
                    SetPropertyValue(_model.Config, keys, item.Value);
                }
            }

            Debug.WriteLine("UpdateModelConfig completed");
        }

        private void SetTopLevelPropertyValue(object obj, string propertyName, object value)
        {
            Debug.WriteLine($"SetTopLevelPropertyValue started. Property: {propertyName}");

            var property = obj.GetType().GetProperty(propertyName);
            if (property != null)
            {
                Debug.WriteLine($"Setting value for property: {propertyName}");
                var targetType = Nullable.GetUnderlyingType(property.PropertyType) ?? property.PropertyType;
                object convertedValue;

                if (targetType == typeof(bool))
                {
                    convertedValue = Convert.ToBoolean(value);
                }
                else if (targetType == typeof(int))
                {
                    convertedValue = Convert.ToInt32(value);
                }
                else if (targetType == typeof(float))
                {
                    convertedValue = Convert.ToSingle(value);
                }
                else if (targetType == typeof(double))
                {
                    convertedValue = Convert.ToDouble(value);
                }
                else if (targetType == typeof(string))
                {
                    convertedValue = Convert.ToString(value);
                }
                else
                {
                    convertedValue = Convert.ChangeType(value, targetType);
                }

                property.SetValue(obj, convertedValue);
                Debug.WriteLine($"Value set successfully: {convertedValue}");
            }
            else
            {
                Debug.WriteLine($"Property not found: {propertyName}");
            }

            Debug.WriteLine("SetTopLevelPropertyValue completed");
        }

        private void SetPropertyValue(object obj, string[] propertyPath, object value)
        {
            Debug.WriteLine($"SetPropertyValue started. Property path: {string.Join(".", propertyPath)}");

            for (int i = 0; i < propertyPath.Length - 1; i++)
            {
                var property = obj.GetType().GetProperty(propertyPath[i]);
                if (property == null)
                {
                    Debug.WriteLine($"Property not found: {propertyPath[i]}");
                    return;
                }

                var propertyValue = property.GetValue(obj);
                if (propertyValue == null)
                {
                    Debug.WriteLine($"Creating new instance for property: {propertyPath[i]}");
                    propertyValue = Activator.CreateInstance(property.PropertyType);
                    property.SetValue(obj, propertyValue);
                }
                obj = propertyValue;
            }

            var lastProperty = obj.GetType().GetProperty(propertyPath.Last());
            if (lastProperty != null)
            {
                Debug.WriteLine($"Setting value for property: {propertyPath.Last()}");
                var targetType = Nullable.GetUnderlyingType(lastProperty.PropertyType) ?? lastProperty.PropertyType;
                object convertedValue;

                if (targetType == typeof(bool))
                {
                    convertedValue = Convert.ToBoolean(value);
                }
                else if (targetType == typeof(int))
                {
                    convertedValue = Convert.ToInt32(value);
                }
                else if (targetType == typeof(float))
                {
                    convertedValue = Convert.ToSingle(value);
                }
                else if (targetType == typeof(double))
                {
                    convertedValue = Convert.ToDouble(value);
                }
                else if (targetType == typeof(string))
                {
                    convertedValue = Convert.ToString(value);
                }
                else
                {
                    convertedValue = Convert.ChangeType(value, targetType);
                }

                lastProperty.SetValue(obj, convertedValue);
                Debug.WriteLine($"Value set successfully: {convertedValue}");
            }
            else
            {
                Debug.WriteLine($"Last property not found: {propertyPath.Last()}");
            }

            Debug.WriteLine("SetPropertyValue completed");
        }
    }
}