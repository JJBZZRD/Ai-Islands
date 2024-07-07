using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Microsoft.Maui.Controls;

namespace frontend
{
    public partial class AIIndexPage : ContentPage
    {
        public ObservableCollection<ModelInfo> Models { get; set; }
        private List<string> downloadedModelNames;

        public AIIndexPage()
        {
            InitializeComponent();
            Models = new ObservableCollection<ModelInfo>();
            BindingContext = this;
            LoadModelData();
        }

        private async void LoadModelData()
        {
            string baseUrl = "http://127.0.0.1:8000";
            try
            {
                using (HttpClient client = new HttpClient())
                {
                    // Fetch downloaded models first
                    var downloadedModels = await client.GetFromJsonAsync<List<ModelInfo>>($"{baseUrl}/models/downloaded");
                    downloadedModelNames = downloadedModels?.ConvertAll(model => model.Name) ?? new List<string>();

                    // Fetch all available models
                    var models = await client.GetFromJsonAsync<List<ModelInfo>>($"{baseUrl}/models/");
                    if (models != null)
                    {
                        foreach (var model in models)
                        {
                            // Disable the "Add to library" button if the model is already in the library
                            if (downloadedModelNames.Contains(model.Name))
                            {
                                model.IsAddToLibraryEnabled = false;
                            }
                            Models.Add(model);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
#if WINDOWS
                await DisplayAlert("Error", $"Failed to load models: {ex.Message}", "OK");
#endif
            }
        }

        private async void OnAddToLibraryClicked(object sender, EventArgs e)
        {
            var button = sender as Button;
            if (button == null || button.BindingContext == null) return;

            var model = button.BindingContext as ModelInfo;
            if (model == null) return;

            // Check if the model is already in the library
            if (downloadedModelNames.Contains(model.Name))
            {
                await DisplayAlert("Information", $"The model {model.Name} already exists in the library.", "OK");
                return;
            }

            string baseUrl = "http://127.0.0.1:8000";
            try
            {
                using (HttpClient client = new HttpClient())
                {
                    var response = await client.GetAsync($"{baseUrl}/models/download/{model.Id}");
                    if (response.IsSuccessStatusCode)
                    {
                        await DisplayAlert("Success", $"Model {model.Name} downloaded successfully.", "OK");
                        downloadedModelNames.Add(model.Name); // Update the downloaded model list
                        model.IsAddToLibraryEnabled = false; // Disable the button
                    }
                    else
                    {
                        await DisplayAlert("Error", $"Failed to download model {model.Name}.", "OK");
                    }
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to download model {model.Name}: {ex.Message}", "OK");
            }
        }
    }
}
