using Microsoft.Maui.Controls;
using frontend.Models;
using frontend.Models.ViewModels;
using frontend.Services;

namespace frontend.Views
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class PlaygroundTabbedPage : ContentPage
    {
        private PlaygroundService _playgroundService;
        private PlaygroundViewModel _playgroundViewModel;

        public PlaygroundTabbedPage(Playground playground, PlaygroundService playgroundService)
        {
            InitializeComponent();

            System.Diagnostics.Debug.WriteLine(System.Text.Json.JsonSerializer.Serialize(playground.Models));

            _playgroundViewModel = new PlaygroundViewModel{ Playground = playground};
            _playgroundService = playgroundService;
            BindingContext = _playgroundViewModel;

            // Ensure Models dictionary is initialized
            _playgroundViewModel.Playground.Models ??= new Dictionary<string, Model>();

            ShowModelPage(); // show model page when initialized
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            Title = _playgroundViewModel.Playground?.PlaygroundId ?? "Playground"; 
        }

        private void OnModelClicked(object sender, EventArgs e) => ShowModelPage();
        private void OnChainClicked(object sender, EventArgs e) => ShowChainPage();
        private void OnConfigClicked(object sender, EventArgs e) => ShowConfigPage();
        private void OnAPIClicked(object sender, EventArgs e) => ShowAPIPage();

        private void ShowModelPage()
        {
            var playgroundModelView = new PlaygroundModelView(_playgroundViewModel, _playgroundService);
            ContentContainer.Content = playgroundModelView;
        }

        private void ShowChainPage()
        {
            // should pass view model instead of playground
            ContentContainer.Content = new PlaygroundInferenceView(_playgroundViewModel.Playground);
        }

        private void ShowConfigPage()
        {
            // should pass view model instead of playground
            ContentContainer.Content = new PlaygroundConfigView(_playgroundViewModel.Playground);
        }

        private void ShowAPIPage()
        {
            // should pass view model instead of playground
            ContentContainer.Content = new PlaygroundAPIView(_playgroundViewModel.Playground);
        }
    }
}