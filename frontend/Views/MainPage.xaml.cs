using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Windows.Input;
using System.Net.Http;
using System.Text.Json;
using System.Collections.Generic;
using System;
using frontend.Models;

namespace frontend.Views
{
    public partial class MainPage : ContentPage, INotifyPropertyChanged
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

        public MainPage()
        {
            InitializeComponent();
            Models = new ObservableCollection<ModelItem>();
            BindingContext = this;
            LoadModels();
        }

        private async void LoadModels()
        {
            var client = new HttpClient();
            var response = await client.GetAsync("http://127.0.0.1:8000/models");
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                System.Diagnostics.Debug.WriteLine($"API Response: {content}");
                var modelsDict = JsonSerializer.Deserialize<Dictionary<string, ModelInfo>>(content);
                foreach (var model in modelsDict)
                {
                    System.Diagnostics.Debug.WriteLine($"Model: {model.Key}");
                    System.Diagnostics.Debug.WriteLine($"  PipelineTag: '{model.Value.PipelineTag}'");
                    System.Diagnostics.Debug.WriteLine($"  Type: '{model.Value.Type}'");
                    var modelItem = new ModelItem
                    {
                        Name = model.Key,
                        PipelineTag = !string.IsNullOrEmpty(model.Value.PipelineTag) ? model.Value.PipelineTag : 
                                    !string.IsNullOrEmpty(model.Value.Type) ? model.Value.Type : "Unknown",
                        IsOnline = model.Value.IsOnline,
                        Description = model.Value.Description ?? "No description available",
                        Tags = string.Join(", ", model.Value.Tags ?? new List<string>()),
                        LoadOrStopCommand = new Command(() => AddToLibrary(model.Key))
                    };
                    System.Diagnostics.Debug.WriteLine($"  ModelItem PipelineTag: '{modelItem.PipelineTag}'");
                    Models.Add(modelItem);
                }
                System.Diagnostics.Debug.WriteLine($"Total models loaded: {Models.Count}");
            }
            else
            {
                System.Diagnostics.Debug.WriteLine($"API request failed with status code: {response.StatusCode}");
            }
        }

        private void AddToLibrary(string modelName)
        {
            // Implement the logic to add the model to the library
            Console.WriteLine($"Adding {modelName} to library");
        }
    }
}