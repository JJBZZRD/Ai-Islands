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
using CommunityToolkit.Mvvm.Messaging;

namespace frontend.Views

{
    public class RefreshLibraryMessage { }
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

        private ObservableCollection<ModelItem> _allModels;
        public ObservableCollection<ModelItem> AllModels
        {
            get => _allModels;
            set
            {
                _allModels = value;
                OnPropertyChanged();
            }
        }
        public ICommand NavigateToModelInfoCommand { get; private set; }

        // page constructor
        public Library()
        {
            InitializeComponent();
            Models = new ObservableCollection<ModelItem>();
            AllModels = new ObservableCollection<ModelItem>();
            BindingContext = this;

            // receive refresh library message from the main page
            WeakReferenceMessenger.Default.Register<RefreshLibraryMessage>(this, async (r, m) =>
            {
                System.Diagnostics.Debug.WriteLine("RefreshLibraryMessage received");
                await MainThread.InvokeOnMainThreadAsync(async () =>
                {
                    await RefreshLibraryModels();
                });
            });

            MainThread.BeginInvokeOnMainThread(async () => await RefreshLibraryModels());
        }

        protected override async void OnAppearing()
        {
            base.OnAppearing();
            await RefreshLibraryModels();
        }

        private async Task RefreshLibraryModels()
        {
            try
            {
                using (HttpClient client = new HttpClient())
                {
                    var response = await client.GetAsync("http://127.0.0.1:8000/models?source=library"); // fetch library data
                    if (response.IsSuccessStatusCode)
                    {
                        // deserialie the json response into a dictionary
                        var jsonString = await response.Content.ReadAsStringAsync();
                        var libraryModels = JsonSerializer.Deserialize<Dictionary<string, ModelInfo>>(jsonString);

                        // create new collection of ModelItem from the deserialised data
                        var newModels = new ObservableCollection<ModelItem>();
                        foreach (var model in libraryModels)
                        {
                            newModels.Add(new ModelItem
                            {
                                Name = model.Key,
                                PipelineTag = model.Value.PipelineTag ?? model.Value.Type ?? "Unknown",
                                IsOnline = model.Value.IsOnline,
                                Description = model.Value.Description ?? "No description available",
                                Tags = model.Value.Tags != null ? new List<string>(model.Value.Tags) : new List<string>(),
                                LoadOrStopCommand = new Command(() => LoadOrStopModel(model.Key))
                            });
                        }

                        AllModels = new ObservableCollection<ModelItem>(newModels);
                        Models = new ObservableCollection<ModelItem>(newModels);

                        OnPropertyChanged(nameof(Models));
                        OnPropertyChanged(nameof(AllModels));
                    }
                    else
                    {
                        await DisplayAlert("Error", "Failed to refresh library models.", "OK");
                    }
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to refresh library models: {ex.Message}", "OK");
            }
        }

        
        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            System.Diagnostics.Debug.WriteLine($"Search text changed to: '{e.NewTextValue}'");

            if (string.IsNullOrWhiteSpace(e.NewTextValue)) 
            {
                Models = new ObservableCollection<ModelItem>(AllModels);
            }
            else
            {
                var searchTerm = e.NewTextValue.ToLower();
                var filteredModels = AllModels.Where(m =>
                    m.Name.ToLower().Contains(searchTerm) ||
                    (m.PipelineTag != null && m.PipelineTag.ToLower().Contains(searchTerm))
                ).ToList();

                Models = new ObservableCollection<ModelItem>(filteredModels);
            }

            System.Diagnostics.Debug.WriteLine($"After filtering: Models count: {Models.Count}");
            OnPropertyChanged(nameof(Models));
        }

        public async Task RefreshModels()
        {
            System.Diagnostics.Debug.WriteLine("RefreshModels started");
            await RefreshLibraryModels();
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
        protected override void OnDisappearing()
        {
            base.OnDisappearing();
            WeakReferenceMessenger.Default.Unregister<RefreshLibraryMessage>(this);
        }
    }
}