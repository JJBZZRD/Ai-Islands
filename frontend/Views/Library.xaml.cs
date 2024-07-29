using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Net.Http;
using System.Text.Json;
using System.IO;
using System.Windows.Input;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.ComponentModel;

namespace frontend.Views
{
    public partial class Library : ContentPage, INotifyPropertyChanged
    {
        private ObservableCollection<ModelItem> _models;
        public ObservableCollection<ModelItem> Models
        {
            get => _models;
            set
            {
                _models = value;
                OnPropertyChanged();
            }
        }

        public Library()
        {
            InitializeComponent();
            Models = new ObservableCollection<ModelItem>();
            BindingContext = this;
            LoadLibraryModels();
        }

        private async void LoadLibraryModels()
        {
            try
            {
                using (HttpClient client = new HttpClient())
                {
                    var response = await client.GetAsync("http://127.0.0.1:8000/models?source=library");
                    if (response.IsSuccessStatusCode)
                    {
                        var jsonString = await response.Content.ReadAsStringAsync();
                        var libraryModels = JsonSerializer.Deserialize<Dictionary<string, ModelInfo>>(jsonString);

                        foreach (var model in libraryModels)
                        {
                            Models.Add(new ModelItem
                            {
                                Name = model.Key,
                                PipelineTag = model.Value.PipelineTag,
                                IsOnline = model.Value.IsOnline,
                                Description = model.Value.Description ?? "No description available",
                                Tags = string.Join(", ", model.Value.Tags ?? new List<string>()),
                                LoadOrStopCommand = new Command(() => LoadOrStopModel(model.Key))
                            });
                        }
                    }
                    else
                    {
                        await DisplayAlert("Error", "Failed to load library models.", "OK");
                    }
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to load library models: {ex.Message}", "OK");
            }
        }

        private async void LoadOrStopModel(string modelName)
        {
            var model = Models.FirstOrDefault(m => m.Name == modelName);
            if (model == null) return;

            string baseUrl = "http://127.0.0.1:8000";
            string endpoint = model.IsOnline ? "stop" : "load";

            try
            {
                using (HttpClient client = new HttpClient())
                {
                    var response = await client.PostAsync($"{baseUrl}/models/{endpoint}?model_id={modelName}", null);
                    if (response.IsSuccessStatusCode)
                    {
                        model.IsOnline = !model.IsOnline;
                        await DisplayAlert("Success", $"Model {modelName} {endpoint}ed successfully.", "OK");
                    }
                    else
                    {
                        await DisplayAlert("Error", $"Failed to {endpoint} model {modelName}.", "OK");
                    }
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to {endpoint} model {modelName}: {ex.Message}", "OK");
            }
        }
    }
}