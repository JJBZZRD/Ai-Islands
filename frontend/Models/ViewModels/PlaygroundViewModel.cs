using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.ObjectModel;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Maui.Controls;

namespace frontend.Models.ViewModels
{
    public partial class PlaygroundViewModel : ObservableObject
    {
        [ObservableProperty]
        private Playground? playground;

        public ObservableCollection<Model> PlaygroundModels { get; }

        public ObservableCollection<ModelViewModel> PlaygroundChain { get; }

        public PlaygroundViewModel()
        {
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
        private string _audioSource;

        [ObservableProperty]
        private bool _isAudioPlayerVisible;

        [ObservableProperty]
        private bool _isOutputTextVisible;

        [ObservableProperty]
        private bool _isProcessedImageVisible;

        [ObservableProperty]
        private string _outputText;

        [ObservableProperty]
        private string _rawJsonText;

        [ObservableProperty]
        private string _jsonOutputText;

        // Method to handle audio output
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

        // Method to handle text output
        public void HandleTextOutput(Dictionary<string, object> result)
        {
            string outputText;
            if (result.TryGetValue("data", out var dataObject))
            {
                outputText = System.Text.Json.JsonSerializer.Serialize(dataObject, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            }
            else
            {
                outputText = System.Text.Json.JsonSerializer.Serialize(result, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            }
            OutputText = outputText;
            IsOutputTextVisible = true;
            IsAudioPlayerVisible = false;
            IsProcessedImageVisible = false;
        }
    }
}