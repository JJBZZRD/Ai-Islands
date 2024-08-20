using frontend.Models;
using Microsoft.Maui.Controls;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.IO;
using Microsoft.Maui.Storage;
using Microsoft.Maui.ApplicationModel.DataTransfer;

namespace frontend.Views
{
    public partial class FineTune : ContentView, INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler PropertyChanged;

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
        
        private Model _model;
        private bool _isFineTuningAvailable;

        public bool IsFineTuningAvailable
        {
            get => _isFineTuningAvailable;
            set
            {
                if (_isFineTuningAvailable != value)
                {
                    _isFineTuningAvailable = value;
                    OnPropertyChanged(nameof(IsFineTuningAvailable));
                }
            }
        }

        public FineTune(Model model)
        {
            InitializeComponent();
            _model = model;
            BindingContext = this;

            GenerateTaskSpecificUI();
        }

        private void GenerateTaskSpecificUI()
        {
            switch (_model.PipelineTag?.ToLower())
            {
                case "object-detection":
                    TaskSpecificContent.Content = CreateObjectDetectionUI();
                    IsFineTuningAvailable = true;
                    break;
                case "text-generation":
                    TaskSpecificContent.Content = CreateNLPUI();
                    IsFineTuningAvailable = true;
                    break;
                // more cases can be added here
                default:
                    TaskSpecificContent.Content = CreateDefaultUI();
                    IsFineTuningAvailable = false;
                    break;
            }
        }

        private View CreateObjectDetectionUI()
        {
            return new VerticalStackLayout
            {
                Children =
                {
                    new Frame
                    {
                        BackgroundColor = Colors.White,
                        Padding = new Thickness(20),
                        CornerRadius = 10,
                        Content = new VerticalStackLayout
                        {
                            Spacing = 15,
                            Children =
                            {
                                new Label { Text = "Fine-tuning parameters", FontSize = 20, FontAttributes = FontAttributes.Bold, TextColor = Color.FromArgb("#555555") },
                                CreateParameterEntryWithInfo("Epochs", "The number of complete passes through the training dataset. Starting with a smaller number of epochs (e.g., 10) is recommended, as it helps prevent overfitting and allows for iterative improvement."),
                                CreateParameterEntryWithInfo("Batch size", "The number of training examples utilised in one iteration. A larger batch size can lead to faster training but may require more memory. It's often a trade-off between speed and generalization performance. Start with a smaller batch size (e.g., 16 or 32) and adjust based on your hardware capabilities and model performance."),
                                CreateParameterEntryWithInfo("Learning rate", "The step size at each iteration while moving toward a minimum of the loss function. It controls how quickly or slowly a neural network model learns a problem. A high learning rate can cause the model to converge too quickly to a suboptimal solution, while a low learning rate can result in a slow learning process. It's often recommended to start with a small value (e.g., 0.001) and adjust based on training performance.")
                            }
                        }
                    },
                    new Frame
                    {
                        BackgroundColor = Colors.White,
                        Padding = new Thickness(20),
                        CornerRadius = 10,
                        Content = new VerticalStackLayout
                        {
                            Spacing = 15,
                            Children =
                            {
                                new Label { Text = "Upload dataset", FontSize = 20, FontAttributes = FontAttributes.Bold, TextColor = Color.FromArgb("#555555") },
                                new Label 
                                { 
                                    Text = "Ensure your dataset are uploaded in the correct format:\n• Download the example dataset to view the dataset structure expected by the model \n• YOLO supports annotation written in .txt file\n• The content in obj.names are the classes in the correct order, ensure there is no space before, between, and after the classes stated\n• Content in .txt file is the class index followed with bounding box coordinate (in the range 0-1)",
                                    FontSize = 14,
                                    TextColor = Color.FromArgb("#555555")
                                },
                                new Button
                                {
                                    Text = "Download Example Dataset",
                                    BackgroundColor = Color.FromArgb("#E0E0E0"),
                                    TextColor = Color.FromArgb("#333333"),
                                    CornerRadius = 5,
                                    Margin = new Thickness(0, 10, 0, 10),
                                    Command = new Command(async () => await DownloadExampleDataset())
                                },
                                CreateUploadButtonWithInfo("Select zip folder", "Choose a dataset zip folder for fine-tuning. Format supported for this model: YOLO.")
                            }
                        }
                    }
                }
            };
        }

