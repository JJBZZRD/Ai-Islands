using System;
using Microsoft.Maui.Controls;
using frontend.Models;
using frontend.Models.ViewModels;
using frontend.Services;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using System.Text.Json;
using System.IO;
using System.Net.Http;
using CommunityToolkit.Maui.Views; 
using CommunityToolkit.Maui;

namespace frontend.Views
{
    public partial class PlaygroundInferenceView : ContentView
    {
        private PlaygroundViewModel _playgroundViewModel;
        private PlaygroundService _playgroundService;
        private string _inputText;
        private string _outputText;
        private string _selectedFilePath;
        private string _rawJsonText;
        private bool _isAudioOutputVisible;
        private bool _isTextOutputVisible = true;
        private string _audioSource;

        public string InputText
        {
            get => _inputText;
            set
            {
                if (_inputText != value)
                {
                    _inputText = value;
                    OnPropertyChanged(nameof(InputText));
                }
            }
        }

        public string OutputText
        {
            get => _outputText;
            set
            {
                if (_outputText != value)
                {
                    _outputText = FormatOutputText(value);
                    OnPropertyChanged(nameof(OutputText));
                }
            }
        }

        public string RawJsonText
        {
            get => _rawJsonText;
            set
            {
                if (_rawJsonText != value)
                {
                    _rawJsonText = value;
                    OnPropertyChanged(nameof(RawJsonText));
                }
            }
        }

        public bool IsAudioOutputVisible
        {
            get => _isAudioOutputVisible;
            set
            {
                if (_isAudioOutputVisible != value)
                {
                    _isAudioOutputVisible = value;
                    OnPropertyChanged(nameof(IsAudioOutputVisible));
                }
            }
        }

        public bool IsTextOutputVisible
        {
            get => _isTextOutputVisible;
            set
            {
                if (_isTextOutputVisible != value)
                {
                    _isTextOutputVisible = value;
                    OnPropertyChanged(nameof(IsTextOutputVisible));
                }
            }
        }

        public string AudioSource
        {
            get => _audioSource;
            set
            {
                if (_audioSource != value)
                {
                    _audioSource = value;
                    OnPropertyChanged(nameof(AudioSource));
                }
            }
        }

        public PlaygroundInferenceView(PlaygroundViewModel playgroundViewModel, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playgroundViewModel = playgroundViewModel;
            _playgroundService = playgroundService;
            BindingContext = this;
            InitializeInputUI();

            // var lastModel = _playgroundViewModel.Playground.Models.Values.LastOrDefault();
            // if (lastModel?.PipelineTag?.ToLower() == "text-to-speech")
            // {
            //     IsAudioOutputVisible = true;
            //     IsTextOutputVisible = false;
            // }
        }

