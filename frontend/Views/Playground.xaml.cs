using Microsoft.Maui.Controls;
using System.Collections.ObjectModel;
using frontend.Services;
using frontend.entities;
using System.Text.Json;

namespace frontend.Views
{
    public partial class Playground : ContentPage
    {
        private readonly PlaygroundService _playgroundService;
        public ObservableCollection<frontend.entities.Playground> PlaygroundList { get; set; }

        public Playground()
        {
            InitializeComponent();
            _playgroundService = new PlaygroundService();
            PlaygroundList = new ObservableCollection<frontend.entities.Playground>();

            LoadPlaygrounds();

            BindingContext = this; 
        }

        private async void LoadPlaygrounds()
        {
            try
            {
                var playgroundsData = await _playgroundService.ListPlaygrounds();
                PlaygroundList.Clear();
                foreach (var playgroundData in playgroundsData)
                {
                    var playground = playgroundData.Value;
                    playground.Id = playgroundData.Key; 
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
                throw;
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
                var playgroundDict = new Dictionary<string, object>
                {
                    { "Id", selectedPlayground.Id ?? Guid.NewGuid().ToString() }, 
                    { "Description", selectedPlayground.Description ?? "No description" }, 
                    { "Models", selectedPlayground.Models ?? new Dictionary<string, Mapping>() }, 
                    { "Chain", selectedPlayground.Chain ?? new List<string>() }, 
                };

                var playgroundService = new PlaygroundService();
                await Navigation.PushAsync(new PlaygroundTabbedPage(playgroundDict, playgroundService));
            }
        }

        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            var searchText = e.NewTextValue;

            
            var filteredList = string.IsNullOrWhiteSpace(searchText)
                ? PlaygroundList
                : new ObservableCollection<frontend.entities.Playground>(
                    PlaygroundList.Where(p => p.Description.Contains(searchText, StringComparison.OrdinalIgnoreCase))
                );

            // for updating the CollectionView with the filtered list
            PlaygroundList.Clear();
            foreach (var playground in filteredList)
            {
                PlaygroundList.Add(playground);
            }
        }
    }
}