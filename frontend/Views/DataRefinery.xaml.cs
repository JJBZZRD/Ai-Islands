using Microsoft.Maui.Controls;
using System;
using System.Threading.Tasks;
using frontend.Services;

namespace frontend.Views
{
    public partial class DataRefinery : ContentPage
    {
        private readonly DataService _dataService;

        public DataRefinery()
        {
            InitializeComponent();
            _dataService = new DataService();
        }

        private async void OnFindDatasetClicked(object sender, EventArgs e)
        {
            try
            {
                var result = await FilePicker.PickAsync();
                if (result != null)
                {
                    FilePathEntry.Text = result.FullPath;
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Unable to pick file: {ex.Message}", "OK");
            }
        }

        private async void OnUploadToAIIslandsClicked(object sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(FilePathEntry.Text))
            {
                await DisplayAlert("Error", "Please select a file first.", "OK");
                return;
            }

            try
            {
                var result = await _dataService.UploadDataset(FilePathEntry.Text);
                await DisplayAlert("Success", "Dataset uploaded successfully!", "OK");
                // You might want to update the UI or perform additional actions here
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to upload dataset: {ex.Message}", "OK");
            }
        }
    }
}