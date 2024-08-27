using frontend.Views;
using frontend.Models;
using frontend.ViewModels;
using Microsoft.Maui.Controls;
using System;
using Plugin.Maui.Audio;

namespace frontend.Views
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class LibraryTabbedPage : ContentPage
    {
        private ButtonViewModel ViewModel => BindingContext as ButtonViewModel;
        public string ModelId { get; set; } = string.Empty;
        private Model? _model;
        private readonly IAudioManager _audioManager;

        public LibraryTabbedPage(Model model, IAudioManager audioManager)
        {
            InitializeComponent();
            _model = model;
            _audioManager = audioManager;
            var viewModel = new ButtonViewModel { Model = _model };
            BindingContext = viewModel;
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            Title = _model?.ModelId;
            ShowInfoPage(); // show Info page by default
        }

        private void OnInfoClicked(object sender, EventArgs e)
        {
            ViewModel.SelectedTab = "Info";
            ShowInfoPage();
        }

        private void OnInferenceClicked(object sender, EventArgs e)
        {
            ViewModel.SelectedTab = "Inference";
            ShowInferencePage();
        }

        private void OnFineTuneClicked(object sender, EventArgs e)
        {
            ViewModel.SelectedTab = "FineTune";
            ShowFineTunePage();
        }

        private void OnModelConfigClicked(object sender, EventArgs e)
        {
            ViewModel.SelectedTab = "Configuration";
            ShowModelConfigPage();
        }

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
                ContentContainer.Content = new Inference(_model, _audioManager);
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
    }
}