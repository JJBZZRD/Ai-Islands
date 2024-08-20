using frontend.Models.ViewModels;


namespace frontend.Views;

public partial class PlaygroundAPIView : ContentView
{
    private PlaygroundViewModel _playgroundViewModel;
    public string ListRequest { get; private set; }
    public string ListResponse { get; private set; }
    public string InfoRequest { get; private set; }
    public string InfoResponse { get; private set; }
    private Dictionary<string, Label> _copiedLabels;

    public PlaygroundAPIView(PlaygroundViewModel playgroundViewModel)
    {
        InitializeComponent();
        _playgroundViewModel = playgroundViewModel;
        
        InitializeApiExamples();
        
        BindingContext = this;

        _copiedLabels = new Dictionary<string, Label>
        {
            { "ListRequest", ListRequestCopiedLabel },
            { "ListResponse", ListResponseCopiedLabel },
            { "InfoRequest", InfoRequestCopiedLabel },
            { "InfoResponse", InfoResponseCopiedLabel }
        };
    }

    private void InitializeApiExamples()
    {
        ListRequest = "http://127.0.0.1:8000/playground/list";
        ListResponse = GetListResponseExample();
        InfoRequest = $"http://127.0.0.1:8000/playground/info?playground_id={_playgroundViewModel.Playground.PlaygroundId}";
        InfoResponse = GetInfoResponseExample();
    }

    private string GetListResponseExample()
    {
        return @"{
  ""data"": {
    ""playground1"": {
      ""description"": ""Example playground 1"",
      ""models"": {...},
      ""chain"": [...]
    },
    ""playground2"": {
      ""description"": ""Example playground 2"",
      ""models"": {...},
      ""chain"": [...]
    }
  }
}";
    }

    private string GetInfoResponseExample()
    {
        return $@"{{
    ""message"": ""Success"",
    ""data"": {{
        ""description"": ""I am description"",
        ""models"": {{
            ""cross-encoder/nli-roberta-base"": {{
                ""input"": ""text"",
                ""output"": ""text"",
                ""pipeline_tag"": ""zero-shot-classification"",
                ""is_online"": false
            }},
            ""suno/bark-small"": {{
                ""input"": ""text"",
                ""output"": ""audio"",
                ""pipeline_tag"": ""text-to-speech"",
                ""is_online"": false
            }}
        }},
        ""chain"": [],
        ""active_chain"": false
    }}
}}";
    }

    private async void OnCopyClicked(object sender, EventArgs e)
    {
        if (sender is Button button && button.CommandParameter is string textToCopy)
        {
            bool success = await CopyToClipboard(textToCopy);
            
            if (success)
            {
                string labelKey = DetermineLabelKey(textToCopy);
                MainThread.BeginInvokeOnMainThread(() => ShowCopiedLabel(labelKey));
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

    private string DetermineLabelKey(string textToCopy)
    {
        if (textToCopy == ListRequest) return "ListRequest";
        if (textToCopy == ListResponse) return "ListResponse";
        if (textToCopy == InfoRequest) return "InfoRequest";
        if (textToCopy == InfoResponse) return "InfoResponse";
        return string.Empty;
    }

    private void ShowCopiedLabel(string labelKey)
    {
        if (_copiedLabels.TryGetValue(labelKey, out Label label))
        {
            label.IsVisible = true;

            // Create a timer to hide the label after 2 seconds
            var timer = new System.Timers.Timer(2000);
            timer.Elapsed += (sender, e) => HideCopiedLabel(label, timer);
            timer.Start();
        }
    }

    private void HideCopiedLabel(Label label, System.Timers.Timer timer)
    {
        MainThread.BeginInvokeOnMainThread(() =>
        {
            label.IsVisible = false;
        });
        timer.Stop();
        timer.Dispose();
    }
}