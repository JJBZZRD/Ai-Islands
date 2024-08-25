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
                if (embedding.EmbeddingArray == null || embedding.EmbeddingArray.Any(e => !double.TryParse(e.ToString(), out _)))
                {
                    return $"Invalid embedding array for ID: {embedding.Id}";
                }
                embeddingsDict[embedding.Id] = embedding.EmbeddingArray;
            }

            var response = await _dataService.ConfigureSpeakerEmbeddings(embeddingsDict);
            return response;
        }
    }

    public class SpeakerEmbedding
    {
        public string? Id { get; set; }

        public List<double>? EmbeddingArray { get; set; }
    }
}