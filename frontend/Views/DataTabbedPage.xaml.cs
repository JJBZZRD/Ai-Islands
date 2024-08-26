using Microsoft.Maui.Controls;
using frontend.Services;
using frontend.Models.ViewModels;

namespace frontend.Views
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class DataTabbedPage : ContentPage
    {

        public DataTabbedPage()
        {
            InitializeComponent();
            ShowDataRefineryPage(); // Show Data Refinery page by default
        }

        // protected override void OnAppearing()
        // {
        //     base.OnAppearing();
        //     Title = "Data Management";
        // }

        private void OnDataRefineryClicked(object sender, EventArgs e) => ShowDataRefineryPage();
        private void OnSpeakerEmbeddingClicked(object sender, EventArgs e) => ShowSpeakerEmbeddingView();

        private void ShowDataRefineryPage()
        {
            ContentContainer.Content = new DataRefinery();
        }

        private void ShowSpeakerEmbeddingView()
        {
            ContentContainer.Content =  new SpeakerEmbeddingView();
        }
    }
}