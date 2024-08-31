using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using frontend.Models;
using frontend.Services;
using Microsoft.Maui.Controls;
using Microsoft.Maui.Storage;
using System.Text.Json;

namespace frontend.Views
{
    public partial class PlaygroundInferenceView : ContentView
    {
        private readonly Playground _playground;
        private readonly PlaygroundService _playgroundService;
        private bool _isChainLoaded = false;
        private string _selectedFilePath;
        private string _inputText;

        private bool _isJsonViewVisible = false;
        public bool IsJsonViewVisible
        {
            get => _isJsonViewVisible;
            set
            {
                _isJsonViewVisible = value;
                OnPropertyChanged(nameof(IsJsonViewVisible));
            }
        }

        private string _audioSource;
        public string AudioSource
        {
            get => _audioSource;
            set
            {
                _audioSource = value;
                OnPropertyChanged(nameof(AudioSource));
            }
        }

        public bool IsAudioPlayerVisible { get; set; }
        public bool IsOutputTextVisible { get; set; }
        public bool IsProcessedImageVisible { get; set; }

        private string _rawJsonText;
        public string RawJsonText
        {
            get => _rawJsonText;
            set
            {
                _rawJsonText = value;
                OnPropertyChanged(nameof(RawJsonText));
            }
        }

        private string _jsonOutputText;
        public string JsonOutputText
        {
            get => _jsonOutputText;
            set
            {
                _jsonOutputText = value;
                OnPropertyChanged(nameof(JsonOutputText));
            }
        }

        public PlaygroundInferenceView(Playground playground, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playground = playground;
            _playgroundService = playgroundService;
            CreateInputUI();
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
                // Computer Vision Models
                case "object-detection":
                case "image-segmentation":
                case "zero-shot-object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image File"));
                    break;

                // NLP Models
                case "text-classification":
                case "zero-shot-classification":
                case "translation":
                case "text-to-speech":
                case "feature-extraction":
                case "text-generation":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;

                // Audio Models
                case "speech-to-text":
                case "automatic-speech-recognition":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Audio File"));
                    break;

