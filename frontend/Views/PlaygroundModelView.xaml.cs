using System.Collections.ObjectModel;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using System.Diagnostics;
using frontend.Models; 
using frontend.Services;
using System.Text.Json;
using frontend.Models.ViewModels;
using Microsoft.Maui.Layouts;
using CommunityToolkit.Mvvm.Messaging;
using System.Windows.Input;

namespace frontend.Views
{
    public partial class PlaygroundModelView : ContentView
    {
        private string _name;
        private PlaygroundViewModel _playgroundViewModel;
        private readonly PlaygroundService _playgroundService;

        internal PlaygroundModelView(PlaygroundViewModel playgroundViewModel, PlaygroundService playgroundService)
        {
            InitializeComponent();
            _playgroundService = playgroundService;
            _playgroundViewModel = playgroundViewModel;
            _name = _playgroundViewModel.Playground.PlaygroundId;

            Debug.WriteLine($"PlaygroundModelView constructor called for {_name}");

            BindingContext = _playgroundViewModel;
        }

        private void OnAddModelClicked(object sender, EventArgs e)
        {
            var modelSelectionPopup = new ModelSelectionPopup
            {
                PlaygroundId = _name ?? string.Empty,
                PlaygroundViewModel = _playgroundViewModel
            };
            AbsoluteLayout.SetLayoutFlags(modelSelectionPopup, AbsoluteLayoutFlags.All);
            AbsoluteLayout.SetLayoutBounds(modelSelectionPopup, new Rect(0, 0, 1, 1));
            MainLayout.Children.Add(modelSelectionPopup); 
            modelSelectionPopup.IsVisible = true;
        }

        private async void OnDeleteModelClicked(object sender, EventArgs e)
        {
            var button = sender as ImageButton;
            var model = button?.BindingContext as Model;

            if (model != null)
            {
                bool confirm = await Application.Current.MainPage.DisplayAlert(
                    "Confirm Deletion", 
                    $"Are you sure you want to remove {model.ModelId} from this playground?", 
                    "Yes", "No");

                if (confirm)
                {
                    try
                    {
                        var result = await _playgroundService.RemoveModelFromPlayground(_playgroundViewModel.Playground.PlaygroundId, model.ModelId);
                        System.Diagnostics.Debug.WriteLine($"RemoveModel result: {JsonSerializer.Serialize(result)}");

                        if (result.ContainsKey("message") && result["message"].ToString() == "Success")
                        {
                            // Remove the model from the PlaygroundViewModel
                            _playgroundViewModel.PlaygroundModels.Remove(model);

                            await Application.Current.MainPage.DisplayAlert("Success", $"{model.ModelId} has been removed from the playground.", "OK");
                        }
                        else
                        {
                            string errorMessage = result.ContainsKey("error") ? result["error"].ToString() : "Unknown error occurred";
                            await Application.Current.MainPage.DisplayAlert("Error", $"Failed to remove model: {errorMessage}", "OK");
                        }
                    }
                    catch (HttpRequestException ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"HTTP Request Exception in OnDeleteModel: {ex.Message}");
                        await Application.Current.MainPage.DisplayAlert("Error", $"Failed to remove model: {ex.Message}", "OK");
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"Exception in OnDeleteModel: {ex.Message}");
                        await Application.Current.MainPage.DisplayAlert("Error", $"Failed to remove model: {ex.Message}", "OK");
                    }
                }
            }
        }
    }
}