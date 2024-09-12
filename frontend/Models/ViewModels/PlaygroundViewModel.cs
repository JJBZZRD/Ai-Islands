// using CommunityToolkit.Mvvm.ComponentModel;
// using CommunityToolkit.Mvvm.Input;
// using System.Collections.ObjectModel;
// using System.IO;
// using System.Text.Json;
// using System.Threading.Tasks;
// using System.Windows.Input;
// using Microsoft.Maui.Controls;
// using frontend.Services;

// namespace frontend.Models.ViewModels
// {
//     public partial class PlaygroundViewModel : ObservableObject
//     {
//         [ObservableProperty]
//         private Playground? playground;

//         public ObservableCollection<Model> PlaygroundModels { get; }

//         public ObservableCollection<ModelViewModel> PlaygroundChain { get; }
//         private readonly PlaygroundService _playgroundService;
//         private readonly ModelService _modelService;

//         [ObservableProperty]
//         private string audioSource;

//         [ObservableProperty]
//         private bool isAudioPlayerVisible;

//         [ObservableProperty]
//         private bool isOutputTextVisible;

//         [ObservableProperty]
//         private bool isProcessedImageVisible;

//         [ObservableProperty]
//         private ImageSource processedImageSource;


//         [ObservableProperty]
//         private string outputText;

//         [ObservableProperty]
//         private string rawJsonText;

//         [ObservableProperty]
//         private string jsonOutputText;

//         [ObservableProperty]
//         private string inputText;

//         private bool _isChainLoaded;
//         public string ChainButtonText => _isChainLoaded ? "Stop Chain" : "Load Chain";

//         public bool IsChainLoaded
//         {
//             get => _isChainLoaded;
//             set
//             {
//                 if (_isChainLoaded != value)
//                 {
//                     SetProperty(ref _isChainLoaded, value);
//                     OnPropertyChanged(nameof(IsChainLoaded));
//                     OnPropertyChanged(nameof(ChainButtonText)); // Notify change for button text
//                 }
//             }
//         }

//         private string _selectedFilePath;
//         public string SelectedFilePath
//         {
//             get => _selectedFilePath;
//             set { SetProperty(ref _selectedFilePath, value); }
//         }

//         public ICommand LoadChainCommand { get; }
//         public ICommand InferenceCommand { get; }

//         public PlaygroundViewModel(PlaygroundService playgroundService, ModelService modelService)
//         {
//             _playgroundService = playgroundService ?? throw new ArgumentNullException(nameof(playgroundService));
//             _modelService = modelService ?? throw new ArgumentNullException(nameof(modelService));
//             PlaygroundModels = new ObservableCollection<Model>();
//             PlaygroundChain = new ObservableCollection<ModelViewModel>();

//             LoadChainCommand = new AsyncRelayCommand(LoadOrStopChain);
//             InferenceCommand = new AsyncRelayCommand(RunInference);
//         }

//         public void SetPlaygroundChainForPicker()
//         {
//             for (int i = 0; i < playground.Chain.Count; i++)
//             {
//                 PlaygroundChain[i].SelectedModel = playground.Models[playground.Chain[i]];
//             }
//         }

//         // This method is called only when the entire Playground has been changed
//         partial void OnPlaygroundChanged(Playground? oldValue, Playground? newValue)
//         {
//             System.Diagnostics.Debug.WriteLine($"======Playground changed");
//             PlaygroundModels.Clear();
//             PlaygroundChain.Clear();

//             if (newValue?.Models != null)
//             {
//                 foreach (var model in newValue.Models.Values)
//                 {   
//                     PlaygroundModels.Add(model);
//                 }
//             }

//             if (newValue?.Chain != null)
//             {
//                 foreach (var modelName in newValue.Chain)
//                 {
//                     var model = newValue.Models?.Values.FirstOrDefault(m => m.ModelId == modelName);
//                     if (model != null)
//                     {
//                         PlaygroundChain.Add(new ModelViewModel { SelectedModel = model });
//                     }
//                 }
//             }
//         }

//         public async Task LoadOrStopChain()
//         {
//             if (Playground == null) return;

