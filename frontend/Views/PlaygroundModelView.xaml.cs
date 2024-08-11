using System.Collections.ObjectModel;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using System.Diagnostics;
using frontend.Models; 
using frontend.Services;
using System.Text.Json.Serialization;
using System.Text.Json;
using frontend.entities;
using Microsoft.Maui.Layouts;
using CommunityToolkit.Mvvm.Messaging;


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

            // Register to listen for ModelAddedMessage
            WeakReferenceMessenger.Default.Register<ModelAddedMessage>(this, (r, m) =>
            {
                // Directly add the model to the PlaygroundModels collection
                PlaygroundModels.Add(m.AddedModel);
            });
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

        private async Task RefreshPlaygroundModels()
        {
            try
            {
                var playgroundInfo = await _playgroundService.GetPlaygroundInfo(Name);
                if (playgroundInfo.TryGetValue("models", out var modelsObj) && modelsObj is Dictionary<string, Mapping> models)
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

                    PlaygroundModels.Clear();
                    await LoadModels(modelDict);
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error refreshing playground models: {ex.Message}");
            }
        }

        private void OnAddModelClicked(object sender, EventArgs e)
        {
            var modelSelectionPopup = new ModelSelectionPopup(this)
            {
                PlaygroundId = this.Name ?? string.Empty
            };
            AbsoluteLayout.SetLayoutFlags(modelSelectionPopup, AbsoluteLayoutFlags.All);
            AbsoluteLayout.SetLayoutBounds(modelSelectionPopup, new Rect(0, 0, 1, 1));
            MainLayout.Children.Add(modelSelectionPopup);
            modelSelectionPopup.IsVisible = true;

            // Unregister any existing handler before registering a new one
            WeakReferenceMessenger.Default.Unregister<Model, string>(this, "ModelAdded");
            WeakReferenceMessenger.Default.Register<Model, string>(this, "ModelAdded", async (sender, model) =>
            {
                await LoadModels(new Dictionary<string, Dictionary<string, object>>
                {
                    { model.ModelId ?? "unknown", new Dictionary<string, object>
                        {
                            { "input", model.Mapping?["input"] ?? "unknown" },
                            { "output", model.Mapping?["output"] ?? "unknown" },
                            { "pipeline_tag", model.PipelineTag ?? "Unknown" },
                            { "is_online", false }
                        }
                    }
                });
            });
        }
    }
}