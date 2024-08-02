using System.Collections.ObjectModel;
using frontend.Models;

namespace frontend.Views
{
    public partial class TagsView : ContentView
    {
        public static readonly BindableProperty TagsProperty =
            BindableProperty.Create(nameof(Tags), typeof(ObservableCollection<string>), typeof(TagsView), new ObservableCollection<string>());

        public ObservableCollection<string> Tags
        {
            get => (ObservableCollection<string>)GetValue(TagsProperty);
            set
            {
                SetValue(TagsProperty, value);
                System.Diagnostics.Debug.WriteLine($"Tags set in TagsView. Count: {value?.Count ?? 0}");
                if (value != null)
                {
                    foreach (var tag in value)
                    {
                        System.Diagnostics.Debug.WriteLine($"Tag: {tag}");
                    }
                }
            }
        }

        public TagsView()
        {
            InitializeComponent();
            //BindingContext = this;
            System.Diagnostics.Debug.WriteLine($"TagsView constructor called. Tags count: {Tags?.Count ?? 0}");
        }

        protected override void OnBindingContextChanged()
        {
            base.OnBindingContextChanged();
            var tagsViewModel = BindingContext as ModelInfoViewModel;
            System.Diagnostics.Debug.WriteLine($"TagsView BindingContext changed. ViewModel Tags count: {tagsViewModel?.Tags?.Count ?? 0}");
        }
    }
}