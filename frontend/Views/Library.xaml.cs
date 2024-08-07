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

namespace frontend.Views
{
    public class RefreshLibraryMessage { }
    public partial class Library : ContentPage, INotifyPropertyChanged
    {
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

        public ObservableCollection<ModelTypeFilter> ModelTypes { get; set; }
        public bool FilterOnline { get; set; }
        public bool FilterOffline { get; set; }

        public ICommand NavigateToModelInfoCommand { get; private set; }

        public Library()
        {
            InitializeComponent();
            Models = new ObservableCollection<ModelItem>();
            AllModels = new ObservableCollection<ModelItem>();
            ModelTypes = new ObservableCollection<ModelTypeFilter>();
            BindingContext = this;

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
            Models = new ObservableCollection<ModelItem>(e.FilteredModels);
            FilterOnline = FilterPopup.FilterOnline;
            FilterOffline = FilterPopup.FilterOffline;
            FilterPopup.IsVisible = false;
        }

        private void OnResetFilters(object sender, EventArgs e)
        {
            Models = new ObservableCollection<ModelItem>(AllModels);
            FilterOnline = false;
            FilterOffline = false;
            FilterPopup.IsVisible = false;
        }

        private async void OnModelSelected(object sender, TappedEventArgs e)
        {
            if (e.Parameter is ModelItem selectedModel)
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
                using (HttpClient client = new HttpClient())
                {
                    var response = await client.GetAsync("http://127.0.0.1:8000/model/get-models?source=library");
                    if (response.IsSuccessStatusCode)
                    {
                        var jsonString = await response.Content.ReadAsStringAsync();
                        var libraryModels = JsonSerializer.Deserialize<Dictionary<string, ModelInfo>>(jsonString);

                        var newModels = new ObservableCollection<ModelItem>(
                            libraryModels.Select(model => new ModelItem
                            {
                                Name = model.Key,
                                PipelineTag = model.Value.PipelineTag ?? model.Value.Type ?? "Unknown",
                                IsOnline = model.Value.IsOnline,
                                Description = model.Value.Description ?? "No description available",
                                Tags = model.Value.Tags ?? new List<string>(),
                                LoadOrStopCommand = new Command(() => LoadOrStopModel(model.Key))
                            })
                        );

                        AllModels = newModels;
                        Models = new ObservableCollection<ModelItem>(AllModels);
                        InitializeFilterPopup();
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
        }

        private async void LoadOrStopModel(string modelName)
        {
            var model = Models.FirstOrDefault(m => m.Name == modelName);
            if (model == null) return;

            string baseUrl = "http://127.0.0.1:8000";
            string endpoint = model.IsOnline ? "unload" : "load";

            try
            {
                using (HttpClient client = new HttpClient())
                {
                    var response = await client.PostAsync($"{baseUrl}/model/{endpoint}?model_id={modelName}", null);
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