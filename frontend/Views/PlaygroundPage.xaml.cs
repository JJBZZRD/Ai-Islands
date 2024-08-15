using Microsoft.Maui.Controls;
using System.Collections.ObjectModel;
using frontend.Services;
using frontend.Entities;
using System.Text.Json;
using frontend.Models;

namespace frontend.Views
{
    public partial class PlaygroundPage : ContentPage
    {
        private readonly PlaygroundService _playgroundService;
        public ObservableCollection<frontend.Entities.Playground> PlaygroundList { get; set; }

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

        public PlaygroundPage()
        {
            InitializeComponent();
            _playgroundService = new PlaygroundService();
            PlaygroundList = new ObservableCollection<frontend.Entities.Playground>();

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
            if (e.Parameter is frontend.Entities.Playground selectedPlayground)
            {
                await Navigation.PushAsync(new PlaygroundTabbedPage(selectedPlayground, _playgroundService));
            }
        }

        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            var searchText = e.NewTextValue?.Trim().ToLower() ?? string.Empty;

            if (string.IsNullOrWhiteSpace(searchText))
            {
                // If search is cleared, reload all playgrounds
                MainThread.BeginInvokeOnMainThread(async () => await LoadPlaygrounds());
            }
            else
            {
                var filteredList = new ObservableCollection<frontend.Entities.Playground>(
                    PlaygroundList.Where(p => 
                        (p.PlaygroundId?.ToLower().Contains(searchText) ?? false) || 
                        (p.Description?.ToLower().Contains(searchText) ?? false))
                );

                PlaygroundList.Clear();
                foreach (var playground in filteredList)
                {
                    PlaygroundList.Add(playground);
                }
            }
        }

        private void OnAddPlaygroundClicked(object sender, EventArgs e)
        {
            // Initialize the properties explicitly
            NewPlaygroundName = string.Empty;
            NewPlaygroundDescription = string.Empty;

            IsPopupVisible = true;
            PopupOverlay.IsVisible = true;

            // Add debug output
            System.Diagnostics.Debug.WriteLine($"Popup opened. Name: '{NewPlaygroundName}', Description: '{NewPlaygroundDescription}'");
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
            if (e.Parameter is frontend.Entities.Playground selectedPlayground)
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

        private async void OnCreatePlaygroundClicked(object sender, EventArgs e)
        {
            System.Diagnostics.Debug.WriteLine($"Create clicked. Name: '{NewPlaygroundName}', Description: '{NewPlaygroundDescription}'");

            if (string.IsNullOrWhiteSpace(NewPlaygroundName))
            {
                await DisplayAlert("Error", "Playground name is required.", "OK");
                return;
            }

            try
            {
                // Ensure description is not null
                string description = NewPlaygroundDescription ?? string.Empty;

                await _playgroundService.CreatePlayground(NewPlaygroundName, description);
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
    }
}