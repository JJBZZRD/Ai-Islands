using System.ComponentModel;
using System.Runtime.CompilerServices;
using frontend.Models;

namespace frontend.ViewModels
{
    public class ButtonViewModel : INotifyPropertyChanged
    {
        private string _selectedTab;
        private Model _model;

        public ButtonViewModel()
        {
            SelectedTab = "Info"; // Default tab
        }

        public ButtonViewModel(Model model)
        {
            _model = model;
            SelectedTab = "Info"; // Default tab
        }

        public string SelectedTab
        {
            get => _selectedTab;
            set
            {
                _selectedTab = value;
                OnPropertyChanged();
            }
        }

        public Model Model
        {
            get => _model;
            set
            {
                _model = value;
                OnPropertyChanged();
            }
        }

        public event PropertyChangedEventHandler PropertyChanged;

        protected void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}