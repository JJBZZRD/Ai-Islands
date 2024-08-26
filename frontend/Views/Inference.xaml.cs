using System;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.Text.Json;
using frontend.Services;
using Microsoft.Maui.Layouts;
using System.Text.Json.Serialization;
using System.Net.WebSockets;
using System.Threading;
using System.IO;
using System.Text;
using OpenCvSharp;
using System.Collections.ObjectModel;

namespace frontend.Views
{
    public class ProcessedImageResult
    {
        [JsonPropertyName("image_url")]
        public string ImageUrl { get; set; }
    }
    public partial class Inference : ContentView
    {
        private Model _model;
        private string _inputText;
        private string _outputText;
        private string _selectedFilePath;
        private readonly ModelService _modelService;
        private string _rawJsonText;
        private ImagePopupView _imagePopUp;

        private bool _isViewImageOutputButtonVisible;
        public bool IsViewImageOutputButtonVisible
        {
            get => _isViewImageOutputButtonVisible;
            set
            {
                if (_isViewImageOutputButtonVisible != value)
                {
                    _isViewImageOutputButtonVisible = value;
                    OnPropertyChanged(nameof(IsViewImageOutputButtonVisible));
                }
            }
        }

        private bool _isOutputTextVisible = true;
        public bool IsOutputTextVisible
        {
            get => _isOutputTextVisible;
            set
            {
                if (_isOutputTextVisible != value)
                {
                    _isOutputTextVisible = value;
                    OnPropertyChanged(nameof(IsOutputTextVisible));
                }
            }
        }

        private bool _isChatHistoryVisible = false;
        public bool IsChatHistoryVisible
        {
            get => _isChatHistoryVisible;
            set
            {
                if (_isChatHistoryVisible != value)
                {
                    _isChatHistoryVisible = value;
                    OnPropertyChanged(nameof(IsChatHistoryVisible));
                }
            }
        }

        private bool _isChatbotVisible = false;
        public bool IsChatbotVisible
        {
            get => _isChatbotVisible;
            set
            {
                if (_isChatbotVisible != value)
                {
                    _isChatbotVisible = value;
                    OnPropertyChanged(nameof(IsChatbotVisible));
                }
            }
        }

        private bool _isInputFrameVisible = true;
        public bool IsInputFrameVisible
        {
            get => _isInputFrameVisible;
            set
            {
                if (_isInputFrameVisible != value)
                {
                    _isInputFrameVisible = value;
                    OnPropertyChanged(nameof(IsInputFrameVisible));
                }
            }
        }

        private bool _isOutputFrameVisible = true;
        public bool IsOutputFrameVisible
        {
            get => _isOutputFrameVisible;
            set
            {
                if (_isOutputFrameVisible != value)
                {
                    _isOutputFrameVisible = value;
                    OnPropertyChanged(nameof(IsOutputFrameVisible));
                }
            }
        }

        private bool _isRunInferenceButtonVisible = true;
        public bool IsRunInferenceButtonVisible
        {
            get => _isRunInferenceButtonVisible;
            set
            {
                if (_isRunInferenceButtonVisible != value)
                {
                    _isRunInferenceButtonVisible = value;
                    OnPropertyChanged(nameof(IsRunInferenceButtonVisible));
                }
            }
        }

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

        private ObservableCollection<ChatMessage> _chatHistory;
        public ObservableCollection<ChatMessage> ChatHistory
        {
            get => _chatHistory;
            set
            {
                if (_chatHistory != value)
                {
                    _chatHistory = value;
                    OnPropertyChanged(nameof(ChatHistory));
                }
            }
        }

        public Inference(Model model)
        {
            InitializeComponent();
            _model = model;
            _modelService = new ModelService();
            ChatHistory = new ObservableCollection<ChatMessage>();
            BindingContext = this;
            CreateInputUI();
        }

