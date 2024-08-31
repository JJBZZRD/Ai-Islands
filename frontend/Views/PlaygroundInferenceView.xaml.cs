using System;
using Microsoft.Maui.Controls;
using frontend.Models;
using frontend.Services;
using frontend.Models.ViewModels;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using System.ComponentModel;
using System.Text.Json;

namespace frontend.Views
{
    public partial class PlaygroundInferenceView : ContentView, INotifyPropertyChanged
    {
        private readonly Playground _playground;
        private readonly PlaygroundService _playgroundService;
        private bool _isChainLoaded = false;  // Track the state of the chain
        private string _inputText;
        private string _selectedFilePath;

        public ICommand LoadChainCommand { get; }
        public ICommand InferenceCommand { get; }
        private bool _isJsonViewVisible = false;  
        private bool _isAudioPlayerVisible = false;  

        public PlaygroundInferenceView(Playground playground, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playground = playground;
            _playgroundService = playgroundService;
            LoadChainCommand = new Command(async () => await LoadOrStopChain());
            InferenceCommand = new Command(async () => await RunInference());
            BindingContext = this;
            CreateInputUI();
            UpdateOutputVisibility();
        }

        public string ChainButtonText => _isChainLoaded ? "Stop Chain" : "Load Chain";

        private async Task LoadOrStopChain()
        {
            if (!_isChainLoaded)
            {
                try
                {
                    await _playgroundService.LoadPlaygroundChain(_playground.PlaygroundId);
                    _isChainLoaded = true;
                    OnPropertyChanged(nameof(ChainButtonText));  // Update button text
                    await Application.Current.MainPage.DisplayAlert("Success", "Chain loaded successfully.", "OK");
                }
                catch (Exception ex)
                {
                    await Application.Current.MainPage.DisplayAlert("Error", $"Failed to load chain: {ex.Message}", "OK");
                }
            }
            else
            {
                try
                {
                    await _playgroundService.StopPlaygroundChain(_playground.PlaygroundId);
                    _isChainLoaded = false;
                    OnPropertyChanged(nameof(ChainButtonText));  
                    await Application.Current.MainPage.DisplayAlert("Success", "Chain stopped successfully.", "OK");
                }
                catch (Exception ex)
                {
                    await Application.Current.MainPage.DisplayAlert("Error", $"Failed to stop chain: {ex.Message}", "OK");
                }
            }
        }

        private async Task RunInference()
        {
            if (!_isChainLoaded)
            {
                await Application.Current.MainPage.DisplayAlert("Error", "Please load the chain first.", "OK");
                return;
            }

            try
            {
                var inputData = GetInputData();
                if (inputData.Count == 0)
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Please provide input data.", "OK");
                    return;
                }

                var inferenceRequest = new Dictionary<string, object>
                {
                    { "playground_id", _playground.PlaygroundId },
                    { "data", inputData }
                };

                var result = await _playgroundService.Inference(_playground.PlaygroundId, inferenceRequest);

                if (result.TryGetValue("error", out var errorMessage))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", errorMessage.ToString(), "OK");
                }
                else if (result.TryGetValue("data", out var dataValue))
                {
                    await HandleInferenceResult(dataValue);
                }
                else
                {
                    HandleTextOutput(result);
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Inference failed: {ex.Message}", "OK");
            }
        }

        private async Task HandleInferenceResult(object dataValue)
        {
            switch (_playground.Models[_playground.Chain.LastOrDefault()].PipelineTag?.ToLower())
            {
                case "text-to-speech":
                    await HandleAudioOutput(dataValue);
                    break;
                case "speech-to-text":
                    HandleTextOutput(dataValue);
                    break;
                default:
                    OutputText.Text = FormatJsonString(dataValue);
                    break;
            }

            UpdateOutputVisibility();
        }

        private async Task HandleAudioOutput(object dataValue)
        {
            if (dataValue is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Object)
            {
                var audioContentBase64 = jsonElement.GetProperty("audio_content").GetString();
                if (!string.IsNullOrEmpty(audioContentBase64))
                {
                    var audioBytes = Convert.FromBase64String(audioContentBase64);
                    var tempFilePath = Path.Combine(FileSystem.CacheDirectory, "temp_audio.wav");
                    await File.WriteAllBytesAsync(tempFilePath, audioBytes);

                    if (File.Exists(tempFilePath))
                    {
                        AudioPlayer.Source = new Uri(tempFilePath);
                        AudioPlayer.IsVisible = true;
                        _isAudioPlayerVisible = true; // Update visibility flag
                        OnPropertyChanged(nameof(_isAudioPlayerVisible));
                    }
                    else
                    {
                        await Application.Current.MainPage.DisplayAlert("Error", "Audio file could not be found or saved.", "OK");
                    }
                }
            }
        }

        private void HandleTextOutput(object dataValue)
        {
            OutputText.Text = dataValue?.ToString() ?? "No output received.";
        }

