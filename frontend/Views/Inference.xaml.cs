using System;
using Microsoft.Maui.Controls;
using frontend.Models;
using frontend.Models.ViewModels;
using frontend.Services;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Threading;
using OpenCvSharp;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;

namespace frontend.Views
{
    public partial class Inference : ContentView
    {
        private readonly InferenceViewModel _viewModel;

        public Inference(Model model)
        {
            InitializeComponent();
            _viewModel = new InferenceViewModel(model, new ModelService());
            BindingContext = _viewModel;
            _viewModel.SetImagePopup(_imagePopupView);
            CreateInputUI();
        }

        private void CreateInputUI()
        {
            System.Diagnostics.Debug.WriteLine("CreateInputUI method called");
            if (InputContainer == null)
            {
                System.Diagnostics.Debug.WriteLine("InputContainer is null");
                return;
            }

            System.Diagnostics.Debug.WriteLine($"PipelineTag: {_viewModel.Model.PipelineTag?.ToLower()}");

            switch (_viewModel.Model.PipelineTag?.ToLower())
            {
                // ------------------------- COMPUTER VISION MODELS -------------------------
                case "object-detection":
                    System.Diagnostics.Debug.WriteLine("Creating UI for object-detection");
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image or Video"));
                    _viewModel.IsViewImageOutputButtonVisible = true;
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    break;
                case "image-segmentation":
                    System.Diagnostics.Debug.WriteLine("Creating UI for image-segmentation");
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image"));
                    _viewModel.IsViewImageOutputButtonVisible = true;
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    break;
                case "zero-shot-object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image"));
                    InputContainer.Children.Add(CreateTextInputUI());
                    _viewModel.IsViewImageOutputButtonVisible = true;
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    break;

                // ------------------------- NLP MODELS -------------------------
                case "text-classification":
                    InputContainer.Children.Add(CreateTextInputUI());
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    break;
                case "zero-shot-classification":
                    InputContainer.Children.Add(CreateTextInputUI());
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    break;
                case "translation":
                    InputContainer.Children.Add(CreateTextInputUI());
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    break;
                case "text-to-speech":
                    InputContainer.Children.Add(CreateTextInputUI());
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    break;


                case "feature-extraction":
                    InputContainer.Children.Add(CreateTextInputUI());
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    _viewModel.IsRunInferenceButtonVisible = true;
                    break;
                
                case "token-classification":

                case "question-answering":

                case "summarization":
                
                case "automatic-speech-recognition":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Audio File"));
                    _viewModel.IsOutputTextVisible = true;
                    _viewModel.IsChatHistoryVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    break;


                case "text-generation":
                    if (_viewModel.Model.Config.ChatHistory == true)
                    {
                        _viewModel.IsChatbotVisible = true;
                        _viewModel.IsInputFrameVisible = false;
                        _viewModel.IsOutputFrameVisible = false;
                        _viewModel.IsRunInferenceButtonVisible = false;
                    }
                    else
                    {
                        InputContainer.Children.Add(CreateTextInputUI());
                        _viewModel.IsChatbotVisible = false;
                        _viewModel.IsInputFrameVisible = true;
                        _viewModel.IsOutputFrameVisible = true;
                        _viewModel.IsRunInferenceButtonVisible = true;
                    }
                    break;
                