        private void CreateInputUI()
        {
            if (InputContainer == null)
            {
                System.Diagnostics.Debug.WriteLine("InputContainer is null");
                return;
            }

            switch (_model.PipelineTag?.ToLower())
            {
                case "object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image or Video"));
                    IsViewImageOutputButtonVisible = true;
                    IsOutputTextVisible = true;
                    IsChatHistoryVisible = false;
                    break;
                case "image-segmentation":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image"));
                    IsViewImageOutputButtonVisible = true;
                    IsOutputTextVisible = true;
                    IsChatHistoryVisible = false;
                    break;
                case "zero-shot-object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image"));
                    InputContainer.Children.Add(CreateTextInputUI());
                    IsViewImageOutputButtonVisible = true;
                    IsOutputTextVisible = true;
                    IsChatHistoryVisible = false;
                    break;
                case "text-classification":
                    InputContainer.Children.Add(CreateTextInputUI());
                    IsOutputTextVisible = true;
                    IsChatHistoryVisible = false;
                    break;
                case "zero-shot-classification":
                    InputContainer.Children.Add(CreateTextInputUI());
                    IsOutputTextVisible = true;
                    IsChatHistoryVisible = false;
                    break;
                case "translation":
                    InputContainer.Children.Add(CreateTextInputUI());
                    IsOutputTextVisible = true;
                    IsChatHistoryVisible = false;
                    break;
                case "text-to-speech":
                    InputContainer.Children.Add(CreateTextInputUI());
                    IsOutputTextVisible = true;
                    IsChatHistoryVisible = false;
                    break;
                case "text-generation":
                    if (_model.Config.ChatHistory == true)
                    {
                        IsChatbotVisible = true;
                        IsInputFrameVisible = false;
                        IsOutputFrameVisible = false;
                        IsRunInferenceButtonVisible = false;
                    }
                    else
                    {
                        InputContainer.Children.Add(CreateTextInputUI());
                        IsChatbotVisible = false;
                        IsInputFrameVisible = true;
                        IsOutputFrameVisible = true;
                        IsRunInferenceButtonVisible = true;
                    }
                    break;
                case "token-classification":
                case "question-answering":
                case "summarization":
                case "automatic-speech-recognition":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Audio File"));
                    IsOutputTextVisible = true;
                    IsChatHistoryVisible = false;
                    break;
                default:
                    InputContainer.Children.Add(new Label { Text = "Input type not supported for this model.", TextColor = Colors.Gray });
                    IsChatbotVisible = false;
                    IsInputFrameVisible = true;
                    IsOutputFrameVisible = true;
                    IsRunInferenceButtonVisible = true;
                    break;
            }
        }

        private View CreateFileSelectionUI(string buttonText)
        {
            var instructionText = "Enter input data and 'Run Inference' to preview the output.";
            
            switch (_model.PipelineTag?.ToLower())
            {
                case "object-detection":
                    instructionText = "Select image or video file and click 'Run Inference' to preview the output.";
                    break;
                case "image-segmentation":
                    instructionText = "Select image file and click 'Run Inference' to preview the output.";
                    break;
                case "zero-shot-object-detection":
                    instructionText = "Select image file and enter text, then click 'Run Inference' to preview the output.";
                    break;
                // other cases
            }

            var fileButton = new Button
            {
                Text = buttonText,
                BackgroundColor = Colors.LightGray,
                TextColor = Colors.Black,
                CornerRadius = 5,
                Margin = new Thickness(0, 20, 0, 10)
            };

            if (buttonText == "Select Image or Video")
            {
                fileButton.Clicked += OnImageOrVideoSelectClicked;
            }
            else if (buttonText == "Select Image")
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
                    new Label { Text = instructionText, FontSize = 14, TextColor = Color.FromArgb("#5D5D5D") },
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

        private async void OnSendMessageClicked(object sender, EventArgs e)
        {
            if (!string.IsNullOrWhiteSpace(ChatInputEntry.Text))
            {
                ChatHistory.Add(new ChatMessage { Role = "user", Content = ChatInputEntry.Text });
                var userMessage = ChatInputEntry.Text;
                ChatInputEntry.Text = string.Empty;

                await SendMessageToChatbot(userMessage);
                
                // Scroll to the bottom of the chat history
                Device.BeginInvokeOnMainThread(() =>
                {
                    ChatHistoryListView.ScrollTo(ChatHistory.Last(), ScrollToPosition.End, false);
                });
            }
        }

        private async Task SendMessageToChatbot(string userMessage)
        {
            try
            {
                var data = new { payload = userMessage };
                var result = await _modelService.Inference(_model.ModelId, data);

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

        private async void OnImageOrVideoSelectClicked(object sender, EventArgs e)
        {
            try
            {
                var customFileType = new FilePickerFileType(
                    new Dictionary<DevicePlatform, IEnumerable<string>>
                    {
                        { DevicePlatform.iOS, new[] { "public.image", "public.movie" } },
                        { DevicePlatform.Android, new[] { "image/*", "video/*" } },
                        { DevicePlatform.WinUI, new[] { ".jpg", ".jpeg", ".png", ".gif",".mp4", ".mov", ".wmv" } }
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
                    var label = (Label)stack.Children[2];
                    label.Text = result.FileName;
                    label.IsVisible = true;
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
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
                    var label = (Label)stack.Children[2];
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
                        { DevicePlatform.WinUI, new[] { ".mp3", ".wav", ".m4a" } },
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
                    var label = (Label)stack.Children[2];
                    label.Text = result.FileName;
                    label.IsVisible = true;
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
        }

        private async void OnRunInferenceClicked(object sender, EventArgs e)
        {
            try
            {
                object data;
                switch (_model.PipelineTag?.ToLower())
                {
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
                    case "text-generation":
                        if (string.IsNullOrEmpty(InputText))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please enter text.", "OK");
                            return;
                        }
                        data = new { payload = InputText };
                        break;
                    case "text-to-speech":
                    
                    default:
                        await Application.Current.MainPage.DisplayAlert("Error", "Unsupported model type for inference.", "OK");
                        return;
                }

                Dictionary<string, object> result = await _modelService.Inference(_model.ModelId, data);

                if (result.TryGetValue("data", out var dataValue))
                {
                    RawJsonText = FormatJsonString(dataValue);
                    OutputText = dataValue.ToString(); // Use OutputText instead of RawJsonText for formatted output
                    System.Diagnostics.Debug.WriteLine($"Extracted data: {OutputText}");
                }
                else
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Invalid result format.", "OK");
                    return;
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred during inference: {ex.Message}", "OK");
            }
        }

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

        private async void OnViewImageOutputClicked(object sender, EventArgs e)
        {
            try
            {
                if (string.IsNullOrEmpty(RawJsonText) || string.IsNullOrEmpty(_selectedFilePath))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Please run inference first.", "OK");
                    return;
                }

                string[] videoExtensions = { ".mp4", ".mov", ".wmv", ".gif" };
                if (videoExtensions.Contains(Path.GetExtension(_selectedFilePath).ToLower()))
                {
                    await Application.Current.MainPage.DisplayAlert("Video Visualization", "Video visualization is not currently supported.", "OK");
                    return;
                }

                var task = _model.PipelineTag?.ToLower();
                System.Diagnostics.Debug.WriteLine($"Processing image with task: {task}");
                System.Diagnostics.Debug.WriteLine($"RawJsonText: {RawJsonText}");

                var result = await _modelService.ProcessImage(_selectedFilePath, RawJsonText, task);
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
                    ((Grid)Content).Children.Add(_imagePopUp);
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
        private string FormatJsonString(object obj)
        {
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            if (obj is string strValue)
            {
                // If it's already a string, try to parse and re-serialize it
                try
                {
                    var jsonElement = JsonSerializer.Deserialize<JsonElement>(strValue);
                    return JsonSerializer.Serialize(jsonElement, options);
                }
                catch
                {
                    // If parsing fails, return the original string
                    return strValue;
                }
            }
            else
            {
                // For non-string objects, serialize with indentation
                return JsonSerializer.Serialize(obj, options);
            }
        }

        private string FormatOutputText(string text)
        {
            if (string.IsNullOrEmpty(text)) return text;

            // Replace "\n" with actual new lines
            text = text.Replace("\\n", "\n");

            // Convert Markdown-style bold to XAML bold
            text = System.Text.RegularExpressions.Regex.Replace(text, @"\*\*(.*?)\*\*", "<Span FontAttributes=\"Bold\">$1</Span>");

            // Convert Markdown-style numbered list to XAML list
            text = System.Text.RegularExpressions.Regex.Replace(text, @"(\d+)\. ", match => 
                $"<Span FontAttributes=\"Bold\">{match.Groups[1].Value}. </Span>");

            return text;
        }
    }

    public class ChatMessage
    {
        public string Role { get; set; }
        public string Content { get; set; }
        public string FormattedContent => FormatContent(Content);

        private string FormatContent(string text)
        {
            if (string.IsNullOrEmpty(text)) return text;

            // Replace "\n" with actual new lines
            text = text.Replace("\\n", "\n");

            // Convert Markdown-style bold to XAML bold
            text = System.Text.RegularExpressions.Regex.Replace(text, @"\*\*(.*?)\*\*", "<Span FontAttributes=\"Bold\">$1</Span>");

            // Convert Markdown-style numbered list to XAML list
            text = System.Text.RegularExpressions.Regex.Replace(text, @"(\d+)\. ", match => 
                $"<Span FontAttributes=\"Bold\">{match.Groups[1].Value}. </Span>");

            return text;
        }
    }
}