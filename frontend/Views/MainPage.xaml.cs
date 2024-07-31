using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Windows.Input;
using System.Net.Http;
using System.Text.Json;
using System.Collections.Generic;
using System;
using frontend.Models;
using CommunityToolkit.Mvvm.Messaging;

namespace frontend.Views
{
    public partial class MainPage : ContentPage, INotifyPropertyChanged //implement inotify for ui updates
    {
        private ObservableCollection<ModelItem> AllModels { get; set; }
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

        public ICommand NavigateToModelInfoCommand { get; private set; }

        // page constructor
        public MainPage()
        {
            InitializeComponent();
            Models = new ObservableCollection<ModelItem>();
            BindingContext = this;
            LoadModels();
        }

        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            System.Diagnostics.Debug.WriteLine($"Search text changed to: '{e.NewTextValue}'");

            if (string.IsNullOrWhiteSpace(e.NewTextValue)) // check if search text is emoty
            {
                // restore the full list back when search is empty
                Models = new ObservableCollection<ModelItem>(AllModels);
            }
            else
            {
                var searchTerm = e.NewTextValue.ToLower();  // converting search term to lowercase for case-sensitive comparison
                // for each model in all models, check if the search term is present in the model name or pipeline tag
                var filteredModels = AllModels.Where(m =>
                    m.Name.ToLower().Contains(searchTerm) ||
                    (m.PipelineTag != null && m.PipelineTag.ToLower().Contains(searchTerm))
                ).ToList();
                // filtered result used to create new collection
                Models = new ObservableCollection<ModelItem>(filteredModels);
            }

            System.Diagnostics.Debug.WriteLine($"After filtering: Models count: {Models.Count}");
            OnPropertyChanged(nameof(Models)); // notify UI that the models collection has changed
        }

        private async void OnModelSelected(object sender, TappedEventArgs e)
        {
            if (sender is Frame frame && frame.BindingContext is ModelItem model)
            {
                try
                {
                    var modelJson = System.Text.Json.JsonSerializer.Serialize(model);
                    System.Diagnostics.Debug.WriteLine($"Model selected: {model.Name}");
                    System.Diagnostics.Debug.WriteLine($"Serialized model: {modelJson}");

                    await Navigation.PushAsync(new ModelInfoPage(model));
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Navigation error: {ex.Message}");
                    System.Diagnostics.Debug.WriteLine($"StackTrace: {ex.StackTrace}");
                    await DisplayAlert("Error", "Unable to open model details.", "OK");
                }
            }
        }

        private void OnAddToLibraryClicked(object sender, EventArgs e)
        {
            if (sender is Button button && button.BindingContext is ModelItem model)
            {
                AddToLibrary(model.Name);
            }
        }

        private async void LoadModels()
        {
            try
            {
                // create HTTP request to client
                var client = new HttpClient();
                var response = await client.GetAsync("http://127.0.0.1:8000/models?source=index");
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    System.Diagnostics.Debug.WriteLine($"API Response: {content}");
                    var modelsDict = JsonSerializer.Deserialize<Dictionary<string, ModelInfo>>(content); // deserialise json response into dictionary of modelinfo objects

                    // clear existing models and populate models collection with new modelitem object
                    
                    Models.Clear();

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
                            Tags = model.Value.Tags ?? new List<string>(),
                            LoadOrStopCommand = new Command(() => AddToLibrary(model.Key))
                        };
                        System.Diagnostics.Debug.WriteLine($"  ModelItem PipelineTag: '{modelItem.PipelineTag}'");
                        Models.Add(modelItem);
                    }
                    System.Diagnostics.Debug.WriteLine($"Total models loaded: {Models.Count}");

                    // initialises AllModels with the same data as Models for search functionality
                    AllModels = new ObservableCollection<ModelItem>(Models);
                    System.Diagnostics.Debug.WriteLine($"AllModels initialized with {AllModels.Count} items");
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine($"API request failed with status code: {response.StatusCode}");
                    await DisplayAlert("Error", "Failed to load models. Please try again.", "OK");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading model data: {ex.Message}");
                await DisplayAlert("Error", $"An error occurred while loading models: {ex.Message}", "OK");
            }
        }

        public async void AddToLibrary(string modelName)
        {
            var alertPage = new AlertPage("Download", $"Starting download for {modelName}", true);
            await Navigation.PushModalAsync(alertPage);
            try
            {
                // call the API to download the model
                var client = new HttpClient();
                var response = await client.PostAsync($"http://127.0.0.1:8000/download-model?model_id={modelName}", null);

                if (response.IsSuccessStatusCode)
                {
                    // Simulate download progress
                    for (int i = 0; i <= 100; i++)
                    {
                        alertPage.UpdateProgress(i / 100.0);
                        await Task.Delay(50); // Adjust this delay to control the speed of the simulation
                    }

                    // wait for user to click "OK"
                    await alertPage.CompletionSource.Task;

                    System.Diagnostics.Debug.WriteLine($"Model {modelName} downloaded successfully");

                    // Update the local state in the ModelItem
                    var model = Models.FirstOrDefault(m => m.Name == modelName);
                    if (model != null)
                    {
                        model.IsInLibrary = true;
                    }
                    System.Diagnostics.Debug.WriteLine("Sending RefreshLibraryMessage");

                    // notify the library page to refresh
                    WeakReferenceMessenger.Default.Send(new RefreshLibraryMessage());
                }
                else
                {
                    await DisplayAlert("Error", $"Failed to download model {modelName}", "OK");
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
            finally
            {
                await Navigation.PopModalAsync();
            }
        }
    }
}