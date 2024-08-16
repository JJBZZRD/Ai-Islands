using System.Globalization;
using frontend.Models;
using frontend.Models.ViewModels;
using System.Collections.ObjectModel;
using frontend.Services;
using System.Net.Http;
using System.Text.Json;

namespace frontend.Views;


public partial class PlaygroundConfigView : ContentView
{
    private PlaygroundViewModel _viewModel;
    private PlaygroundService _playgroundService;

    internal PlaygroundConfigView(PlaygroundViewModel viewModel, PlaygroundService playgroundService)
    {
        InitializeComponent();
        _viewModel = viewModel;
        _playgroundService = playgroundService;
        BindingContext = _viewModel;

        System.Diagnostics.Debug.WriteLine($"Current chain: {string.Join(", ", _viewModel.PlaygroundChain.Select(m => m.ModelId))}");
    }

    private void OnAddModelClicked(object sender, EventArgs e)
    {
        // Add a new model to the chain (for demonstration purposes, adding a dummy model)
        var newModel = new Model { ModelId = "new_model" };
        _viewModel.PlaygroundChain.Add(newModel);
    }

    private void OnDeleteModelClicked(object sender, EventArgs e)
    {
        var button = sender as ImageButton;
        var model = button?.CommandParameter as Model;

        if (model != null)
        {
            _viewModel.PlaygroundChain.Remove(model);
        }
    }

    private async void OnSaveConfigClicked(object sender, EventArgs e)
    {
        try
        {
            List<string> chainModelIds = _viewModel.PlaygroundChain.Select(m => m.ModelId).ToList();
            var response = await _playgroundService.ConfigureChain(_viewModel.Playground.PlaygroundId, chainModelIds);

            if (response.IsSuccessStatusCode)
            {
                await Application.Current.MainPage.DisplayAlert("Success", "Configuration saved successfully", "OK");
            }
            else
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                var errorJson = JsonSerializer.Deserialize<JsonElement>(errorContent);
                var errorMessage = errorJson.GetProperty("error").GetProperty("message").GetString();
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save configuration: {errorMessage}", "OK");
            }
        }
        catch (Exception ex)
        {
            await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save configuration: {ex.Message}", "OK");
        }
    }
}