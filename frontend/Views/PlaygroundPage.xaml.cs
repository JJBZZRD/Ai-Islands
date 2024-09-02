using Microsoft.Maui.Controls;
using System.Collections.ObjectModel;
using frontend.Services;
using frontend.Models;
using System.Text.Json;

namespace frontend.Views
{
    public partial class PlaygroundPage : ContentPage
    {
        private readonly PlaygroundService _playgroundService;
        private readonly ModelService _modelService;
        public ObservableCollection<Playground> PlaygroundList { get; set; }

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

        private bool _isEditMode;
        public bool IsEditMode
        {
            get => _isEditMode;
            set
            {
                if (_isEditMode != value)
                {
                    _isEditMode = value;
                    OnPropertyChanged(nameof(IsEditMode));
                    OnPropertyChanged(nameof(PopupTitle));
                    OnPropertyChanged(nameof(NameLabel));
                    OnPropertyChanged(nameof(DescriptionLabel));
                    OnPropertyChanged(nameof(ActionButtonText));
                }
            }
        }

        public string PopupTitle => IsEditMode ? "Update Playground" : "Create New Playground";
        public string NameLabel => IsEditMode ? "Update Playground Name:" : "Playground Name:";
        public string DescriptionLabel => IsEditMode ? "Update Playground Description (Optional):" : "Description (Optional):";
        public string ActionButtonText => IsEditMode ? "Update" : "Create";

        private Playground _playgroundToEdit;

        public PlaygroundPage()
        {
            InitializeComponent();
            _playgroundService = new PlaygroundService();
            PlaygroundList = new ObservableCollection<Playground>();

            BindingContext = this;

            // Use MainThread to ensure UI is ready before loading playgrounds
            MainThread.InvokeOnMainThreadAsync(async () => await LoadPlaygrounds());
        }

        protected override async void OnAppearing()
        {
            base.OnAppearing();
            await LoadPlaygrounds();
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
            if (e.Parameter is Playground selectedPlayground)
            {
                var libraryService = new LibraryService();

                // Initialize the Models dictionary if it's null
                selectedPlayground.Models ??= new Dictionary<string, Model>();

                // Populate the Models dictionary with actual Model objects
                if (selectedPlayground.ModelIds != null)
                {
                    foreach (var modelKvp in selectedPlayground.ModelIds)
                    {
                        var modelInfo = await libraryService.GetModelInfoLibrary(modelKvp.Key);
                        System.Diagnostics.Debug.WriteLine($"Adding Model info {modelKvp.Key}: {JsonSerializer.Serialize(modelInfo)}");
                        selectedPlayground.Models[modelKvp.Key] = modelInfo;
                    }

                    System.Diagnostics.Debug.WriteLine(System.Text.Json.JsonSerializer.Serialize(selectedPlayground.Models));
                    await Navigation.PushAsync(new PlaygroundTabbedPage(selectedPlayground, _playgroundService));
                }
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
                var filteredList = new ObservableCollection<Playground>(
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
            IsEditMode = false;
        }

        private void OnPopupOverlayTapped(object sender, EventArgs e)
        {
            // Close the popup when tapping outside
            IsPopupVisible = false;
            PopupOverlay.IsVisible = false;
            NewPlaygroundName = string.Empty;
            NewPlaygroundDescription = string.Empty;
            IsEditMode = false;
        }

        private async void OnDeletePlaygroundClicked(object sender, EventArgs e)
        {
            var button = sender as ImageButton;
            var playground = button?.BindingContext as Playground;

            if (playground != null)
            {
                bool answer = await DisplayAlert("Confirm Delete",
                    $"Are you sure you want to delete the playground '{playground.PlaygroundId}'?",
                    "Yes", "No");

                if (answer)
                {
                    try
                    {
                        await _playgroundService.DeletePlayground(playground.PlaygroundId);
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

        private async void OnActionButtonClicked(object sender, EventArgs e)
        {
            if (IsEditMode)
            {
                await UpdatePlayground();
            }
            else
            {
                await CreatePlayground();
            }
        }

        private async Task CreatePlayground()
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

        private async Task UpdatePlayground()
        {
            if (string.IsNullOrWhiteSpace(NewPlaygroundName))
            {
                await DisplayAlert("Error", "Playground name is required.", "OK");
                return;
            }

            try
            {
                string description = NewPlaygroundDescription ?? string.Empty;

                var response = await _playgroundService.UpdatePlayground(_playgroundToEdit.PlaygroundId, NewPlaygroundName, description);
                
                if (response.IsSuccessStatusCode)
                {
                    await LoadPlaygrounds();

                    IsPopupVisible = false;
                    PopupOverlay.IsVisible = false;

                    NewPlaygroundName = string.Empty;
                    NewPlaygroundDescription = string.Empty;
                    IsEditMode = false;

                    await DisplayAlert("Success", "Playground updated successfully", "OK");
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    await DisplayAlert("Error", $"Failed to update playground. Status: {response.StatusCode}, Content: {errorContent}", "OK");
                }
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HTTP Request Error: {ex.Message}");
                if (ex.InnerException != null)
                {
                    System.Diagnostics.Debug.WriteLine($"Inner Exception: {ex.InnerException.Message}");
                }
                await DisplayAlert("Error", $"Failed to update playground: {ex.Message}", "OK");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error updating playground: {ex.Message}");
                await DisplayAlert("Error", $"Failed to update playground: {ex.Message}", "OK");
            }
        }

        private async void OnEditPlaygroundClicked(object sender, EventArgs e)
        {
            var button = sender as ImageButton;
            _playgroundToEdit = button?.BindingContext as Playground;

            if (_playgroundToEdit != null)
            {
                IsEditMode = true;
                NewPlaygroundName = _playgroundToEdit.PlaygroundId;
                NewPlaygroundDescription = _playgroundToEdit.Description;

                IsPopupVisible = true;
                PopupOverlay.IsVisible = true;

                System.Diagnostics.Debug.WriteLine($"Edit popup opened. Name: '{NewPlaygroundName}', Description: '{NewPlaygroundDescription}'");
            }
        }
    }
}