                default:
                    InputContainer.Children.Add(new Label { Text = "Input type not supported for this model." });
                    break;
            }
        }

        private VerticalStackLayout CreateFileSelectionUI(string buttonText)
        {
            var layout = new VerticalStackLayout();
            var button = new Button { Text = buttonText };
            button.Clicked += OnFileSelectClicked;
            layout.Children.Add(button);
            return layout;
        }

        private VerticalStackLayout CreateTextInputUI()
        {
            var layout = new VerticalStackLayout();
            var entry = new Entry { Placeholder = "Enter text here" };
            layout.Children.Add(entry);
            return layout;
        }

        private async void OnFileSelectClicked(object sender, EventArgs e)
        {
            var button = sender as Button;
            if (button == null) return;

            PickOptions pickOptions;
            string pickerTitle;

            if (button.Text.Contains("Image"))
            {
                pickOptions = new PickOptions { FileTypes = FilePickerFileType.Images };
                pickerTitle = "Select an image file";
            }
            else if (button.Text.Contains("Audio"))
            {
                pickOptions = new PickOptions
                {
                    FileTypes = new FilePickerFileType(
                        new Dictionary<DevicePlatform, IEnumerable<string>>
                        {
                            { DevicePlatform.iOS, new[] { "public.audio" } },
                            { DevicePlatform.Android, new[] { "audio/*" } },
                            { DevicePlatform.WinUI, new[] { ".mp3", ".wav", ".m4a" } }
                        })
                };
                pickerTitle = "Select an audio file";
            }
            else
            {
                return;
            }

            pickOptions.PickerTitle = pickerTitle;

            var result = await FilePicker.PickAsync(pickOptions);

            if (result != null)
            {
                UpdateFileNameLabel(Path.GetFileName(result.FullPath));
                _selectedFilePath = result.FullPath;
                button.CommandParameter = result.FullPath;
            }
        }

        private async void OnLoadChainClicked(object sender, EventArgs e)
        {
            if (!_isChainLoaded)
            {
                try
                {
                    var result = await _playgroundService.LoadPlaygroundChain(_playground.PlaygroundId);
                    _isChainLoaded = true;
                    LoadChainButton.Text = "Stop Chain";
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
                    var result = await _playgroundService.StopPlaygroundChain(_playground.PlaygroundId);
                    _isChainLoaded = false;
                    LoadChainButton.Text = "Load Chain";
                    await Application.Current.MainPage.DisplayAlert("Success", "Chain stopped successfully.", "OK");
                }
                catch (Exception ex)
                {
                    await Application.Current.MainPage.DisplayAlert("Error", $"Failed to stop chain: {ex.Message}", "OK");
                }
            }
        }

        private async void OnInferenceClicked(object sender, EventArgs e)
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

                System.Diagnostics.Debug.WriteLine($"Inference Request: {System.Text.Json.JsonSerializer.Serialize(inferenceRequest)}");

                var result = await _playgroundService.Inference(_playground.PlaygroundId, inferenceRequest);

                if (result.TryGetValue("error", out var errorMessage))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", errorMessage.ToString(), "OK");
                }
                else if (result.TryGetValue("data", out var dataValue))
                {
                    RawJsonText = FormatJsonString(dataValue);
                    JsonOutputText = FormatJsonString(dataValue) ?? "No data available.";

                    switch (_playground.Models[_playground.Chain.LastOrDefault()].PipelineTag?.ToLower())
                    {
                        // ------------------------- COMPUTER VISION MODELS -------------------------
                        case "text-to-speech":
                            if (dataValue is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Object)
                            {
                                var audioContentBase64 = jsonElement.GetProperty("audio_content").GetString();
                                if (!string.IsNullOrEmpty(audioContentBase64))
                                {
                                    var audioBytes = Convert.FromBase64String(audioContentBase64);
                                    var tempFilePath = Path.Combine(FileSystem.CacheDirectory, "temp_audio.wav");
                                    await File.WriteAllBytesAsync(tempFilePath, audioBytes);
                                    AudioSource = tempFilePath;
                                    IsAudioPlayerVisible = true;
                                }
                            }
                            break;
                        case "speech-to-text":
                            if (dataValue is JsonElement sttJsonElement && sttJsonElement.ValueKind == JsonValueKind.Object)
                            {
                                var transcription = sttJsonElement.GetProperty("transcription").GetString();
                                OutputText.Text = $"Transcription: {transcription}";
                            }
                            else
                            {
                                OutputText.Text = "Unexpected response format for speech-to-text.";
                            }
                            break;

                        // ------------------------- DEFAULT CASE -------------------------
                        default:
                            OutputText.Text = RawJsonText;
                            break;
                    }

                    UpdateOutputVisibility();
                }
                else
                {
                    HandleTextOutput(result);
                }
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HttpRequestException: {ex.Message}");
                if (ex.InnerException != null)
                {
                    System.Diagnostics.Debug.WriteLine($"Inner Exception: {ex.InnerException.Message}");
                }
                await Application.Current.MainPage.DisplayAlert("Network Error", $"Network error occurred: {ex.Message}", "OK");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Exception in OnInferenceClicked: {ex}");
                await Application.Current.MainPage.DisplayAlert("Error", $"Inference failed: {ex.Message}", "OK");
            }
        }

        private Dictionary<string, object> GetInputData()
        {
            var firstModelKey = _playground.Chain.FirstOrDefault();
            if (firstModelKey == null || !_playground.Models.TryGetValue(firstModelKey, out var firstModel))
            {
                return new Dictionary<string, object>();
            }

            // Define the input data object
            Dictionary<string, object> inputData = new Dictionary<string, object>();

            // Prepare the input based on the model type
            switch (firstModel.PipelineTag?.ToLower())
            {
                case "object-detection":
                case "image-segmentation":
                    if (string.IsNullOrEmpty(_selectedFilePath))
                    {
                        throw new InvalidOperationException("Please select an image file.");
                    }
                    inputData["image_path"] = _selectedFilePath;
                    break;

                case "zero-shot-object-detection":
                    if (string.IsNullOrEmpty(_selectedFilePath) || string.IsNullOrEmpty(_inputText))
                    {
                        throw new InvalidOperationException("Please select an image file and enter text.");
                    }
                    inputData["payload"] = new { image = _selectedFilePath, text = _inputText.Split(',').Select(t => t.Trim()).ToList() };
                    break;

                case "text-generation":
                case "text-to-speech":
                case "translation":
                case "text-classification":
                case "feature-extraction":
                    if (string.IsNullOrWhiteSpace(_inputText))
                    {
                        throw new InvalidOperationException("Please enter text input.");
                    }
                    inputData["text"] = _inputText;
                    break;

                case "speech-to-text":
                case "automatic-speech-recognition":
                    if (string.IsNullOrEmpty(_selectedFilePath))
                    {
                        throw new InvalidOperationException("Please select an audio file.");
                    }
                    inputData["audio_path"] = _selectedFilePath;
                    break;

                default:
                    throw new ArgumentException("Unsupported model type for inference.");
            }

            return inputData; // Return the inputData directly, without wrapping it in another dictionary
        }

        private void HandleTextOutput(Dictionary<string, object> result)
        {
            string outputText;
            if (result.TryGetValue("data", out var dataObject) && dataObject is Dictionary<string, object> data)
            {
                outputText = System.Text.Json.JsonSerializer.Serialize(data, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            }
            else
            {
                outputText = System.Text.Json.JsonSerializer.Serialize(result, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            }
            OutputText.Text = outputText;
            IsOutputTextVisible = true;
            IsAudioPlayerVisible = false;
            IsProcessedImageVisible = false;
            UpdateOutputVisibility();
        }

        private async Task HandleAudioOutput(Dictionary<string, object> result)
        {
            if (result.TryGetValue("data", out var dataObject) && dataObject is Dictionary<string, object> data)
            {
                if (data.TryGetValue("audio_content", out var audioContent) && audioContent is string audioContentBase64)
                {
                    try
                    {
                        var audioBytes = Convert.FromBase64String(audioContentBase64);
                        var tempFilePath = Path.Combine(FileSystem.CacheDirectory, "temp_audio.wav");
                        await File.WriteAllBytesAsync(tempFilePath, audioBytes);

                        AudioSource = tempFilePath;
                        IsAudioPlayerVisible = true;
                        IsOutputTextVisible = false;
                        IsProcessedImageVisible = false;
                        UpdateOutputVisibility();
                    }
                    catch (Exception ex)
                    {
                        await Application.Current.MainPage.DisplayAlert("Error", $"Failed to process audio: {ex.Message}", "OK");
                        HandleTextOutput(result);
                    }
                }
                else
                {
                    HandleTextOutput(result);
                }
            }
            else
            {
                HandleTextOutput(result);
            }
        }

        private void HandleImageOutput(Dictionary<string, object> result)
        {
            // Implement image processing logic here
            // For now, we'll just display the JSON
            string outputText = System.Text.Json.JsonSerializer.Serialize(result, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            OutputText.Text = outputText;
            IsOutputTextVisible = true;
            IsAudioPlayerVisible = false;
            IsProcessedImageVisible = false;
            UpdateOutputVisibility();
        }

        private void UpdateOutputVisibility()
        {
            OutputText.IsVisible = IsOutputTextVisible && !IsJsonViewVisible;
            AudioPlayer.IsVisible = IsAudioPlayerVisible;
            // Implement ProcessedImage visibility when you add image processing
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

        public void ToggleJsonView()
        {
            IsJsonViewVisible = !IsJsonViewVisible;
            UpdateOutputVisibility();
        }

        private void OnJsonViewToggled(object sender, ToggledEventArgs e)
        {
            ToggleJsonView();
        }

        private string FormatJsonString(object data)
        {
            return System.Text.Json.JsonSerializer.Serialize(data, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
        }

        private async Task ViewImageOutput(Dictionary<string, object> result)
        {
            // Implement image processing logic here
            // For now, we'll just display the JSON
            string outputText = System.Text.Json.JsonSerializer.Serialize(result, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            OutputText.Text = outputText;
            IsOutputTextVisible = true;
            IsAudioPlayerVisible = false;
            IsProcessedImageVisible = false;
            UpdateOutputVisibility();
        }

        private (object, object) FormatTranslationInput(string inputText)
        {
            // Implement translation input formatting logic here
            return (inputText, null);
        }

        private string FormatTranslationOutput(object dataValue, object originalStructure)
        {
            // Implement translation output formatting logic here
            return dataValue.ToString();
        }
    }
}