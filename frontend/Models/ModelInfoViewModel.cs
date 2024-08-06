using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace frontend.Models
{
    public class ModelInfoViewModel : INotifyPropertyChanged
    {
        private ModelItem _model;
        public ModelItem Model
        {
            get => _model;
            set
            {
                if (_model != value)
                {
                    _model = value;
                    OnPropertyChanged();
                    LoadTags();
                }
            }
        }

        private ObservableCollection<string> _tags = new ObservableCollection<string>();
        public ObservableCollection<string> Tags
        {
            get => _tags;
            set
            {
                if (_tags != value)
                {
                    _tags = value;
                    OnPropertyChanged();
                }
            }
        }

        public ModelInfoViewModel(ModelItem model)
        {
            System.Diagnostics.Debug.WriteLine($"ModelInfoViewModel constructor called with model: {model?.Name}");
            Model = model;
            System.Diagnostics.Debug.WriteLine($"Tags count after setting Model: {Tags.Count}");
        }

        private void LoadTags()
        {
            Tags.Clear();
            System.Diagnostics.Debug.WriteLine($"LoadTags called. Model.Tags count: {Model?.Tags?.Count}");
            if (Model?.Tags != null)
            {
                foreach (var tag in Model.Tags)
                {
                    Tags.Add(tag);
                }
            }
            System.Diagnostics.Debug.WriteLine($"Tags loaded. Count: {Tags.Count}");
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}