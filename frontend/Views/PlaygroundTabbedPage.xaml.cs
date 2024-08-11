using Microsoft.Maui.Controls;
using System.Collections.Generic;
using frontend.Models;
using frontend.Services;
using frontend.entities;
namespace frontend.Views
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class PlaygroundTabbedPage : ContentPage
    {
        private Dictionary<string, object> _playground;
        private PlaygroundService _playgroundService;

        public PlaygroundTabbedPage(Dictionary<string, object> playground, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playground = playground;
            _playgroundService = playgroundService;
            BindingContext = this;

            ShowModelPage(); // show model page when initialised
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            Title = _playground["Id"] as string ?? "Playground"; 
        }

        private void OnModelClicked(object sender, EventArgs e) => ShowModelPage();
        private void OnChainClicked(object sender, EventArgs e) => ShowChainPage();
        private void OnConfigClicked(object sender, EventArgs e) => ShowConfigPage();
        private void OnAPIClicked(object sender, EventArgs e) => ShowAPIPage();

        private void ShowModelPage()
        {
            ContentContainer.Content = new PlaygroundModelView(_playground, _playgroundService);
        }

        private void ShowChainPage()
        {
            ContentContainer.Content = new Chain(_playground);
        }

        private void ShowConfigPage()
        {
            ContentContainer.Content = new ChainConfig(_playground);
        }

        private void ShowAPIPage()
        {
            ContentContainer.Content = new ChainAPI(_playground);
        }
    }
}