//             if (!_isChainLoaded)
//             {
//                 try
//                 {
//                     await _playgroundService.LoadPlaygroundChain(Playground.PlaygroundId);
//                     _isChainLoaded = true;

//                     foreach (var modelId in Playground.Chain)
//                     {
//                         if (Playground.Models.TryGetValue(modelId, out var model))
//                         {
//                             model.IsLoaded = true;
//                         }
//                     }

//                     await Application.Current.MainPage.DisplayAlert("Success", "Chain loaded successfully.", "OK");
//                 }
//                 catch (Exception ex)
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", $"Failed to load chain: {ex.Message}", "OK");
//                 }
//             }
//             else
//             {
//                 try
//                 {
//                     await _playgroundService.StopPlaygroundChain(Playground.PlaygroundId);
//                     _isChainLoaded = false;

//                     foreach (var modelId in Playground.Chain)
//                     {
//                         if (Playground.Models.TryGetValue(modelId, out var model))
//                         {
//                             model.IsLoaded = false;
//                         }
//                     }

//                     await Application.Current.MainPage.DisplayAlert("Success", "Chain stopped successfully.", "OK");
//                 }
//                 catch (Exception ex)
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", $"Failed to stop chain: {ex.Message}", "OK");
//                 }
//             }

//             UpdateOutputVisibility();
//         }

//         public async Task RunInference()
//         {
//             if (Playground == null || !_isChainLoaded)
//             {
//                 await Application.Current.MainPage.DisplayAlert("Error", "Please load the chain first.", "OK");
//                 return;
//             }

//             try
//             {
//                 var inputData = GetInputData();
//                 if (inputData.Count == 0)
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", "Please provide input data.", "OK");
//                     return;
//                 }

//                 var inferenceRequest = new Dictionary<string, object>
//                 {
//                     { "playground_id", Playground.PlaygroundId },
//                     { "data", inputData }
//                 };

//                 var result = await _playgroundService.Inference(Playground.PlaygroundId, inferenceRequest);

//                 if (result.TryGetValue("error", out var errorMessage))
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", errorMessage.ToString(), "OK");
//                 }
//                 else if (result.TryGetValue("data", out var dataValue))
//                 {
//                     RawJsonText = FormatJsonString(dataValue);
//                     JsonOutputText = FormatJsonString(dataValue) ?? "No data available.";
//                     await HandleInferenceResult(dataValue);
//                 }
//             }
//             catch (Exception ex)
//             {
//                 await Application.Current.MainPage.DisplayAlert("Error", $"Inference failed: {ex.Message}", "OK");
//             }
//         }

//         private async Task HandleInferenceResult(object dataValue)
//         {
//             var lastModelId = Playground.Chain.LastOrDefault();
//             var pipelineTag = Playground.Models[lastModelId]?.PipelineTag?.ToLower();

//             switch (pipelineTag)
//             {
//                 // Computer Vision Models
//                 case "object-detection":
//                 case "image-segmentation":
//                 case "zero-shot-object-detection":
//                     await ViewImageOutput();
//                     break;

//                 // NLP Models
//                 case "translation":
//                     OutputText = FormatTranslationOutput(dataValue, GetOriginalStructure());
//                     break;
//                 case "text-to-speech":
//                     await HandleAudioOutput(dataValue);
//                     break;
//                 default:
//                     OutputText = JsonSerializer.Serialize(dataValue, new JsonSerializerOptions { WriteIndented = true });
//                     break;
//             }

//             JsonOutputText = JsonSerializer.Serialize(dataValue, new JsonSerializerOptions { WriteIndented = true });

//             UpdateOutputVisibility();
//         }

//         private async Task HandleAudioOutput(object dataValue)
//         {
//             if (dataValue is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Object)
//             {
//                 var audioContentBase64 = jsonElement.GetProperty("audio_content").GetString();
//                 if (!string.IsNullOrEmpty(audioContentBase64))
//                 {
//                     var audioBytes = Convert.FromBase64String(audioContentBase64);
//                     var tempFilePath = Path.Combine(FileSystem.CacheDirectory, "temp_audio.wav");
//                     await File.WriteAllBytesAsync(tempFilePath, audioBytes);

