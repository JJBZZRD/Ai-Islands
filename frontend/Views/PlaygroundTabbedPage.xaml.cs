using Microsoft.Maui.Controls;
using System.Collections.Generic;

namespace frontend.Views
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class PlaygroundTabbedPage : ContentPage
    {
        private Dictionary<string, object> _playground;

        public PlaygroundTabbedPage(Dictionary<string, object> playground)
        {
            InitializeComponent();
            _playground = playground;
            BindingContext = _playground;
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            Title = _playground["Name"] as string ?? "Playground";
            ShowModelPage();
        }

        private void OnModelClicked(object sender, EventArgs e) => ShowModelPage();
        private void OnChainClicked(object sender, EventArgs e) => ShowChainPage();
        private void OnConfigClicked(object sender, EventArgs e) => ShowConfigPage();
        private void OnAPIClicked(object sender, EventArgs e) => ShowAPIPage();

        private void ShowModelPage()
        {
            ContentContainer.Content = new PlaygroundModelView(_playground);
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