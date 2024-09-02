using frontend.Models;
using frontend.ViewModels;

namespace frontend.Views;

public partial class LibraryAPIView : ContentView
{
    private LibraryAPIViewModel _libraryAPIViewModel;
    private Dictionary<string, Label> _buttonToLabelMap;

    public LibraryAPIView(Model model)
    {
        InitializeComponent();
        _libraryAPIViewModel = new LibraryAPIViewModel(model);
        BindingContext = _libraryAPIViewModel;
        
        _buttonToLabelMap = new Dictionary<string, Label>
        {
            { "LoadModelRequestCopyButton", LoadModelRequestCopiedLabel },
            { "LoadModelResponseCopyButton", LoadModelResponseCopiedLabel },
            { "UnloadModelRequestCopyButton", UnloadModelRequestCopiedLabel },
            { "UnloadModelResponseCopyButton", UnloadModelResponseCopiedLabel },
            { "InferenceRequestCopyButton", InferenceRequestCopiedLabel },
            { "InferenceRequestBodyCopyButton", InferenceRequestBodyCopiedLabel },
            { "InferenceResponseCopyButton", InferenceResponseCopiedLabel }
        };
    }

    private async void OnCopyClicked(object sender, EventArgs e)
    {
        if (sender is Button button && button.CommandParameter is string textToCopy)
        {
            bool success = await CopyToClipboard(textToCopy);
            
            if (success)
            {
                if (_buttonToLabelMap.TryGetValue(button.StyleId, out Label label))
                {
                    label.IsVisible = true;
                    await Task.Delay(2000);
                    label.IsVisible = false;
                }
            }
            else
            {
                await ShowCopyFailedAlert();
            }
        }
    }

    private async Task<bool> CopyToClipboard(string text)
    {
        try
        {
            await Clipboard.SetTextAsync(text);
            return true;
        }
        catch (Exception)
        {
            return false;
        }
    }

    private async Task ShowCopyFailedAlert()
    {
        await Application.Current.MainPage.DisplayAlert("Copy Failed", "Unable to copy text to clipboard.", "OK");
    }
}
