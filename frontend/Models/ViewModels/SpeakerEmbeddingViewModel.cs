using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using System.Diagnostics;
using frontend.Services;

namespace frontend.Models.ViewModels
{
    public partial class SpeakerEmbeddingViewModel : ObservableObject
    {
        public ObservableCollection<SpeakerEmbedding> EmbeddingsList { get; }
        private readonly DataService _dataService;

        public SpeakerEmbeddingViewModel()
        {
            _dataService = new DataService();
            EmbeddingsList = new ObservableCollection<SpeakerEmbedding>();
            LoadEmbeddings();
        }

        internal async void LoadEmbeddings()
        {
            var embeddings = await _dataService.GetSpeakerEmbedding();
            
            foreach (var embedding in embeddings)
            {
                Debug.WriteLine($"Embedding ID: {embedding.Key}, Values: [{string.Join(", ", embedding.Value)}]");
                EmbeddingsList.Add(new SpeakerEmbedding
                {
                    Id = embedding.Key,
                    EmbeddingArray = embedding.Value
                });
            }
        }

        internal async Task<string> ConfigureEmbeddings()
        {
            var embeddingsDict = new Dictionary<string, List<double>>();

            foreach (var embedding in EmbeddingsList)
            {
                if (string.IsNullOrWhiteSpace(embedding.EmbeddingArrayString))
                {
                    return $"Empty or null embedding array for ID: {embedding.Id}";
                }

                var parsedArray = new List<double>();
                var items = embedding.EmbeddingArrayString.Split(", ");

                foreach (var item in items)
                {
                    if (string.IsNullOrWhiteSpace(item))
                    {
                        return $"Empty value found in embedding array for ID: {embedding.Id}";
                    }

                    if (!double.TryParse(item.Trim(), out double value))
                    {
                        return $"Invalid value '{item}' in embedding array for ID: {embedding.Id}";
                    }

                    parsedArray.Add(value);
                }

                // If we've made it here, all values are valid
                embedding.EmbeddingArray = parsedArray;  // Update the EmbeddingArray
                embeddingsDict[embedding.Id] = parsedArray;
            }

            var response = await _dataService.ConfigureSpeakerEmbeddings(embeddingsDict);
            return response;
        }
    }

    public partial class SpeakerEmbedding : ObservableObject
    {
        [ObservableProperty]
        private string? id;

        [ObservableProperty]
        private List<double>? embeddingArray;

        [ObservableProperty]
        private string? embeddingArrayString;

        partial void OnEmbeddingArrayChanged(List<double>? value)
        {
            if (value == null)
            {
                EmbeddingArrayString = null;
            }
            else
            {
                EmbeddingArrayString = string.Join(", ", value.Select(d => d.ToString()));
            }
        }

        partial void OnEmbeddingArrayStringChanged(string? value)
        {
            // This method is called when EmbeddingArrayString is set
            // We don't update EmbeddingArray here to avoid circular updates
            // EmbeddingArray will be updated in the ConfigureEmbeddings method
        }
    }
}