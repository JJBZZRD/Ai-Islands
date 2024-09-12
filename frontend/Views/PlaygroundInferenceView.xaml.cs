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
using System.ComponentModel;
using System.Text.Json;
using Microsoft.Maui.Storage;
using System.Text;
using System.Runtime.CompilerServices;

namespace frontend.Views
{
    public partial class PlaygroundInferenceView : ContentView, INotifyPropertyChanged
    {
        private readonly Playground _playground;
        private readonly PlaygroundService _playgroundService;
        private readonly ModelService _modelService;
        private bool _isChainLoaded = false;
        private string _inputText;
        private bool _isJsonViewVisible = false;
        private bool _isAudioPlayerVisible = false;
        private string _jsonOutputText = "No data available. Please run inference first.";
        private string _formattedOutputText = "No data available. Please run inference first.";
        private string _selectedFilePath;

        public string SelectedFilePath
        {
            get => _selectedFilePath;
            set { SetProperty(ref _selectedFilePath, value); }
        }

        public ICommand LoadChainCommand { get; }
        public ICommand InferenceCommand { get; }

        private bool _isPreviewImageVisible;
        public bool IsPreviewImageVisible
        {
            get => _isPreviewImageVisible;
            set => SetProperty(ref _isPreviewImageVisible, value);
        }

        private bool _isPreviewVideoVisible;
        public bool IsPreviewVideoVisible
        {
            get => _isPreviewVideoVisible;
            set => SetProperty(ref _isPreviewVideoVisible, value);
        }

        private ImageSource _previewImageSource;
        public ImageSource PreviewImageSource
        {
            get => _previewImageSource;
            set => SetProperty(ref _previewImageSource, value);
        }

        private string _previewVideoSource;
        public string PreviewVideoSource
        {
            get => _previewVideoSource;
            set => SetProperty(ref _previewVideoSource, value);
        }

        public PlaygroundInferenceView(Playground playground, PlaygroundService playgroundService, ModelService modelService)
        {
            InitializeComponent();
            _playground = playground;
            _playgroundService = playgroundService;
            _modelService = modelService ?? throw new ArgumentNullException(nameof(modelService), "ModelService cannot be null.");
            LoadChainCommand = new Command(async () => await LoadOrStopChain());
            InferenceCommand = new Command(async () => await RunInference());
            BindingContext = this;
            CreateInputUI();

            ((App)Application.Current).RegisterView(this);

            // Initialize chain state based on model states
            InitializeChainState();

            UpdateButtonState();
            UpdateOutputVisibility();
        }

        private async void InitializeChainState()
        {
            bool allModelsUnloaded = true;

            foreach (var modelId in _playground.Chain)
            {
                if (_playground.Models.TryGetValue(modelId, out var model))
                {
                    // Check if any model in the chain is loaded
                    if (await _modelService.IsModelLoaded(modelId))
                    {
                        allModelsUnloaded = false;
                        break;
                    }
                }
            }

            // If all models are unloaded, set IsChainLoaded to false
            IsChainLoaded = !allModelsUnloaded;
            Preferences.Set($"{_playground.PlaygroundId}_isChainLoaded", IsChainLoaded);
        }

        public bool IsChainLoaded
        {
            get => _isChainLoaded;
            set
            {
                if (_isChainLoaded != value)
                {
                    _isChainLoaded = value;
                    OnPropertyChanged(nameof(IsChainLoaded));
                    OnPropertyChanged(nameof(ChainButtonText));
                    UpdateButtonState();
                }
            }
        }

        private void UpdateButtonState()
        {
            OnPropertyChanged(nameof(ChainButtonText));
        }

        public string ChainButtonText => IsChainLoaded ? "Stop Chain" : "Load Chain";

        private ImageSource _processedImageSource;
        public ImageSource ProcessedImageSource
        {
            get => _processedImageSource;
            set => SetProperty(ref _processedImageSource, value);
        }

        private bool _isProcessedImageVisible;
        public bool IsProcessedImageVisible
        {
            get => _isProcessedImageVisible;
            set => SetProperty(ref _isProcessedImageVisible, value);
        }

        private string _rawJsonText;
        public string RawJsonText
        {
            get => _rawJsonText;
            set => SetProperty(ref _rawJsonText, value);
        }

        public bool IsJsonViewVisible
        {
            get => _isJsonViewVisible;
            set
            {
                if (_isJsonViewVisible != value)
                {
                    _isJsonViewVisible = value;
                    OnPropertyChanged(nameof(IsJsonViewVisible));
                    OnPropertyChanged(nameof(IsOutputTextVisible));
                    UpdateOutputVisibility();
                }
            }
        }

