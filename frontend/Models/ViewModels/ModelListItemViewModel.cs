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

        public ModelListItemViewModel(Model model)
        {
            Model = model;
            IsLoaded = model.IsLoaded;
        }

        public event PropertyChangedEventHandler PropertyChanged;

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}