        private Dictionary<string, object> GetInputData()
        {
            var firstModelKey = _playground.Chain.FirstOrDefault();
            if (firstModelKey == null || !_playground.Models.TryGetValue(firstModelKey, out var firstModel))
            {
                return new Dictionary<string, object>();
            }

            var inputData = new Dictionary<string, object>();

            switch (firstModel.PipelineTag?.ToLower())
            {
                case "object-detection":
                case "image-segmentation":
                    if (string.IsNullOrEmpty(_selectedFilePath))
                        throw new InvalidOperationException("Please select an image file.");
                    inputData["image_path"] = _selectedFilePath;
                    break;
                case "zero-shot-object-detection":
                    if (string.IsNullOrEmpty(_selectedFilePath) || string.IsNullOrEmpty(_inputText))
                        throw new InvalidOperationException("Please select an image file and enter text.");
                    inputData["payload"] = new { image = _selectedFilePath, text = _inputText.Split(',').Select(t => t.Trim()).ToList() };
                    break;
                case "text-generation":
                case "text-to-speech":
                case "translation":
                case "text-classification":
                case "feature-extraction":
                    if (string.IsNullOrWhiteSpace(_inputText))
                        throw new InvalidOperationException("Please enter text input.");
                    inputData["payload"] = _inputText;
                    break;
                case "speech-to-text":
                case "automatic-speech-recognition":
                    if (string.IsNullOrEmpty(_selectedFilePath))
                        throw new InvalidOperationException("Please select an audio file.");
                    inputData["audio_path"] = _selectedFilePath;
                    break;
                default:
                    throw new ArgumentException("Unsupported model type for inference.");
            }

            return inputData;
        }

        private void CreateInputUI()
        {
            var firstModelKey = _playground.Chain.FirstOrDefault();
            if (firstModelKey == null || !_playground.Models.TryGetValue(firstModelKey, out var firstModel))
            {
                return;
            }

            switch (firstModel.PipelineTag?.ToLower())
            {
                case "object-detection":
                case "image-segmentation":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image"));
                    break;
                case "zero-shot-object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image"));
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "text-classification":
                case "zero-shot-classification":
                case "translation":
                case "text-to-speech":
                case "text-generation":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "speech-to-text":
                case "automatic-speech-recognition":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Audio File"));
                    break;
                default:
                    InputContainer.Children.Add(new Label { Text = "Input type not supported for this model." });
                    break;
            }
        }

        private View CreateFileSelectionUI(string buttonText)
        {
            var fileButton = new Button
            {
                Text = buttonText,
                BackgroundColor = Colors.LightGray,
                TextColor = Colors.Black,
                CornerRadius = 5,
                Margin = new Thickness(0, 20, 0, 10)
            };

            if (buttonText == "Select Image")
            {
                fileButton.Clicked += OnImageSelectClicked;
            }
            else if (buttonText == "Select Audio File")
            {
                fileButton.Clicked += OnAudioSelectClicked;
            }

            var fileNameLabel = new Label
            {
                TextColor = Colors.Black,
                IsVisible = false
            };

            return new VerticalStackLayout
            {
                Children =
                {
                    fileButton,
                    fileNameLabel
                }
            };
        }

        private View CreateTextInputUI()
        {
            var editor = new Editor
            {
                Placeholder = "Enter your input here...",
                PlaceholderColor = Colors.Gray,
                HeightRequest = 150,
                Text = _inputText
            };
            editor.TextChanged += (sender, e) => _inputText = ((Editor)sender)?.Text ?? string.Empty;
            return editor;
        }

        private async void OnImageSelectClicked(object sender, EventArgs e)
        {
            try
            {
                var customFileType = new FilePickerFileType(
                    new Dictionary<DevicePlatform, IEnumerable<string>>
                    {
                        { DevicePlatform.iOS, new[] { "public.jpeg", "public.png" } },
                        { DevicePlatform.Android, new[] { "image/jpeg", "image/png" } },
                        { DevicePlatform.WinUI, new[] { ".jpg", ".jpeg", ".png" } }
                    });

                var result = await FilePicker.PickAsync(new PickOptions
                {
                    FileTypes = customFileType,
                    PickerTitle = "Select an image file"
                });

                if (result != null)
                {
                    _selectedFilePath = result.FullPath;
                    var stack = (VerticalStackLayout)((Button)sender).Parent;
                    var label = (Label)stack.Children[1];
                    label.Text = result.FileName;
                    label.IsVisible = true;
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
        }

        private async void OnAudioSelectClicked(object sender, EventArgs e)
        {
            try
            {
                var customFileType = new FilePickerFileType(
                    new Dictionary<DevicePlatform, IEnumerable<string>>
                    {
                        { DevicePlatform.iOS, new[] { "public.audio" } },
                        { DevicePlatform.Android, new[] { "audio/*" } },
                        { DevicePlatform.WinUI, new[] { ".mp3", ".wav", ".m4a" } }
                    });

                var result = await FilePicker.Default.PickAsync(new PickOptions
                {
                    PickerTitle = "Please select an audio file",
                    FileTypes = customFileType,
                });

                if (result != null)
                {
                    _selectedFilePath = result.FullPath;
                    var stack = (VerticalStackLayout)((Button)sender).Parent;
                    var label = (Label)stack.Children[1];
                    label.Text = result.FileName;
                    label.IsVisible = true;
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
        }

        private void UpdateFileNameLabel(string fileName)
        {
            var fileSelectionUI = InputContainer.Children.OfType<VerticalStackLayout>().FirstOrDefault();
            var button = fileSelectionUI?.Children.OfType<Button>().FirstOrDefault();
            if (button != null)
            {
                button.Text = fileName;
            }
        }

        private void UpdateOutputVisibility()
        {
            var lastModelKey = _playground.Chain.LastOrDefault();
            if (lastModelKey != null && _playground.Models.TryGetValue(lastModelKey, out var lastModel))
            {
                _isAudioPlayerVisible = lastModel.PipelineTag?.ToLower() == "text-to-speech";
            }
            else
            {
                _isAudioPlayerVisible = false;
            }

            OutputText.IsVisible = !_isJsonViewVisible;
            AudioPlayer.IsVisible = _isAudioPlayerVisible;
        }

        private string FormatJsonString(object data)
        {
            return System.Text.Json.JsonSerializer.Serialize(data, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
        }
    }
}
