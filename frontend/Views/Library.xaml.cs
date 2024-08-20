using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Net.Http;
using System.Text.Json;
using System.Windows.Input;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.ComponentModel;
using CommunityToolkit.Mvvm.Messaging;
using frontend.Services;


namespace frontend.Views
{
    public class RefreshLibraryMessage { }
    public partial class Library : ContentPage, INotifyPropertyChanged
    {
        private ObservableCollection<Model> _allModels;
        public ObservableCollection<Model> AllModels
        {
            get => _allModels;
            set
            {
                _allModels = value;
                OnPropertyChanged();
            }
        }

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

        public ObservableCollection<ModelTypeFilter> ModelTypes { get; set; }
        public bool FilterOnline { get; set; }
        public bool FilterOffline { get; set; }

        public ICommand NavigateToModelInfoCommand { get; private set; }

        private readonly LibraryService _libraryService;
        private readonly ModelService _modelService;

        public Library()
        {
            InitializeComponent();
            Models = new ObservableCollection<Model>();
            AllModels = new ObservableCollection<Model>();
            ModelTypes = new ObservableCollection<ModelTypeFilter>();
            BindingContext = this;
            _libraryService = new LibraryService();
            _modelService = new ModelService();

            WeakReferenceMessenger.Default.Register<RefreshLibraryMessage>(this, async (r, m) =>
            {
                await MainThread.InvokeOnMainThreadAsync(async () => await RefreshLibraryModels());
            });

            MainThread.BeginInvokeOnMainThread(async () => await RefreshLibraryModels());
        }

        private void InitializeFilterPopup()
        {
            var distinctTypes = AllModels.Select(m => m.PipelineTag).Distinct().OrderBy(t => t).ToList();
            ModelTypes = new ObservableCollection<ModelTypeFilter>(
                distinctTypes.Select(tag => new ModelTypeFilter { TypeName = tag, IsSelected = false })
            );
            FilterPopup.ModelTypes = ModelTypes;
            FilterPopup.AllModels = AllModels;
            FilterPopup.FilterOnline = FilterOnline;
            FilterPopup.FilterOffline = FilterOffline;

            System.Diagnostics.Debug.WriteLine($"InitializeFilterPopup: ModelTypes count: {ModelTypes.Count}");
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

        private void OnApplyFilters(object sender, FilteredModelsEventArgs e)
        {
            Models = new ObservableCollection<Model>(e.FilteredModels);
            FilterOnline = FilterPopup.FilterOnline;
            FilterOffline = FilterPopup.FilterOffline;
            FilterPopup.IsVisible = false;
        }

        private void OnResetFilters(object sender, EventArgs e)
        {
            Models = new ObservableCollection<Model>(AllModels);
            FilterOnline = false;
            FilterOffline = false;
            FilterPopup.IsVisible = false;
        }

        private async void OnModelSelected(object sender, TappedEventArgs e)
        {
            if (e.Parameter is Model selectedModel)
            {
                await Navigation.PushAsync(new LibraryTabbedPage(selectedModel));
            }
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
                var modelList = await _libraryService.GetLibrary(); // Fetch models from the library

                var newModels = new ObservableCollection<Model>();

                foreach (var model in modelList)
                {
                    // Add LoadOrStopCommand to the model
                    model.LoadOrStopCommand = new Command(() => LoadOrStopModel(model.ModelId));

                    // Set PipelineTag if it's null or empty
                    if (string.IsNullOrEmpty(model.PipelineTag))
                    {
                        model.PipelineTag = !string.IsNullOrEmpty(model.ModelClass) ? model.ModelClass : "Unknown";
                    }

                    // Check if the model is currently loaded e
                    bool isLoaded = await _modelService.IsModelLoaded(model.ModelId);
                    model.IsLoaded = isLoaded; 
                    System.Diagnostics.Debug.WriteLine($"Model: {model.ModelId}, PipelineTag: {model.PipelineTag}, IsLoaded: {isLoaded}");

                    newModels.Add(model);
                }

                AllModels = newModels;
                Models = new ObservableCollection<Model>(AllModels);
                System.Diagnostics.Debug.WriteLine($"Total models loaded: {Models.Count}");

                InitializeFilterPopup();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading library model data: {ex.Message}");
                await DisplayAlert("Error", $"Failed to refresh library models: {ex.Message}", "OK");
            }
        }

        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(e.NewTextValue))
            {
                Models = new ObservableCollection<Model>(AllModels);
            }
            else
            {
                var searchTerm = e.NewTextValue.ToLower();
                var filteredModels = AllModels.Where(m =>
                    m.ModelId.ToLower().Contains(searchTerm) ||
                    (m.PipelineTag != null && m.PipelineTag.ToLower().Contains(searchTerm))
                ).ToList();

                Models = new ObservableCollection<Model>(filteredModels);
            }
        }

        private async void LoadOrStopModel(string ModelId)
        {
            var model = Models.FirstOrDefault(m => m.ModelId == ModelId);
            if (model == null) return;

            var isLoaded = await _modelService.IsModelLoaded(ModelId);
            string action = isLoaded ? "unload" : "load";

            try
            {
                var terminalPage = new TerminalPage($"{action.ToUpperInvariant()} MODEL: {ModelId}");
                await Navigation.PushAsync(terminalPage);

                HttpResponseMessage response;
                if (isLoaded)
                {
                    response = await _modelService.UnloadModel(ModelId);
                    terminalPage.AppendOutput($"Unloading model {ModelId}...");
                }
                else
                {
                    response = await _modelService.LoadModel(ModelId);
                    terminalPage.AppendOutput($"Loading model {ModelId}...");
                }

                if (response.IsSuccessStatusCode)
                {
                    model.IsLoaded = !isLoaded; // Update the IsLoaded property
                    terminalPage.AppendOutput($"Model {ModelId} {action}ed successfully.");
                }
                else
                {
                    terminalPage.AppendOutput($"Failed to {action} model {ModelId}.");
                    var errorContent = await response.Content.ReadAsStringAsync();
                    var errorJson = JsonSerializer.Deserialize<JsonElement>(errorContent);
                    var errorMessage = errorJson.GetProperty("error").GetProperty("message").GetString();
                    await DisplayAlert("Error", $"Failed to {action} model {ModelId}: {errorMessage}", "OK");
                }

                await Task.Delay(2000); // Give user time to read the output
                await Navigation.PopAsync(); // Close the terminal page

                OnPropertyChanged(nameof(Models)); // Notify UI of changes
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to {action} model {ModelId}: {ex.Message}", "OK");
            }
        }

        protected override void OnDisappearing()
        {
            base.OnDisappearing();
            WeakReferenceMessenger.Default.Unregister<RefreshLibraryMessage>(this);
        }
    }
}