        private View CreateNLPUI()
        {
            return new VerticalStackLayout
            {
                Children =
                {
                    new Frame
                    {
                        BackgroundColor = Colors.White,
                        Padding = new Thickness(20),
                        CornerRadius = 10,
                        Content = new VerticalStackLayout
                        {
                            Spacing = 15,
                            Children =
                            {
                                new Label { Text = "Parameters", FontSize = 20, FontAttributes = FontAttributes.Bold, TextColor = Color.FromArgb("#555555") },
                                CreateParameterEntryWithInfo("Vocabulary size", "The number of unique tokens in the model's vocabulary."),
                                CreateParameterEntryWithInfo("Embedding dimension", "The size of the vector space in which words are embedded."),
                            }
                        }
                    },
                    new Frame
                    {
                        BackgroundColor = Colors.White,
                        Padding = new Thickness(20),
                        CornerRadius = 10,
                        Content = new VerticalStackLayout
                        {
                            Spacing = 15,
                            Children =
                            {
                                new Label { Text = "Upload text corpus", FontSize = 20, FontAttributes = FontAttributes.Bold, TextColor = Color.FromArgb("#555555") },
                                CreateUploadButtonWithInfo("Select file", "Choose a text corpus file for fine-tuning. Recommended format: TXT or CSV.")
                            }
                        }
                    }
                }
            };
        }

        private View CreateParameterEntryWithInfo(string parameterName, string infoText)
        {
            var grid = new Grid
            {
                RowDefinitions =
                {
                    new RowDefinition { Height = GridLength.Auto },
                    new RowDefinition { Height = GridLength.Auto },
                    new RowDefinition { Height = GridLength.Auto }
                },
                ColumnDefinitions =
                {
                    new ColumnDefinition { Width = GridLength.Star },
                    new ColumnDefinition { Width = GridLength.Auto }
                }
            };

            var label = new Label
            {
                Text = parameterName,
                TextColor = Color.FromArgb("#333333"),
                VerticalOptions = LayoutOptions.Center
            };
            grid.Add(label, 0, 0);

            var button = new Button
            {
                Text = "?",
                FontSize = 12,
                WidthRequest = 25,
                HeightRequest = 25,
                CornerRadius = 12,
                Padding = new Thickness(0),
                Margin = new Thickness(5, 0, 0, 0),
                BackgroundColor = Color.FromArgb("#E0E0E0"),
                TextColor = Color.FromArgb("#333333"),
                Command = new Command(() => ShowInfoPopup(parameterName, infoText))
            };
            grid.Add(button, 1, 0);

            var entry = new Entry
            {
                Placeholder = $"Enter {parameterName.ToLower()}",
                TextColor = Color.FromArgb("#333333")
            };
            grid.Add(entry, 0, 2);
            Grid.SetColumnSpan(entry, 2);

            return grid;
        }

        private View CreateUploadButtonWithInfo(string buttonText, string infoText)
        {
            return new HorizontalStackLayout
            {
                Children =
                {
                    new Button { Text = buttonText, BackgroundColor = Color.FromArgb("#E0E0E0"), TextColor = Color.FromArgb("#333333"), CornerRadius = 5 },
                    new Button
                    {
                        Text = "?",
                        FontSize = 12,
                        WidthRequest = 25,
                        HeightRequest = 25,
                        CornerRadius = 12,
                        Padding = new Thickness(0),
                        Margin = new Thickness(5, 0, 0, 0),
                        BackgroundColor = Color.FromArgb("#E0E0E0"),
                        TextColor = Color.FromArgb("#333333"),
                        Command = new Command(() => ShowInfoPopup("Dataset", infoText))
                    }
                }
            };
        }

        private async void ShowInfoPopup(string title, string message)
        {
            await Application.Current.MainPage.DisplayAlert(title, message, "OK");
        }

        private View CreateDefaultUI()
        {
            return new StackLayout
            {
                Children =
        {
            new Label
            {
                Text = "Fine-tuning is not available for this model.",
                TextColor = Color.FromArgb("#333333"),
                HorizontalOptions = LayoutOptions.Center,
                VerticalOptions = LayoutOptions.CenterAndExpand,
                FontSize = 18
            }
        }
            };
        }

        private async Task DownloadExampleDataset()
        {
            try
            {
                string fileName = "example_yolo_dataset.zip";
                using var stream = await FileSystem.OpenAppPackageFileAsync($"Resources/ExampleDataset/{fileName}");
                var downloadsFolder = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                downloadsFolder = Path.Combine(downloadsFolder, "Downloads");
                var targetFile = Path.Combine(downloadsFolder, fileName);

                using (var fileStream = File.Create(targetFile))
                {
                    await stream.CopyToAsync(fileStream);
                }

                await Application.Current.MainPage.DisplayAlert("Success", $"Example dataset downloaded to:\n{targetFile}", "OK");
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to download example dataset: {ex.Message}", "OK");
            }
        }
    }
}