using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading.Tasks;
using frontend.Models;
using frontend.Services;
using Microsoft.Maui.Controls;
using System.Linq;
using System.Text.Json.Serialization;
using frontend.Views;
using System.Net.WebSockets;
using System.Threading;
using System.Text;
using OpenCvSharp;
using CommunityToolkit.Maui.Views;
using CommunityToolkit.Maui.Core.Primitives;

namespace frontend.Models.ViewModels
{
    public class InferenceViewModel : INotifyPropertyChanged
    {
        private ImagePopupView _imagePopUp;
        private readonly ModelService _modelService;
        private Model _model;
        public Model Model
        {
            get => _model;
            set { SetProperty(ref _model, value); }
        }

        private string _inputText;
        public string InputText
        {
            get => _inputText;
            set 
            {
                // Normalize line endings
                // var normalizedText = value?.Replace("\r\n", "\n").Replace("\r", "\n");
                // SetProperty(ref _inputText, normalizedText);

                // No normalization - we can use the method NormalizeLineEndings below in the format section...
                SetProperty(ref _inputText, value); 
            }
        }

        private string _outputText;
        public string OutputText
        {
            get => _outputText;
            set { SetProperty(ref _outputText, FormatOutputText(value)); }
        }

        private string _selectedFilePath;
        public string SelectedFilePath
        {
            get => _selectedFilePath;
            set { SetProperty(ref _selectedFilePath, value); }
        }

        private string _rawJsonText;
        public string RawJsonText
        {
            get => _rawJsonText;
            set { SetProperty(ref _rawJsonText, value); }
        }

        private bool _isViewImageOutputButtonVisible;
        public bool IsViewImageOutputButtonVisible
        {
            get => _isViewImageOutputButtonVisible;
            set { SetProperty(ref _isViewImageOutputButtonVisible, value); }
        }

        private bool _isOutputTextVisible;
        public bool IsOutputTextVisible
        {
            get => _isOutputTextVisible;
            set { SetProperty(ref _isOutputTextVisible, value); }
        }

        private bool _isChatHistoryVisible;
        public bool IsChatHistoryVisible
        {
            get => _isChatHistoryVisible;
            set { SetProperty(ref _isChatHistoryVisible, value); }
        }

        private bool _isChatbotVisible;
        public bool IsChatbotVisible
        {
            get => _isChatbotVisible;
            set { SetProperty(ref _isChatbotVisible, value); }
        }

        private bool _isInputFrameVisible;
        public bool IsInputFrameVisible
        {
            get => _isInputFrameVisible;
            set { SetProperty(ref _isInputFrameVisible, value); }
        }

        private bool _isOutputFrameVisible;
        public bool IsOutputFrameVisible
        {
            get => _isOutputFrameVisible;
            set { SetProperty(ref _isOutputFrameVisible, value); }
        }

        private bool _isRunInferenceButtonVisible;
        public bool IsRunInferenceButtonVisible
        {
            get => _isRunInferenceButtonVisible;
            set { SetProperty(ref _isRunInferenceButtonVisible, value); }
        }

        private ObservableCollection<ChatMessage> _chatHistory;
        public ObservableCollection<ChatMessage> ChatHistory
        {
            get => _chatHistory;
            set { SetProperty(ref _chatHistory, value); }
        }

        // Add these properties
        private bool _isAudioPlayerVisible;
        public bool IsAudioPlayerVisible
        {
            get => _isAudioPlayerVisible;
            set
            {
                _isAudioPlayerVisible = value;
                OnPropertyChanged();
            }
        }

        private string _audioSource;
        public string AudioSource
        {
            get => _audioSource;
            set
            {
                _audioSource = value;
                OnPropertyChanged();
            }
        }

        private string _playPauseButtonText = "Play";
        public string PlayPauseButtonText
        {
            get => _playPauseButtonText;
            set
            {
                _playPauseButtonText = value;
                OnPropertyChanged();
            }
        }

