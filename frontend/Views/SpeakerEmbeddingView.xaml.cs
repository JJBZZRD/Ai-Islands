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
                    await Application.Current.MainPage.DisplayAlert("Error", "Failed to save embeddings", "OK");
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save embeddings: {ex.Message}", "OK");
            }
        }
    }
}