                default:
                    System.Diagnostics.Debug.WriteLine("Creating default UI");
                    InputContainer.Children.Add(new Label { Text = "Input type not supported for this model.", TextColor = Colors.Gray });
                    _viewModel.IsChatbotVisible = false;
                    _viewModel.IsInputFrameVisible = true;
                    _viewModel.IsOutputFrameVisible = true;
                    _viewModel.IsRunInferenceButtonVisible = true;
                    break;
            }
        }

        private View CreateFileSelectionUI(string buttonText)
        {
            var instructionText = "Enter input data and 'Run Inference' to preview the output.";
            
            switch (_viewModel.Model.PipelineTag?.ToLower())
            {
                case "object-detection":
                    instructionText = "Select image or video file and click 'Run Inference' to preview the output.";
                    break;
                case "image-segmentation":
                    instructionText = "Select image file and click 'Run Inference' to preview the output.";
                    break;
                case "zero-shot-object-detection":
                    instructionText = "Select image file and enter text, then click 'Run Inference' to preview the output.";
                    break;
                // other cases
            }

            var fileButton = new Button
            {
                Text = buttonText,
                BackgroundColor = Colors.LightGray,
                TextColor = Colors.Black,
                CornerRadius = 5,
                Margin = new Thickness(0, 20, 0, 10)
            };

            if (buttonText == "Select Image or Video")
            {
                fileButton.Clicked += OnImageOrVideoSelectClicked;
            }
            else if (buttonText == "Select Image")
            {
                fileButton.Clicked += OnImageSelectClicked;
            }
            else if (buttonText == "Select Audio File")
            {
                fileButton.Clicked += OnAudioSelectClicked;
            }

            var fileNameLabel = new Label
            {
                TextColor = Colors.Black,
                IsVisible = false
            };

            return new VerticalStackLayout
            {
                Children =
                {
                    new Label { Text = instructionText, FontSize = 14, TextColor = Color.FromArgb("#5D5D5D") },
                    fileButton,
                    fileNameLabel
                }
            };
        }

        private View CreateTextInputUI()
        {
            var editor = new Editor
            {
                Placeholder = "Enter your input here...",
                PlaceholderColor = Colors.Gray,
                HeightRequest = 150,
                Text = _viewModel.InputText
            };
            editor.TextChanged += (sender, e) => 
            {
                _viewModel.InputText = ((Editor)sender)?.Text ?? string.Empty;
                System.Diagnostics.Debug.WriteLine($"Text input changed. New value: '{_viewModel.InputText}'");
            };
            return editor;
        }

        private async void OnSendMessageClicked(object sender, EventArgs e)
        {
            if (!string.IsNullOrWhiteSpace(ChatInputEntry.Text))
            {
                var userMessage = ChatInputEntry.Text;
                ChatInputEntry.Text = string.Empty;

                await _viewModel.SendMessage(userMessage);
                
                // Scroll to the bottom of the chat history
                Device.BeginInvokeOnMainThread(() =>
                {
                    ChatHistoryListView.ScrollTo(_viewModel.ChatHistory.Last(), ScrollToPosition.End, false);
                });
            }
        }

        private async void OnRunInferenceClicked(object sender, EventArgs e)
        {
            System.Diagnostics.Debug.WriteLine($"OnRunInferenceClicked called. ViewModel.InputText: '{_viewModel.InputText}'");
            await _viewModel.RunInference();
        }

        private async void OnViewImageOutputClicked(object sender, EventArgs e)
        {
            await _viewModel.ViewImageOutput();
        }

        private async void OnImageOrVideoSelectClicked(object sender, EventArgs e)
        {
            if (await _viewModel.SelectFile("image_or_video"))
            {
                UpdateFileNameLabel(Path.GetFileName(_viewModel.SelectedFilePath));
            }
        }

        private async void OnImageSelectClicked(object sender, EventArgs e)
        {
            if (await _viewModel.SelectFile("image"))
            {
                UpdateFileNameLabel(Path.GetFileName(_viewModel.SelectedFilePath));
            }
        }

        private async void OnAudioSelectClicked(object sender, EventArgs e)
        {
            if (await _viewModel.SelectFile("audio"))
            {
                UpdateFileNameLabel(Path.GetFileName(_viewModel.SelectedFilePath));
            }
        }

        private void UpdateFileNameLabel(string fileName)
        {
            var fileSelectionUI = InputContainer.Children.FirstOrDefault(c => c is VerticalStackLayout) as VerticalStackLayout;
            var fileNameLabel = fileSelectionUI?.Children.LastOrDefault() as Label;
            if (fileNameLabel != null)
            {
                fileNameLabel.Text = fileName;
                fileNameLabel.IsVisible = true;
            }
        }
    }
}