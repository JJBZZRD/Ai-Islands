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
using Plugin.Maui.Audio;

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

        private const string AUDIO_FILE_PATH = "Resources/Audio/Output.wav";

        private bool _isAudioPlayerVisible;
        public bool IsAudioPlayerVisible
        {
            get => _isAudioPlayerVisible;
            set { SetProperty(ref _isAudioPlayerVisible, value); }
        }

        private bool _isNewAudioAvailable;
        public bool IsNewAudioAvailable
        {
            get => _isNewAudioAvailable;
            set { SetProperty(ref _isNewAudioAvailable, value); }
        }

        private string _audioFilePath;
        public string AudioFilePath
        {
            get => _audioFilePath;
            set { SetProperty(ref _audioFilePath, value); }
        }

        private bool _isJsonOutputVisible = true;
        public bool IsJsonOutputVisible
        {
            get => _isJsonOutputVisible;
            set { SetProperty(ref _isJsonOutputVisible, value); }
        }

        private bool _isAudioOutputAvailable;
        public bool IsAudioOutputAvailable
        {
            get => _isAudioOutputAvailable;
            set { SetProperty(ref _isAudioOutputAvailable, value); }
        }

        public string ToggleOutputButtonText => IsJsonOutputVisible ? "View Audio Player" : "View JSON Output";

        private IAudioPlayer _audioPlayer;
        private readonly IAudioManager _audioManager;

        private bool _isPlaying;
        public bool IsPlaying
        {
            get => _isPlaying;
            set
            {
                if (SetProperty(ref _isPlaying, value))
                {
                    OnPropertyChanged(nameof(AudioButtonText));
                }
            }
        }

        private string _audioButtonText = "Play";
        public string AudioButtonText
        {
            get => _audioButtonText;
            set { SetProperty(ref _audioButtonText, value); }
        }

        public InferenceViewModel(Model model, ModelService modelService, IAudioManager audioManager)
        {
            _model = model;
            _modelService = modelService;
            ChatHistory = new ObservableCollection<ChatMessage>();
            _audioManager = audioManager;
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
                    case "text-to-speech":
                        data = new { payload = InputText };
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


                    default:
                        throw new ArgumentException("Unsupported model type for inference.");
                }

                Dictionary<string, object> result = await _modelService.Inference(Model.ModelId, data);
                System.Diagnostics.Debug.WriteLine($"Received inference result: {JsonSerializer.Serialize(result)}");

                // ------------------------------------------- OUTPUT FORMAT CASE SWITCH ---------------------------- (See output format section below)

                // Set IsAudioPlayerVisible to false by default
                IsAudioPlayerVisible = false;

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
                            if (dataValue is JsonElement jsonElement)
                            {
                                await HandleTextToSpeechResponse(jsonElement);
                            }
                            else
                            {
                                OutputText = "Invalid text-to-speech result format.";
                                IsAudioPlayerVisible = false;
                                IsAudioOutputAvailable = false;
                            }
                            break;
                            
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

                if (Model.PipelineTag?.ToLower() == "text-to-speech")
                {
                    IsAudioOutputAvailable = true;
                    IsAudioPlayerVisible = true;
                    IsJsonOutputVisible = false;
                }
                else
                {
                    IsAudioOutputAvailable = false;
                    IsAudioPlayerVisible = false;
                    IsJsonOutputVisible = true;
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

        public void ToggleOutputView()
        {
            IsJsonOutputVisible = !IsJsonOutputVisible;
            IsAudioPlayerVisible = !IsJsonOutputVisible;
            OnPropertyChanged(nameof(IsJsonOutputVisible));
            OnPropertyChanged(nameof(IsAudioPlayerVisible));
            OnPropertyChanged(nameof(ToggleOutputButtonText));
        }

        public async Task PlayPauseAudio()
        {
            if (_audioPlayer == null || IsNewAudioAvailable)
            {
                await CreateAudioPlayer();
            }

            if (_audioPlayer != null)
            {
                if (_audioPlayer.IsPlaying)
                {
                    _audioPlayer.Pause();
                    AudioButtonText = "Play";
                }
                else
                {
                    _audioPlayer.Play();
                    AudioButtonText = "Pause";
                }
                IsPlaying = _audioPlayer.IsPlaying;
            }
            else
            {
                System.Diagnostics.Debug.WriteLine("Audio player is null");
            }
        }

        private async Task HandleTextToSpeechResponse(JsonElement dataValue)
        {
            if (dataValue.TryGetProperty("audio_path", out var audioPathElement))
            {
                string apiAudioPath = audioPathElement.GetString();
                System.Diagnostics.Debug.WriteLine($"API audio path: {apiAudioPath}");

                try
                {
                    string fileName = Path.GetFileName(apiAudioPath);
                    string[] possiblePaths = new[]
                    {
                        Path.Combine(FileSystem.AppDataDirectory, fileName),
                        Path.Combine(FileSystem.CacheDirectory, fileName),
                        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), fileName),
                        Path.Combine(AppDomain.CurrentDomain.BaseDirectory, apiAudioPath)
                    };

                    string audioFilePath = possiblePaths.FirstOrDefault(File.Exists);

                    if (!string.IsNullOrEmpty(audioFilePath))
                    {
                        AudioFilePath = audioFilePath;
                        System.Diagnostics.Debug.WriteLine($"Audio file found at: {AudioFilePath}");

                        IsNewAudioAvailable = true;
                        IsAudioPlayerVisible = true;
                        IsAudioOutputAvailable = true;
                        OutputText = FormatJsonString(dataValue);

                        await CreateAudioPlayer();
                    }
                    else
                    {
                        HandleAudioError($"Audio file not found. Checked paths: {string.Join(", ", possiblePaths)}");
                    }
                }
                catch (Exception ex)
                {
                    HandleAudioError($"Error handling audio file: {ex.Message}");
                }
            }
            else
            {
                HandleAudioError("Audio path is missing from the response");
            }
        }

        private async Task CreateAudioPlayer()
        {
            if (_audioManager != null && !string.IsNullOrEmpty(AudioFilePath))
            {
                try
                {
                    System.Diagnostics.Debug.WriteLine($"Attempting to load audio file: {AudioFilePath}");
                    System.Diagnostics.Debug.WriteLine($"File exists: {File.Exists(AudioFilePath)}");

                    if (!File.Exists(AudioFilePath))
                    {
                        throw new FileNotFoundException($"Audio file not found at {AudioFilePath}");
                    }

                    var fileInfo = new FileInfo(AudioFilePath);
                    System.Diagnostics.Debug.WriteLine($"Audio file size: {fileInfo.Length} bytes");

                    if (fileInfo.Length == 0)
                    {
                        throw new InvalidOperationException("Audio file is empty");
                    }

                    byte[] fileHeader = new byte[12];
                    using (var fileStream = File.OpenRead(AudioFilePath))
                    {
                        await fileStream.ReadAsync(fileHeader, 0, 12);
                    }
                    System.Diagnostics.Debug.WriteLine($"File header: {BitConverter.ToString(fileHeader)}");

                    _audioPlayer?.Dispose();
                    _audioPlayer = _audioManager.CreatePlayer(AudioFilePath);
                    IsNewAudioAvailable = false;

                    System.Diagnostics.Debug.WriteLine("Audio player created successfully");

                    _audioPlayer.Volume = 1.0;
                    System.Diagnostics.Debug.WriteLine($"Audio duration: {_audioPlayer.Duration} seconds");

                    if (_audioPlayer.Duration == 0)
                    {
                        System.Diagnostics.Debug.WriteLine("Warning: Audio duration is 0 seconds");
                    }

                    var playbackTask = Task.Run(async () =>
                    {
                        _audioPlayer.Play();
                        AudioButtonText = "Pause";
                        IsPlaying = true;
                        System.Diagnostics.Debug.WriteLine("Audio playback started");

                        var startTime = DateTime.Now;
                        var lastPosition = -1.0;
                        var samePositionCount = 0;
                        while (_audioPlayer.IsPlaying)
                        {
                            await Task.Delay(100);
                            var elapsed = (DateTime.Now - startTime).TotalSeconds;
                            var currentPosition = _audioPlayer.CurrentPosition;
                            System.Diagnostics.Debug.WriteLine($"Audio is playing. Elapsed time: {elapsed:F2} seconds, Current position: {currentPosition:F2}");

                            if (Math.Abs(currentPosition - lastPosition) < 0.001)
                            {
                                samePositionCount++;
                                if (samePositionCount > 50) // 5 seconds of no progress
                                {
                                    System.Diagnostics.Debug.WriteLine("Audio playback seems to be stuck. Stopping.");
                                    _audioPlayer.Stop();
                                    break;
                                }
                            }
                            else
                            {
                                samePositionCount = 0;
                            }
                            lastPosition = currentPosition;
                        }

                        var totalPlayTime = (DateTime.Now - startTime).TotalSeconds;
                        System.Diagnostics.Debug.WriteLine($"Audio playback finished. Total play time: {totalPlayTime:F2} seconds");
                    });

                    await Task.WhenAny(playbackTask, Task.Delay(TimeSpan.FromSeconds(30)));

                    if (_audioPlayer.IsPlaying)
                    {
                        System.Diagnostics.Debug.WriteLine("Audio playback timed out after 30 seconds");
                        _audioPlayer.Stop();
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Error in CreateAudioPlayer: {ex}");
                    await Application.Current.MainPage.DisplayAlert("Error", $"Unable to load audio: {ex.Message}", "OK");
                }
            }
        }

        private void HandleAudioError(string errorMessage)
        {
            System.Diagnostics.Debug.WriteLine(errorMessage);
            IsAudioPlayerVisible = false;
            IsAudioOutputAvailable = false;
            OutputText = $"Error: {errorMessage}";
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
                            var predictionJson = System.Text.Encoding.UTF8.GetString(buffer, 0, response.Count);
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

    