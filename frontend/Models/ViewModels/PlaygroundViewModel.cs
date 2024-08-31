using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Collections.ObjectModel;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Input;
using Microsoft.Maui.Controls;
using frontend.Services;

namespace frontend.Models.ViewModels
{
    public partial class PlaygroundViewModel : ObservableObject
    {
        [ObservableProperty]
        private Playground? playground;

        public ObservableCollection<Model> PlaygroundModels { get; }

        public ObservableCollection<ModelViewModel> PlaygroundChain { get; }
        private readonly PlaygroundService _playgroundService;

        public PlaygroundViewModel(PlaygroundService playgroundService)
        {
            _playgroundService = playgroundService;
            PlaygroundModels = new ObservableCollection<Model>();
            PlaygroundChain = new ObservableCollection<ModelViewModel>();
        }

        public void SetPlaygroundChainForPicker()
        {
            for (int i = 0; i < playground.Chain.Count; i++)
            {
                PlaygroundChain[i].SelectedModel = playground.Models[playground.Chain[i]];
            }
        }

        // This method is called only when the entire Playground has been changed
        partial void OnPlaygroundChanged(Playground? oldValue, Playground? newValue)
        {
            System.Diagnostics.Debug.WriteLine($"======Playground changed");
            PlaygroundModels.Clear();
            PlaygroundChain.Clear();

            if (newValue?.Models != null)
            {
                foreach (var model in newValue.Models.Values)
                {   
                    PlaygroundModels.Add(model);
                }
            }

            if (newValue?.Chain != null)
            {
                foreach (var modelName in newValue.Chain)
                {
                    var model = newValue.Models?.Values.FirstOrDefault(m => m.ModelId == modelName);
                    if (model != null)
                    {
                        PlaygroundChain.Add(new ModelViewModel { SelectedModel = model });
                    }
                }
            }
        }

         // Add properties for audio and output visibility
        [ObservableProperty]
        private string audioSource;

        [ObservableProperty]
        private bool isAudioPlayerVisible;

        [ObservableProperty]
        private bool isOutputTextVisible;

        [ObservableProperty]
        private bool isProcessedImageVisible;

        [ObservableProperty]
        private string outputText;

        [ObservableProperty]
        private string rawJsonText;

        [ObservableProperty]
        private string jsonOutputText;
        private bool _isChainLoaded;
        private string _selectedFilePath;
        private string _inputText; 


        public async Task HandleAudioOutput(Dictionary<string, object> result)
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

        public void HandleTextOutput(Dictionary<string, object> result)
        {
            string outputText;
            if (result.TryGetValue("data", out var dataObject))
            {
                outputText = JsonSerializer.Serialize(dataObject, new JsonSerializerOptions { WriteIndented = true });
            }
            else
            {
                outputText = JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true });
            }
            OutputText = outputText;
            IsOutputTextVisible = true;
            IsAudioPlayerVisible = false;
            IsProcessedImageVisible = false;
        }

        private async Task LoadOrStopChain()
        {
            if (Playground == null) return;

            if (!_isChainLoaded)
            {
                try
                {
                    await _playgroundService.LoadPlaygroundChain(Playground.PlaygroundId);
                    _isChainLoaded = true;
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
                    await _playgroundService.StopPlaygroundChain(Playground.PlaygroundId);
                    _isChainLoaded = false;
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
            if (Playground == null || !_isChainLoaded)
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
                    { "playground_id", Playground.PlaygroundId },
                    { "data", inputData }
                };

                var result = await _playgroundService.Inference(Playground.PlaygroundId, inferenceRequest);

                if (result.TryGetValue("error", out var errorMessage))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", errorMessage.ToString(), "OK");
                }
                else if (result.TryGetValue("data", out var dataValue))
                {
                    RawJsonText = FormatJsonString(dataValue);
                    JsonOutputText = FormatJsonString(dataValue) ?? "No data available.";

                    switch (Playground.Models[Playground.Chain.LastOrDefault()].PipelineTag?.ToLower())
                    {
                        case "text-to-speech":
                            await HandleAudioOutput(result);
                            break;
                        case "speech-to-text":
                            HandleTextOutput(result);
                            break;
                        default:
                            OutputText = RawJsonText;
                            break;
                    }
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

        private Dictionary<string, object> GetInputData()
        {
            if (Playground == null) return new Dictionary<string, object>();

            var firstModelKey = Playground.Chain.FirstOrDefault();
            if (firstModelKey == null || !Playground.Models.TryGetValue(firstModelKey, out var firstModel))
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

        private string FormatJsonString(object data)
        {
            return JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = true });
        }
    }
}