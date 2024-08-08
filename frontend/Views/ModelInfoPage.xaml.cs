using frontend.Models;
using Microsoft.Maui.Controls;

namespace frontend.Views
{
    public partial class ModelInfoPage : ContentPage
    {
        private ModelInfoViewModel ViewModel => BindingContext as ModelInfoViewModel;

        public ModelInfoPage(ModelItem model)
        {
            InitializeComponent();
            BindingContext = new ModelInfoViewModel(model);
            System.Diagnostics.Debug.WriteLine($"ModelInfoPage constructor called with model: {model?.Name}");
        }
    }
}