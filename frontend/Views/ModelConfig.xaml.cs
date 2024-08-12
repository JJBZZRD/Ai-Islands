using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.Text.Json;

namespace frontend.Views
{
    public partial class ModelConfig : ContentView
    {
        private Model _model;
        private Dictionary<string, object> _configValues = new Dictionary<string, object>();

        public ModelConfig(Model model)
        {
            InitializeComponent();
            _model = model;
            CreateConfigUI();
        }

        private void CreateConfigUI()
        {
            if (_model.Config == null) return;

            foreach (var section in _model.Config)
            {
                AddSectionToUI(section.Key, section.Value as Dictionary<string, object>);
            }
        }

        private void AddSectionToUI(string sectionName, Dictionary<string, object> sectionConfig)
        {
            if (sectionConfig == null) return;

            var sectionLabel = new Label
            {
                Text = char.ToUpper(sectionName[0]) + sectionName.Substring(1),
                FontSize = 18,
                FontAttributes = FontAttributes.Bold,
                TextColor = Color.FromHex("#5D5D5D"),
                Margin = new Thickness(0, 10, 0, 5)
            };
            ConfigContainer.Children.Add(sectionLabel);

            foreach (var item in sectionConfig)
            {
                AddConfigItemToUI(sectionName, item.Key, item.Value);
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
            else
            {
                var entry = new Entry { Text = value?.ToString() ?? "" };
                entry.TextChanged += (s, e) => _configValues[dictionaryKey] = entry.Text;
                inputView = entry;
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
                var updatedConfig = new Dictionary<string, object>(_model.Config);

                foreach (var item in _configValues)
                {
                    var keys = item.Key.Split('.');
                    var section = keys[0];
                    var key = keys[1];

                    if (!updatedConfig.ContainsKey(section))
                    {
                        updatedConfig[section] = new Dictionary<string, object>();
                    }

                    ((Dictionary<string, object>)updatedConfig[section])[key] = item.Value;
                }

                _model.Config = updatedConfig;

                // Here you would typically call a service to update the model in the backend
                // For example: await _modelService.UpdateModelConfig(_model.ModelId, updatedConfig);

                await Application.Current.MainPage.DisplayAlert("Success", "Configuration saved successfully", "OK");
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save configuration: {ex.Message}", "OK");
            }
        }
    }
}