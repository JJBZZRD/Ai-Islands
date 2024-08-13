using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.Text.Json;
using frontend.Services;

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
            AddConfigSection("System Prompt", _model.Config.SystemPrompt);
            AddConfigSection("User Prompt", _model.Config.UserPrompt);
            AddConfigSection("Assistant Prompt", _model.Config.AssistantPrompt);
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
                var switchControl = new Switch { IsToggled = boolValue };
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
            try
            {
                var updatedConfig = new Dictionary<string, object>();

                foreach (var item in _configValues)
                {
                    var keys = item.Key.Split('.');
                    var section = keys[0];
                    var key = string.Join(".", keys.Skip(1));

                    if (!updatedConfig.ContainsKey(section))
                    {
                        updatedConfig[section] = new Dictionary<string, object>();
                    }

                    var sectionDict = (Dictionary<string, object>)updatedConfig[section];
                    SetNestedValue(sectionDict, key.Split('.'), item.Value);
                }

                var request = new
                {
                    model_id = _model.ModelId,
                    data = updatedConfig
                };

                var result = await _modelService.ConfigureModel(_model.ModelId, request);

                // Update the local model configuration
                _model.Config = JsonSerializer.Deserialize<Config>(JsonSerializer.Serialize(updatedConfig));

                await Application.Current.MainPage.DisplayAlert("Success", "Configuration saved successfully", "OK");
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save configuration: {ex.Message}", "OK");
            }
        }

        private void SetNestedValue(Dictionary<string, object> dict, string[] keys, object value)
        {
            for (int i = 0; i < keys.Length - 1; i++)
            {
                if (!dict.ContainsKey(keys[i]))
                {
                    dict[keys[i]] = new Dictionary<string, object>();
                }
                dict = (Dictionary<string, object>)dict[keys[i]];
            }
            dict[keys[keys.Length - 1]] = value;
        }
    }
}