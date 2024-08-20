using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Windows.Input;
using System.Net.Http;
using System.Text.Json;
using System.Collections.Generic;
using System;
using frontend.Models;
using CommunityToolkit.Mvvm.Messaging;
using System.Linq;
using frontend.Services;
using Newtonsoft.Json;

namespace frontend.Views
{
    public partial class ModelIndex : ContentPage, INotifyPropertyChanged //implement inotify for ui updates
    {
        public ObservableCollection<Model> AllModels { get; set; }
        private ObservableCollection<Model> _models;
        public ObservableCollection<Model> Models
        {
            get => _models;
            set
            {
                _models = value;
                OnPropertyChanged();
            }
        }

        // public ICommand NavigateToModelInfoCommand { get; private set; }
        private ObservableCollection<ModelTypeFilter> _modelTypes;
        public ObservableCollection<ModelTypeFilter> ModelTypes
        {
            get => _modelTypes;
            set
            {
                _modelTypes = value;
                OnPropertyChanged(nameof(ModelTypes));
            }
        }
        public bool FilterOnline { get; set; }
        public bool FilterOffline { get; set; }

        private readonly LibraryService _libraryService;

        // page constructor
        public ModelIndex()
        {
            InitializeComponent();
            Models = new ObservableCollection<Model>();
            AllModels = new ObservableCollection<Model>();
            ModelTypes = new ObservableCollection<ModelTypeFilter>();
            FilterOnline = FilterOffline = false;
            BindingContext = this;
            _libraryService = new LibraryService();
            LoadModels();
            AuthTokenPopup.InputSubmitted += OnAuthTokenSubmitted;
            AuthTokenPopup.InputCancelled += OnAuthTokenCancelled;
            System.Diagnostics.Debug.WriteLine("AuthTokenPopup initialized and events wired up");
        }

        private void OnFilterClicked(object sender, EventArgs e)
        {
            FilterPopup.IsVisible = true;
        }

        private void OnCloseFilterPopup(object sender, EventArgs e)
        {
            FilterPopup.IsVisible = false;
        }

        private void OnOverlayTapped(object sender, EventArgs e)
        {
            FilterPopup.IsVisible = false;
        }

        private void InitializeFilterPopup()
        {
            var distinctTypes = AllModels.Select(m => m.PipelineTag).Distinct().OrderBy(t => t).ToList();
            FilterPopup.ModelTypes = new ObservableCollection<ModelTypeFilter>(
                distinctTypes.Select(tag => new ModelTypeFilter { TypeName = tag, IsSelected = false })
            );
            FilterPopup.AllModels = AllModels;

            System.Diagnostics.Debug.WriteLine($"Initialized FilterPopup with {FilterPopup.ModelTypes.Count} types");
            foreach (var type in FilterPopup.ModelTypes)
            {
                System.Diagnostics.Debug.WriteLine($"Type: {type.TypeName}");
            }
        }

        private void OnApplyFilters(object sender, FilteredModelsEventArgs e)
        {
            FilterPopup.IsVisible = false;
            Models = e.FilteredModels;
        }

        private void OnResetFilters(object sender, EventArgs e)
        {
            FilterPopup.IsVisible = false;
            Models = new ObservableCollection<Model>(AllModels);
        }

        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            System.Diagnostics.Debug.WriteLine($"Search text changed to: '{e.NewTextValue}'");

            if (string.IsNullOrWhiteSpace(e.NewTextValue)) // check if search text is emoty
            {
                // restore the full list back when search is empty
                Models = new ObservableCollection<Model>(AllModels);
            }
            else
            {
                var searchTerm = e.NewTextValue.ToLower();  // converting search term to lowercase for case-sensitive comparison
                // for each model in all models, check if the search term is present in the model name or pipeline tag
                var filteredModels = AllModels.Where(m =>
                    m.ModelId.ToLower().Contains(searchTerm) ||
                    (m.PipelineTag != null && m.PipelineTag.ToLower().Contains(searchTerm))
                ).ToList();
                // filtered result used to create new collection
                Models = new ObservableCollection<Model>(filteredModels);
            }

            System.Diagnostics.Debug.WriteLine($"After filtering: Models count: {Models.Count}");
            OnPropertyChanged(nameof(Models)); // notify UI that the models collection has changed
        }

        private async void OnModelSelected(object sender, TappedEventArgs e)
        {
            if (e.Parameter is Model selectedModel)
            {
                await Navigation.PushAsync(new ModelInfoPage(selectedModel));
            }
        }

