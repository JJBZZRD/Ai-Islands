using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using frontend.Models;

namespace frontend.ViewModels
{
    public class ModelListItemViewModel : INotifyPropertyChanged
    {
        public Model Model { get; }

        public string ModelId => Model.ModelId;
        public string PipelineTag => Model.PipelineTag;
        public string Status => Model.Status;
        public string BaseModel => Model.BaseModel;

        private bool _isCustomised;
        public bool IsCustomised
        {
            get => Model.IsCustomised ?? false;
            set
            {
                if (_isCustomised != value)
                {
                    _isCustomised = value;
                    Model.IsCustomised = value;
                    OnPropertyChanged();
                    IsCustomisedChanged?.Invoke(this, value);
                }
            }
        }

        // Event to notify the View
        public event EventHandler<bool> IsCustomisedChanged;

        private bool _isLoaded;
        public bool IsLoaded
        {
            get => _isLoaded;
            set
            {
                if (_isLoaded != value)
                {
                    _isLoaded = value;
                    OnPropertyChanged();
                }
            }
        }

        private bool _isButtonEnabled = true;
        public bool IsButtonEnabled
        {
            get => _isButtonEnabled;
            set
            {
                if (_isButtonEnabled != value)
                {
                    _isButtonEnabled = value;
                    OnPropertyChanged();
                }
            }
        }

        public ICommand LoadOrStopCommand { get; set; }

        private Color _customLabelColor;
        public Color CustomLabelColor
        {
            get => _customLabelColor;
            set
            {
                if (_customLabelColor != value)
                {
                    _customLabelColor = value;
                    OnPropertyChanged();
                }
            }
        }

        public ModelListItemViewModel(Model model)
        {
            Model = model;
            IsLoaded = model.IsLoaded;
            _isCustomised = model.IsCustomised ?? false;
        }

        public event PropertyChangedEventHandler PropertyChanged;

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        public void UpdateCustomLabelColor()
        {
            Color trueColor = Color.FromArgb("#34C759");
            Color falseColorLight = Color.FromArgb("#E5E5EA");
            Color falseColorDark = Color.FromArgb("#3A3A3C");

            if (IsCustomised)
            {
                CustomLabelColor = trueColor;
            }
            else
            {
                CustomLabelColor = Application.Current.RequestedTheme == AppTheme.Dark ? falseColorDark : falseColorLight;
            }
        }
    }
}