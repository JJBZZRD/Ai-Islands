using System.Collections.ObjectModel;
using System.Text.Json;
using frontend.Services;
using System.Text.Json.Serialization;
using frontend.Views;
using System.Net.WebSockets;
using System.Text;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace frontend.Models.ViewModels
{
    public partial class InferenceViewModel : ObservableObject
    {
        private readonly ModelService _modelService;

        [ObservableProperty]
        private Model model;

        [ObservableProperty]
        private string inputText;

        [ObservableProperty]
        private string outputText;

        [ObservableProperty]
        private string selectedFilePath;

        [ObservableProperty]
        private string rawJsonText;

        [ObservableProperty]
        private bool isViewImageOutputButtonVisible;

        [ObservableProperty]
        private bool isOutputTextVisible;

        [ObservableProperty]
        private bool isChatHistoryVisible;

        [ObservableProperty]
        private bool isChatbotVisible;

        [ObservableProperty]
        private bool isInputFrameVisible;

        [ObservableProperty]
        private bool isOutputFrameVisible;

        [ObservableProperty]
        private bool isRerankerInputVisible;

        [ObservableProperty]
        private bool isRunInferenceButtonVisible;

        [ObservableProperty]
        private bool isAudioPlayerVisible;

        [ObservableProperty]
        private string audioSource;

        [ObservableProperty]
        private bool isSecondaryOutputVisible = false;

        public bool IsPrimaryOutputVisible => !IsSecondaryOutputVisible;

        [ObservableProperty]
        private string jsonOutputText = "No data available. Please run inference first.";

        [ObservableProperty]
        private ImageSource processedImageSource;

        [ObservableProperty]
        private bool isProcessedImageVisible;

        [ObservableProperty]
        private bool isPreviewImageVisible;

        [ObservableProperty]
        private bool isPreviewVideoVisible;

        [ObservableProperty]
        private ImagePopupView imagePopUp;

        [ObservableProperty]
        private ImageSource previewImageSource;

        [ObservableProperty]
        private string previewVideoSource;

        [ObservableProperty]
        private string rerankerQuery;

        public ObservableCollection<Passage> RerankerPassages { get; } = new();

        public ObservableCollection<ChatMessage> ChatHistory { get; } = new();

        public InferenceViewModel(Model model, ModelService modelService)
        {
            Model = model;
            _modelService = modelService;
            IsSecondaryOutputVisible = false; // Ensure it's set to false initially
            JsonOutputText = "No data available. Please run inference first.";
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
                    await UpdatePreview(result.FullPath, fileType);
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

        private async Task UpdatePreview(string filePath, string fileType)
        {
            IsPreviewImageVisible = false;
            IsPreviewVideoVisible = false;

            if (fileType.ToLower() == "image" || (fileType.ToLower() == "image_or_video" && !IsVideoFile(filePath)))
            {
                PreviewImageSource = ImageSource.FromFile(filePath);
                IsPreviewImageVisible = true;
            }
            else if (fileType.ToLower() == "image_or_video" && IsVideoFile(filePath))
            {
                PreviewVideoSource = filePath;
                IsPreviewVideoVisible = true;
            }
        }

        private bool IsVideoFile(string filePath)
        {
            string[] videoExtensions = { ".mp4", ".mov", ".wmv", ".avi" };
            return videoExtensions.Contains(Path.GetExtension(filePath).ToLower());
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
                        if (string.IsNullOrEmpty(SelectedFilePath))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an image or video file.", "OK");
                            return;
                        }
                        string[] videoExtensions = { ".mp4", ".mov", ".wmv", ".gif" };
                        if (videoExtensions.Contains(Path.GetExtension(SelectedFilePath).ToLower()))
                        {
                            IsOutputTextVisible = true;
                            await RunVideoInference();
                            return;
                        }
                        else
                        {
                            IsOutputTextVisible = false;
                        }
                        data = new { image_path = SelectedFilePath };
                        break;
                    case "image-segmentation":
                        if (string.IsNullOrEmpty(SelectedFilePath))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an image file.", "OK");
                            return;
                        }
                        data = new { payload = SelectedFilePath };
                        break;
                    case "zero-shot-object-detection":
                        if (string.IsNullOrEmpty(SelectedFilePath) || string.IsNullOrEmpty(InputText))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an image file and enter text.", "OK");
                            return;
                        }
                        data = new { payload = new { image = SelectedFilePath, text = InputText.Split(',').Select(t => t.Trim()).ToList() } };
                        break;

                    // ------------------------- NLP MODELS -------------------------

                    case "text-classification":
                        if (Model.IsReranker)
                        {
                            data = new
                            {
                                payload = RerankerPassages.Select(p => new
                                {
                                    text = RerankerQuery,
                                    text_pair = p.Content
                                }).ToList()
                            };
                        }
                        else
                        {
                            data = new { payload = InputText };
                        }
                        System.Diagnostics.Debug.WriteLine($"Text classification data: {JsonSerializer.Serialize(data)}");
                        break;
                    case "zero-shot-classification":
                        data = new { payload = InputText };
                        break;
                    case "translation":
                        var (translationPayload, originalStructure) = FormatTranslationInput(InputText);
                        data = translationPayload;
                        // Store originalStructure for later use
                        break;
                    case "text-to-speech":
                        data = new { payload = InputText };
                        break;
                    case "speech-to-text":
                        if (string.IsNullOrEmpty(SelectedFilePath))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an audio file.", "OK");
                            return;
                        }
                        data = new { file_path = SelectedFilePath };
                        break;
                    case "automatic-speech-recognition":
                        if (string.IsNullOrEmpty(SelectedFilePath))
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", "Please select an audio file.", "OK");
                            return;
                        }
                        data = new { payload = SelectedFilePath };
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

                if (result.TryGetValue("data", out var dataValue))
                {
                    System.Diagnostics.Debug.WriteLine($"dataValue type: {dataValue?.GetType()}");
                    RawJsonText = FormatJsonString(dataValue);
                    // Store raw JSON output for alt view
                    JsonOutputText = FormatJsonString(dataValue) ?? "No data available.";

                    switch (Model.PipelineTag?.ToLower())
                    {
                        // ------------------------- COMPUTER VISION MODELS -------------------------
                        case "object-detection":
                            await ViewImageOutput();
                            break;
                        case "image-segmentation":
                            await ViewImageOutput();
                            break;
                        case "zero-shot-object-detection":
                            await ViewImageOutput();
                            break;

                        // ------------------------- NLP MODELS -------------------------
                        case "translation":
                            var (translationPayload, originalStructure) = FormatTranslationInput(InputText);
                            data = translationPayload;
                            // ... (after getting the result)
                            OutputText = FormatTranslationOutput(dataValue, originalStructure);
                            break;
                        case "text-to-speech":
                            if (dataValue is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Object)
                            {
                                var audioContentBase64 = jsonElement.GetProperty("audio_content").GetString();
                                if (!string.IsNullOrEmpty(audioContentBase64))
                                {
                                    var audioBytes = Convert.FromBase64String(audioContentBase64);
                                    var tempFilePath = Path.Combine(FileSystem.CacheDirectory, "temp_audio.wav");
                                    await File.WriteAllBytesAsync(tempFilePath, audioBytes);
                                    System.Diagnostics.Debug.WriteLine($"Audio file saved to: {tempFilePath}");
                                    AudioSource = tempFilePath;
                                    IsAudioPlayerVisible = true;
                                }
                            }
                            break;
                        case "speech-to-text":
                            if (dataValue is JsonElement sttJsonElement && sttJsonElement.ValueKind == JsonValueKind.Object)
                            {
                                var transcription = sttJsonElement.GetProperty("transcription").GetString();
                                OutputText = $"Transcription: {transcription}";
                            }
                            else
                            {
                                OutputText = "Unexpected response format for speech-to-text.";
                            }
                            break;
                        case "automatic-speech-recognition":
                            if (dataValue is JsonElement asrJsonElement && asrJsonElement.ValueKind == JsonValueKind.Object)
                            {
                                var transcription = asrJsonElement.GetProperty("text").GetString();
                                OutputText = transcription;
                            }
                            else
                            {
                                OutputText = "Unexpected response format for automatic speech recognition.";
                            }
                            break;
                        case "text-classification":
                            if (Model.IsReranker)
                            {
                                OutputText = FormatRerankerOutput(dataValue, RerankerPassages);
                            }
                            else
                            {
                                OutputText = FormatTextClassificationOutput(dataValue);
                            }
                            break;

                        case "zero-shot-classification":
                            OutputText = FormatZeroShotTextClassificationOutput(dataValue);
                            break;

                        // ------------------------- TEXT GENERATION MODELS LLMS -------------------------
                        case "text-generation":
                            OutputText = dataValue.ToString();
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
                    JsonOutputText = "No data available.";
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
                JsonOutputText = $"An error occurred: {ex.Message}";
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

                ProcessedImageSource = ImageSource.FromFile(imageFullPath);
                IsProcessedImageVisible = true;
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

            }
        }

        public void SetImagePopup(ImagePopupView imagePopup)
        {
            ImagePopUp = imagePopup;
        }



        // Private methods -----------------------------------------------------------------------------------------------------

        private async Task RunVideoInference()
        {
            using var videoCapture = new OpenCvSharp.VideoCapture(SelectedFilePath);
            var cts = new CancellationTokenSource();

            try
            {
                var frameInterval = 2;
                var resizeFactor = 0.5;

                await _modelService.PredictLive(
                    Model.ModelId,
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

        // ... elsewhere in the class ...

        // CLASSIFICATION MODELS OPTION 1

        private string FormatTextClassificationOutput(Object dataValue)
        {
            if (dataValue == null || !(dataValue is JsonElement jsonElement))
                return "No data available.";

            if (jsonElement.ValueKind == JsonValueKind.Null)
            {
                return "No data available.";
            }
            else if (jsonElement.ValueKind == JsonValueKind.Array)
            {
                var sb = new StringBuilder();
                foreach (var element in jsonElement.EnumerateArray())
                {
                    sb.AppendLine(FormatSingleTextClassificationOutput(element));
                }
                return sb.ToString().TrimEnd();
            }
            else if (jsonElement.ValueKind == JsonValueKind.Object)
            {
                return FormatSingleTextClassificationOutput(jsonElement);
            }
            return "Invalid data format.";
        }

        private string FormatSingleTextClassificationOutput(JsonElement jsonElement)
        {
            var sb = new StringBuilder();

            if (jsonElement.TryGetProperty("label", out var label))
                sb.AppendLine($"Label: {label}");

            if (jsonElement.TryGetProperty("score", out var score))
            {
                if (score.ValueKind == JsonValueKind.Number)
                {
                    double scoreValue = score.GetDouble();
                    sb.AppendLine($"Confident Level: {scoreValue:P2}");
                }
            }

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

    private string FormatRerankerOutput(object dataValue, ObservableCollection<Passage> passages)
    {
        var jsonElement = (JsonElement)dataValue;
        var dataList = jsonElement.EnumerateArray().Select((element, index) => new
        {
            Passage = passages[index],
            Score = element.GetProperty("score").GetDouble()
        }).OrderByDescending(x => x.Score).ToList();

        var sb = new StringBuilder();
        for (int i = 0; i < dataList.Count; i++)
        {
            sb.AppendLine($"Rank {i + 1}:");
            sb.AppendLine($"passage: \"{dataList[i].Passage.Content}\"");
            sb.AppendLine($"relevancy score: {dataList[i].Score}");
            sb.AppendLine();
        }

        return sb.ToString();
    }

        // CLASSIFICATION MODELS END OPTION 1

        // CLASSIFICATION MODELS OPTION 2

        // private string FormatTextClassificationOutput(object dataValue)
        // {
        //     if (dataValue == null)
        //         return "No data available.";

        //     var jsonElement = dataValue as JsonElement? ?? JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize(dataValue));
        //     return FormatJsonElementToText(jsonElement);
        // }

        // private string FormatJsonElementToText(JsonElement element, int indent = 0)
        // {
        //     var result = new StringBuilder();
        //     string indentation = new string(' ', indent * 2);

        //     switch (element.ValueKind)
        //     {
        //         case JsonValueKind.Object:
        //             foreach (var property in element.EnumerateObject())
        //             {
        //                 string formattedValue = FormatJsonElementToText(property.Value, indent + 1);
        //                 if (!string.IsNullOrWhiteSpace(formattedValue))
        //                 {
        //                     result.AppendLine($"{indentation}{FormatPropertyName(property.Name)}:");
        //                     result.Append(formattedValue);
        //                 }
        //             }
        //             break;

        //         case JsonValueKind.Array:
        //             var items = element.EnumerateArray().ToList();
        //             for (int i = 0; i < items.Count; i++)
        //             {
        //                 string formattedValue = FormatJsonElementToText(items[i], indent + 1);
        //                 if (!string.IsNullOrWhiteSpace(formattedValue))
        //                 {
        //                     result.Append(formattedValue);
        //                 }
        //             }
        //             break;

        //         case JsonValueKind.String:
        //         case JsonValueKind.Number:
        //         case JsonValueKind.True:
        //         case JsonValueKind.False:
        //             string value = element.ToString();
        //             if (element.ValueKind == JsonValueKind.Number && double.TryParse(value, out double number))
        //             {
        //                 value = number.ToString("F4");
        //             }
        //             result.AppendLine($"{indentation}{value}");
        //             break;

        //         case JsonValueKind.Null:
        //             result.AppendLine($"{indentation}N/A");
        //             break;
        //     }

        //     return result.ToString();
        // }

        // private string FormatPropertyName(string name)
        // {
        //     // Convert camelCase or snake_case to Title Case
        //     string[] words = System.Text.RegularExpressions.Regex.Split(name, @"(?<!^)(?=[A-Z])|_");
        //     return string.Join(" ", words.Select(word => char.ToUpper(word[0]) + word.Substring(1).ToLower()));
        // }


        // CLASSIFICATION MODELS END OPTION 2

        // Case specific methods:

        private string FormatZeroShotTextClassificationOutput(object dataValue)
        {
            if (dataValue == null)
                return "No data available.";

            var jsonElement = dataValue as JsonElement? ?? JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize(dataValue));

            if (jsonElement.ValueKind == JsonValueKind.Null)
                return "No data available.";

            var sb = new StringBuilder();

            if (jsonElement.TryGetProperty("labels", out var labels) && labels.ValueKind == JsonValueKind.Array &&
                jsonElement.TryGetProperty("scores", out var scores) && scores.ValueKind == JsonValueKind.Array)
            {
                var labelScorePairs = labels.EnumerateArray()
                    .Zip(scores.EnumerateArray(), (label, score) => new { Label = label.GetString(), Score = score.GetDouble() })
                    .OrderByDescending(pair => pair.Score)
                    .ToList();

                if (labelScorePairs.Any())
                {

                    // Add the most relevant label and score at the top
                    var mostRelevant = labelScorePairs.First();
                    sb.AppendLine($"Most Relevant: {mostRelevant.Label} ({mostRelevant.Score:P1})"); // Show as percentage with 1 decimal place

                    sb.AppendLine();
                    // Append each label with its corresponding score
                    foreach (var pair in labelScorePairs)
                    {
                        sb.AppendLine($"{pair.Label} : {pair.Score:P2}");
                    }
                }
            }

            return sb.ToString().TrimEnd();
        }



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

        [RelayCommand]
        private void AddPassage()
        {
            RerankerPassages.Add(new Passage { Content = string.Empty });
        }

        [RelayCommand]
        private void RemovePassage(Passage passage)
        {
            RerankerPassages.Remove(passage);
        }
    }

    // -------------------------- LOCAL METHODS -------------------------------------------------------------------------------


    public partial class ChatMessage : ObservableObject
    {
        [ObservableProperty]
        public string role;
        [ObservableProperty]
        public string content;
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

    public partial class Passage : ObservableObject
    {
        [ObservableProperty]
        private string? content;
    }
}

