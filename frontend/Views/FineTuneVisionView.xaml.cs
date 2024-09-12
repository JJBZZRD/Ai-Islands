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
using static System.Net.Mime.MediaTypeNames;
using System.Collections.Generic;
using System;
using System.Diagnostics;
using System.Text.RegularExpressions;

namespace frontend.Views
{
    public partial class FineTuneVisionView : ContentView, INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler PropertyChanged;

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        private const string ZipPathPreferenceKey = "SelectedZipPath";
        private const string DatasetIdPreferenceKey = "DatasetId";
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

        private void UpdateSelectedZipLabel()
        {
            MainThread.BeginInvokeOnMainThread(() =>
            {
                _selectedZipLabel.Text = string.IsNullOrEmpty(SelectedZipPath) ? "No folder selected" : $"Selected folder: {Path.GetFileName(SelectedZipPath)}";
            });
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

        public FineTuneVisionView(Model model)
        {
            InitializeComponent();
            _model = model;
            BindingContext = this;

            TaskSpecificContent.Content = GenerateTaskSpecificUI();
            RestoreSavedState();
        
        }

        private void RestoreSavedState()
        {
            // Restore Zip Path
            if (Preferences.ContainsKey(ZipPathPreferenceKey))
            {
                SelectedZipPath = Preferences.Get(ZipPathPreferenceKey, string.Empty);
                UpdateSelectedZipLabel(); // Update label with the restored path
            }

            // Restore Dataset ID
            if (Preferences.ContainsKey(DatasetIdPreferenceKey))
            {
                DatasetId = Preferences.Get(DatasetIdPreferenceKey, string.Empty);
                if (!string.IsNullOrEmpty(DatasetId))
                {
                    _startVisFineTuningButton.IsEnabled = true;
                }
            }
        }

        private View GenerateTaskSpecificUI()
        {
            View taskSpecificContent;
            // Disable fine-tuning for yolov10
            if (_model.ModelId.StartsWith("yolov10", StringComparison.OrdinalIgnoreCase))
            {
                taskSpecificContent = CreateDefaultUI();
                IsFineTuningAvailable = false;
            }
            else
            {
                taskSpecificContent = CreateObjectDetectionUI();
                IsFineTuningAvailable = true;
            }
            return taskSpecificContent;
        }

        private string _selectedZipPath;
        public string SelectedZipPath
        {
            get => _selectedZipPath;
            set
            {
                if (_selectedZipPath != value)
                {
                    _selectedZipPath = value;
                    OnPropertyChanged(nameof(SelectedZipPath));
                    Preferences.Set(ZipPathPreferenceKey, _selectedZipPath); 
                    UpdateSelectedZipLabel(); // Update the label whenever the path changes

                    System.Diagnostics.Debug.WriteLine($"SelectedZipPath updated to: {_selectedZipPath}");
                }
            }
        }

        private Label _selectedZipLabel;

        private View CreateObjectDetectionUI()
        {
            Parameters = new ObservableCollection<Parameter>
            {
                new Parameter { Name = "Epochs", Value = _model.FineTuningParameters?.GetValueOrDefault("Epochs", "10") ?? "10", Description = "The number of complete passes through the training dataset.", Parent = this },
                new Parameter { Name = "Batch size", Value = _model.FineTuningParameters?.GetValueOrDefault("Batch size", "16") ?? "16", Description = "The number of training examples used in one iteration.", Parent = this },
                new Parameter { Name = "Learning rate", Value = _model.FineTuningParameters?.GetValueOrDefault("Learning rate", "0.001") ?? "0.001", Description = "The step size at each iteration while moving toward a minimum of the loss function.", Parent = this }
            };

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
                    new ColumnDefinition { Width = GridLength.Auto }, 
                    new ColumnDefinition { Width = new GridLength(1, GridUnitType.Auto) }, 
                    new ColumnDefinition { Width = GridLength.Auto } 
                }
            };

