using System.Collections.ObjectModel;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using System.Diagnostics;
using frontend.Models; 
using frontend.Services;
using System.Text.Json.Serialization;
using System.Text.Json;
using frontend.entities;

namespace frontend.Views
{
    public partial class PlaygroundModelView : ContentView
    {
        public ObservableCollection<Model> PlaygroundModels { get; set; } = new ObservableCollection<Model>();
        public string? Name { get; set; }
        private readonly PlaygroundService _playgroundService;

        public PlaygroundModelView(Dictionary<string, object> playground, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playgroundService = playgroundService;

            Debug.WriteLine($"Playground Object: {JsonSerializer.Serialize(playground)}");

            if (playground.TryGetValue("Id", out var id) && id is string playgroundId)
            {
                Name = playgroundId;
                Debug.WriteLine($"PlaygroundModelView constructor called for {Name}");

                if (playground.TryGetValue("Models", out var modelsObj) && 
                    modelsObj is Dictionary<string, Mapping> models) 
                {
                    var modelDict = new Dictionary<string, Dictionary<string, object>>();

                    foreach (var model in models)
                    {
                        var modelDetails = new Dictionary<string, object>
                        {
                            { "input", model.Value.Input ?? "default_input" }, 
                            { "output", model.Value.Output ?? "default_output" }, 
                            { "pipeline_tag", model.Value.PipelineTag ?? "Unknown" }, 
                            { "is_online", model.Value.IsOnline }
                        };
                        modelDict[model.Key] = modelDetails;
                    }

                    Debug.WriteLine($"Found {modelDict.Count} models in playground");
                    _ = LoadModels(modelDict); 
                }
                else
                {
                    Debug.WriteLine("No models found in playground or incorrect format");
                    Debug.WriteLine($"Models Object: {JsonSerializer.Serialize(modelsObj)}");
                }
            }
            else
            {
                Debug.WriteLine("Incorrect playground data format");
            }

            BindingContext = this;
        }

        private async Task LoadModels(Dictionary<string, Dictionary<string, object>> models)
        {
            Debug.WriteLine($"LoadModels called with {models.Count} models");

            foreach (var modelEntry in models)
            {
                var modelId = modelEntry.Key;
                var modelInfo = modelEntry.Value;

                var model = new Model
                {
                    ModelId = modelId,
                    PipelineTag = modelInfo.ContainsKey("pipeline_tag") ? modelInfo["pipeline_tag"].ToString() : "Unknown",
                    IsOnline = modelInfo.ContainsKey("is_online") && (bool)modelInfo["is_online"],
                    Mapping = new Dictionary<string, object>
                    {
                        { "input", modelInfo["input"] },
                        { "output", modelInfo["output"] }
                    }
                };

                PlaygroundModels.Add(model);
                Debug.WriteLine($"Added Model: {model.ModelId}, PipelineTag: {model.PipelineTag}, IsOnline: {model.IsOnline}");
            }

            Debug.WriteLine($"Final PlaygroundModels count: {PlaygroundModels.Count}");
        }
    }
}