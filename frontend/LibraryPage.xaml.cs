using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Microsoft.Maui.Controls;

namespace frontend
{
    public partial class LibraryPage : ContentPage
    {
        public ObservableCollection<ModelInfo> DownloadedModels { get; set; }

        public LibraryPage()
        {
            InitializeComponent();
            DownloadedModels = new ObservableCollection<ModelInfo>();
            BindingContext = this;
            LoadDownloadedModels();
        }

        private async void LoadDownloadedModels()
        {
            string baseUrl = "http://127.0.0.1:8000";
            try
            {
                using (HttpClient client = new HttpClient())
                {
                    var models = await client.GetFromJsonAsync<List<ModelInfo>>($"{baseUrl}/models/downloaded");
                    if (models != null)
                    {
                        foreach (var model in models)
                        {
                            DownloadedModels.Add(model);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
#if WINDOWS
                await DisplayAlert("Error", $"Failed to load downloaded models: {ex.Message}", "OK");
#endif
            }
        }

        private async void OnLoadModelClicked(object sender, EventArgs e)
        {
            var button = sender as Button;
            if (button == null || button.BindingContext == null) return;

            var model = button.BindingContext as ModelInfo;
            if (model == null) return;

            string baseUrl = "http://127.0.0.1:8000";
            try
            {
                using (HttpClient client = new HttpClient())
                {
                    var response = await client.PostAsync($"{baseUrl}/models/load/{model.Name}", null);
                    if (response.IsSuccessStatusCode)
                    {
                        await DisplayAlert("Success", $"Model {model.Name} loaded successfully.", "OK");
                    }
                    else
                    {
                        await DisplayAlert("Error", $"Failed to load model {model.Name}.", "OK");
                    }
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to load model {model.Name}: {ex.Message}", "OK");
            }
        }
    }
}
