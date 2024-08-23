using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using frontend.Models;

public class ModelIndexTypeFilter : INotifyPropertyChanged
{
    public string TypeName { get; set; }
    private bool _isSelected;
    public bool IsSelected
    {
        get => _isSelected;
        set
        {
            _isSelected = value;
            OnPropertyChanged(nameof(IsSelected));
        }
    }

    public event PropertyChangedEventHandler PropertyChanged;
    protected virtual void OnPropertyChanged(string propertyName)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}

namespace frontend.Views
{
    public partial class ModelIndexFilterPopup : ContentView
    {
        public event EventHandler CloseRequested;
        public event EventHandler<ModelIndexFilteredModelsEventArgs> ApplyFiltersRequested;
        public event EventHandler ResetFiltersRequested;

        public static readonly BindableProperty ModelTypesProperty =
            BindableProperty.Create(nameof(ModelTypes), typeof(ObservableCollection<ModelIndexTypeFilter>), typeof(ModelIndexFilterPopup), null);

        public static readonly BindableProperty FilterOnlineProperty =
            BindableProperty.Create(nameof(FilterOnline), typeof(bool), typeof(ModelIndexFilterPopup), false);

        public static readonly BindableProperty FilterOfflineProperty =
            BindableProperty.Create(nameof(FilterOffline), typeof(bool), typeof(ModelIndexFilterPopup), false);

        public static readonly BindableProperty AllModelsProperty =
            BindableProperty.Create(nameof(AllModels), typeof(ObservableCollection<Model>), typeof(ModelIndexFilterPopup), null);

        public ObservableCollection<ModelIndexTypeFilter> ModelTypes
        {
            get => (ObservableCollection<ModelIndexTypeFilter>)GetValue(ModelTypesProperty);
            set
            {
                SetValue(ModelTypesProperty, value);
                System.Diagnostics.Debug.WriteLine($"ModelTypes set in ModelIndexFilterPopup. Count: {value?.Count ?? 0}");
                if (value != null)
                {
                    foreach (var type in value)
                    {
                        System.Diagnostics.Debug.WriteLine($"Type: {type.TypeName}");
                    }
                }
            }
        }

        public bool FilterOnline
        {
            get => (bool)GetValue(FilterOnlineProperty);
            set => SetValue(FilterOnlineProperty, value);
        }

        public bool FilterOffline
        {
            get => (bool)GetValue(FilterOfflineProperty);
            set => SetValue(FilterOfflineProperty, value);
        }

        public ObservableCollection<Model> AllModels
        {
            get => (ObservableCollection<Model>)GetValue(AllModelsProperty);
            set => SetValue(AllModelsProperty, value);
        }

        public ModelIndexFilterPopup()
        {
            InitializeComponent();
            BindingContext = this;
        }

        private void OnCloseFilterPopup(object sender, EventArgs e)
        {
            CloseRequested?.Invoke(this, EventArgs.Empty);
        }

        private void OnApplyFilters(object sender, EventArgs e)
        {
            var filteredModels = ApplyFilters();
            ApplyFiltersRequested?.Invoke(this, new ModelIndexFilteredModelsEventArgs(filteredModels));
        }

        private void OnResetFilters(object sender, EventArgs e)
        {
            ResetFilters();
            ResetFiltersRequested?.Invoke(this, EventArgs.Empty);
        }

        private ObservableCollection<Model> ApplyFilters()
        {
            var selectedTypes = ModelTypes.Where(mt => mt.IsSelected).Select(mt => mt.TypeName).ToList();

            var filteredModels = AllModels.Where(m =>
                (selectedTypes.Count == 0 || selectedTypes.Contains(m.PipelineTag)) &&
                ((!FilterOnline && !FilterOffline) ||
                 (FilterOnline && m.Status == "Online") ||
                 (FilterOffline && m.Status == "Offline"))
            ).ToList();

            return new ObservableCollection<Model>(filteredModels);
        }

        private void ResetFilters()
        {
            foreach (var modelType in ModelTypes)
            {
                modelType.IsSelected = false;
            }
            FilterOnline = false;
            FilterOffline = false;
        }
    }

    public class ModelIndexFilteredModelsEventArgs : EventArgs
    {
        public ObservableCollection<Model> FilteredModels { get; }

        public ModelIndexFilteredModelsEventArgs(ObservableCollection<Model> filteredModels)
        {
            FilteredModels = filteredModels;
        }
    }
}