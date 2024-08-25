using System.Collections.ObjectModel;
using System.Diagnostics;
using frontend.Models.ViewModels;
using frontend.Services;

namespace frontend.Views
{
    public partial class SpeakerEmbeddingView : ContentView
    {
        private SpeakerEmbeddingViewModel speakerEmbeddingViewModel;

        public SpeakerEmbeddingView()
        {
            InitializeComponent();
            speakerEmbeddingViewModel = new SpeakerEmbeddingViewModel();
            BindingContext = speakerEmbeddingViewModel;
        }

        private void OnAddEmbeddingClicked(object sender, EventArgs e)
        {
            var newEmbedding = new SpeakerEmbedding
            {
                Id = $"New Embedding {speakerEmbeddingViewModel.EmbeddingsList.Count + 1}",
                EmbeddingArray = new List<double>() // Initialize with empty list or default values
            };
            speakerEmbeddingViewModel.EmbeddingsList.Add(newEmbedding);
        }

        private void OnDeleteEmbeddingClicked(object sender, EventArgs e)
        {
            var button = sender as ImageButton;
            var embedding = button?.CommandParameter as SpeakerEmbedding;

            if (embedding != null)
            {
                speakerEmbeddingViewModel.EmbeddingsList.Remove(embedding);
            }
        }

        private async void OnSaveEmbeddingsClicked(object sender, EventArgs e)
        {
            try
            {
                string response = await speakerEmbeddingViewModel.ConfigureEmbeddings();

                if (response == "Successfully Overwrite Speaker Embeddings")
                {
                    await Application.Current.MainPage.DisplayAlert("Success", response, "OK");
                }
                else
                {
                    await Application.Current.MainPage.DisplayAlert("Error", response, "OK");
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save embeddings: {ex.Message}", "OK");
            }
        }
    }
}