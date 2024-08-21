using frontend.Models;
using Microsoft.Maui.Controls;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.IO;
using Microsoft.Maui.Storage;
using Microsoft.Maui.ApplicationModel.DataTransfer;
using frontend.Services;
using System.Threading.Tasks;
using System.Collections.ObjectModel;

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

        private ObservableCollection<Parameter> _parameters;
        public ObservableCollection<Parameter> Parameters
        {
            get => _parameters;
            set
            {
                if (_parameters != value)
                {
                    _parameters = value;
                    OnPropertyChanged();
                    SaveVisParameters();
                }
            }
        }

        private Button _startVisFineTuningButton;

        public FineTune(Model model)
        {
            InitializeComponent();
            _model = model;
            BindingContext = this;

            TaskSpecificContent.Content = GenerateTaskSpecificUI();
        }

        private View GenerateTaskSpecificUI()
        {
            View taskSpecificContent;
            // disable fine-tuning for yolov10
            if (_model.ModelId.StartsWith("yolov10", StringComparison.OrdinalIgnoreCase))
            {
                taskSpecificContent = CreateDefaultUI();
                IsFineTuningAvailable = false;
            }
            else
            {
                switch (_model.PipelineTag?.ToLower())
                {
                    case "object-detection":
                        taskSpecificContent = CreateObjectDetectionUI();
                        IsFineTuningAvailable = true;
                        break;
                    case "text-generation":
                        taskSpecificContent = CreateNLPUI();
                        IsFineTuningAvailable = true;
                        break;
                    // more cases here
                    default:
                        // taskSpecificContent = new Label { Text = "Unsupported task" };
                        taskSpecificContent = CreateDefaultUI();
                        IsFineTuningAvailable = false;
                        break;
                }
            }
            return taskSpecificContent;
        }

        private string _selectedZipPath;
        private Label _selectedZipLabel;

        private View CreateObjectDetectionUI()
        {
            Parameters = new ObservableCollection<Parameter>
            {
                new Parameter { Name = "Epochs", Value = _model.FineTuningParameters?.GetValueOrDefault("Epochs", "10") ?? "10", Description = "The number of complete passes through the training dataset. Starting with a smaller number of epochs (e.g., 10) is recommended, as it helps prevent overfitting and allows for iterative improvement.", Parent = this },
                new Parameter { Name = "Batch size", Value = _model.FineTuningParameters?.GetValueOrDefault("Batch size", "16") ?? "16", Description = "The number of training examples utilised in one iteration. A larger batch size can lead to faster training but may require more memory. It's often a trade-off between speed and generalization performance. Start with a smaller batch size (e.g., 16 or 32) and adjust based on your hardware capabilities and model performance.", Parent = this },
                new Parameter { Name = "Learning rate", Value = _model.FineTuningParameters?.GetValueOrDefault("Learning rate", "0.001") ?? "0.001", Description = "The step size at each iteration while moving toward a minimum of the loss function. It controls how quickly or slowly a neural network model learns a problem. A high learning rate can cause the model to converge too quickly to a suboptimal solution, while a low learning rate can result in a slow learning process. It's often recommended to start with a small value (e.g., 0.001) and adjust based on training performance.", Parent = this }
            };

            var selectZipButton = new Button
            {
                Text = "Select zip folder (max permitted size: 3.5GB)",
                BackgroundColor = Color.FromArgb("#E0E0E0"),
                TextColor = Color.FromArgb("#333333"),
                CornerRadius = 5,
                Margin = new Thickness(0, 10, 0, 10),
                Command = new Command(async () => await SelectZipFolder())
            };

            var submitVisDatasetButton = new Button
            {
                Text = "Submit Dataset",
                BackgroundColor = Color.FromArgb("#4CAF50"),
                TextColor = Colors.White,
                CornerRadius = 5,
                Margin = new Thickness(0, 10, 0, 10),
                IsVisible = true, 
                Command = new Command(async () => await SubmitVisDataset())
            };

            _selectedZipLabel = new Label
            {
                Text = "No folder selected",
                TextColor = Color.FromArgb("#555555"),
                Margin = new Thickness(0, 10, 0, 10)
            };

            var saveButton = new Button
            {
                Text = "Save Parameters",
                BackgroundColor = Color.FromArgb("#3366FF"),
                TextColor = Colors.White,
                CornerRadius = 5,
                Margin = new Thickness(0, 0, 0, 0),
                Command = new Command(OnSaveParametersClicked),
                HorizontalOptions = LayoutOptions.End
            };
            Grid.SetColumn(saveButton, 1);

            _startVisFineTuningButton = new Button
            {
                Text = "Start Fine-Tuning",
                BackgroundColor = Color.FromArgb("#3366FF"),
                TextColor = Colors.White,
                CornerRadius = 5,
                Margin = new Thickness(0, 10, 0, 0),
                Command = new Command(StartVisFineTuning),
                IsEnabled = false,
                AutomationId = "startVisFineTuningButton"
            };

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
                                new Grid
                                {
                                    ColumnDefinitions =
                                    {
                                        new ColumnDefinition { Width = GridLength.Star },
                                        new ColumnDefinition { Width = GridLength.Auto }
                                    },
                                    Children =
                                    {
                                        new Label { Text = "Fine-tuning parameters", FontSize = 20, FontAttributes = FontAttributes.Bold, TextColor = Color.FromArgb("#555555") },
                                        saveButton
                                    }
                                },
                                new CollectionView
                                {
                                    ItemsSource = Parameters,
                                    ItemTemplate = new DataTemplate(() =>
                                    {
                                        return CreateParameterEntryWithInfo();
                                    })
                                }
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
                                selectZipButton,
                                _selectedZipLabel, 
                                submitVisDatasetButton
                            }
                        }   
                    },
                    _startVisFineTuningButton   
                }
            };
        }

        private string _datasetId;

        private async void StartVisFineTuning()
        {
            if (string.IsNullOrEmpty(_datasetId))
            {
                await Application.Current.MainPage.DisplayAlert("Error", "Please submit a dataset first", "OK");
                return;
            }

            try
            {
                var epochs = Parameters.FirstOrDefault(p => p.Name == "Epochs")?.Value;
                var batchSize = Parameters.FirstOrDefault(p => p.Name == "Batch size")?.Value;
                var learningRate = Parameters.FirstOrDefault(p => p.Name == "Learning rate")?.Value;

                if (string.IsNullOrEmpty(epochs) || string.IsNullOrEmpty(batchSize) || string.IsNullOrEmpty(learningRate))
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Please ensure all parameters are filled", "OK");
                    return;
                }

                var fineTuningData = new
                {
                        epochs = int.Parse(epochs),
                        batch_size = int.Parse(batchSize),
                        learning_rate = double.Parse(learningRate),
                        dataset_id = _datasetId,
                        imgsz = 640
                };

                var modelService = new ModelService();
                await Application.Current.MainPage.DisplayAlert("Fine-Tuning", "Fine-tuning process is starting. This may take a while.", "OK");
                var result = await modelService.TrainModel(_model.ModelId, fineTuningData);

                if (result != null)
                {
                    await Application.Current.MainPage.DisplayAlert("Success", $"Fine-tuning started successfully. Dataset ID: {_datasetId}", "OK");
                }
                else
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Failed to start fine-tuning", "OK");
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
        }

        private async void OnSaveParametersClicked()
        {
            SaveVisParameters();
            await Application.Current.MainPage.DisplayAlert("Success", "Parameters saved successfully", "OK");
        }

        private View CreateNLPUI()
        {
            Parameters = new ObservableCollection<Parameter>
            {
                new Parameter { Name = "Vocabulary size", Value = "", Description = "The number of unique tokens in the model's vocabulary." },
                new Parameter { Name = "Embedding dimension", Value = "", Description = "The size of the vector space in which words are embedded." }
            };

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
                                new CollectionView
                                {
                                    ItemsSource = Parameters,
                                    ItemTemplate = new DataTemplate(() =>
                                    {
                                        return CreateParameterEntryWithInfo();
                                    })
                                }
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

        private View CreateParameterEntryWithInfo()
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
                TextColor = Color.FromArgb("#333333"),
                VerticalOptions = LayoutOptions.Center
            };
            label.SetBinding(Label.TextProperty, "Name");
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
                TextColor = Color.FromArgb("#333333")
            };
            button.SetBinding(Button.CommandProperty, new Binding("Name", source: null, converter: new InfoButtonCommandConverter(this)));
            grid.Add(button, 1, 0);

            var entry = new Entry
            {
                TextColor = Color.FromArgb("#333333")
            };
            entry.SetBinding(Entry.TextProperty, "Value");
            entry.SetBinding(Entry.PlaceholderProperty, new Binding("Name", stringFormat: "Enter {0}"));
            grid.Add(entry, 0, 2);
            Grid.SetColumnSpan(entry, 2);

            var parameter = new Parameter { Name = "", Value = "", Description = "", Parent = this };
            grid.BindingContext = parameter;

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

        public async void ShowInfoPopup(string title, string message)
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

        private async Task SelectZipFolder()
        {
            try
            {
                var result = await FilePicker.PickAsync(new PickOptions
                {
                    FileTypes = new FilePickerFileType(new Dictionary<DevicePlatform, IEnumerable<string>>
                    {
                        { DevicePlatform.iOS, new[] { "public.zip-archive" } },
                        { DevicePlatform.Android, new[] { "application/zip" } },
                        { DevicePlatform.WinUI, new[] { ".zip" } },
                        { DevicePlatform.macOS, new[] { "zip" } }
                    }),
                    PickerTitle = "Please select a zip folder (max permitted size: 3.5GB)"
                });

                if (result != null)
                {
                    var fileInfo = new FileInfo(result.FullPath);
                    const long maxSizeInBytes = (long)(3.5 * 1024 * 1024 * 1024); // Max permitted 3.5 GB in bytes

                    if (fileInfo.Length > maxSizeInBytes)
                    {
                        await Application.Current.MainPage.DisplayAlert("Error", "The selected file exceeds the maximum allowed size of 3.5 GB.", "OK");
                        return;
                    }

                    _selectedZipPath = result.FullPath;
                    _selectedZipLabel.Text = $"Selected folder: {Path.GetFileName(_selectedZipPath)}"; // Update the label text
                    OnPropertyChanged(nameof(_selectedZipPath));
                    await Application.Current.MainPage.DisplayAlert("Success", "Zip file selected successfully", "OK");
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Unable to pick file: {ex.Message}", "OK");
            }
        }

        private async Task SubmitVisDataset()
        {
            if (string.IsNullOrEmpty(_selectedZipPath))
            {
                await Application.Current.MainPage.DisplayAlert("Error", "Please select a zip file first", "OK");
                return;
            }

            try
            {
                var filePath = _selectedZipPath;
                var modelId = _model.ModelId;
                var dataService = new DataService();

                await Application.Current.MainPage.DisplayAlert("Upload", "Please click 'OK' and wait. Dataset is being processed. Approximate maximum time: 2 minutes", "OK");

                // Start the upload process
                await Task.Run(async () =>
                {
                    try
                    {
                        var result = await dataService.UploadImageDataset(filePath, modelId);

                        System.Diagnostics.Debug.WriteLine($"Upload result: {result}");

                        if (result != null && result.TryGetValue("dataset_id", out var datasetIdObj))
                        {
                            _datasetId = datasetIdObj?.ToString();
                            Dispatcher.Dispatch(async () =>
                            {
                                await Application.Current.MainPage.DisplayAlert("Success", $"Dataset uploaded and processed successfully! Dataset ID: {_datasetId}", "OK");
                                if (_startVisFineTuningButton != null)
                                {
                                    _startVisFineTuningButton.IsEnabled = true;
                                }
                                else
                                {
                                    System.Diagnostics.Debug.WriteLine("Start Fine-Tuning button is null");
                                }
                            });
                        }
                        else
                        {
                            Dispatcher.Dispatch(async () =>
                            {
                                await Application.Current.MainPage.DisplayAlert("Error", "Failed to upload dataset: No dataset ID returned", "OK");
                            });
                        }
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"UploadImageDataset error: {ex.Message}");
                        System.Diagnostics.Debug.WriteLine($"Stack Trace: {ex.StackTrace}");

                        Dispatcher.Dispatch(async () =>
                        {
                            await Application.Current.MainPage.DisplayAlert("Error", $"Failed to upload dataset: {ex.Message}", "OK");
                        });
                    }
                });
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"SubmitVisDataset error: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Stack Trace: {ex.StackTrace}");

                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to upload dataset: {ex.Message}", "OK");
            }
        }

        public void SaveVisParameters()
        {
            if (_model != null)
            {
                if (_model.FineTuningParameters == null)
                {
                    _model.FineTuningParameters = new Dictionary<string, string>();
                }

                foreach (var parameter in Parameters)
                {
                    _model.FineTuningParameters[parameter.Name] = parameter.Value;
                }
            }
        }
    }

    public class Parameter : INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler PropertyChanged;

        public string Name { get; set; }
        private string _value;
        public string Value
        {
            get => _value;
            set
            {
                if (_value != value)
                {
                    _value = value;
                    OnPropertyChanged();
                    Parent?.SaveVisParameters();
                }
            }
        }
        public string Description { get; set; }
        public FineTune Parent { get; set; }

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    public class InfoButtonCommandConverter : IValueConverter
    {
        private readonly FineTune _fineTune;

        public InfoButtonCommandConverter(FineTune fineTune)
        {
            _fineTune = fineTune;
        }

        public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            return new Command(() => _fineTune.ShowInfoPopup(value.ToString(), _fineTune.Parameters.FirstOrDefault(p => p.Name == value.ToString())?.Description));
        }

        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}