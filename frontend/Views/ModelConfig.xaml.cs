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

        private Dictionary<string, List<string>> _dropdownOptions = new Dictionary<string, List<string>>
        {
            // ParametersConfig
            { "Parameters.Temperature", new List<string> { "0.1", "0.5", "0.7", "1.0" } },
            { "Parameters.TopP", new List<string> { "0.1", "0.5", "0.9", "1.0" } },
            { "Parameters.TopK", new List<string> { "10", "20", "50", "100" } },
            { "Parameters.MaxNewTokens", new List<string> { "100", "200", "500", "1000" } },
            { "Parameters.MinNewTokens", new List<string> { "10", "20", "50", "100" } },
            { "Parameters.RepetitionPenalty", new List<string> { "1.0", "1.1", "1.2", "1.3" } },

            // RagSettings
            { "RagSettings.SimilarityThreshold", new List<string> { "0.5", "0.6", "0.7", "0.8" } },

            // ModelConfig
            { "ModelConfig.TorchDtype", new List<string> { "float16", "float32", "bfloat16" } },

            // TokenizerConfig
            { "TokenizerConfig.EosToken", new List<string> { " ", "<|endoftext|>", "[EOS]" } },
            { "TokenizerConfig.UnkToken", new List<string> { " ", "[UNK]", "?" } },

            // PipelineConfig
            { "PipelineConfig.MaxLength", new List<string> { "512", "1024", "2048" } },
            { "PipelineConfig.MaxNewTokens", new List<string> { "100", "200", "500" } },
            { "PipelineConfig.NumBeams", new List<string> { "1", "2", "4", "8" } },
            { "PipelineConfig.SrcLang", new List<string> { "en", "fr", "de", "es" } },
            { "PipelineConfig.TgtLang", new List<string> { "en", "fr", "de", "es" } },
            { "PipelineConfig.ChunkLengthS", new List<string> { "10", "20", "30" } },
            { "PipelineConfig.BatchSize", new List<string> { "1", "2", "4", "8" } },

            // GenerateKwargs
            { "PipelineConfig.GenerateKwargs.Language", new List<string> { "English", "French", "German", "Spanish" } },
            { "PipelineConfig.GenerateKwargs.Task", new List<string> { "summarization", "translation", "question-answering" } },

            // DeviceConfig
            { "DeviceConfig.Device", new List<string> { "cpu", "cuda", "mps" } },

            // TranslationConfig
            { "TranslationConfig.SrcLang", new List<string> { "en", "fr", "de", "es" } },
            { "TranslationConfig.TgtLang", new List<string> { "en", "fr", "de", "es" } },

            // QuantizationConfig
            { "QuantizationConfig.CurrentMode", new List<string> { "4-bit", "8-bit", "bfloat16" } },

            // FourBitConfig
            { "QuantizationConfigOptions.4-bit.Bnb4BitQuantType", new List<string> { "fp4", "nf4" } },
            { "QuantizationConfigOptions.4-bit.Bnb4BitComputeDtype", new List<string> { "float16", "bfloat16" } },

            // SystemPrompt, UserPrompt, AssistantPrompt
            { "SystemPrompt.Role", new List<string> { "system", "assistant", "user" } },
            { "UserPrompt.Role", new List<string> { "user", "human" } },
            { "AssistantPrompt.Role", new List<string> { "assistant", "ai" } },

            // Other Config properties
            { "Voice", new List<string> { "male", "female", "neutral" } },
            { "Pitch", new List<string> { "-10", "-5", "0", "5", "10" } },
            { "Speed", new List<string> { "0.5", "0.75", "1.0", "1.25", "1.5" } },
            { "ContentType", new List<string> { "text", "audio", "image" } },
            { "EmbeddingDimensions", new List<string> { "128", "256", "512", "1024" } },
            { "MaxInputTokens", new List<string> { "512", "1024", "2048", "4096" } },
            { "SpeakerEmbeddingConfig", new List<string> { "default", "custom" } }
        };

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
            else if (sectionConfig is List<ConversationTurn> list)
            {
                AddExampleConversationToUI(sectionName, list);
                
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

        private void AddExampleConversationToUI(string sectionName, List<ConversationTurn> conversation)
        {
            var conversationLayout = new VerticalStackLayout();
            for (int i = 0; i < conversation.Count; i++)
            {
                var turn = conversation[i];
                var turnLayout = new VerticalStackLayout
                {
                    Margin = new Thickness(0, 0, 0, 10)
                };

                var roleEntry = new Entry
                {
                    Text = turn.Role,
                    Placeholder = "Enter role"
                };
                roleEntry.TextChanged += (s, e) => 
                {
                    _configValues[$"{sectionName}[{i}].Role"] = roleEntry.Text;
                };

                var contentEntry = new Entry
                {
                    Text = turn.Content,
                    Placeholder = "Enter content"
                };
                contentEntry.TextChanged += (s, e) => 
                {
                    _configValues[$"{sectionName}[{i}].Content"] = contentEntry.Text;
                };

                turnLayout.Children.Add(new Label { Text = "Role:", FontSize = 14, TextColor = Color.FromHex("#333333") });
                turnLayout.Children.Add(roleEntry);
                turnLayout.Children.Add(new Label { Text = "Content:", FontSize = 14, TextColor = Color.FromHex("#333333") });
                turnLayout.Children.Add(contentEntry);

                conversationLayout.Children.Add(turnLayout);
            }

            // Add a button to add new conversation turns
            var addButton = new Button
            {
                Text = "Add Turn",
                Command = new Command(() => AddNewConversationTurn(conversationLayout, sectionName, conversation.Count))
            };
            conversationLayout.Children.Add(addButton);

            ConfigContainer.Children.Add(conversationLayout);
        }

        private void AddNewConversationTurn(VerticalStackLayout conversationLayout, string sectionName, int index)
        {
            var turnLayout = new VerticalStackLayout
            {
                Margin = new Thickness(0, 0, 0, 10)
            };

            var roleEntry = new Entry
            {
                Placeholder = "Enter role"
            };
            roleEntry.TextChanged += (s, e) => 
            {
                _configValues[$"{sectionName}[{index}].Role"] = roleEntry.Text;
            };

            var contentEntry = new Entry
            {
                Placeholder = "Enter content"
            };
            contentEntry.TextChanged += (s, e) => 
            {
                _configValues[$"{sectionName}[{index}].Content"] = contentEntry.Text;
            };

            turnLayout.Children.Add(new Label { Text = "Role:", FontSize = 14, TextColor = Color.FromHex("#333333") });
            turnLayout.Children.Add(roleEntry);
            turnLayout.Children.Add(new Label { Text = "Content:", FontSize = 14, TextColor = Color.FromHex("#333333") });
            turnLayout.Children.Add(contentEntry);

            conversationLayout.Children.Insert(conversationLayout.Children.Count - 1, turnLayout);
        }

        private void AddConfigItemToUI(string sectionName, string key, object value, int depth = 0)
        {
            var displayKey = FormatNameForDisplay(key);
            string dictionaryKey = $"{sectionName}.{key}";

            if (key == "quantization_config_options")
            {
                AddQuantizationConfigOptions(value as Dictionary<string, object>, depth);
                return;
            }

            View inputView;
            bool isDropdown = false;

            if (_dropdownOptions.ContainsKey(dictionaryKey))
            {
                var picker = new Picker { Title = displayKey };
                foreach (var option in _dropdownOptions[dictionaryKey])
                {
                    picker.Items.Add(option);
                }
                picker.SelectedItem = value?.ToString();
                picker.SelectedIndexChanged += (s, e) => _configValues[dictionaryKey] = picker.SelectedItem;
                inputView = picker;
                isDropdown = true;
            }
            else if (value is bool boolValue)
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
            else if (value is IEnumerable<string> stringList)
            {
                var entry = new Entry
                {
                    Text = string.Join(", ", stringList),
                    Placeholder = "Enter comma-separated values"
                };
                entry.TextChanged += (s, e) => 
                {
                    _configValues[dictionaryKey] = entry.Text.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries)
                                                        .Select(s => s.Trim())
                                                        .ToList();
                };
                inputView = entry;
            }
            else if (value is Dictionary<string, object> dictValue)
            {
                var stackLayout = new VerticalStackLayout();
                foreach (var kvp in dictValue)
                {
                    AddConfigItemToUI($"{dictionaryKey}", kvp.Key, kvp.Value, depth + 1);
                }
                inputView = stackLayout;
            }
            else if (value != null && value.GetType().IsClass)
            {
                var stackLayout = new VerticalStackLayout();
                foreach (var prop in value.GetType().GetProperties())
                {
                    var propValue = prop.GetValue(value);
                    if (propValue != null)
                    {
                        AddConfigItemToUI(dictionaryKey, prop.Name, propValue, depth + 1);
                    }
                }
                inputView = stackLayout;
            }
            else
            {
                inputView = new Label { Text = value?.ToString() ?? "null" };
            }

            _configValues[dictionaryKey] = value;

            VerticalStackLayout itemLayout;
            if (isDropdown)
            {
                itemLayout = new VerticalStackLayout
                {
                    Children = { inputView },
                    Margin = new Thickness(depth * 10, 0, 0, 10)
                };
            }
            else
            {
                var label = new Label
                {
                    Text = displayKey,
                    FontSize = 14,
                    TextColor = Color.FromHex("#333333")
                };
                itemLayout = new VerticalStackLayout
                {
                    Children = { label, inputView },
                    Margin = new Thickness(depth * 10, 0, 0, 10)
                };
            }

            ConfigContainer.Children.Add(itemLayout);
        }

        private void AddQuantizationConfigOptions(Dictionary<string, object> options, int depth)
        {
            if (options == null) return;

            var label = new Label
            {
                Text = "Quantization Config Options",
                FontSize = 18,
                FontAttributes = FontAttributes.Bold,
                TextColor = Color.FromHex("#5D5D5D"),
                Margin = new Thickness(depth * 10, 10, 0, 5)
            };
            ConfigContainer.Children.Add(label);

            foreach (var kvp in options)
            {
                var subLabel = new Label
                {
                    Text = FormatNameForDisplay(kvp.Key),
                    FontSize = 16,
                    FontAttributes = FontAttributes.Bold,
                    TextColor = Color.FromHex("#333333"),
                    Margin = new Thickness((depth + 1) * 10, 5, 0, 5)
                };
                ConfigContainer.Children.Add(subLabel);

                if (kvp.Value is Dictionary<string, object> subOptions)
                {
                    foreach (var subKvp in subOptions)
                    {
                        AddConfigItemToUI($"quantization_config_options.{kvp.Key}", subKvp.Key, subKvp.Value, depth + 2);
                    }
                }
            }
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

            var exampleConversationUpdates = new Dictionary<int, Dictionary<string, string>>();

            foreach (var item in _configValues)
            {
                Debug.WriteLine($"Updating config item: {item.Key} = {item.Value}");

                var keys = item.Key.Split('.');
                Debug.WriteLine($"Keys: [{string.Join(", ", keys)}]");
                if (keys[0].StartsWith("ExampleConversation"))
                {
                    UpdateExampleConversationItem(exampleConversationUpdates, keys, item.Value);
                }
                else if (keys.Distinct().ToArray().Length == 1)
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

            // Apply the updates to the ExampleConversation list
            if (exampleConversationUpdates.Count > 0)
            {
                var exampleConversation = _model.Config.ExampleConversation ?? new List<ConversationTurn>();
                foreach (var update in exampleConversationUpdates)
                {
                    while (exampleConversation.Count <= update.Key)
                    {
                        exampleConversation.Add(new ConversationTurn());
                    }

                    var turn = exampleConversation[update.Key];
                    if (update.Value.ContainsKey("Role"))
                    {
                        turn.Role = update.Value["Role"];
                    }
                    if (update.Value.ContainsKey("Content"))
                    {
                        turn.Content = update.Value["Content"];
                    }
                }
                _model.Config.ExampleConversation = exampleConversation;
            }

            Debug.WriteLine("UpdateModelConfig completed");
        }

        private void UpdateExampleConversationItem(Dictionary<int, Dictionary<string, string>> conversationUpdates, string[] keys, object value)
        {
            // Extract the index from the keys[0] format "ExampleConversation[i]"
            var match = System.Text.RegularExpressions.Regex.Match(keys[0], @"ExampleConversation\[(\d+)\]");
            if (!match.Success)
            {
                Debug.WriteLine($"Invalid ExampleConversation key format: {keys[0]}");
                return;
            }

            int index = int.Parse(match.Groups[1].Value);
            string property = keys[1];

            if (!conversationUpdates.ContainsKey(index))
            {
                conversationUpdates[index] = new Dictionary<string, string>();
            }

            conversationUpdates[index][property] = value?.ToString();
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
                else if (targetType == typeof(List<string>) || targetType == typeof(string[]))
                {
                    if (value is IEnumerable<string> stringList)
                    {
                        convertedValue = stringList.ToList();
                    }
                    else if (value is string stringValue)
                    {
                        convertedValue = stringValue.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries)
                                                    .Select(s => s.Trim())
                                                    .ToList();
                    }
                    else
                    {
                        convertedValue = new List<string>();
                    }
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
                else if (targetType == typeof(List<string>) || targetType == typeof(string[]))
                {
                    if (value is IEnumerable<string> stringList)
                    {
                        convertedValue = stringList.ToList();
                    }
                    else if (value is string stringValue)
                    {
                        convertedValue = stringValue.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries)
                                                    .Select(s => s.Trim())
                                                    .ToList();
                    }
                    else
                    {
                        convertedValue = new List<string>();
                    }
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