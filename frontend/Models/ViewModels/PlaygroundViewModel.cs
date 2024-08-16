using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.ObjectModel;

namespace frontend.Models.ViewModels
{
    internal partial class PlaygroundViewModel : ObservableObject
    {
        [ObservableProperty]
        private Playground? playground;

        public ObservableCollection<Model> PlaygroundModels { get; }

        public ObservableCollection<Model> PlaygroundChain { get; }

        public PlaygroundViewModel()
        {
            PlaygroundModels = new ObservableCollection<Model>();
            PlaygroundChain = new ObservableCollection<Model>();
        }

        partial void OnPlaygroundChanged(Playground? oldValue, Playground? newValue)
        {
            PlaygroundModels.Clear();
            PlaygroundChain.Clear();

            if (newValue?.Models != null)
            {
                foreach (var model in newValue.Models.Values)
                {
                    PlaygroundModels.Add(model);
                }
            }

            if (newValue?.Chain != null)
            {
                foreach (var modelName in newValue.Chain)
                {
                    var model = newValue.Models?.Values.FirstOrDefault(m => m.ModelId == modelName);
                    if (model != null)
                    {
                        PlaygroundChain.Add(model);
                    }
                }
            }
        }
    }
}