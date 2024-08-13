using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.Text.Json;
using frontend.Services;
using System.Diagnostics;
using System.Linq;

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

            AddConfigSection("Prompt", _model.Config.Prompt);
            AddConfigSection("Parameters", _model.Config.Parameters);
            AddConfigSection("RagSettings", _model.Config.RagSettings);
            AddConfigSection("ModelConfig", _model.Config.ModelConfig);
            AddConfigSection("TokenizerConfig", _model.Config.TokenizerConfig);
            AddConfigSection("ProcessorConfig", _model.Config.ProcessorConfig);
            AddConfigSection("PipelineConfig", _model.Config.PipelineConfig);
            AddConfigSection("DeviceConfig", _model.Config.DeviceConfig);
            AddConfigSection("TranslationConfig", _model.Config.TranslationConfig);
            AddConfigSection("QuantizationConfig", _model.Config.QuantizationConfig);
            AddConfigSection("SystemPrompt", _model.Config.SystemPrompt);
            AddConfigSection("UserPrompt", _model.Config.UserPrompt);
            AddConfigSection("AssistantPrompt", _model.Config.AssistantPrompt);
        }

        private void AddConfigSection(string sectionName, object sectionConfig)
        {
            if (sectionConfig == null) return;

            var sectionLabel = new Label
            {
                Text = sectionName,
                FontSize = 18,
                FontAttributes = FontAttributes.Bold,
                TextColor = Color.FromHex("#5D5D5D"),
                Margin = new Thickness(0, 10, 0, 5)
            };
            ConfigContainer.Children.Add(sectionLabel);

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

        private void AddConfigItemToUI(string sectionName, string key, object value)
        {
            var label = new Label
            {
                Text = char.ToUpper(key[0]) + key.Substring(1).Replace('_', ' '),
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

        private async void OnSaveConfigClicked(object sender, EventArgs e)
        {
            Debug.WriteLine("OnSaveConfigClicked started");
            try
            {
                Debug.WriteLine("Updating model config");
                UpdateModelConfig();

                var request = new
                {
                    model_id = _model.ModelId,
                    data = _model.Config
                };

                Debug.WriteLine($"Sending request to configure model. ModelId: {_model.ModelId}");
                Debug.WriteLine($"Config data: {JsonSerializer.Serialize(_model.Config)}");

                var result = await _modelService.ConfigureModel(_model.ModelId, request);

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
                var section = keys[0];
                var key = string.Join(".", keys.Skip(1));

                var sectionProperty = typeof(Config).GetProperty(section);
                if (sectionProperty != null)
                {
                    Debug.WriteLine($"Found section property: {section}");
                    var sectionObject = sectionProperty.GetValue(_model.Config);
                    if (sectionObject == null)
                    {
                        Debug.WriteLine($"Creating new instance for section: {section}");
                        sectionObject = Activator.CreateInstance(sectionProperty.PropertyType);
                        sectionProperty.SetValue(_model.Config, sectionObject);
                    }
                    SetPropertyValue(sectionObject, key.Split('.'), item.Value);
                }
                else
                {
                    Debug.WriteLine($"Section property not found: {section}");
                }
            }

            Debug.WriteLine("UpdateModelConfig completed");
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
                var convertedValue = Convert.ChangeType(value, targetType);
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