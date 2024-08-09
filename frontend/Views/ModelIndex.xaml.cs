﻿using System.Collections.ObjectModel;
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
                AddToLibrary(model.ModelId);
            }
        }

        private async void LoadModels()
        {
            try
            {
                var modelList = await _libraryService.GetModelIndex();

                Models.Clear();

                foreach (var model in modelList)
                {
                    // Add LoadOrStopCommand to the model
                    model.LoadOrStopCommand = new Command(() => AddToLibrary(model.ModelId));

                    // Set PipelineTag if it's null or empty
                    if (string.IsNullOrEmpty(model.PipelineTag))
                    {
                        model.PipelineTag = !string.IsNullOrEmpty(model.ModelClass) ? model.ModelClass : "Unknown";
                    }

                    Models.Add(model);
                    System.Diagnostics.Debug.WriteLine($"Model: {model.ModelId}, PipelineTag: {model.PipelineTag}, IsOnline: {model.IsOnline}");
                }

                System.Diagnostics.Debug.WriteLine($"Total models loaded: {Models.Count}");

                // Initialize AllModels with the same data as Models for search functionality
                AllModels = new ObservableCollection<Model>(Models);
                System.Diagnostics.Debug.WriteLine($"AllModels initialized with {AllModels.Count} items");

                // Update ModelTypes
                var types = AllModels.Select(m => m.PipelineTag).Where(t => !string.IsNullOrEmpty(t)).Distinct().OrderBy(t => t);
                ModelTypes.Clear();
                foreach (var type in types)
                {
                    ModelTypes.Add(new ModelTypeFilter { TypeName = type, IsSelected = false });
                }

                InitializeFilterPopup();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading model data: {ex.Message}");
                await DisplayAlert("Error", $"An error occurred while loading models: {ex.Message}", "OK");
            }
        }

        public async void AddToLibrary(string ModelId)
        {
            var alertPage = new AlertPage("Download", $"Starting download for {ModelId}", true);
            await Navigation.PushModalAsync(alertPage);
            try
            {
                // call the API to download the model
                var client = new HttpClient();
                var response = await client.PostAsync($"http://127.0.0.1:8000/model/download-model?model_id={ModelId}", null);

                if (response.IsSuccessStatusCode)
                {
                    // simulate download progress. I guess this should be modified to reflect actual download progress
                    for (int i = 0; i <= 100; i++)
                    {
                        alertPage.UpdateProgress(i / 100.0);
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
                else
                {
                    await DisplayAlert("Error", $"Failed to download model {ModelId}", "OK");
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
}