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

            AddConfigSection("Prompt", _model.Config.Prompt);
            AddConfigSection("Parameters", _model.Config.Parameters);
            AddConfigSection("RAG Settings", _model.Config.RagSettings);
            AddConfigSection("Model Config", _model.Config.ModelConfig);
            AddConfigSection("Tokenizer Config", _model.Config.TokenizerConfig);
            AddConfigSection("Processor Config", _model.Config.ProcessorConfig);
            AddConfigSection("Pipeline Config", _model.Config.PipelineConfig);
            AddConfigSection("Device Config", _model.Config.DeviceConfig);
            AddConfigSection("Translation Config", _model.Config.TranslationConfig);
            AddConfigSection("Quantization Config", _model.Config.QuantizationConfig);
            AddConfigSection("Quantization Config Options", _model.Config.QuantizationConfigOptions);
            AddConfigSection("System Prompt", _model.Config.SystemPrompt);
            AddConfigSection("User Prompt", _model.Config.UserPrompt);
            AddConfigSection("Assistant Prompt", _model.Config.AssistantPrompt);
            AddConfigSection("Example Conversation", _model.Config.ExampleConversation);
            AddConfigSection("Service Name", _model.Config.ServiceName);
            AddConfigSection("Features", _model.Config.Features);
            AddConfigSection("Voice", _model.Config.Voice);
            AddConfigSection("Pitch", _model.Config.Pitch);
            AddConfigSection("Speed", _model.Config.Speed);
            AddConfigSection("Model", _model.Config.Model);
            AddConfigSection("Content Type", _model.Config.ContentType);
            AddConfigSection("Embedding Dimensions", _model.Config.EmbeddingDimensions);
            AddConfigSection("Max Input Tokens", _model.Config.MaxInputTokens);
            AddConfigSection("Supported Languages", _model.Config.SupportedLanguages);
            AddConfigSection("Speaker Embedding Config", _model.Config.SpeakerEmbeddingConfig);
        }

        private void AddConfigSection(string sectionName, object sectionConfig)
        {
            if (sectionConfig == null) return;

            var sectionLabel = new Label
            {
                Text = sectionName,
                FontSize = 18,
                FontAttributes = FontAttributes.Bold,
                TextColor = Color.FromArgb("#5D5D5D"),
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
            var displayKey = key.Replace("_", " ");
            var label = new Label
            {
                Text = char.ToUpper(displayKey[0]) + displayKey.Substring(1),
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

        private string MapSectionNameToPropertyName(string sectionName)
        {
            return sectionName.Replace(" ", "") switch
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
                _ => sectionName
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
                    var propertyName = string.Join(".", keys.Skip(1));

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