        private void OnAddToLibraryClicked(object sender, EventArgs e)
        {
            if (sender is Button button && button.BindingContext is Model model)
            {
                System.Diagnostics.Debug.WriteLine($"Add to Library clicked for model: {model.ModelId}");
                
                bool requiresAuth = false;

                if (model.Requirements != null && 
                    model.Requirements.TryGetValue("requires_auth", out JsonElement requiresAuthValue))
                {
                    System.Diagnostics.Debug.WriteLine($"requires_auth raw value: {requiresAuthValue}, Type: {requiresAuthValue.ValueKind}");
                    
                    switch (requiresAuthValue.ValueKind)
                    {
                        case JsonValueKind.True:
                            requiresAuth = true;
                            break;
                        case JsonValueKind.False:
                            requiresAuth = false;
                            break;
                        case JsonValueKind.String:
                            var stringValue = requiresAuthValue.GetString();
                            requiresAuth = stringValue?.Equals("True", StringComparison.OrdinalIgnoreCase) ?? false;
                            break;
                        default:
                            System.Diagnostics.Debug.WriteLine($"Unexpected requires_auth value kind: {requiresAuthValue.ValueKind}");
                            break;
                    }
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine("requires_auth key not found in Requirements");
                }

                System.Diagnostics.Debug.WriteLine($"requires_auth parsed as: {requiresAuth}");

                if (requiresAuth)
                {
                    System.Diagnostics.Debug.WriteLine($"Model {model.ModelId} requires authentication");
                    AuthTokenPopup.BindingContext = model;
                    AuthTokenPopup.IsVisible = true;
                    System.Diagnostics.Debug.WriteLine("AuthTokenPopup set to visible");
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine($"Model {model.ModelId} does not require authentication");
                    AddToLibrary(model.ModelId);
                }
            }
            else
            {
                System.Diagnostics.Debug.WriteLine("Button BindingContext is not a Model");
            }
        }

        private void OnAuthTokenSubmitted(object sender, string authToken)
        {
            System.Diagnostics.Debug.WriteLine("Auth token submitted");
            if (AuthTokenPopup.BindingContext is Model model)
            {
                System.Diagnostics.Debug.WriteLine($"Adding model {model.ModelId} to library with auth token");
                AddToLibrary(model.ModelId, authToken);
                AuthTokenPopup.IsVisible = false;
            }
        }

        private void OnAuthTokenCancelled(object sender, EventArgs e)
        {
            System.Diagnostics.Debug.WriteLine("Auth token input cancelled");
            AuthTokenPopup.IsVisible = false;
        }