            grid.Add(new Label { Text = "Epochs", VerticalOptions = LayoutOptions.Center, TextColor = Colors.Black, Margin = new Thickness(0, 0, 10, 0) }, 0, 0); 

            var epochsEntry = new Entry { Text = "10", TextColor = Colors.Black, BackgroundColor = Colors.White, Margin = new Thickness(0), WidthRequest = 300 }; 
            var epochsEntryFrame = new Frame
            {
                Content = epochsEntry,
                BorderColor = Colors.Black, 
                CornerRadius = 5,
                Padding = new Thickness(0),
                HasShadow = false,
                Margin = new Thickness(0, 5, 0, 5) 
            };
            grid.Add(epochsEntryFrame, 1, 0);

            var epochsInfoButton = new Button
            {
                Text = "?",
                FontSize = 12,
                WidthRequest = 25,
                HeightRequest = 25,
                CornerRadius = 12,
                Padding = new Thickness(0),
                Margin = new Thickness(10, 0, 0, 0),
                BackgroundColor = Color.FromArgb("#E0E0E0"),
                TextColor = Color.FromArgb("#333333"),
                VerticalOptions = LayoutOptions.Center
            };
            epochsInfoButton.Clicked += (s, e) => ShowInfoPopup("Epochs", "The number of complete passes through the training dataset.");
            grid.Add(epochsInfoButton, 2, 0);

            grid.Add(new Label { Text = "Batch size", VerticalOptions = LayoutOptions.Center, TextColor = Colors.Black, Margin = new Thickness(0, 0, 10, 0) }, 0, 1); 

            var batchSizeEntry = new Entry { Text = "16", TextColor = Colors.Black, BackgroundColor = Colors.White, Margin = new Thickness(0), WidthRequest = 300 }; 
            var batchSizeEntryFrame = new Frame
            {
                Content = batchSizeEntry,
                BorderColor = Colors.Black, 
                CornerRadius = 5,
                Padding = new Thickness(0), 
                HasShadow = false,
                Margin = new Thickness(0, 5, 0, 5) 
            };
            grid.Add(batchSizeEntryFrame, 1, 1);

            var batchSizeInfoButton = new Button
            {
                Text = "?",
                FontSize = 12,
                WidthRequest = 25,
                HeightRequest = 25,
                CornerRadius = 12,
                Padding = new Thickness(0),
                Margin = new Thickness(10, 0, 0, 0),
                BackgroundColor = Color.FromArgb("#E0E0E0"),
                TextColor = Color.FromArgb("#333333"),
                VerticalOptions = LayoutOptions.Center
            };
            batchSizeInfoButton.Clicked += (s, e) => ShowInfoPopup("Batch size", "The number of training examples used in one iteration.");
            grid.Add(batchSizeInfoButton, 2, 1);

            grid.Add(new Label { Text = "Learning rate", VerticalOptions = LayoutOptions.Center, TextColor = Colors.Black, Margin = new Thickness(0, 0, 10, 0) }, 0, 2); 

            var learningRateEntry = new Entry { Text = "0.001", TextColor = Colors.Black, BackgroundColor = Colors.White, Margin = new Thickness(0), WidthRequest = 300 }; 
            var learningRateEntryFrame = new Frame
            {
                Content = learningRateEntry,
                BorderColor = Colors.Black, 
                CornerRadius = 5,
                Padding = new Thickness(0), 
                HasShadow = false,
                Margin = new Thickness(0, 5, 0, 5) 
            };
            grid.Add(learningRateEntryFrame, 1, 2);

