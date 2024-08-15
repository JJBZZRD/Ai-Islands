using Microsoft.Maui.Controls;
using frontend.Models;
using frontend.Services;

namespace frontend.Views
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class PlaygroundTabbedPage : ContentPage
    {
        private Playground _playground;
        private PlaygroundService _playgroundService;

        public PlaygroundTabbedPage(Playground playground, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playground = playground;
            _playgroundService = playgroundService;
            BindingContext = this;

            // Ensure Models dictionary is initialized
            _playground.Models ??= new Dictionary<string, Model>();

            // If ModelIds is not null, populate Models dictionary
            if (_playground.ModelIds != null)
            {
                foreach (var modelKvp in _playground.ModelIds)
                {
                    if (!_playground.Models.ContainsKey(modelKvp.Key))
                    {
                        // Create a basic Model object if it doesn't exist
                        _playground.Models[modelKvp.Key] = new Model
                        {
                            ModelId = modelKvp.Key,
                            // You can add more properties here if they're available in modelKvp.Value
                        };
                    }
                }
            }

            ShowModelPage(); // show model page when initialized
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            Title = _playground.PlaygroundId ?? "Playground"; 
        }

        private void OnModelClicked(object sender, EventArgs e) => ShowModelPage();
        private void OnChainClicked(object sender, EventArgs e) => ShowChainPage();
        private void OnConfigClicked(object sender, EventArgs e) => ShowConfigPage();
        private void OnAPIClicked(object sender, EventArgs e) => ShowAPIPage();

        private void ShowModelPage()
        {
            var playgroundModelView = new PlaygroundModelView(_playground, _playgroundService);
            ContentContainer.Content = playgroundModelView;
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