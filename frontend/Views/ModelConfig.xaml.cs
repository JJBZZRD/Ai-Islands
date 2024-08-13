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
                Text = char.ToUpper(sectionName[0]) + sectionName.Substring(1).Replace('_', ' '),
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
            string dictionaryKey = $"{sectionName}.{key}"; // Keep original key names

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
            try
            {
                // Update the _model.Config object with the new values
                foreach (var item in _configValues)
                {
                    var keys = item.Key.Split('.');
                    var sectionName = keys[0];
                    var propertyName = string.Join(".", keys.Skip(1));

                    var sectionProperty = typeof(Config).GetProperty(sectionName, BindingFlags.IgnoreCase | BindingFlags.Public | BindingFlags.Instance);
                    if (sectionProperty != null)
                    {
                        var sectionObject = sectionProperty.GetValue(_model.Config) ?? Activator.CreateInstance(sectionProperty.PropertyType);
                        var property = sectionObject.GetType().GetProperty(propertyName, BindingFlags.IgnoreCase | BindingFlags.Public | BindingFlags.Instance);
                        if (property != null)
                        {
                            var convertedValue = Convert.ChangeType(item.Value, Nullable.GetUnderlyingType(property.PropertyType) ?? property.PropertyType);
                            property.SetValue(sectionObject, convertedValue);
                        }
                        sectionProperty.SetValue(_model.Config, sectionObject);
                    }
                }

                // Send the updated Config object to the server
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