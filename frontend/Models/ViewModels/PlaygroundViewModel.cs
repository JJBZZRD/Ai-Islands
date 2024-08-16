using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.ObjectModel;

namespace frontend.Models.ViewModels
{
    internal partial class PlaygroundViewModel : ObservableObject
    {
        [ObservableProperty]
        private Playground? playground;

        public ObservableCollection<Model> PlaygroundModels { get; }

        public PlaygroundViewModel()
        {
            PlaygroundModels = new ObservableCollection<Model>();
        }

        partial void OnPlaygroundChanged(Playground? oldValue, Playground? newValue)
        {
            PlaygroundModels.Clear();

            if (newValue?.Models != null)
            {
                foreach (var model in newValue.Models.Values)
                {
                    PlaygroundModels.Add(model);
                }
            }
        }
    }
}