        public bool IsOutputTextVisible => !_isJsonViewVisible && !_isAudioPlayerVisible;

        public string JsonOutputText
        {
            get => _jsonOutputText;
            set
            {
                if (_jsonOutputText != value)
                {
                    _jsonOutputText = value;
                    OnPropertyChanged(nameof(JsonOutputText));
                }
            }
        }

        public string FormattedOutputText
        {
            get => _formattedOutputText;
            set
            {
                _formattedOutputText = value;
                OnPropertyChanged(nameof(FormattedOutputText));
            }
        }

        public bool IsAudioPlayerVisible
        {
            get => _isAudioPlayerVisible;
            set
            {
                if (_isAudioPlayerVisible != value)
                {
                    _isAudioPlayerVisible = value;
                    OnPropertyChanged();
                }
            }
        }

        private async Task LoadOrStopChain()
        {
            var app = (App)Application.Current;

            if (!IsChainLoaded)
            {
                try
                {
                    await _playgroundService.LoadPlaygroundChain(_playground.PlaygroundId);
                    IsChainLoaded = true;
                    Preferences.Set($"{_playground.PlaygroundId}_isChainLoaded", true);

                    app.AddLoadedChain(_playground.PlaygroundId);

                    foreach (var modelId in _playground.Chain)
                    {
                        if (_playground.Models.TryGetValue(modelId, out var model))
                        {
                            model.IsLoaded = true;
                        }
                    }

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
                    IsChainLoaded = false;
                    Preferences.Set($"{_playground.PlaygroundId}_isChainLoaded", false);

                    // Mark chain as unloaded in the app
                    app.RemoveLoadedChain(_playground.PlaygroundId);

                    foreach (var modelId in _playground.Chain)
                    {
                        if (_playground.Models.TryGetValue(modelId, out var model))
                        {
                            model.IsLoaded = false;
                        }
                    }

                    await Application.Current.MainPage.DisplayAlert("Success", "Chain stopped successfully.", "OK");
                }
                catch (Exception ex)
                {
                    await Application.Current.MainPage.DisplayAlert("Error", $"Failed to stop chain: {ex.Message}", "OK");
                }
            }

            UpdateOutputVisibility();
        }

        private async Task RunInference()
        {
            System.Diagnostics.Debug.WriteLine("RunInference called.");
            if (!IsChainLoaded)
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
                    RawJsonText = FormatJsonString(dataValue);
                    JsonOutputText = FormatJsonString(dataValue) ?? "No data available.";
                    await HandleInferenceResult(dataValue);
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Inference failed: {ex.Message}", "OK");
            }
        }

