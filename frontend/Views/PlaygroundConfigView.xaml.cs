using frontend.Models;
using frontend.Models.ViewModels;
using frontend.Services;
using System.Net.Http;
using System.Text.Json;
using System.Diagnostics;

namespace frontend.Views;


public partial class PlaygroundConfigView : ContentView
{
    private PlaygroundViewModel _viewModel;
    private PlaygroundService _playgroundService;

    public PlaygroundConfigView(PlaygroundViewModel viewModel, PlaygroundService playgroundService)
    {
        InitializeComponent();
        _viewModel = viewModel;
        _playgroundService = playgroundService;
        BindingContext = _viewModel;

        InitializeAsync();
    }

    private async void InitializeAsync()
    {
        // dealy 500ms to make sure the picker is loaded
        // the delay time might have to be longer, depending on the time taken to load the picker
        await Task.Delay(500);
        _viewModel.SetPlaygroundChainForPicker();

        Debug.WriteLine($"Current chain: {string.Join(", ", _viewModel.PlaygroundChain.Select(m => m.SelectedModel?.ModelId))}");
    }

    private void OnAddModelClicked(object sender, EventArgs e)
    {
        var newModel = new Model { ModelId = "new_model" };
        _viewModel.PlaygroundChain.Add(new ModelViewModel { SelectedModel = newModel });

    }

    private void OnDeleteModelClicked(object sender, EventArgs e)
    {
        var button = sender as ImageButton;
        var model = button?.CommandParameter as ModelViewModel;

        if (model != null)
        {
            _viewModel.PlaygroundChain.Remove(model);
        }
    }

    private async void OnSaveConfigClicked(object sender, EventArgs e)
    {
        try
        {
            List<string> chainModelIds = _viewModel.PlaygroundChain
                .Select(m => m.SelectedModel?.ModelId ?? string.Empty)
                .Where(id => !string.IsNullOrEmpty(id))
                .ToList();
            var response = await _playgroundService.ConfigureChain(_viewModel.Playground.PlaygroundId, chainModelIds);

            if (response.IsSuccessStatusCode)
            {
                await Application.Current.MainPage.DisplayAlert("Success", "Configuration saved successfully", "OK");
                _viewModel.Playground.Chain = chainModelIds;
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