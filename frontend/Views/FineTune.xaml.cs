using frontend.Models;
using Microsoft.Maui.Controls;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace frontend.Views
{
    public partial class FineTune : ContentView, INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler PropertyChanged;

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
        
        private ModelItem _model;
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

        public FineTune(ModelItem model)
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
                            new Label { Text = "Training parameters", FontSize = 20, FontAttributes = FontAttributes.Bold, TextColor = Color.FromArgb("#555555") },
                            CreateParameterEntry("Epochs"),
                            CreateParameterEntry("Batch size"),
                            CreateParameterEntry("Learning rate")
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
                            new Button { Text = "Select file", BackgroundColor = Color.FromArgb("#E0E0E0"), TextColor = Color.FromArgb("#333333"), CornerRadius = 5 }
                        }
                    }
                }
            }
            };
        }

        private View CreateNLPUI()
        {
            // i'm not sure about the exact parameters etc that are needed for this task
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
                            CreateParameterEntry("Vocabulary size"),
                            CreateParameterEntry("Embedding dimension"),
                            
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
                            new Button { Text = "Select file", BackgroundColor = Color.FromArgb("#E0E0E0"), TextColor = Color.FromArgb("#333333"), CornerRadius = 5 }
                        }
                    }
                }
            }
            };
        }

        private VerticalStackLayout CreateParameterEntry(string parameterName)
        {
            return new VerticalStackLayout
            {
                Spacing = 5,
                Children =
            {
                new Label { Text = parameterName, TextColor = Color.FromArgb("#333333") },
                new Entry { Placeholder = $"Enter {parameterName.ToLower()}", TextColor = Color.FromArgb("#333333") }
            }
            };
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

    }
}