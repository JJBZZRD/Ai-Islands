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
    }
}