        private MediaElement _audioPlayer;

        public InferenceViewModel(Model model, ModelService modelService, MediaElement audioPlayer)
        {
            _model = model;
            _modelService = modelService;
            ChatHistory = new ObservableCollection<ChatMessage>();
            _audioPlayer = audioPlayer;
        }

        public async Task<bool> SelectFile(string fileType)
        {
            try
            {
                FilePickerFileType customFileType;
                string pickerTitle;

                switch (fileType.ToLower())
                {
                    case "image_or_video":
                        customFileType = new FilePickerFileType(
                            new Dictionary<DevicePlatform, IEnumerable<string>>
                            {
                                { DevicePlatform.iOS, new[] { "public.image", "public.movie" } },
                                { DevicePlatform.Android, new[] { "image/*", "video/*" } },
                                { DevicePlatform.WinUI, new[] { ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".wmv" } }
                            });
                        pickerTitle = "Select an image or video file";
                        break;
                    case "image":
                        customFileType = new FilePickerFileType(
                            new Dictionary<DevicePlatform, IEnumerable<string>>
                            {
                                { DevicePlatform.iOS, new[] { "public.jpeg", "public.png" } },
                                { DevicePlatform.Android, new[] { "image/jpeg", "image/png" } },
                                { DevicePlatform.WinUI, new[] { ".jpg", ".jpeg", ".png" } }
                            });
                        pickerTitle = "Select an image file";
                        break;
                    case "audio":
                        customFileType = new FilePickerFileType(
                            new Dictionary<DevicePlatform, IEnumerable<string>>
                            {
                                { DevicePlatform.iOS, new[] { "public.audio" } },
                                { DevicePlatform.Android, new[] { "audio/*" } },
                                { DevicePlatform.WinUI, new[] { ".mp3", ".wav", ".m4a" } }
                            });
                        pickerTitle = "Please select an audio file";
                        break;
                    default:
                        throw new ArgumentException("Invalid file type specified");
                }

                var result = await FilePicker.PickAsync(new PickOptions
                {
                    FileTypes = customFileType,
                    PickerTitle = pickerTitle
                });

                if (result != null)
                {
                    SelectedFilePath = result.FullPath;
                    return true;
                }
                return false;
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
                return false;
            }
        }

        public async Task RunInference()
        {
            try
            {
                object data;
                switch (Model.PipelineTag?.ToLower())
                {
                    // ------------------------------------------- INPUT FORMAT CASE SWITCH ---------------------------- (See input format section below)
                    
                    // ------------------------- COMPUTER VISION MODELS -------------------------
                    case "object-detection":
                        if (string.IsNullOrEmpty(_selectedFilePath))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an image or video file.", "OK");
                            return;
                        }
                        string[] videoExtensions = { ".mp4", ".mov", ".wmv", ".gif" };
                        if (videoExtensions.Contains(Path.GetExtension(_selectedFilePath).ToLower()))
                        {
                            await RunVideoInference();
                            return;
                        }
                        data = new { image_path = _selectedFilePath };
                        break;
                    case "image-segmentation":
                        if (string.IsNullOrEmpty(_selectedFilePath))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an image file.", "OK");
                            return;
                        }
                        data = new { payload = _selectedFilePath };
                        break;
                    case "zero-shot-object-detection":
                        if (string.IsNullOrEmpty(_selectedFilePath) || string.IsNullOrEmpty(InputText))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an image file and enter text.", "OK");
                            return;
                        }
                        data = new { payload = new { image = _selectedFilePath, text = InputText.Split(',').Select(t => t.Trim()).ToList() } };
                        break;

                    // ------------------------- NLP MODELS -------------------------

                    case "text-classification":
                        data = new { payload = InputText };
                        System.Diagnostics.Debug.WriteLine($"Text classification data: {JsonSerializer.Serialize(data)}");
                        break;
                    case "zero-shot-classification":
                        data = new { text = InputText };
                        break;
                    case "translation":
                        var (translationPayload, originalStructure) = FormatTranslationInput(InputText);
                        data = translationPayload;
                        // Store originalStructure for later use
                        break;

