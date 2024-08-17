using CommunityToolkit.Mvvm.ComponentModel;

namespace frontend.Models.ViewModels
{
    public partial class ModelViewModel : ObservableObject
    {
        [ObservableProperty]
        private Model? selectedModel;
    }
}