            var learningRateInfoButton = new Button
            {
                Text = "?",
                FontSize = 12,
                WidthRequest = 25,
                HeightRequest = 25,
                CornerRadius = 12,
                Padding = new Thickness(0),
                Margin = new Thickness(10, 0, 0, 0),
                BackgroundColor = Color.FromArgb("#E0E0E0"),
                TextColor = Color.FromArgb("#333333"),
                VerticalOptions = LayoutOptions.Center
            };
            learningRateInfoButton.Clicked += (s, e) => ShowInfoPopup("Learning rate", "The step size at each iteration while moving toward a minimum of the loss function.");
            grid.Add(learningRateInfoButton, 2, 2);

            _selectedZipLabel = new Label
            {
                Text = "No folder selected",
                TextColor = Color.FromArgb("#555555"),
                Margin = new Thickness(0, 10, 0, 10)
            };

            var selectZipButton = new Button
            {
                Text = "Select zip folder (max permitted size: 3.5GB)",
                BackgroundColor = Color.FromArgb("#E0E0E0"),
                TextColor = Color.FromArgb("#333333"),
                CornerRadius = 5,
                HorizontalOptions = LayoutOptions.Start,
                WidthRequest = 320,
                Command = new Command(async () => await SelectZipFolder())
            };

            var uploadDatasetLabel = new Label 
            { 
                Text = "Upload dataset", 
                FontSize = 20, 
                FontAttributes = FontAttributes.Bold, 
                TextColor = Color.FromArgb("#555555")
            };

            var submitVisDatasetButton = new Button
            {
                Text = "Submit Dataset",
                BackgroundColor = Color.FromArgb("#4CAF50"),
                TextColor = Colors.White,
                CornerRadius = 5,
                Margin = new Thickness(10, 0, 0, 0),
                HorizontalOptions = LayoutOptions.Start,
                WidthRequest = 130,
                IsVisible = true,
                Command = new Command(async () => await SubmitVisDataset())
            };

            var buttonGrid = new Grid
            {
                ColumnDefinitions =
                {
                    new ColumnDefinition { Width = GridLength.Auto },
                    new ColumnDefinition { Width = GridLength.Auto }
                }
            };

            buttonGrid.Add(selectZipButton, 0, 0); 
            buttonGrid.Add(submitVisDatasetButton, 1, 0);

            var datasetDescriptionLabel = new Label 
            { 
                Text = "Ensure your dataset is uploaded in the correct format:\n• Download the example dataset to view the dataset structure expected by the model.\n• YOLO supports annotations written in .txt files.\n• The content in obj.names are the classes in the correct order; ensure there is no space before, between, or after the classes.\n• The .txt file contains the class index followed by bounding box coordinates (in the range 0-1).",
                FontSize = 14,
                TextColor = Color.FromArgb("#555555"),
                Margin = new Thickness(0, 10, 0, 0)
            };

            var downloadExampleDatasetButton = new Button
            {
                Text = "Download Example Dataset",
                BackgroundColor = Color.FromArgb("#E0E0E0"),
                TextColor = Color.FromArgb("#333333"),
                CornerRadius = 5,
                HorizontalOptions = LayoutOptions.End,
                WidthRequest = 210,
                Command = new Command(async () => await DownloadExampleDataset())
            };

           
            var descriptionGrid = new Grid
            {
                ColumnDefinitions =
                {
                    new ColumnDefinition { Width = GridLength.Star }, 
                    new ColumnDefinition { Width = GridLength.Auto }  
                }
            };

