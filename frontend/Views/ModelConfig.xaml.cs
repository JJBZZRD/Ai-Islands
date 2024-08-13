using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.Text.Json;
using frontend.Services;
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
                // Fallback for non-dictionary configs (though this shouldn't be necessary if all configs are standardized)
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
                TextColor = Color.FromArgb("#5D5D5D"),
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
                    AddConfigItemToUI(sectionName, property.Name, value);
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
                TextColor = Color.FromArgb("#333333")
            };

            View inputView;
            string dictionaryKey = $"{sectionName}.{key}";

            if (value is bool boolValue)
            {
                var switchControl = new Switch { IsToggled = boolValue };
                switchControl.Toggled += (s, e) => _configValues[dictionaryKey] = switchControl.IsToggled;
                inputView = switchControl;
            }
            else if (value is int || value is double || value is float)
            {
                var entry = new Entry { Text = value.ToString(), Keyboard = Keyboard.Numeric };
                entry.TextChanged += (s, e) => 
                {
                    if (double.TryParse(entry.Text, out double result))
                    {
                        _configValues[dictionaryKey] = result;
                    }
                };
                inputView = entry;
            }
            else if (value is string stringValue)
            {
                var entry = new Entry { Text = stringValue };
                entry.TextChanged += (s, e) => _configValues[dictionaryKey] = entry.Text;
                inputView = entry;
            }
            else if (value is IDictionary<string, object> dictValue)
            {
                var stackLayout = new VerticalStackLayout();
                foreach (var kvp in dictValue)
                {
                    AddConfigItemToUI($"{sectionName}.{key}", kvp.Key, kvp.Value);
                }
                inputView = stackLayout;
            }
            else if (value is IList<object> listValue)
            {
                var stackLayout = new VerticalStackLayout();
                for (int i = 0; i < listValue.Count; i++)
                {
                    AddConfigItemToUI($"{sectionName}.{key}", $"[{i}]", listValue[i]);
                }
                inputView = stackLayout;
            }
            else
            {
                inputView = new Label { Text = value?.ToString() ?? "null" };
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

        private string MapSectionNameToPropertyName(string sectionName)
        {
            // Remove spaces and convert to PascalCase
            string pascalCase = string.Concat(sectionName.Split(' ').Select(s => char.ToUpper(s[0]) + s.Substring(1)));

            return pascalCase switch
            {
                "RAGSettings" => "RagSettings",
                "QuantizationConfigOptions" => "QuantizationConfigOptions",
                "SystemPrompt" => "SystemPrompt",
                "UserPrompt" => "UserPrompt",
                "AssistantPrompt" => "AssistantPrompt",
                "ExampleConversation" => "ExampleConversation",
                "ServiceName" => "ServiceName",
                "ContentType" => "ContentType",
                "EmbeddingDimensions" => "EmbeddingDimensions",
                "MaxInputTokens" => "MaxInputTokens",
                "SupportedLanguages" => "SupportedLanguages",
                "SpeakerEmbeddingConfig" => "SpeakerEmbeddingConfig",
                _ => pascalCase
            };
        }

        private async void OnSaveConfigClicked(object sender, EventArgs e)
        {
            try
            {
                foreach (var item in _configValues)
                {
                    var keys = item.Key.Split('.');
                    var sectionName = MapSectionNameToPropertyName(keys[0]);
                    var propertyName = string.Join(".", keys.Skip(1).Select(MapSectionNameToPropertyName));

                    var sectionProperty = typeof(Config).GetProperty(sectionName, BindingFlags.Public | BindingFlags.Instance);
                    if (sectionProperty != null)
                    {
                        var sectionObject = sectionProperty.GetValue(_model.Config) ?? Activator.CreateInstance(sectionProperty.PropertyType);
                        var property = sectionObject.GetType().GetProperty(propertyName, BindingFlags.Public | BindingFlags.Instance);
                        
                        if (property != null)
                        {
                            object convertedValue;
                            var targetType = Nullable.GetUnderlyingType(property.PropertyType) ?? property.PropertyType;

                            if (targetType == typeof(bool))
                            {
                                convertedValue = Convert.ToBoolean(item.Value);
                            }
                            else if (targetType == typeof(int))
                            {
                                convertedValue = Convert.ToInt32(item.Value);
                            }
                            else if (targetType == typeof(float))
                            {
                                convertedValue = Convert.ToSingle(item.Value);
                            }
                            else if (targetType == typeof(double))
                            {
                                convertedValue = Convert.ToDouble(item.Value);
                            }
                            else if (targetType == typeof(string))
                            {
                                convertedValue = Convert.ToString(item.Value);
                            }
                            else
                            {
                                convertedValue = Convert.ChangeType(item.Value, targetType);
                            }

                            property.SetValue(sectionObject, convertedValue);
                        }
                        sectionProperty.SetValue(_model.Config, sectionObject);
                    }
                }

                var result = await _modelService.ConfigureModel(_model.ModelId, _model.Config);
                await Application.Current.MainPage.DisplayAlert("Success", "Configuration saved successfully", "OK");
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save configuration: {ex.Message}", "OK");
            }
        }
    }
}