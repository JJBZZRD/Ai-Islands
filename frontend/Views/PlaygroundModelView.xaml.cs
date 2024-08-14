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
        private frontend.entities.Playground _playground;
        private readonly PlaygroundService _playgroundService;

        public PlaygroundModelView(frontend.entities.Playground playground, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playgroundService = playgroundService;
            _playground = playground;

            Name = playground.PlaygroundId;
            Debug.WriteLine($"PlaygroundModelView constructor called for {Name}");

            LoadPlaygroundModels();

            BindingContext = this;

            // Register to listen for RefreshPlaygroundModelsMessage
            WeakReferenceMessenger.Default.Register<RefreshPlaygroundModelsMessage>(this, (r, m) =>
            {
                Debug.WriteLine($"Received RefreshPlaygroundModelsMessage for {m.PlaygroundId}");
                if (m.PlaygroundId == Name)
                {
                    Debug.WriteLine("Calling RefreshPlaygroundModels");
                    MainThread.BeginInvokeOnMainThread(async () => await RefreshPlaygroundModels());
                }
            });
        }

        private async Task RefreshPlaygroundModels()
        {
            try
            {
                Debug.WriteLine("RefreshPlaygroundModels called");
                var updatedPlayground = await _playgroundService.GetPlaygroundInfo(_playground.PlaygroundId);
                _playground = updatedPlayground;
                LoadPlaygroundModels();
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error refreshing playground models: {ex.Message}");
            }
        }

        private void LoadPlaygroundModels()
        {
            PlaygroundModels.Clear();
            if (_playground.Models != null)
            {
                foreach (var model in _playground.Models.Values)
                {
                    PlaygroundModels.Add(model);
                }
            }
            Debug.WriteLine($"Loaded {PlaygroundModels.Count} models");
            OnPropertyChanged(nameof(PlaygroundModels));
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
        }
    }
}