        private async void LoadModels()
        {
            System.Diagnostics.Debug.WriteLine("LoadModels method started");
            try
            {
                System.Diagnostics.Debug.WriteLine("Calling GetModelIndex from LibraryService");
                var modelList = await _libraryService.GetModelIndex();
                System.Diagnostics.Debug.WriteLine($"GetModelIndex returned {modelList.Count} models");

                Models.Clear();
                System.Diagnostics.Debug.WriteLine("Cleared existing Models collection");

                foreach (var model in modelList)
                {
                    System.Diagnostics.Debug.WriteLine($"Processing model: {model.ModelId}");
                    
                    model.LoadOrStopCommand = new Command(() => AddToLibrary(model.ModelId));
                    System.Diagnostics.Debug.WriteLine($"Added LoadOrStopCommand for model: {model.ModelId}");

                    if (string.IsNullOrEmpty(model.PipelineTag))
                    {
                        model.PipelineTag = !string.IsNullOrEmpty(model.ModelClass) ? model.ModelClass : "Unknown";
                        System.Diagnostics.Debug.WriteLine($"Set PipelineTag for model {model.ModelId}: {model.PipelineTag}");
                    }

                    Models.Add(model);
                    System.Diagnostics.Debug.WriteLine($"Added model to Models collection: {model.ModelId}, PipelineTag: {model.PipelineTag}, IsOnline: {model.IsOnline}");
                }

                System.Diagnostics.Debug.WriteLine($"Total models loaded: {Models.Count}");

                AllModels = new ObservableCollection<Model>(Models);
                System.Diagnostics.Debug.WriteLine($"AllModels initialized with {AllModels.Count} items");

                System.Diagnostics.Debug.WriteLine("Updating ModelTypes");
                var types = AllModels.Select(m => m.PipelineTag).Where(t => !string.IsNullOrEmpty(t)).Distinct().OrderBy(t => t);
                ModelTypes.Clear();
                foreach (var type in types)
                {
                    ModelTypes.Add(new ModelTypeFilter { TypeName = type, IsSelected = false });
                    System.Diagnostics.Debug.WriteLine($"Added ModelType: {type}");
                }
                System.Diagnostics.Debug.WriteLine($"Total ModelTypes: {ModelTypes.Count}");

                System.Diagnostics.Debug.WriteLine("Initializing FilterPopup");
                InitializeFilterPopup();
                System.Diagnostics.Debug.WriteLine("FilterPopup initialized");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error in LoadModels: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"StackTrace: {ex.StackTrace}");
                await DisplayAlert("Error", $"An error occurred while loading models: {ex.Message}", "OK");
            }
            System.Diagnostics.Debug.WriteLine("LoadModels method completed");
        }

        public async void AddToLibrary(string ModelId, string authToken = null)
        {
            var alertPage = new AlertPage("Download", $"Starting download for {ModelId}", true);
            await Navigation.PushModalAsync(alertPage);
            try
            {
                using (var client = new HttpClient())
                {
                    client.Timeout = TimeSpan.FromMilliseconds(-1);

                    var requestUri = $"http://127.0.0.1:8000/model/download-model?model_id={ModelId}";
                    if (!string.IsNullOrEmpty(authToken))
                    {
                        requestUri += $"&auth_token={authToken}";
                    }

                    var response = await client.PostAsync(requestUri, null);

                    if (response.IsSuccessStatusCode)
                    {
                        // simulate download progress. I guess this should be modified to reflect actual download progress
                        for (int i = 0; i <= 100; i++)
                        {
                            alertPage.UpdateDownloadProgress(i / 100.0);
                            await Task.Delay(50); // adjust this delay to control the speed of the simulation
                        }

                        // wait for user to click "OK"
                        await alertPage.CompletionSource.Task;

                        System.Diagnostics.Debug.WriteLine($"Model {ModelId} downloaded successfully");

                        // update the local state in the Model
                        var model = Models.FirstOrDefault(m => m.ModelId == ModelId);
                        if (model != null)
                        {
                            model.IsInLibrary = true;
                        }
                        System.Diagnostics.Debug.WriteLine("Sending RefreshLibraryMessage");

                        // notify the library page to refresh
                        WeakReferenceMessenger.Default.Send(new RefreshLibraryMessage());
                    }
                    else if (response.StatusCode == System.Net.HttpStatusCode.ServiceUnavailable)
                    {
                        var errorContent = await response.Content.ReadAsStringAsync();
                        System.Diagnostics.Debug.WriteLine($"Error content: {errorContent}");
                        var errorMessage = ParseErrorMessage(errorContent);
                        await DisplayAlert("Model Unavailable", errorMessage, "OK");
                    }
                    else
                    {
                        var errorContent = await response.Content.ReadAsStringAsync();
                        System.Diagnostics.Debug.WriteLine($"Error content: {errorContent}");
                        var errorMessage = ParseErrorMessage(errorContent);
                        await DisplayAlert("Error", $"Failed to download model: {errorMessage}", "OK");
                    }
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

        private string ParseErrorMessage(string errorContent)
        {
            try
            {
                var errorResponse = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(errorContent);
                if (errorResponse != null && errorResponse.TryGetValue("error", out var errorObj))
                {
                    if (errorObj is JsonElement jsonElement && jsonElement.TryGetProperty("message", out var messageElement))
                    {
                        return messageElement.GetString() ?? "Unknown error occurred";
                    }
                }
            }
            catch (System.Text.Json.JsonException)
            {
                // JSON parsing failed, fall back to checking for "not found" in the raw content
            }

            if (errorContent.Contains("not found", StringComparison.OrdinalIgnoreCase))
            {
                return "Model not found in the repository";
            }

            return errorContent.Length > 100 ? errorContent.Substring(0, 100) + "..." : errorContent;
        }
    }

    public class ModelTypeFilter : INotifyPropertyChanged
    {
        public string TypeName { get; set; }
        private bool _isSelected;
        public bool IsSelected
        {
            get => _isSelected;
            set
            {
                _isSelected = value;
                OnPropertyChanged(nameof(IsSelected));
            }
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    public class ErrorResponse
    {
        public required string Message { get; set; }
    }
}