        private async Task HandleInferenceResult(object dataValue)
        {
            var lastModelId = _playground.Chain.LastOrDefault();
            var pipelineTag = _playground.Models[lastModelId]?.PipelineTag?.ToLower();

            switch (pipelineTag)
            {
                // Computer Vision Models
                case "object-detection":
                case "image-segmentation":
                case "zero-shot-object-detection":
                    await ViewImageOutput();
                    break;

                // NLP Models
                case "translation":
                    FormattedOutputText = FormatTranslationOutput(dataValue, GetOriginalStructure());
                    break;
                case "text-to-speech":
                    await HandleAudioOutput(dataValue);
                    break;
                case "speech-to-text":
                case "automatic-speech-recognition":
                    if (dataValue is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Object)
                    {
                        var transcription = jsonElement.GetProperty("text").GetString();
                        FormattedOutputText = transcription;
                    }
                    else
                    {
                        FormattedOutputText = "Unexpected response format.";
                    }
                    break;
                case "text-classification":
                    FormattedOutputText = FormatTextClassificationOutput(dataValue);
                    break;

                // Text Generation Models (LLMs)
                case "text-generation":
                    FormattedOutputText = dataValue.ToString();
                    break;

                default:
                    FormattedOutputText = JsonSerializer.Serialize(dataValue, new JsonSerializerOptions { WriteIndented = true });
                    break;
            }

            JsonOutputText = JsonSerializer.Serialize(dataValue, new JsonSerializerOptions { WriteIndented = true });

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

                    AudioPlayer.Source = tempFilePath;
                    IsAudioPlayerVisible = true;

                }
            }
        }

        private List<string> GetOriginalStructure()
        {
            return _inputText?.Split('\n').ToList() ?? new List<string>();
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
                        { DevicePlatform.iOS, new[] { "public.image", "public.movie" } },
                        { DevicePlatform.Android, new[] { "image/*", "video/*" } },
                        { DevicePlatform.WinUI, new[] { ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".wmv", ".avi" } }
                    });

                var result = await FilePicker.PickAsync(new PickOptions
                {
                    FileTypes = customFileType,
                    PickerTitle = "Select an image or video file"
                });

                if (result != null)
                {
                    _selectedFilePath = result.FullPath;
                    var stack = (VerticalStackLayout)((Button)sender).Parent;
                    var label = (Label)stack.Children[1];
                    label.Text = result.FileName;
                    label.IsVisible = true;

                    await UpdatePreview(_selectedFilePath);
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

        public void UpdateOutputVisibility()
        {
            if (_isAudioPlayerVisible)
            {
                AudioPlayer.IsVisible = true;
                JsonOutputLabel.IsVisible = false;
                FormattedOutputLabel.IsVisible = false;
                ProcessedImage.IsVisible = false;
            }
            else if (_isJsonViewVisible)
            {
                AudioPlayer.IsVisible = false;
                JsonOutputLabel.IsVisible = true;
                FormattedOutputLabel.IsVisible = false;
                ProcessedImage.IsVisible = false;
            }
            else if (_isProcessedImageVisible)
            {
                AudioPlayer.IsVisible = false;
                JsonOutputLabel.IsVisible = false;
                FormattedOutputLabel.IsVisible = false;
                ProcessedImage.IsVisible = true;
            }
            else
            {
                AudioPlayer.IsVisible = false;
                JsonOutputLabel.IsVisible = false;
                FormattedOutputLabel.IsVisible = true;
                ProcessedImage.IsVisible = false;
            }
        }

        private string FormatJsonString(object data)
        {
            return System.Text.Json.JsonSerializer.Serialize(data, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
        }

        private string FormatOutputText(string text)
        {
            if (string.IsNullOrEmpty(text)) return text;

            text = text.Replace("\\n", "\n");
            text = System.Text.RegularExpressions.Regex.Replace(text, @"\*\*(.*?)\*\*", "<Span FontAttributes=\"Bold\">$1</Span>");
            text = System.Text.RegularExpressions.Regex.Replace(text, @"(\d+)\. ", match =>
                $"<Span FontAttributes=\"Bold\">{match.Groups[1].Value}. </Span>");

            return text;
        }

        private string FormatTextClassificationOutput(object dataValue)
        {
            if (dataValue == null || !(dataValue is JsonElement jsonElement))
                return "No data available.";

            var sb = new StringBuilder();

            if (jsonElement.TryGetProperty("sentiment", out var sentiment))
                sb.AppendLine($"Sentiment: {FormatSentiment(sentiment)}");

            if (jsonElement.TryGetProperty("emotion", out var emotion))
                sb.AppendLine($"Emotion: {FormatEmotion(emotion)}");

            if (jsonElement.TryGetProperty("entities", out var entities))
                sb.AppendLine($"Entities: {FormatEntities(entities)}");

            if (jsonElement.TryGetProperty("keywords", out var keywords))
                sb.AppendLine($"Keywords: {FormatKeywords(keywords)}");

            if (jsonElement.TryGetProperty("categories", out var categories))
                sb.AppendLine($"Categories: {FormatCategories(categories)}");

            if (jsonElement.TryGetProperty("concepts", out var concepts))
                sb.AppendLine($"Concepts: {FormatConcepts(concepts)}");

            if (jsonElement.TryGetProperty("relations", out var relations))
                sb.AppendLine($"Relations: {FormatRelations(relations)}");

            if (jsonElement.TryGetProperty("semantic_roles", out var semanticRoles))
                sb.AppendLine($"Semantic Roles: {FormatSemanticRoles(semanticRoles)}");

            return sb.ToString().TrimEnd();
        }

        private string FormatSentiment(JsonElement sentiment) =>
            sentiment.TryGetProperty("document", out var doc) && doc.TryGetProperty("label", out var label)
            ? label.GetString()
            : "N/A";

        private string FormatEmotion(JsonElement emotion) =>
            emotion.TryGetProperty("document", out var doc) && doc.TryGetProperty("emotion", out var emo)
            ? string.Join(", ", emo.EnumerateObject().OrderByDescending(p => p.Value.GetDouble()).Take(2).Select(p => $"{p.Name} ({p.Value.GetDouble():F2})"))
            : "N/A";

        private string FormatEntities(JsonElement entities) =>
            string.Join(", ", entities.EnumerateArray().Take(3).Select(e => e.GetProperty("text").GetString()));

        private string FormatKeywords(JsonElement keywords) =>
            string.Join(", ", keywords.EnumerateArray().Take(3).Select(k => k.GetProperty("text").GetString()));

        private string FormatCategories(JsonElement categories) =>
            string.Join(", ", categories.EnumerateArray().Take(3).Select(c => c.GetProperty("label").GetString().Split('/').Last()));

        private string FormatConcepts(JsonElement concepts) =>
            string.Join(", ", concepts.EnumerateArray().Take(3).Select(c => c.GetProperty("text").GetString()));

        private string FormatRelations(JsonElement relations) =>
            relations.GetArrayLength() > 0 ? "Present" : "None found";

        private string FormatSemanticRoles(JsonElement semanticRoles) =>
            semanticRoles.GetArrayLength() > 0 ? "Present" : "None found";

        private string FormatTranslationOutput(object dataValue, List<string> originalStructure)
        {
            System.Diagnostics.Debug.WriteLine($"FormatTranslationOutput received: {JsonSerializer.Serialize(dataValue)}");

            if (dataValue is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Array)
            {
                var translatedLines = jsonElement.EnumerateArray()
                    .Select(element => element.TryGetProperty("translation_text", out var translationText)
                        ? translationText.GetString()
                        : null)
                    .Where(text => text != null)
                    .ToList();

                System.Diagnostics.Debug.WriteLine($"Extracted Translated Lines: {string.Join(", ", translatedLines)}");

                var result = new List<string>();
                int translationIndex = 0;

                if (originalStructure == null || originalStructure.Count == 0)
                {
                    System.Diagnostics.Debug.WriteLine("Original structure is empty or null.");
                    return "No translation available.";
                }

                foreach (var line in originalStructure)
                {
                    if (string.IsNullOrWhiteSpace(line))
                    {
                        result.Add(string.Empty);
                    }
                    else if (translationIndex < translatedLines.Count)
                    {
                        result.Add(translatedLines[translationIndex]);
                        translationIndex++;
                    }
                    else
                    {
                        result.Add("No translation available for this line.");
                    }
                }

                var formattedResult = string.Join("\n", result);
                System.Diagnostics.Debug.WriteLine($"Formatted translation result: {formattedResult}");
                return formattedResult;
            }

            System.Diagnostics.Debug.WriteLine("Translation data not in expected format");
            return "No translation available.";
        }

        private async Task ViewImageOutput()
        {
            try
            {
                if (string.IsNullOrEmpty(RawJsonText) || string.IsNullOrEmpty(SelectedFilePath))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Please run inference first.", "OK");
                    return;
                }

                var lastModelId = _playground.Chain.LastOrDefault();
                var task = _playground.Models[lastModelId]?.PipelineTag?.ToLower();

                if (task == null)
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Pipeline task is not defined.", "OK");
                    return;
                }

                var result = await _modelService.ProcessImage(SelectedFilePath, RawJsonText, task);
                System.Diagnostics.Debug.WriteLine($"ProcessImage result: {result}");

                var processedImageResult = JsonSerializer.Deserialize<ProcessedImageResult>(result);

                if (processedImageResult?.ImageUrl == null)
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Failed to process image. The ImageUrl is null.", "OK");
                    return;
                }

                string imageFullPath = processedImageResult.ImageUrl;

                if (!File.Exists(imageFullPath))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", $"Image file not found: {imageFullPath}", "OK");
                    return;
                }

                ProcessedImageSource = ImageSource.FromFile(imageFullPath);
                IsProcessedImageVisible = true;
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
                System.Diagnostics.Debug.WriteLine($"Detailed error: {ex}");
            }
        }

        private async Task UpdatePreview(string filePath)
        {
            IsPreviewImageVisible = false;
            IsPreviewVideoVisible = false;

            if (IsImageFile(filePath))
            {
                PreviewImageSource = ImageSource.FromFile(filePath);
                IsPreviewImageVisible = true;
            }
            else if (IsVideoFile(filePath))
            {
                PreviewVideoSource = filePath;
                IsPreviewVideoVisible = true;
            }
        }

        private bool IsImageFile(string filePath)
        {
            string[] imageExtensions = { ".jpg", ".jpeg", ".png", ".gif" };
            return imageExtensions.Contains(Path.GetExtension(filePath).ToLower());
        }

        private bool IsVideoFile(string filePath)
        {
            string[] videoExtensions = { ".mp4", ".mov", ".wmv", ".avi" };
            return videoExtensions.Contains(Path.GetExtension(filePath).ToLower());
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string propertyName = null)
        {
            if (EqualityComparer<T>.Default.Equals(field, value)) return false;
            field = value;
            OnPropertyChanged(propertyName);
            return true;
        }
    }
}