            descriptionGrid.Add(uploadDatasetLabel, 0, 0); 
            descriptionGrid.Add(downloadExampleDatasetButton, 1, 0); 

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
                                grid
                            }
                        }
                    },
                    new Frame
                    {
                        BackgroundColor = Colors.White,
                        Padding = new Thickness(20),
                        CornerRadius = 10,
                        Margin = new Thickness(0, 20, 0, 0),
                        Content = new VerticalStackLayout
                        {
                            Spacing = 15,
                            Children =
                            {
                                descriptionGrid, 
                                datasetDescriptionLabel,
                                buttonGrid,     
                                _selectedZipLabel
                            }
                        }
                    },
                    _startVisFineTuningButton
                }
            };
        }

        private string _datasetId;
        public string DatasetId
        {
            get => _datasetId;
            set
            {
                if (_datasetId != value)
                {
                    _datasetId = value;
                    OnPropertyChanged(nameof(DatasetId));
                    Preferences.Set(DatasetIdPreferenceKey, _datasetId);
                }
            }
        }

        private async void StartVisFineTuning()
        {
            if (string.IsNullOrEmpty(_datasetId))
            {
                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", "Please submit a dataset first", "OK");
                return;
            }

            try
            {
                var epochs = Parameters.FirstOrDefault(p => p.Name == "Epochs")?.Value;
                var batchSize = Parameters.FirstOrDefault(p => p.Name == "Batch size")?.Value;
                var learningRate = Parameters.FirstOrDefault(p => p.Name == "Learning rate")?.Value;

                if (string.IsNullOrEmpty(epochs) || string.IsNullOrEmpty(batchSize) || string.IsNullOrEmpty(learningRate))
                {
                    await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", "Please ensure all parameters are filled", "OK");
                    return;
                }

                var currentDirectory = AppDomain.CurrentDomain.BaseDirectory;
                var projectRootDirectory = Path.GetFullPath(Path.Combine(currentDirectory, @"..\..\..\..\..\.."));
                var backendUtilsDirectory = Path.Combine(projectRootDirectory, "backend", "utils");
                var scriptPath = Path.Combine(backendUtilsDirectory, "train_vis.py");

                string arguments;
                if (Environment.OSVersion.Platform == PlatformID.Win32NT)
                {
                    // For Windows
                    var venvPath = Path.Combine(projectRootDirectory, "venv", "Scripts", "activate.bat");

                    arguments = $"/c echo Activating venv && call \"{venvPath}\" && " +
                                $"echo Navigating to: {backendUtilsDirectory} && cd /d \"{backendUtilsDirectory}\" && " +
                                $"echo Now in Directory: && cd && " +
                                $"echo Running Python Version && python --version && " +
                                $"echo Running Script && python \"{scriptPath}\" --model_id \"{_model.ModelId}\" --action fine_tune --epochs {epochs} --batch_size {batchSize} --learning_rate {learningRate} --dataset_id {_datasetId} --imgsz 640";
                }
                else
                {
                    // For Unix
                    var venvPath = Path.Combine(projectRootDirectory, "venv", "bin", "activate");

                    arguments = $"/c bash -c 'echo Activating venv && source \"{venvPath}\" && " +
                                $"echo Navigating to: {backendUtilsDirectory} && cd \"{backendUtilsDirectory}\" && " +
                                $"echo Now in Directory: && pwd && " +
                                $"echo Running Python Version && python --version && " +
                                $"echo Running Script && python \"{scriptPath}\" --model_id \"{_model.ModelId}\" --action fine_tune --epochs {epochs} --batch_size {batchSize} --learning_rate {learningRate} --dataset_id {_datasetId} --imgsz 640'";
                }

                ProcessStartInfo processInfo = new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = arguments,
                    CreateNoWindow = false,
                    UseShellExecute = true,
                    WindowStyle = ProcessWindowStyle.Normal
                };

                Process process = Process.Start(processInfo);

                if (process == null)
                {
                    await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", "Failed to start fine-tuning process.", "OK");
                    return;
                }

                process.WaitForExit();

                if (process.ExitCode == 0)
                {
                    await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Success", "Fine-tuning completed successfully. The fine-tuned model has been added to the library.", "OK");
                }
                else
                {
                    await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", "Fine-tuning failed. Please try again.", "OK");
                }
            }
            catch (Exception ex)
            {
                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
            }
        }

        private async void OnSaveParametersClicked()
        {
            SaveVisParameters();
            await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Success", "Parameters saved successfully", "OK");
        }

        private View CreateParameterEntryWithInfo()
        {
            var grid = new Grid
            {
                RowDefinitions =
                {
                    new RowDefinition { Height = GridLength.Auto }
                },
                ColumnDefinitions =
                {
                    new ColumnDefinition { Width = GridLength.Auto },
                    new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) },
                    new ColumnDefinition { Width = GridLength.Auto }
                }
            };

            var label = new Label
            {
                TextColor = Color.FromArgb("#333333"),
                VerticalOptions = LayoutOptions.Center,
                Margin = new Thickness(0, 0, 10, 0) 
            };
            label.SetBinding(Label.TextProperty, "Name");
            grid.Add(label, 0, 0);

            var entry = new Entry
            {
                TextColor = Color.FromArgb("#333333"),
                BackgroundColor = Colors.White,
                VerticalOptions = LayoutOptions.Center,
                Margin = new Thickness(0, 0, 0, 0) 
            };
            entry.SetBinding(Entry.TextProperty, "Value");
            entry.SetBinding(Entry.PlaceholderProperty, new Binding("Name", stringFormat: "Enter {0}"));

            var entryFrame = new Frame
            {
                Content = entry,
                BorderColor = Colors.Black,
                CornerRadius = 5,
                Padding = new Thickness(0),
                HasShadow = false,
                Margin = new Thickness(0, 5, 0, 5)
            };

            grid.Add(entryFrame, 1, 0);

            var button = new Button
            {
                Text = "?",
                FontSize = 12,
                WidthRequest = 25,
                HeightRequest = 25,
                CornerRadius = 12,
                Padding = new Thickness(0),
                Margin = new Thickness(10, 0, 0, 0), 
                BackgroundColor = Color.FromArgb("#E0E0E0"),
                TextColor = Color.FromArgb("#333333"),
                VerticalOptions = LayoutOptions.Center
            };
            button.SetBinding(Button.CommandProperty, new Binding("Name", source: null, converter: new InfoButtonCommandConverter(this)));
            grid.Add(button, 2, 0);

            var parameter = new Parameter { Name = "", Value = "", Description = "", Parent = this };
            grid.BindingContext = parameter;

            return grid;
        }

        public async void ShowInfoPopup(string title, string message)
        {
            await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert(title, message, "OK");
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

                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Success", $"Example dataset downloaded to:\n{targetFile}", "OK");
            }
            catch (Exception ex)
            {
                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", $"Failed to download example dataset: {ex.Message}", "OK");
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
                { DevicePlatform.macOS, new[] { "zip" }}
            }),
                    PickerTitle = "Please select a zip folder (max permitted size: 3.5GB)"
                });

                if (result != null)
                {
                    var fileInfo = new FileInfo(result.FullPath);
                    const long maxSizeInBytes = (long)(3.5 * 1024 * 1024 * 1024); // Max permitted 3.5 GB in bytes

                    if (fileInfo.Length > maxSizeInBytes)
                    {
                        await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", "The selected file exceeds the maximum allowed size of 3.5 GB.", "OK");
                        return;
                    }

                    // Asking the user for confirmation if an existing dataset is present
                    if (!string.IsNullOrEmpty(DatasetId))
                    {
                        bool confirmDelete = await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert(
                            "Confirm",
                            "An existing dataset has been uploaded. Do you want to delete it and upload a new one?",
                            "Yes", "No");

                        if (!confirmDelete)
                        {
                            await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Cancelled", "The upload process has been cancelled. The old dataset remains.", "OK");
                            return;
                        }

                        // If confirmed, old dataset folder is deleted
                        DeleteDatasetFolder(DatasetId);
                    }

                    SelectedZipPath = result.FullPath; 

                    // Reset DatasetId to ensure new dataset upload is required
                    DatasetId = null;
                    _startVisFineTuningButton.IsEnabled = false;

                    await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Success", "Zip file selected successfully", "OK");
                }
            }
            catch (Exception ex)
            {
                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", $"Unable to pick file: {ex.Message}", "OK");
            }
        }


        private async Task SubmitVisDataset()
        {
            if (string.IsNullOrEmpty(SelectedZipPath))
            {
                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", "Please select a zip file first", "OK");
                return;
            }

            try
            {
                var filePath = SelectedZipPath;
                var modelId = _model.ModelId;
                var dataService = new DataService();

                
                System.Diagnostics.Debug.WriteLine($"Current DatasetId before deletion: {DatasetId}");

                if (!string.IsNullOrEmpty(DatasetId))
                {
                    DeleteDatasetFolder(DatasetId);
                }

                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Upload", "Please click 'OK' and wait. Dataset is being processed. Approximate maximum time: 2 minutes", "OK");

                // Start the upload process
                await Task.Run(async () =>
                {
                    try
                    {
                        var result = await dataService.UploadImageDataset(filePath, modelId);

                        System.Diagnostics.Debug.WriteLine($"Upload result: {result}");

                        if (result != null && result.TryGetValue("dataset_id", out var datasetIdObj))
                        {
                            DatasetId = datasetIdObj?.ToString(); 
                            System.Diagnostics.Debug.WriteLine($"New DatasetId after upload: {DatasetId}");

                            Dispatcher.Dispatch(async () =>
                            {
                                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Success", $"Dataset uploaded and processed successfully! Dataset ID: {DatasetId}", "OK");
                                _startVisFineTuningButton.IsEnabled = true;

                                if (_startVisFineTuningButton == null)
                                {
                                    System.Diagnostics.Debug.WriteLine("Start Fine-Tuning button is null");
                                }
                            });
                        }
                        else
                        {
                            Dispatcher.Dispatch(async () =>
                            {
                                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", "Failed to upload dataset: No dataset ID returned", "OK");
                            });
                        }
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"UploadImageDataset error: {ex.Message}");
                        System.Diagnostics.Debug.WriteLine($"Stack Trace: {ex.StackTrace}");

                        Dispatcher.Dispatch(async () =>
                        {
                            await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", $"Failed to upload dataset: {ex.Message}", "OK");
                        });
                    }
                });
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"SubmitVisDataset error: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Stack Trace: {ex.StackTrace}");

                await Microsoft.Maui.Controls.Application.Current.MainPage.DisplayAlert("Error", $"Failed to upload dataset: {ex.Message}", "OK");
            }
        }

        private void DeleteDatasetFolder(string datasetId)
        {
            try
            {
                var currentDirectory = AppDomain.CurrentDomain.BaseDirectory;
                var projectRootDirectory = Path.GetFullPath(Path.Combine(currentDirectory, @"..\..\..\..\..\.."));

                var datasetDirectory = Path.Combine(projectRootDirectory, "data", "uploaded_dataset", datasetId);

                System.Diagnostics.Debug.WriteLine($"Attempting to delete dataset directory: {datasetDirectory}");

                if (Directory.Exists(datasetDirectory))
                {
                    Directory.Delete(datasetDirectory, true);
                    System.Diagnostics.Debug.WriteLine($"Old dataset folder deleted: {datasetDirectory}");
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine($"Dataset folder does not exist: {datasetDirectory}");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error deleting old dataset folder: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Stack Trace: {ex.StackTrace}");
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
        public FineTuneVisionView Parent { get; set; }

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    public class InfoButtonCommandConverter : IValueConverter
    {
        private readonly FineTuneVisionView _fineTuneVisionView;

        public InfoButtonCommandConverter(FineTuneVisionView fineTuneVisionView)
        {
            _fineTuneVisionView = fineTuneVisionView;
        }

        public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            return new Command(() => _fineTuneVisionView.ShowInfoPopup(value.ToString(), _fineTuneVisionView.Parameters.FirstOrDefault(p => p.Name == value.ToString())?.Description));
        }

        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
