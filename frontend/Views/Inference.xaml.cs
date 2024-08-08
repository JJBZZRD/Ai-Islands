using System;
using Microsoft.Maui.Controls;
using frontend.Models;

namespace frontend.Views
{
    public partial class Inference : ContentView
    {
        private ModelItem _model;
        private string _inputText;
        private string _outputText;
        private string _selectedFilePath;

        public string InputText
        {
            get => _inputText;
            set
            {
                if (_inputText != value)
                {
                    _inputText = value;
                    OnPropertyChanged(nameof(InputText));
                }
            }
        }

        public string OutputText
        {
            get => _outputText;
            set
            {
                if (_outputText != value)
                {
                    _outputText = value;
                    OnPropertyChanged(nameof(OutputText));
                }
            }
        }

        public Inference(ModelItem model)
        {
            InitializeComponent();
            _model = model;
            BindingContext = this;
            CreateInputUI();
        }

        private void CreateInputUI()
        {
            if (InputContainer == null)
            {
                System.Diagnostics.Debug.WriteLine("InputContainer is null");
                return;
            }

            switch (_model.PipelineTag?.ToLower())
            {
                case "object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image or Video"));
                    break;
                case "image-segmentation":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image or Video"));
                    break;
                case "zero-shot-object-detection":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Image or Video"));
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "text-classification":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "zero-shot-classification":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "translation":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "text-to-speech":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                case "token-classification":
                case "question-answering":
                case "summarization":
                case "automatic-speech-recognition":
                    InputContainer.Children.Add(CreateFileSelectionUI("Select Audio File"));
                    break;
                case "text-generation":
                    InputContainer.Children.Add(CreateTextInputUI());
                    break;
                default:
                    InputContainer.Children.Add(new Label { Text = "Input type not supported for this model.", TextColor = Colors.Gray });
                    break;
            }
        }

        private View CreateFileSelectionUI(string buttonText)
        {
            var fileButton = new Button
            {
                Text = buttonText,
                BackgroundColor = Colors.LightGray,
                TextColor = Colors.Black,
                CornerRadius = 5
            };
            if (buttonText == "Select Image or Video")
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
                Children = { fileButton, fileNameLabel }
            };
        }

        private View CreateTextInputUI()
        {
            return new Editor
            {
                Placeholder = "Enter your input here...",
                PlaceholderColor = Colors.Gray,
                TextColor = Colors.Black,
                HeightRequest = 150
            };
        }

        private async void OnImageSelectClicked(object sender, EventArgs e)
        {
            try
            {
                var result = await FilePicker.PickAsync(new PickOptions
                {
                    FileTypes = FilePickerFileType.Images,
                    PickerTitle = "Select an image or video file"
                });

                if (result != null)
                {
                    _selectedFilePath = result.FullPath;
                    var stack = (VerticalStackLayout)((Button)sender).Parent;
                    var label = (Label)stack.Children[1];
                    label.Text = result.FileName;
                    label.IsVisible = true;
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
        }

        private async void OnAudioSelectClicked(object sender, EventArgs e)
        {
            try
            {
                // Define a custom file type filter for audio files
                var customFileType = new FilePickerFileType(
                    new Dictionary<DevicePlatform, IEnumerable<string>>
                    {
                        { DevicePlatform.iOS, new[] { "public.audio" } }, // For iOS
                        { DevicePlatform.Android, new[] { "audio/*" } },  // For Android
                        { DevicePlatform.WinUI, new[] { ".mp3", ".wav", ".m4a" } }, // For Windows
                    });

                PickOptions options = new()
                {
                    PickerTitle = "Please select an audio file",
                    FileTypes = customFileType,
                };

                // Show the file picker and wait for the user to select a file
                var result = await FilePicker.Default.PickAsync(options);

                if (result != null)
                {
                    _selectedFilePath = result.FullPath;
                    var stack = (VerticalStackLayout)((Button)sender).Parent;
                    var label = (Label)stack.Children[1];
                    label.Text = result.FileName;
                    label.IsVisible = true;
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
        }

        private void OnRunInferenceClicked(object sender, EventArgs e)
        {
            // we call the inference API here
            // for now, it's just echo the input or file path as a placeholder
            if (!string.IsNullOrEmpty(_selectedFilePath))
            {
                OutputText = $"Inference result for model {_model.Name} with file: {_selectedFilePath}";
            }
            else
            {
                OutputText = $"Inference result for model {_model.Name}:\n\n{InputText}";
            }
        }
    }
}