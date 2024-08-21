using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using frontend.Models;

public class ModelTypeFilter : INotifyPropertyChanged
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
    public partial class FilterPopup : ContentView
    {
        public event EventHandler CloseRequested;
        public event EventHandler<FilteredModelsEventArgs> ApplyFiltersRequested;
        public event EventHandler ResetFiltersRequested;

        public static readonly BindableProperty ModelTypesProperty =
            BindableProperty.Create(nameof(ModelTypes), typeof(ObservableCollection<ModelTypeFilter>), typeof(FilterPopup), null);

        public static readonly BindableProperty FilterOnlineProperty =
            BindableProperty.Create(nameof(FilterOnline), typeof(bool), typeof(FilterPopup), false);

        public static readonly BindableProperty FilterOfflineProperty =
            BindableProperty.Create(nameof(FilterOffline), typeof(bool), typeof(FilterPopup), false);

        public static readonly BindableProperty AllModelsProperty =
            BindableProperty.Create(nameof(AllModels), typeof(ObservableCollection<Model>), typeof(FilterPopup), null);

        public static readonly BindableProperty BaseModelTypesProperty =
            BindableProperty.Create(nameof(BaseModelTypes), typeof(ObservableCollection<ModelTypeFilter>), typeof(FilterPopup), null);

        public static readonly BindableProperty FilterCustomProperty =
            BindableProperty.Create(nameof(FilterCustom), typeof(bool), typeof(FilterPopup), false);

        public static readonly BindableProperty FilterNonCustomProperty =
            BindableProperty.Create(nameof(FilterNonCustom), typeof(bool), typeof(FilterPopup), false);

        public ObservableCollection<ModelTypeFilter> ModelTypes
        {
            get => (ObservableCollection<ModelTypeFilter>)GetValue(ModelTypesProperty);
            set
            {
                SetValue(ModelTypesProperty, value);
                System.Diagnostics.Debug.WriteLine($"ModelTypes set in FilterPopup. Count: {value?.Count ?? 0}");
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

        public ObservableCollection<ModelTypeFilter> BaseModelTypes
        {
            get => (ObservableCollection<ModelTypeFilter>)GetValue(BaseModelTypesProperty);
            set => SetValue(BaseModelTypesProperty, value);
        }

        public bool FilterCustom
        {
            get => (bool)GetValue(FilterCustomProperty);
            set => SetValue(FilterCustomProperty, value);
        }

        public bool FilterNonCustom
        {
            get => (bool)GetValue(FilterNonCustomProperty);
            set => SetValue(FilterNonCustomProperty, value);
        }

        public FilterPopup()
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
            ApplyFiltersRequested?.Invoke(this, new FilteredModelsEventArgs(filteredModels));
        }

        private void OnResetFilters(object sender, EventArgs e)
        {
            ResetFilters();
            ResetFiltersRequested?.Invoke(this, EventArgs.Empty);
        }

        private ObservableCollection<Model> ApplyFilters()
        {
            var selectedTypes = ModelTypes.Where(mt => mt.IsSelected).Select(mt => mt.TypeName).ToList();
            var selectedBaseModels = BaseModelTypes.Where(bmt => bmt.IsSelected).Select(bmt => bmt.TypeName).ToList();

            var filteredModels = AllModels.Where(m =>
                (selectedTypes.Count == 0 || selectedTypes.Contains(m.PipelineTag)) &&
                (selectedBaseModels.Count == 0 || selectedBaseModels.Contains(m.BaseModel)) &&
                ((!FilterOnline && !FilterOffline) ||
                 (FilterOnline && m.Status == "Online") ||
                 (FilterOffline && m.Status == "Offline")) &&
                ((!FilterCustom && !FilterNonCustom) ||
                 (FilterCustom && m.IsCustomised == true) ||
                 (FilterNonCustom && m.IsCustomised != true))
            ).ToList();

            return new ObservableCollection<Model>(filteredModels);
        }

        private void ResetFilters()
        {
            foreach (var modelType in ModelTypes)
            {
                modelType.IsSelected = false;
            }
            foreach (var baseModelType in BaseModelTypes)
            {
                baseModelType.IsSelected = false;
            }
            FilterOnline = false;
            FilterOffline = false;
            FilterCustom = false;
            FilterNonCustom = false;
        }
    }

    public class FilteredModelsEventArgs : EventArgs
    {
        public ObservableCollection<Model> FilteredModels { get; }

        public FilteredModelsEventArgs(ObservableCollection<Model> filteredModels)
        {
            FilteredModels = filteredModels;
        }
    }
}