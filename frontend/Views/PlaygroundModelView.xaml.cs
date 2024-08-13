using System.Collections.ObjectModel;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using System.Diagnostics;
using frontend.Models; 
using frontend.Services;
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
        private readonly frontend.entities.Playground _playground;

        public PlaygroundModelView(frontend.entities.Playground playground, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playgroundService = playgroundService;
            _playground = playground;

            Debug.WriteLine($"Playground Object: {JsonSerializer.Serialize(playground)}");

            Name = playground.PlaygroundId;
            Debug.WriteLine($"PlaygroundModelView constructor called for {Name}");

            if (playground.Models != null && playground.Models.Count > 0)
            {
                Debug.WriteLine($"Found {playground.Models.Count} models in playground");
                LoadModels(playground.Models);
            }
            else if (playground.ModelIds != null && playground.ModelIds.Count > 0)
            {
                Debug.WriteLine($"Found {playground.ModelIds.Count} model IDs in playground");
                LoadModelIds(playground.ModelIds);
            }
            else
            {
                Debug.WriteLine("No models found in playground");
            }

            BindingContext = this;

            // Register to listen for ModelAddedMessage
            WeakReferenceMessenger.Default.Register<ModelAddedMessage>(this, (r, m) =>
            {
                // Directly add the model to the PlaygroundModels collection
                PlaygroundModels.Add(m.AddedModel);
            });
        }

        private void LoadModels(Dictionary<string, Model> models)
        {
            Debug.WriteLine($"LoadModels called with {models.Count} models");

            foreach (var modelEntry in models)
            {
                var modelId = modelEntry.Key;
                var model = modelEntry.Value;

                model.ModelId = modelId;
                PlaygroundModels.Add(model);
                Debug.WriteLine($"Added Model: {model.ModelId}, PipelineTag: {model.PipelineTag}, IsOnline: {model.IsOnline}");
                if (model.Mapping != null)
                {
                    Debug.WriteLine($"Model Mapping - Input: {model.Mapping.Input}, Output: {model.Mapping.Output}");
                }
            }

            Debug.WriteLine($"Final PlaygroundModels count: {PlaygroundModels.Count}");
        }

        private void LoadModelIds(Dictionary<string, object> modelIds)
        {
            Debug.WriteLine($"LoadModelIds called with {modelIds.Count} model IDs");

            foreach (var modelEntry in modelIds)
            {
                var modelId = modelEntry.Key;
                var modelInfo = modelEntry.Value as Dictionary<string, object>;

                var model = new Model
                {
                    ModelId = modelId,
                    PipelineTag = modelInfo?.ContainsKey("pipeline_tag") == true ? modelInfo["pipeline_tag"].ToString() : "Unknown",
                    IsOnline = modelInfo?.ContainsKey("is_online") == true && (bool)modelInfo["is_online"],
                    Mapping = new Mapping
                    {
                        Input = modelInfo?.ContainsKey("input") == true ? modelInfo["input"].ToString() : "default_input",
                        Output = modelInfo?.ContainsKey("output") == true ? modelInfo["output"].ToString() : "default_output"
                    }
                };

                PlaygroundModels.Add(model);
                Debug.WriteLine($"Added Model: {model.ModelId}, PipelineTag: {model.PipelineTag}, IsOnline: {model.IsOnline}");
                Debug.WriteLine($"Model Mapping - Input: {model.Mapping.Input}, Output: {model.Mapping.Output}");
            }

            Debug.WriteLine($"Final PlaygroundModels count: {PlaygroundModels.Count}");
        }

        private async Task RefreshPlaygroundModels()
        {
            try
            {
                var updatedPlayground = await _playgroundService.GetPlaygroundInfo(_playground.PlaygroundId);
                if (updatedPlayground.Models != null && updatedPlayground.Models.Count > 0)
                {
                    PlaygroundModels.Clear();
                    LoadModels(updatedPlayground.Models);
                }
                else if (updatedPlayground.ModelIds != null && updatedPlayground.ModelIds.Count > 0)
                {
                    PlaygroundModels.Clear();
                    LoadModelIds(updatedPlayground.ModelIds);
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
            WeakReferenceMessenger.Default.Register<Model, string>(this, "ModelAdded", (sender, model) =>
            {
                PlaygroundModels.Add(model);
                if (_playground.Models == null)
                {
                    _playground.Models = new Dictionary<string, Model>();
                }
                _playground.Models[model.ModelId] = model;
            });
        }
    }
}