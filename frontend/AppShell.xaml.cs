using Microsoft.Maui.Controls;
using System.Windows.Input;
using System.Diagnostics;

namespace frontend.Views
{
    public partial class AppShell : Shell
    {
        public ICommand NavigateCommand { get; }
        private Library libraryPage;
        public AppShell()
        {
            InitializeComponent();
            Routing.RegisterRoute("ModelIndex", typeof(ModelIndex));
            libraryPage = new Library();
            Routing.RegisterRoute("Library", typeof(Library));

            NavigateCommand = new Command<string>(async (route) =>
            {
                if (route == "LibraryPage")
                {
                    // Use the existing Library instance
                    await Navigation.PushAsync(libraryPage);
                }
                else
                {
                    await Shell.Current.GoToAsync(route);
                }
            });
            Routing.RegisterRoute("Playground", typeof(PlaygroundPage));
            Routing.RegisterRoute("DataRefinery", typeof(DataRefinery));
            Routing.RegisterRoute("Setting", typeof(Setting));
            Routing.RegisterRoute(nameof(LibraryTabbedPage), typeof(LibraryTabbedPage));
            NavigateCommand = new Command<string>(async (route) => await Shell.Current.GoToAsync(route));
            BindingContext = this;
        }

        private async void OnStartTutorialClicked(object sender, EventArgs e)
        {
            // Placeholder for tutorial slideshow
            await DisplayAlert("Tutorial", "This would start a slideshow tutorial.", "OK");
            // TODO: Implement actual slideshow logic
        }

        private async void OnGoToIBMCloudClicked(object sender, EventArgs e)
        {
            // Open IBM Cloud login page in default browser
            try
            {
                await Browser.OpenAsync("https://cloud.ibm.com/login", BrowserLaunchMode.SystemPreferred);
            }
            catch (Exception ex)
            {
                // Handle exceptions (e.g., no internet connection)
                await DisplayAlert("Error", $"Could not open IBM Cloud: {ex.Message}", "OK");
            }
        }

        private async void OnHelpClicked(object sender, EventArgs e)
        {
            // Placeholder for help information
            await DisplayAlert("About AI Islands", 
                "AI Islands is an application designed to help you explore and utilize various AI models for Natural Language Processing, Computer Vision, and Generative AI tasks. " +
                "It provides a user-friendly interface to interact with powerful AI capabilities.", 
                "OK");
            // TODO: Implement more comprehensive help system
        }
    }
}