                    // ------------------------- OTHER -------------------------

                    case "feature-extraction":
                        data = new { payload = InputText };
                        System.Diagnostics.Debug.WriteLine($"Text input data: {JsonSerializer.Serialize(data)}");
                        break;

                    // ------------------------- TEXT GENERATION MODELS LLMS -------------------------

                    case "text-generation":
                        data = new { payload = InputText };
                        break;

                    // Add this case for text-to-speech
                    case "text-to-speech":
                        data = new { payload = InputText };
                        break;

                    default:
                        throw new ArgumentException("Unsupported model type for inference.");
                }

                Dictionary<string, object> result = await _modelService.Inference(Model.ModelId, data);
                System.Diagnostics.Debug.WriteLine($"Received inference result: {JsonSerializer.Serialize(result)}");

                // ------------------------------------------- OUTPUT FORMAT CASE SWITCH ---------------------------- (See output format section below)

                if (result.TryGetValue("data", out var dataValue))
                {
                    RawJsonText = FormatJsonString(dataValue);
                    switch (Model.PipelineTag?.ToLower())
                    {
                        case "translation":
                            var (translationPayload, originalStructure) = FormatTranslationInput(InputText);
                            data = translationPayload;
                            // ... (after getting the result)
                            OutputText = FormatTranslationOutput(dataValue, originalStructure);
                            break;
                        case "text-generation":
                            OutputText = dataValue.ToString();
                            break;
                        case "text-to-speech":
                            if (dataValue is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Object)
                            {
                                var audioPath = jsonElement.GetProperty("audio_path").GetString();
                                if (!string.IsNullOrEmpty(audioPath))
                                {
                                    AudioSource = audioPath;
                                    IsAudioPlayerVisible = true;
                                }
                            }
                            break;
                        // ... (handle other cases as needed)
                        default:
                            OutputText = RawJsonText; // If output format not specified, always return raw json
                            break;
                    }
                }
                else
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Invalid result format.", "OK");
                    return;
                }
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HttpRequestException in RunInference: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Inner Exception: {ex.InnerException?.Message}");
                await Application.Current.MainPage.DisplayAlert("Error", $"Network error during inference: {ex.Message}", "OK");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error in RunInference: {ex}");
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred during inference: {ex.Message}", "OK");
            }
        }


        public async Task ViewImageOutput()
        {
            try
            {
                if (string.IsNullOrEmpty(RawJsonText) || string.IsNullOrEmpty(SelectedFilePath))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Please run inference first.", "OK");
                    return;
                }

                string[] videoExtensions = { ".mp4", ".mov", ".wmv", ".gif" };
                if (videoExtensions.Contains(Path.GetExtension(SelectedFilePath).ToLower()))
                {
                    await Application.Current.MainPage.DisplayAlert("Video Visualization", "Video visualization is not currently supported.", "OK");
                    return;
                }

                var task = Model.PipelineTag?.ToLower();
                System.Diagnostics.Debug.WriteLine($"Processing image with task: {task}");
                System.Diagnostics.Debug.WriteLine($"RawJsonText: {RawJsonText}");

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

                var imageSource = ImageSource.FromFile(imageFullPath);

                if (_imagePopUp == null)
                {
                    _imagePopUp = new ImagePopupView();
                    Grid.SetRowSpan(_imagePopUp, 2);
                    Grid.SetColumnSpan(_imagePopUp, 2);
                    if (Application.Current.MainPage is ContentPage contentPage)
                    {
                        ((Grid)contentPage.Content).Children.Add(_imagePopUp);
                    }
                }

                _imagePopUp.SetImage(imageSource);
                _imagePopUp.IsVisible = true;
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
                System.Diagnostics.Debug.WriteLine($"Detailed error: {ex}");
            }
        }

        public async Task SendMessage(string message)
        {
            if (!string.IsNullOrWhiteSpace(message))
            {
                ChatHistory.Add(new ChatMessage { Role = "user", Content = message });

                await SendMessageToChatbot(message);
                
                // Notify the view that the chat history has been updated
                OnPropertyChanged(nameof(ChatHistory));
            }
        }

        public void SetImagePopup(ImagePopupView imagePopup)
        {
            _imagePopUp = imagePopup;
        }

        public void TogglePlayPause()
        {
            if (_audioPlayer.CurrentState == MediaElementState.Playing)
            {
                _audioPlayer.Pause();
                PlayPauseButtonText = "Play";
            }
            else
            {
                _audioPlayer.Play();
                PlayPauseButtonText = "Pause";
            }
        }



        // Private methods -----------------------------------------------------------------------------------------------------

        private async Task RunVideoInference()
        {
            using var videoCapture = new OpenCvSharp.VideoCapture(_selectedFilePath);
            var cts = new CancellationTokenSource();

            try
            {
                var frameInterval = 2; 
                var resizeFactor = 0.5; 

                await _modelService.PredictLive(
                    _model.ModelId,
                    async (webSocket, token) =>
                    {
                        int frameCount = 0;
                        while (!token.IsCancellationRequested)
                        {   
                            using var frame = new OpenCvSharp.Mat();
                            if (!videoCapture.Read(frame))
                                break;

                            frameCount++;
                            if (frameCount % frameInterval != 0)
                                continue;
                            
                            var resizedFrame = frame.Resize(new OpenCvSharp.Size(), resizeFactor, resizeFactor);
                            var jpegData = resizedFrame.ImEncode(".jpg");

                            await webSocket.SendAsync(new ArraySegment<byte>(jpegData), WebSocketMessageType.Binary, true, token);

                            var buffer = new byte[8192];
                            var response = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), token);
                            var predictionJson = Encoding.UTF8.GetString(buffer, 0, response.Count);
                            var prediction = JsonSerializer.Deserialize<Dictionary<string, object>>(predictionJson);
                            
                            Device.BeginInvokeOnMainThread(() =>
                            {
                                var newPrediction = JsonSerializer.Serialize(prediction, new JsonSerializerOptions { WriteIndented = true });
                                OutputText += (string.IsNullOrEmpty(OutputText) ? "" : "\n\n") + newPrediction;
                            });
                        }
                    },
                    cts.Token
                );

                await Application.Current.MainPage.DisplayAlert("Inference Complete", "Video inference has finished.", "OK");
            }
            catch (WebSocketException wsEx)
            {
                Console.WriteLine($"WebSocket error: {wsEx.Message}");
                await Application.Current.MainPage.DisplayAlert("WebSocket Error", $"WebSocket connection failed: {wsEx.Message}", "OK");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Unexpected error: {ex.Message}");
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred during video inference: {ex.Message}", "OK");
            }
            finally
            {
                cts.Cancel();
            }
        }


        private async Task SendMessageToChatbot(string userMessage)
        {
            try
            {
                var data = new { payload = userMessage };
                var result = await _modelService.Inference(Model.ModelId, data);

                System.Diagnostics.Debug.WriteLine($"Raw result: {JsonSerializer.Serialize(result)}");

                if (result.TryGetValue("data", out var dataValue))
                {
                    string assistantMessage;
                    if (dataValue is string stringResponse)
                    {
                        assistantMessage = stringResponse;
                    }
                    else if (dataValue is JsonElement jsonElement)
                    {
                        if (jsonElement.ValueKind == JsonValueKind.String)
                        {
                            assistantMessage = jsonElement.GetString();
                        }
                        else if (jsonElement.ValueKind == JsonValueKind.Object && jsonElement.TryGetProperty("response", out var responseProperty))
                        {
                            assistantMessage = responseProperty.GetString();
                        }
                        else
                        {
                            assistantMessage = $"Unexpected response format: {jsonElement}";
                        }
                    }
                    else if (dataValue is Dictionary<string, object> responseDict)
                    {
                        assistantMessage = responseDict.TryGetValue("response", out var responseValue) 
                            ? responseValue?.ToString() 
                            : $"Unexpected response format: {JsonSerializer.Serialize(responseDict)}";
                    }
                    else
                    {
                        assistantMessage = $"Unexpected data type: {dataValue?.GetType().Name}";
                    }

                    ChatHistory.Add(new ChatMessage { Role = "assistant", Content = assistantMessage });
                    System.Diagnostics.Debug.WriteLine($"Assistant message: {assistantMessage}");
                }
                else
                {
                    var errorMessage = $"Invalid result format. Raw result: {JsonSerializer.Serialize(result)}";
                    ChatHistory.Add(new ChatMessage { Role = "assistant", Content = errorMessage });
                    System.Diagnostics.Debug.WriteLine(errorMessage);
                }
            }
            catch (Exception ex)
            {
                var errorMessage = $"An error occurred: {ex.Message}\nStack trace: {ex.StackTrace}";
                ChatHistory.Add(new ChatMessage { Role = "assistant", Content = errorMessage });
                System.Diagnostics.Debug.WriteLine($"Error in SendMessageToChatbot: {errorMessage}");
            }
        }



        // ------------------------- FORMATTING METHODS ------------------------- (See case switch above in run inference method)

        // INPUT FORMATS
        
        // General methods:

        private string NormalizeLineEndings(string text)
        {
            return text?.Replace("\r\n", "\n").Replace("\r", "\n");
        }

        // Case specific methods:
        private (object payload, List<string> originalStructure) FormatTranslationInput(string inputText)
        {
            var normalizedText = NormalizeLineEndings(inputText);
            var inputLines = normalizedText.Split('\n', StringSplitOptions.None).ToList();
            var nonEmptyLines = inputLines.Where(line => !string.IsNullOrWhiteSpace(line)).ToList();
            return (new { payload = nonEmptyLines }, inputLines);
        }


        // OUTPUT FORMATS

        // General methods:

        private string FormatJsonString(object obj)
        {
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            if (obj is string strValue)
            {
                try
                {
                    var jsonElement = JsonSerializer.Deserialize<JsonElement>(strValue);
                    return JsonSerializer.Serialize(jsonElement, options);
                }
                catch
                {
                    return strValue;
                }
            }
            else
            {
                return JsonSerializer.Serialize(obj, options);
            }
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

        // Case specific methods:


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

                var result = new List<string>();
                int translationIndex = 0;
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
                }

                var formattedResult = string.Join("\n", result);
                System.Diagnostics.Debug.WriteLine($"Formatted translation result: {formattedResult}");
                return formattedResult;
            }
            
            System.Diagnostics.Debug.WriteLine("Translation data not in expected format");
            return "No translation available.";
        }



        // INotifyPropertyChanged implementation ----------------------------------------------------------------------------------


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



    // -------------------------- LOCAL METHODS -------------------------------------------------------------------------------


    public class ChatMessage
    {
        public string Role { get; set; }
        public string Content { get; set; }
        public string FormattedContent => FormatContent(Content);

        private string FormatContent(string text)
        {
            if (string.IsNullOrEmpty(text)) return text;

            text = text.Replace("\\n", "\n");
            text = System.Text.RegularExpressions.Regex.Replace(text, @"\*\*(.*?)\*\*", "<Span FontAttributes=\"Bold\">$1</Span>");
            text = System.Text.RegularExpressions.Regex.Replace(text, @"(\d+)\. ", match => 
                $"<Span FontAttributes=\"Bold\">{match.Groups[1].Value}. </Span>");

            return text;
        }
    }

    public class ProcessedImageResult
    {
        [JsonPropertyName("image_url")]
        public string ImageUrl { get; set; }
    }
}

    