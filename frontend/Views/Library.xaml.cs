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
using frontend.ViewModels;

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

        private ObservableCollection<ModelListItemViewModel> _models;
        public ObservableCollection<ModelListItemViewModel> Models
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
            Models = new ObservableCollection<ModelListItemViewModel>();
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
            Models = new ObservableCollection<ModelListItemViewModel>(e.FilteredModels.Select(m => new ModelListItemViewModel(m)
            {
                LoadOrStopCommand = new Command(() => LoadOrStopModel(m.ModelId))
            }));
            FilterOnline = FilterPopup.FilterOnline;
            FilterOffline = FilterPopup.FilterOffline;
            FilterPopup.IsVisible = false;
        }

        private void OnResetFilters(object sender, EventArgs e)
        {
            Models = new ObservableCollection<ModelListItemViewModel>(AllModels.Select(m => new ModelListItemViewModel(m)
            {
                LoadOrStopCommand = new Command(() => LoadOrStopModel(m.ModelId))
            }));
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
                Models = new ObservableCollection<ModelListItemViewModel>(AllModels.Select(m => new ModelListItemViewModel(m)
                {
                    LoadOrStopCommand = new Command(() => LoadOrStopModel(m.ModelId))
                }));
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
                Models = new ObservableCollection<ModelListItemViewModel>(AllModels.Select(m => new ModelListItemViewModel(m)
                {
                    LoadOrStopCommand = new Command(() => LoadOrStopModel(m.ModelId))
                }));
            }
            else
            {
                var searchTerm = e.NewTextValue.ToLower();
                var filteredModels = AllModels.Where(m =>
                    m.ModelId.ToLower().Contains(searchTerm) ||
                    (m.PipelineTag != null && m.PipelineTag.ToLower().Contains(searchTerm))
                ).ToList();

                Models = new ObservableCollection<ModelListItemViewModel>(filteredModels.Select(m => new ModelListItemViewModel(m)
                {
                    LoadOrStopCommand = new Command(() => LoadOrStopModel(m.ModelId))
                }));
            }
        }

        private async void LoadOrStopModel(string ModelId)
        {
            var viewModel = Models.FirstOrDefault(vm => vm.ModelId == ModelId);
            if (viewModel == null) return;

            viewModel.IsButtonEnabled = false;
            string action = viewModel.IsLoaded ? "unload" : "load";

            try
            {
                LoadingOverlay.IsVisible = true;
                LoadingIndicator.IsRunning = true;
                LoadingText.Text = $"{char.ToUpper(action[0])}{action.Substring(1)}ing Model...";

                HttpResponseMessage response;
                if (viewModel.IsLoaded)
                {
                    response = await _modelService.UnloadModel(ModelId);
                }
                else
                {
                    response = await _modelService.LoadModel(ModelId);
                }

                if (response.IsSuccessStatusCode)
                {
                    viewModel.IsLoaded = !viewModel.IsLoaded;
                    LoadingText.Text = "Success!";
                    await Task.Delay(1000); // Show success message for 1 second
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    var errorJson = JsonSerializer.Deserialize<JsonElement>(errorContent);
                    var errorMessage = errorJson.GetProperty("error").GetProperty("message").GetString();
                    await DisplayAlert("Error", $"Failed to {action} model {ModelId}: {errorMessage}", "OK");
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to {action} model {ModelId}: {ex.Message}", "OK");
            }
            finally
            {
                LoadingIndicator.IsRunning = false;
                LoadingOverlay.IsVisible = false;
                viewModel.IsButtonEnabled = true;
            }
        }

        private async void OnLoadAllClicked(object sender, EventArgs e)
        {
            await LoadOrUnloadAllModels(true);
        }

        private async void OnUnloadAllClicked(object sender, EventArgs e)
        {
            await LoadOrUnloadAllModels(false);
        }

        private async Task LoadOrUnloadAllModels(bool load)
        {
            LoadingOverlay.IsVisible = true;
            LoadingIndicator.IsRunning = true;
            LoadingText.Text = load ? "Loading All Models..." : "Unloading All Models...";

            try
            {
                foreach (var viewModel in Models)
                {
                    if (load && !viewModel.IsLoaded || !load && viewModel.IsLoaded)
                    {
                        LoadingText.Text = $"{(load ? "Loading" : "Unloading")} Model {viewModel.ModelId}...";
                        HttpResponseMessage response = load
                            ? await _modelService.LoadModel(viewModel.ModelId)
                            : await _modelService.UnloadModel(viewModel.ModelId);

                        if (response.IsSuccessStatusCode)
                        {
                            viewModel.IsLoaded = load;
                        }
                        else
                        {
                            var errorContent = await response.Content.ReadAsStringAsync();
                            var errorJson = JsonSerializer.Deserialize<JsonElement>(errorContent);
                            var errorMessage = errorJson.GetProperty("error").GetProperty("message").GetString();
                            await DisplayAlert("Error", $"Failed to {(load ? "load" : "unload")} model {viewModel.ModelId}: {errorMessage}", "OK");
                        }
                    }
                }

                LoadingText.Text = "Operation Completed!";
                await Task.Delay(1000); // Show completion message for 1 second
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
            finally
            {
                LoadingIndicator.IsRunning = false;
                LoadingOverlay.IsVisible = false;
            }
        }

        protected override void OnDisappearing()
        {
            base.OnDisappearing();
            WeakReferenceMessenger.Default.Unregister<RefreshLibraryMessage>(this);
        }

        private async void OnDeleteModelClicked(object sender, EventArgs e)
        {
            var button = sender as ImageButton;
            var model = button?.CommandParameter as ModelListItemViewModel;

            if (model != null)
            {
                bool confirm = await DisplayAlert(
                    "Confirm Deletion", 
                    $"Are you sure you want to delete model {model.ModelId}?", 
                    "Yes", "No");

                if (confirm)
                {
                    try
                    {
                        bool success = await _modelService.DeleteModel(model.ModelId);
                        if (success)
                        {
                            Models.Remove(model);
                            AllModels.Remove(model.Model);
                            await DisplayAlert("Success", $"Model {model.ModelId} has been deleted.", "OK");
                        }
                        else
                        {
                            await DisplayAlert("Error", $"Failed to delete model {model.ModelId}.", "OK");
                        }
                    }
                    catch (Exception ex)
                    {
                        await DisplayAlert("Error", $"An error occurred while deleting the model: {ex.Message}", "OK");
                    }
                }
            }
        }
    }
}