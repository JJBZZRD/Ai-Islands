using Microsoft.Maui.Controls;
using System.Collections.ObjectModel;
using frontend.Services;
using frontend.entities;
using System.Text.Json;
using frontend.Models;

namespace frontend.Views
{
    public partial class Playground : ContentPage
    {
        private readonly PlaygroundService _playgroundService;
        public ObservableCollection<frontend.entities.Playground> PlaygroundList { get; set; }

        private bool _isPopupVisible;
        public bool IsPopupVisible
        {
            get => _isPopupVisible;
            set
            {
                if (_isPopupVisible != value)
                {
                    _isPopupVisible = value;
                    OnPropertyChanged(nameof(IsPopupVisible));
                }
            }
        }

        private string _newPlaygroundName;
        public string NewPlaygroundName
        {
            get => _newPlaygroundName;
            set
            {
                _newPlaygroundName = value;
                OnPropertyChanged(nameof(NewPlaygroundName));
            }
        }

        private string _newPlaygroundDescription;
        public string NewPlaygroundDescription
        {
            get => _newPlaygroundDescription;
            set
            {
                _newPlaygroundDescription = value;
                OnPropertyChanged(nameof(NewPlaygroundDescription));
            }
        }

        public Playground()
        {
            InitializeComponent();
            _playgroundService = new PlaygroundService();
            PlaygroundList = new ObservableCollection<frontend.entities.Playground>();

            BindingContext = this;

            // Use MainThread to ensure UI is ready before loading playgrounds
            MainThread.InvokeOnMainThreadAsync(async () => await LoadPlaygrounds());
        }

        private async Task LoadPlaygrounds()
        {
            try
            {
                var playgrounds = await _playgroundService.ListPlaygrounds();
                PlaygroundList.Clear();
                foreach (var playground in playgrounds)
                {
                    PlaygroundList.Add(playground);
                }
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HTTP Request Error: {ex.Message}");
                if (ex.InnerException != null)
                {
                    System.Diagnostics.Debug.WriteLine($"Inner Exception: {ex.InnerException.Message}");
                }
                await DisplayAlert("Error", "An error occurred while loading playgrounds.", "OK");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading playgrounds: {ex.Message}");
                await DisplayAlert("Error", "An error occurred while loading playgrounds.", "OK");
            }
        }

        private async void OnPlaygroundSelected(object sender, TappedEventArgs e)
        {
            if (e.Parameter is frontend.entities.Playground selectedPlayground)
            {
                var playgroundService = new PlaygroundService();
                await Navigation.PushAsync(new PlaygroundTabbedPage(selectedPlayground, playgroundService));
            }
        }

        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            var searchText = e.NewTextValue;

            var filteredList = string.IsNullOrWhiteSpace(searchText)
                ? PlaygroundList
                : new ObservableCollection<frontend.entities.Playground>(
                    PlaygroundList.Where(p => p.Description != null && p.Description.Contains(searchText, StringComparison.OrdinalIgnoreCase))
                );

            // for updating the CollectionView with the filtered list
            PlaygroundList.Clear();
            foreach (var playground in filteredList)
            {
                PlaygroundList.Add(playground);
            }
        }

        private void OnAddPlaygroundClicked(object sender, EventArgs e)
        {
            IsPopupVisible = true;
            PopupOverlay.IsVisible = true;
        }

        private async void OnCreatePlaygroundClicked(object sender, EventArgs e)
        {
            if (string.IsNullOrWhiteSpace(NewPlaygroundName))
            {
                await DisplayAlert("Error", "Playground name is required.", "OK");
                return;
            }

            try
            {
                await _playgroundService.CreatePlayground(NewPlaygroundName, NewPlaygroundDescription);
                await LoadPlaygrounds();
                
                IsPopupVisible = false;
                PopupOverlay.IsVisible = false;
                
                NewPlaygroundName = string.Empty;
                NewPlaygroundDescription = string.Empty;
                
                await DisplayAlert("Success", "New playground created successfully", "OK");
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HTTP Request Error: {ex.Message}");
                if (ex.InnerException != null)
                {
                    System.Diagnostics.Debug.WriteLine($"Inner Exception: {ex.InnerException.Message}");
                }
                await DisplayAlert("Error", $"Failed to create playground: {ex.Message}", "OK");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Unexpected error in OnCreatePlaygroundClicked: {ex.Message}");
                await DisplayAlert("Error", $"Failed to create playground: {ex.Message}", "OK");
            }
        }

        private void OnCancelClicked(object sender, EventArgs e)
        {
            IsPopupVisible = false;
            PopupOverlay.IsVisible = false;
            NewPlaygroundName = string.Empty;
            NewPlaygroundDescription = string.Empty;
        }

        private void OnPopupOverlayTapped(object sender, EventArgs e)
        {
            // Close the popup when tapping outside
            IsPopupVisible = false;
            PopupOverlay.IsVisible = false;
            NewPlaygroundName = string.Empty;
            NewPlaygroundDescription = string.Empty;
        }

        private async void OnDeletePlaygroundClicked(object sender, TappedEventArgs e)
        {
            if (e.Parameter is frontend.entities.Playground selectedPlayground)
            {
                bool answer = await DisplayAlert("Confirm Delete", 
                    $"Are you sure you want to delete the playground '{selectedPlayground.PlaygroundId}'?", 
                    "Yes", "No");
                
                if (answer)
                {
                    try
                    {
                        await _playgroundService.DeletePlayground(selectedPlayground.PlaygroundId);
                        await LoadPlaygrounds();
                        // Optionally, show a success message
                        await DisplayAlert("Success", "Playground deleted successfully", "OK");
                    }
                    catch (Exception ex)
                    {
                        await DisplayAlert("Error", $"Failed to delete playground: {ex.Message}", "OK");
                    }
                }
            }
        }
    }
}