//                     if (File.Exists(tempFilePath))
//                     {
//                         AudioSource = tempFilePath;
//                         IsAudioPlayerVisible = true;
//                     }
//                     else
//                     {
//                         await Application.Current.MainPage.DisplayAlert("Error", "Audio file could not be found or saved.", "OK");
//                     }
//                 }
//             }
//         }

//         private Dictionary<string, object> GetInputData()
//         {
//             var firstModelKey = Playground.Chain.FirstOrDefault();
//             if (firstModelKey == null || !Playground.Models.TryGetValue(firstModelKey, out var firstModel))
//             {
//                 return new Dictionary<string, object>();
//             }

//             var inputData = new Dictionary<string, object>();

//             switch (firstModel.PipelineTag?.ToLower())
//             {
//                 case "object-detection":
//                 case "image-segmentation":
//                     if (string.IsNullOrEmpty(SelectedFilePath))
//                         throw new InvalidOperationException("Please select an image file.");
//                     inputData["image_path"] = SelectedFilePath;
//                     break;
//                 case "zero-shot-object-detection":
//                     if (string.IsNullOrEmpty(SelectedFilePath) || string.IsNullOrEmpty(InputText))
//                         throw new InvalidOperationException("Please select an image file and enter text.");
//                     inputData["payload"] = new { image = SelectedFilePath, text = InputText.Split(',').Select(t => t.Trim()).ToList() };
//                     break;
//                 case "text-generation":
//                 case "text-to-speech":
//                 case "translation":
//                 case "text-classification":
//                 case "feature-extraction":
//                     if (string.IsNullOrWhiteSpace(InputText))
//                         throw new InvalidOperationException("Please enter text input.");
//                     inputData["payload"] = InputText;
//                     break;
//                 case "speech-to-text":
//                 case "automatic-speech-recognition":
//                     if (string.IsNullOrEmpty(SelectedFilePath))
//                         throw new InvalidOperationException("Please select an audio file.");
//                     inputData["audio_path"] = SelectedFilePath;
//                     break;
//                 default:
//                     throw new ArgumentException("Unsupported model type for inference.");
//             }

//             return inputData;
//         }

//         private void UpdateOutputVisibility()
//         {
//             if (IsAudioPlayerVisible)
//             {
//                 IsOutputTextVisible = false;
//                 IsProcessedImageVisible = false;
//             }
//             else if (IsProcessedImageVisible)
//             {
//                 IsOutputTextVisible = false;
//             }
//             else
//             {
//                 IsOutputTextVisible = true;
//             }
//         }

//         private string FormatJsonString(object data)
//         {
//             return JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = true });
//         }

//         private string FormatTranslationOutput(object dataValue, List<string> originalStructure)
//         {
//             if (dataValue is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Array)
//             {
//                 var translatedLines = jsonElement.EnumerateArray()
//                     .Select(element => element.TryGetProperty("translation_text", out var translationText) 
//                         ? translationText.GetString() 
//                         : null)
//                     .Where(text => text != null)
//                     .ToList();

//                 var result = new List<string>();
//                 int translationIndex = 0;

//                 if (originalStructure == null || originalStructure.Count == 0)
//                 {
//                     return "No translation available.";
//                 }

//                 foreach (var line in originalStructure)
//                 {
//                     if (string.IsNullOrWhiteSpace(line))
//                     {
//                         result.Add(string.Empty);
//                     }
//                     else if (translationIndex < translatedLines.Count)
//                     {
//                         result.Add(translatedLines[translationIndex]);
//                         translationIndex++;
//                     }
//                     else
//                     {
//                         result.Add("No translation available for this line.");
//                     }
//                 }

//                 return string.Join("\n", result);
//             }

//             return "No translation available.";
//         }

//         private List<string> GetOriginalStructure()
//         {
//             return InputText?.Split('\n').ToList() ?? new List<string>();
//         }

//         private async Task ViewImageOutput()
//         {
//             try
//             {
//                 if (_modelService == null)
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", "Model service is not initialized.", "OK");
//                     return;
//                 }

//                 if (string.IsNullOrEmpty(RawJsonText) || string.IsNullOrEmpty(SelectedFilePath))
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", "Please run inference first.", "OK");
//                     return;
//                 }

