using Microsoft.Maui.Controls;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace frontend.Views
{
    public partial class Playground : ContentPage
    {
        private List<Dictionary<string, object>> allPlaygrounds;
        private List<Dictionary<string, object>> filteredPlaygrounds;

        public Playground()
        {
            InitializeComponent();
            allPlaygrounds = CreateExamplePlaygrounds();
            filteredPlaygrounds = new List<Dictionary<string, object>>(allPlaygrounds);
            PlaygroundList.ItemsSource = filteredPlaygrounds;
        }

        private List<Dictionary<string, object>> CreateExamplePlaygrounds()
        {
            return new List<Dictionary<string, object>>
            {
                new Dictionary<string, object>
                {
                    {"Id", "playground_1"},
                    {"Name", "Playground 1"},
                    {"Description", "I am a playground description for Playground 1"},
                    {"Models", new Dictionary<string, object>()},
                    {"Chain", new List<object>()},
                    {"ActiveChain", false}
                },
                new Dictionary<string, object>
                {
                    {"Id", "playground_2"},
                    {"Name", "Playground 2"},
                    {"Description", "I am a playground description for Playground 2"},
                    {"Models", new Dictionary<string, object>()},
                    {"Chain", new List<object>()},
                    {"ActiveChain", true}
                },
                new Dictionary<string, object>
                {
                    {"Id", "playground_3"},
                    {"Name", "Playground 3"},
                    {"Description", "I am a playground description for Playground 3"},
                    {"Models", new Dictionary<string, object>()},
                    {"Chain", new List<object>()},
                    {"ActiveChain", false}
                }
            };
        }

        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            System.Diagnostics.Debug.WriteLine($"Search text changed to: '{e.NewTextValue}'");

            if (string.IsNullOrWhiteSpace(e.NewTextValue))
            {
                // Restore the full list when search is empty
                filteredPlaygrounds = new List<Dictionary<string, object>>(allPlaygrounds);
            }
            else
            {
                var searchTerm = e.NewTextValue.ToLower();
                filteredPlaygrounds = allPlaygrounds.Where(p =>
                    (p["Name"] as string)?.ToLower().Contains(searchTerm) == true ||
                    (p["Description"] as string)?.ToLower().Contains(searchTerm) == true
                ).ToList();
            }

            PlaygroundList.ItemsSource = filteredPlaygrounds;
            System.Diagnostics.Debug.WriteLine($"After filtering: Playgrounds count: {filteredPlaygrounds.Count}");
        }

        private async void OnPlaygroundSelected(object sender, TappedEventArgs e)
        {
            if (e.Parameter is Dictionary<string, object> selectedPlayground)
            {
                await Navigation.PushAsync(new PlaygroundTabbedPage(selectedPlayground));
            }
        }
    }
}