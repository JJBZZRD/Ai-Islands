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
using System.Threading;

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
                    _outputText = value;
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

        public Inference(Model model)
        {
            InitializeComponent();
            _model = model;
            _modelService = new ModelService();
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

            // var viewImageOutputButton = CreateViewImageOutputButton();

            switch (_model.PipelineTag?.ToLower())
            {
                case "object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image or Video"));
                    IsViewImageOutputButtonVisible = true;
                    break;
                case "image-segmentation":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image"));
                    IsViewImageOutputButtonVisible = true;
                    break;
                case "zero-shot-object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image"));
                    InputContainer.Children.Add(CreateTextInputUI());
                    IsViewImageOutputButtonVisible = true;
                    break;
                case "text-classification":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "zero-shot-classification":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "translation":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "text-to-speech":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "token-classification":
                case "question-answering":
                case "summarization":
                case "automatic-speech-recognition":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Audio File"));
                    break;
                case "text-generation":
                    InputContainer.Children.Add(CreateTextInputUI());
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
                CornerRadius = 5
            };
            if (buttonText == "Select Image or Video")
            {
                fileButton.Clicked += OnImageOrVideoSelectClicked;
            }
            else if (buttonText == "Select Image File")
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
                Children = { fileButton, fileNameLabel }
            };
        }

        private View CreateTextInputUI()
        {
            var editor = new Editor
            {
                Placeholder = "Enter your input here...",
                PlaceholderColor = Colors.Gray,
                TextColor = Colors.Black,
                HeightRequest = 150,
                Text = InputText
            };
            editor.TextChanged += (sender, e) => InputText = ((Editor)sender)?.Text ?? string.Empty;
            return editor;
        }

        private View CreateViewImageOutputButton()
        {
            var button = new Button
            {
                Text = "View Image Output",
                BackgroundColor = Colors.LightBlue,
                TextColor = Colors.Black,
                CornerRadius = 5
            };
            button.Clicked += OnViewImageOutputClicked;
            return button;
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
                    PickerTitle = "Select an image or video file"
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
                // Define a custom file type filter for audio files
                var customFileType = new FilePickerFileType(
                    new Dictionary<DevicePlatform, IEnumerable<string>>
                    {
                        { DevicePlatform.iOS, new[] { "public.audio" } }, // For iOS
                        { DevicePlatform.Android, new[] { "audio/*" } },  // For Android
                        { DevicePlatform.WinUI, new[] { ".mp3", ".wav", ".m4a" } }, // For Windows
                    });

                PickOptions options = new()
                {
                    PickerTitle = "Please select an audio file",
                    FileTypes = customFileType,
                };

                // Show the file picker and wait for the user to select a file
                var result = await FilePicker.Default.PickAsync(options);

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
                    case "text-to-speech":
                      // etc..
                    default:
                        await Application.Current.MainPage.DisplayAlert("Error", "Unsupported model type for inference.", "OK");
                        return;
                }

                var result = await _modelService.Inference(_model.ModelId, data);

                RawJsonText = JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true });
                
                // Deserialize RawJsonText to a dictionary
                var resultDict = JsonSerializer.Deserialize<Dictionary<string, object>>(RawJsonText);

                // Extracting the value of "data"
                if (resultDict != null && resultDict.TryGetValue("data", out var dataValue))
                {
                    // Storing the value of "data" in RawJsonText, modifying previous RawJsonText
                    RawJsonText = JsonSerializer.Serialize(dataValue, new JsonSerializerOptions { WriteIndented = true });
                    System.Diagnostics.Debug.WriteLine($"Extracted data: {RawJsonText}");
                }
                else
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Invalid result format.", "OK");
                }

                // Add this line after processing the result
                await Application.Current.MainPage.DisplayAlert("Inference Complete", "The output is ready.", "OK");
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
                            // Reading frame from video
                            using var frame = new OpenCvSharp.Mat();
                            if (!videoCapture.Read(frame))
                                break;

                            frameCount++;
                            if (frameCount % frameInterval != 0)
                                continue;
                            
                            // Resize frame
                            var resizedFrame = frame.Resize(new OpenCvSharp.Size(), resizeFactor, resizeFactor);
                            // Encode frame to jpeg and send to backend via websocket
                            var jpegData = resizedFrame.ImEncode(".jpg");

                            await webSocket.SendAsync(new ArraySegment<byte>(jpegData), WebSocketMessageType.Binary, true, token);

                            var buffer = new byte[8192];
                            var response = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), token);
                            var predictionJson = Encoding.UTF8.GetString(buffer, 0, response.Count);
                            var prediction = JsonSerializer.Deserialize<Dictionary<string, object>>(predictionJson);
                            OnPredictionReceived(prediction);
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

        private void OnPredictionReceived(Dictionary<string, object> prediction)
        {
            // Serialize the new prediction
            var newPrediction = JsonSerializer.Serialize(prediction, new JsonSerializerOptions { WriteIndented = true });

            // Append the new prediction to the existing RawJsonText
            RawJsonText += (string.IsNullOrEmpty(RawJsonText) ? "" : "\n\n") + newPrediction;

            // Ensure the UI updates
            OnPropertyChanged(nameof(RawJsonText));

            Device.BeginInvokeOnMainThread(() =>
            {
                if (RawJsonOutput != null)
                {
                    RawJsonOutput.CursorPosition = RawJsonOutput.Text.Length;
                }
            });
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

                // Using full path returned from the backend
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
    }
}