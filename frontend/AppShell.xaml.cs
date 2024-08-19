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

        

        private async void OnGettingStartedClicked(object sender, EventArgs e)
        {
            // Placeholder for getting started information
            await DisplayAlert("Getting Started", "This would show a getting started guide.", "OK");
            // TODO: Implement actual getting started guide
        }

        private async void OnTutorialClicked(object sender, EventArgs e)
        {
            // Placeholder for tutorial
            await DisplayAlert("Tutorial", "This would start a tutorial.", "OK");
            // TODO: Implement actual tutorial
        }

        private async void OnIBMCloudClicked(object sender, EventArgs e)
        {
            // Open IBM Cloud login page in default browser
            try
            {
                await Browser.OpenAsync("https://cloud.ibm.com/login", BrowserLaunchMode.SystemPreferred);
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Could not open IBM Cloud: {ex.Message}", "OK");
            }
        }

        private async void OnHuggingFaceClicked(object sender, EventArgs e)
        {
            // Open Hugging Face documentation in default browser
            try
            {
                await Browser.OpenAsync("https://huggingface.co/docs/transformers/en/index", BrowserLaunchMode.SystemPreferred);
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Could not open Hugging Face: {ex.Message}", "OK");
            }
        }

        private async void OnUltralyticsClicked(object sender, EventArgs e)
        {
            // Open Ultralytics website in default browser
            try
            {
                await Browser.OpenAsync("https://www.ultralytics.com/", BrowserLaunchMode.SystemPreferred);
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Could not open Ultralytics: {ex.Message}", "OK");
            }
        }

        private async void OnAboutClicked(object sender, EventArgs e)
        {
            // Placeholder for about information
            await DisplayAlert("About AI Islands", 
                "AI Islands is an application designed to help you explore and utilize various AI models for Natural Language Processing, Computer Vision, and Generative AI tasks. " +
                "It provides a user-friendly interface to interact with powerful AI capabilities.", 
                "OK");
            // TODO: Implement more comprehensive about information
        }

        private async void OnHelpClicked(object sender, EventArgs e)
        {
            // Placeholder for help information
            await DisplayAlert("Help", "This would show help information.", "OK");
            // TODO: Implement comprehensive help system
        }
    }
}