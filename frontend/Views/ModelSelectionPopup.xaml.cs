using System.Collections.ObjectModel;
using Microsoft.Maui.Controls;
using System.Windows.Input;
using frontend.Models;
using frontend.Services;
using CommunityToolkit.Mvvm.Messaging;

namespace frontend.Views
{
    public partial class ModelSelectionPopup : ContentView
    {
        public ObservableCollection<Model> LibraryModels { get; set; }
        public ICommand AddModelCommand { get; }
        private readonly LibraryService _libraryService;
        public required string PlaygroundId { get; set; }
        private readonly PlaygroundModelView _playgroundModelView;

        public ModelSelectionPopup(PlaygroundModelView playgroundModelView)
        {
            InitializeComponent();
            _playgroundModelView = playgroundModelView;
            LibraryModels = new ObservableCollection<Model>();
            AddModelCommand = new Command<Model>(OnAddModel);
            _libraryService = new LibraryService();
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
                var playgroundService = new PlaygroundService();
                var result = await playgroundService.AddModelToPlayground(PlaygroundId, model.ModelId);
                
                // Notify the parent view (the playground model view) that a model has been added
                WeakReferenceMessenger.Default.Send(new ModelAddedMessage(model));
                
                // Directly add the model to the PlaygroundModels collection
                _playgroundModelView.PlaygroundModels.Add(model);
                
                await (Application.Current?.MainPage?.DisplayAlert("Success", $"Model {model.ModelId} has been added to the playground.", "OK") ?? Task.CompletedTask);
                
                
                ClosePopup();
            }
            catch (Exception ex)
            {
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

    public class ModelAddedMessage
    {
        public Model AddedModel { get; }
        public ModelAddedMessage(Model model) => AddedModel = model;
    }
}