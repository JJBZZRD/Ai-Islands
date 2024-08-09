using System.Collections.ObjectModel;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using System.Diagnostics;

namespace frontend.Views
{
    public partial class PlaygroundModelView : ContentView
    {
        public ObservableCollection<Dictionary<string, object>> PlaygroundModels { get; set; }
        public string Name { get; set; }

        public PlaygroundModelView(Dictionary<string, object> playground)
        {
            InitializeComponent();

            PlaygroundModels = new ObservableCollection<Dictionary<string, object>>();
            Name = playground["Name"] as string ?? "Playground";

            Debug.WriteLine($"Playground: {Name}");
            Debug.WriteLine($"Playground contents: {string.Join(", ", playground.Keys)}");

            if (playground.ContainsKey("Models"))
            {
                Debug.WriteLine($"Models type: {playground["Models"].GetType()}");
                if (playground["Models"] is Dictionary<string, object> models)
                {
                    foreach (var model in models)
                    {
                        if (model.Value is Dictionary<string, object> modelDetails)
                        {
                            PlaygroundModels.Add(new Dictionary<string, object>
                {
                    { "Name", model.Key },
                    { "PipelineTag", modelDetails.ContainsKey("PipelineTag") ? modelDetails["PipelineTag"] : "Unknown" },
                    { "Status", modelDetails.ContainsKey("Status") ? modelDetails["Status"] : "Unknown" }
                });
                        }
                    }
                }
                else
                {
                    Debug.WriteLine("Models is not a Dictionary<string, object>");
                }
            }

            Debug.WriteLine($"PlaygroundModels count: {PlaygroundModels.Count}");

            BindingContext = this;
        }
    }
}