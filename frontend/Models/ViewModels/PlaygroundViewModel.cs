using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.ObjectModel;

namespace frontend.Models.ViewModels
{
    public partial class PlaygroundViewModel : ObservableObject
    {
        [ObservableProperty]
        private Playground? playground;

        public ObservableCollection<Model> PlaygroundModels { get; }

        public ObservableCollection<ModelViewModel> PlaygroundChain { get; }

        public PlaygroundViewModel()
        {
            PlaygroundModels = new ObservableCollection<Model>();
            PlaygroundChain = new ObservableCollection<ModelViewModel>();
        }

        public void SetPlaygroundChainForPicker()
        {
            for (int i = 0; i < PlaygroundChain.Count; i++)
            {
                PlaygroundChain[i].SelectedModel = playground.Models[playground.Chain[i]];
            }
        }

        partial void OnPlaygroundChanged(Playground? oldValue, Playground? newValue)
        {
            System.Diagnostics.Debug.WriteLine($"======Playground changed");
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
                        PlaygroundChain.Add(new ModelViewModel { SelectedModel = model });
                    }
                }
            }
        }
    }
}