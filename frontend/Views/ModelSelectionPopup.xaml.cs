using System.Collections.ObjectModel;
using Microsoft.Maui.Controls;
using System.Windows.Input;
using frontend.Models;
using frontend.Services;
using CommunityToolkit.Mvvm.Messaging;
using System.Diagnostics;
using System.Text.Json;
using frontend.Models.ViewModels;

namespace frontend.Views
{
    public partial class ModelSelectionPopup : ContentView
    {
        public ObservableCollection<Model> LibraryModels { get; set; }
        public PlaygroundViewModel PlaygroundViewModel { get; set; }
        public ICommand AddModelCommand { get; }
        private readonly LibraryService _libraryService;
        private readonly PlaygroundService _playgroundService;
        public required string PlaygroundId { get; set; }

        public ModelSelectionPopup()
        {
            InitializeComponent();
            LibraryModels = new ObservableCollection<Model>();

            AddModelCommand = new Command<Model>(OnAddModel);
            _libraryService = new LibraryService();
            _playgroundService = new PlaygroundService();
            BindingContext = this;
            LoadLibraryModels();
        }

        private async void LoadLibraryModels()
        {
            try
            {
                var modelList = await _libraryService.GetLibrary(); // Fetch models from the library
                LibraryModels.Clear();
                
                foreach (var model in modelList)
                {
                   
                    if (string.IsNullOrEmpty(model.PipelineTag))
                    {
                        model.PipelineTag = !string.IsNullOrEmpty(model.ModelClass) ? model.ModelClass : "Unknown";
                    }
                    LibraryModels.Add(model); // Add each model to the collection
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading library models: {ex.Message}");
            }
        }

        private async void OnAddModel(Model model)
        {
            try
            {
                var result = await _playgroundService.AddModelToPlayground(PlaygroundId, model.ModelId);
                System.Diagnostics.Debug.WriteLine($"AddModel result: {result}");
                
                foreach (var kvp in result)
                {
                    System.Diagnostics.Debug.WriteLine($"Key: {kvp.Key}, Value: {kvp.Value}");
                }

                // Fetch the model using the model ID
                var addedModel = await _libraryService.GetModelInfoLibrary(model.ModelId);
                
                // Add the model to the PlaygroundViewModel
                PlaygroundViewModel.Playground.Models.Add(model.ModelId, addedModel);

                // Since only the Playground has Observable Property
                // We have to manually update the Observable Collection
                PlaygroundViewModel.PlaygroundModels.Add(addedModel);

                // If we've reached this point, it means the operation was successful
                Debug.WriteLine($"Model {model.ModelId} added successfully. Sending refresh message.");

                await (Application.Current?.MainPage?.DisplayAlert("Success", $"Model {model.ModelId} has been added to the playground.", "OK") ?? Task.CompletedTask);
                ClosePopup();
            }
            catch (HttpRequestException ex)
            {
                Debug.WriteLine($"HTTP Request Exception in OnAddModel: {ex.Message}");
                await (Application.Current?.MainPage?.DisplayAlert("Error", $"Failed to add model: {ex.Message}", "OK") ?? Task.CompletedTask);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Exception in OnAddModel: {ex.Message}");
                await (Application.Current?.MainPage?.DisplayAlert("Error", $"Failed to add model: {ex.Message}", "OK") ?? Task.CompletedTask);
            }
        }

        private void OnBackgroundTapped(object sender, EventArgs e)
        {
            ClosePopup();
        }

        private void OnCloseClicked(object sender, EventArgs e)
        {
            ClosePopup();
        }

        public void ClosePopup()
        {
            IsVisible = false;
            (Parent as AbsoluteLayout)?.Children.Remove(this);
        }
    }

    public class RefreshPlaygroundModelsMessage
    {
        public string PlaygroundId { get; }
        public RefreshPlaygroundModelsMessage(string playgroundId) => PlaygroundId = playgroundId;
    }
}