        private void InitializeInputUI()
        {
            if (InputContainer == null)
            {
                System.Diagnostics.Debug.WriteLine("InputContainer is null");
                return;
            }

            var firstModel = _playgroundViewModel.Playground?.Models?.Values.FirstOrDefault();
            if (firstModel == null)
            {
                InputContainer.Children.Add(new Label { Text = "No models available in the playground.", TextColor = Colors.Gray });
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
                case "token-classification":
                case "question-answering":
                case "summarization":
                case "automatic-speech-recognition":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Audio File"));
                    break;
                default:
                    InputContainer.Children.Add(new Label { Text = "Input type not supported for this model.", TextColor = Colors.Gray });
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
                Text = InputText
            };
            editor.TextChanged += (sender, e) => InputText = ((Editor)sender)?.Text ?? string.Empty;
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

        private async void OnLoadChainClicked(object sender, EventArgs e)
        {
            try
            {
                var result = await _playgroundService.LoadPlaygroundChain(_playgroundViewModel.Playground.PlaygroundId);
                System.Diagnostics.Debug.WriteLine($"Load Chain Result: {JsonSerializer.Serialize(result)}");
                await Application.Current.MainPage.DisplayAlert("Success", "Chain loaded successfully.", "OK");
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to load chain: {ex.Message}", "OK");
            }
        }

        private async void OnSubmitForInferenceClicked(object sender, EventArgs e)
        {
            try
            {
                Dictionary<string, object> data;
                var lastModelKey = _playgroundViewModel.Playground.Chain.LastOrDefault();
                var lastModel = _playgroundViewModel.Playground.Models[lastModelKey];

                var firstModelKey = _playgroundViewModel.Playground.Chain.FirstOrDefault();
                if (firstModelKey == null)
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "No models available in the playground.", "OK");
                    return;
                }

                var firstModel = _playgroundViewModel.Playground.Models[firstModelKey];

                // Handle input based on the first model
                switch (firstModel.PipelineTag?.ToLower())
                {
                    case "object-detection":
                    case "image-segmentation":
                        if (string.IsNullOrEmpty(_selectedFilePath))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an image file.", "OK");
                            return;
                        }
                        data = new Dictionary<string, object> { { "image_path", _selectedFilePath } };
                        break;
                    case "zero-shot-object-detection":
                        if (string.IsNullOrEmpty(_selectedFilePath) || string.IsNullOrEmpty(InputText))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an image file and enter text.", "OK");
                            return;
                        }
                        data = new Dictionary<string, object>
                        {
                            { "payload", new Dictionary<string, object>
                                {
                                    { "image", _selectedFilePath },
                                    { "text", InputText.Split(',').Select(t => t.Trim()).ToList() }
                                }
                            }
                        };
                        break;
                    case "text-generation":
                    case "text-to-speech":
                    case "translation":
                        if (string.IsNullOrEmpty(InputText))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please enter text.", "OK");
                            return;
                        }
                        data = new Dictionary<string, object> { { "payload", InputText } };
                        break;
                    default:
                        await Application.Current.MainPage.DisplayAlert("Error", "Unsupported model type for inference.", "OK");
                        return;
                }

                Dictionary<string, object> result = await _playgroundService.Inference(_playgroundViewModel.Playground.PlaygroundId, data);
                if (result.TryGetValue("data", out var dataValue))
                {
                    var lastModelInChain = _playgroundViewModel.Playground.Models.Values.LastOrDefault();
                    if (lastModelInChain?.PipelineTag?.ToLower() == "text-to-speech" && dataValue is Dictionary<string, object> outputData)
                    {
                        if (outputData.TryGetValue("audio_path", out var audioPath) && audioPath is string audioUrl)
                        {
                            IsAudioOutputVisible = true;
                            IsTextOutputVisible = false;
                            AudioSource = audioUrl;
                            OutputText = "Audio generated successfully. Use the player to listen.";
                            RawJsonText = FormatJsonString(outputData);
                            
                            // Trigger audio playback
                            await PlayAudio(audioUrl);
                        }
                        else
                        {
                            IsAudioOutputVisible = false;
                            IsTextOutputVisible = true;
                            OutputText = "Audio generation failed or audio path not found in the response.";
                            RawJsonText = FormatJsonString(outputData);
                        }
                    }
                    else
                    {
                        IsAudioOutputVisible = false;
                        IsTextOutputVisible = true;
                        RawJsonText = FormatJsonString(dataValue);
                        OutputText = FormatOutputText(dataValue.ToString());
                    }
                }
                else
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Invalid result format.", "OK");
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred during inference: {ex.Message}", "OK");
            }
        }

        private async Task PlayAudio(string audioUrl)
        {
            try
            {
                var player = Plugin.SimpleAudioPlayer.CrossSimpleAudioPlayer.Current;
                player.Load(audioUrl);
                player.Play();
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to play audio: {ex.Message}", "OK");
            }
        }

        private string FormatJsonString(object obj)
        {
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };
            return JsonSerializer.Serialize(obj, options);
        }

        private string FormatOutputText(string text)
        {
            if (string.IsNullOrEmpty(text)) return text;
            return text.Replace("\\n", "\n");
        }

        private async void OnDownloadAudioClicked(object sender, EventArgs e)
        {
            try
            {
                if (string.IsNullOrEmpty(_selectedFilePath))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "No audio file available for download.", "OK");
                    return;
                }

                var audioFileUrl = _selectedFilePath;
                var fileName = Path.GetFileName(audioFileUrl);
                var downloadsFolder = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                var targetFile = Path.Combine(downloadsFolder, "Downloads", fileName);

                using (var client = new HttpClient())
                {
                    var response = await client.GetAsync(audioFileUrl);
                    response.EnsureSuccessStatusCode();

                    using (var fileStream = new FileStream(targetFile, FileMode.Create, FileAccess.Write, FileShare.None))
                    {
                        await response.Content.CopyToAsync(fileStream);
                    }
                }

                await Application.Current.MainPage.DisplayAlert("Success", $"Audio file downloaded to:\n{targetFile}", "OK");
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to download audio file: {ex.Message}", "OK");
            }
        }
    }
}