//                 var lastModelId = Playground.Chain.LastOrDefault();
//                 var task = Playground.Models[lastModelId]?.PipelineTag?.ToLower();

//                 if (task == null)
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", "Pipeline task is not defined.", "OK");
//                     return;
//                 }

//                 var result = await _modelService.ProcessImage(SelectedFilePath, RawJsonText, task);
//                 var processedImageResult = JsonSerializer.Deserialize<ProcessedImageResult>(result);

//                 if (processedImageResult?.ImageUrl == null)
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", "Failed to process image. The ImageUrl is null.", "OK");
//                     return;
//                 }

//                 string imageFullPath = processedImageResult.ImageUrl;

//                 if (!File.Exists(imageFullPath))
//                 {
//                     await Application.Current.MainPage.DisplayAlert("Error", $"Image file not found: {imageFullPath}", "OK");
//                     return;
//                 }

//                 ProcessedImageSource = ImageSource.FromFile(imageFullPath);
//                 IsProcessedImageVisible = true;
//             }
//             catch (Exception ex)
//             {
//                 await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
//             }
//         }
//     }
// }

using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Collections.ObjectModel;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Input;
using Microsoft.Maui.Controls;
using frontend.Services;
using System.Text;

namespace frontend.Models.ViewModels
{
    public partial class PlaygroundViewModel : ObservableObject
    {
        [ObservableProperty]
        private Playground? playground;

        public ObservableCollection<Model> PlaygroundModels { get; }

        public ObservableCollection<ModelViewModel> PlaygroundChain { get; }
        private readonly PlaygroundService _playgroundService;
        private readonly ModelService _modelService;

        [ObservableProperty]
        private string audioSource;

        [ObservableProperty]
        private bool isAudioPlayerVisible;

        [ObservableProperty]
        private bool isOutputTextVisible;

        [ObservableProperty]
        private bool isProcessedImageVisible;

        [ObservableProperty]
        private ImageSource processedImageSource;

        [ObservableProperty]
        private string outputText;

        [ObservableProperty]
        private string rawJsonText;

        [ObservableProperty]
        private string jsonOutputText;

        [ObservableProperty]
        private string inputText;

        [ObservableProperty]
        private bool isJsonViewVisible;

        private bool _isChainLoaded;
        public string ChainButtonText => _isChainLoaded ? "Stop Chain" : "Load Chain";

        public bool IsChainLoaded
        {
            get => _isChainLoaded;
            set
            {
                if (_isChainLoaded != value)
                {
                    SetProperty(ref _isChainLoaded, value);
                    OnPropertyChanged(nameof(IsChainLoaded));
                    OnPropertyChanged(nameof(ChainButtonText)); // Notify change for button text
                }
            }
        }

        private string _selectedFilePath;
        public string SelectedFilePath
        {
            get => _selectedFilePath;
            set { SetProperty(ref _selectedFilePath, value); }
        }

        // public ICommand LoadChainCommand { get; }
        // public ICommand InferenceCommand { get; }

        public PlaygroundViewModel(PlaygroundService playgroundService, ModelService modelService)
        {
            _playgroundService = playgroundService ?? throw new ArgumentNullException(nameof(playgroundService));
            _modelService = modelService ?? throw new ArgumentNullException(nameof(modelService));
            PlaygroundModels = new ObservableCollection<Model>();
            PlaygroundChain = new ObservableCollection<ModelViewModel>();

            // LoadChainCommand = new AsyncRelayCommand(LoadOrStopChain);
            // InferenceCommand = new AsyncRelayCommand(RunInference);
        }

        public void SetPlaygroundChainForPicker()
        {
            for (int i = 0; i < playground.Chain.Count; i++)
            {
                PlaygroundChain[i].SelectedModel = playground.Models[playground.Chain[i]];
            }
        }

        public void RefreshPlaygroundChain()
        {
            PlaygroundChain.Clear();
            foreach (var modelName in playground.Chain)
            {
                var model = playground.Models?.Values.FirstOrDefault(m => m.ModelId == modelName);
                if (model != null)
                {
                    PlaygroundChain.Add(new ModelViewModel { SelectedModel = model });
                }
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
    }
}


