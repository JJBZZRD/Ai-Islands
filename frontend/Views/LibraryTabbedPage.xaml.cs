using frontend.Views;
using frontend.Models;
using Microsoft.Maui.Controls;


namespace frontend.Views
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class LibraryTabbedPage : ContentPage
    {
        public string ModelId { get; set; } = string.Empty;
        private Model? _model;

        public LibraryTabbedPage(Model model)
        {
            InitializeComponent();
            _model = model;
            BindingContext = _model;

            // System.Diagnostics.Debug.WriteLine($"LibraryTabbedPage constructor - Model Name: {_model?.ModelId}");
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();

            Title = _model?.ModelId;

            // System.Diagnostics.Debug.WriteLine($"LibraryTabbedPage OnAppearing - Model Name: {_model?.ModelId}");

            ShowInfoPage(); //show Info page by default
        }

        private void OnInfoClicked(object sender, EventArgs e) => ShowInfoPage();
        private void OnInferenceClicked(object sender, EventArgs e) => ShowInferencePage();
        private void OnFineTuneClicked(object sender, EventArgs e) => ShowFineTunePage();
        private void OnModelConfigClicked(object sender, EventArgs e) => ShowModelConfigPage();
        private void ShowInfoPage()
        {
            if (_model != null)
            {
                ContentContainer.Content = new ModelInfoView { BindingContext = _model };
            }
        }

        private void ShowInferencePage()
        {
            if (_model != null)
            {
                ContentContainer.Content = new Inference(_model);
            }
        }

        private void ShowFineTunePage()
        {
            if (_model != null)
            {
                ContentContainer.Content = new FineTune(_model);
            }
        }

        private void ShowModelConfigPage()
        {
            if (_model != null)
            {
                ContentContainer.Content = new ModelConfig(_model);
            }
        }  



        // private Model LoadModel(string modelId)
        // {
        //     return new Model { Name = modelId };
        // }

        // private async void OnBackClicked(object sender, EventArgs e)
        // {
        //     await Shell.Current.GoToAsync("..");
        // }
    }
}