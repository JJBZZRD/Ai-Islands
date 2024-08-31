using frontend.Views;
using frontend.Models;
using frontend.ViewModels;
using Microsoft.Maui.Controls;
using System;

namespace frontend.Views
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class LibraryTabbedPage : ContentPage
    {
        private ButtonViewModel ViewModel => BindingContext as ButtonViewModel;
        public string ModelId { get; set; } = string.Empty;
        private Model? _model;

        public LibraryTabbedPage(Model model)
        {
            InitializeComponent();
            _model = model;
            var viewModel = new ButtonViewModel { Model = _model };
            BindingContext = viewModel;
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            Title = _model?.ModelId;
            ShowInfoPage(); // show Info page by default
        }

        protected override void OnDisappearing()
        {
            base.OnDisappearing();
            ClearCurrentContent();
        }

        private void OnInfoClicked(object sender, EventArgs e)
        {
            ClearCurrentContent();
            ViewModel.SelectedTab = "Info";
            ShowInfoPage();
        }

        private void OnInferenceClicked(object sender, EventArgs e)
        {
            ClearCurrentContent();
            ViewModel.SelectedTab = "Inference";
            ShowInferencePage();
        }

        private void OnFineTuneClicked(object sender, EventArgs e)
        {
            ClearCurrentContent();
            ViewModel.SelectedTab = "FineTune";
            ShowFineTunePage();
        }

        private void OnModelConfigClicked(object sender, EventArgs e)
        {
            ClearCurrentContent();
            ViewModel.SelectedTab = "Configuration";
            ShowModelConfigPage();
        }

        private void ClearCurrentContent()
        {
            if (ContentContainer.Content is IDisposable disposable)
            {
                disposable.Dispose();
            }
            ContentContainer.Content = null;
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
                ContentContainer.Content = new Inference(_model);
            }
        }

        private void ShowFineTunePage()
        {
            if (_model != null)
            {
                ContentView fineTunePage;
                switch (_model.PipelineTag?.ToLower())
                {
                    case "object-detection":
                        fineTunePage = new FineTuneVisionView(_model);
                        break;
                    case "text-classification":
                        if (_model.IsOnline == false)
                        {
                            fineTunePage = new FineTuneNLPView(_model);
                            break;
                        }
                        else
                        {
                            goto default;
                        }
                    default:
                        fineTunePage = new FineTuneUnavailableView();
                        break;
                }
                ContentContainer.Content = fineTunePage;
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