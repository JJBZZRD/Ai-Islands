using frontend.Models.ViewModels;

namespace frontend.Views;

public partial class PlaygroundAPIView : ContentView
{
    private PlaygroundAPIViewModel _playgroundAPIViewModel;
    private Dictionary<string, Label> _buttonToLabelMap;

    public PlaygroundAPIView(PlaygroundViewModel playgroundViewModel)
    {
        InitializeComponent();
        _playgroundAPIViewModel = new PlaygroundAPIViewModel(playgroundViewModel);
        BindingContext = _playgroundAPIViewModel;
        // reference to labels
        _buttonToLabelMap = new Dictionary<string, Label>
        {
            { "ListRequestCopyButton", ListRequestCopiedLabel },
            { "ListResponseCopyButton", ListResponseCopiedLabel },
            { "InfoRequestCopyButton", InfoRequestCopiedLabel },
            { "InfoResponseCopyButton", InfoResponseCopiedLabel },
            { "LoadChainRequestCopyButton", LoadChainRequestCopiedLabel },
            { "LoadChainResponseCopyButton", LoadChainResponseCopiedLabel },
            { "StopChainRequestCopyButton", StopChainRequestCopiedLabel },
            { "InferenceRequestCopyButton", InferenceRequestCopiedLabel },
            { "InferenceResponseCopyButton", InferenceResponseCopiedLabel }
        };
    }

    private async void OnCopyClicked(object sender, EventArgs e)
    {
        if (sender is Button button && button.CommandParameter is string textToCopy && button.StyleId is string buttonName)
        {
            bool success = await CopyToClipboard(textToCopy);
            
            if (success)
            {
                if (_buttonToLabelMap.TryGetValue(buttonName, out Label label))
                {
                    //show the label "Copied"
                    label.IsVisible = true;
                    // wait 2 seconds
                    await Task.Delay(2000);
                    // hide the label
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