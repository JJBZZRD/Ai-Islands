using System.ComponentModel;
using System.Windows.Input;

namespace frontend.Views;

public partial class Setting : ContentPage, INotifyPropertyChanged
{
    private string _apiKey;
    public string ApiKey
    {
        get => _apiKey;
        set
        {
            if (_apiKey != value)
            {
                _apiKey = value;
                OnPropertyChanged();
            }
        }
    }

    private string _location;
    public string Location
    {
        get => _location;
        set
        {
            if (_location != value)
            {
                _location = value;
                OnPropertyChanged();
            }
        }
    }

    private string _projectId;
    public string ProjectId
    {
        get => _projectId;
        set
        {
            if (_projectId != value)
            {
                _projectId = value;
                OnPropertyChanged();
            }
        }
    }

    private bool _useChunking;
    public bool UseChunking
    {
        get => _useChunking;
        set
        {
            if (_useChunking != value)
            {
                _useChunking = value;
                OnPropertyChanged();
            }
        }
    }

    private string _chunkSize;
    public string ChunkSize
    {
        get => _chunkSize;
        set
        {
            if (_chunkSize != value)
            {
                _chunkSize = value;
                OnPropertyChanged();
            }
        }
    }

    private string _chunkOverlap;
    public string ChunkOverlap
    {
        get => _chunkOverlap;
        set
        {
            if (_chunkOverlap != value)
            {
                _chunkOverlap = value;
                OnPropertyChanged();
            }
        }
    }

    private string _chunkMethod;
    public string ChunkMethod
    {
        get => _chunkMethod;
        set
        {
            if (_chunkMethod != value)
            {
                _chunkMethod = value;
                OnPropertyChanged();
            }
        }
    }

    private string _rowsPerChunk;
    public string RowsPerChunk
    {
        get => _rowsPerChunk;
        set
        {
            if (_rowsPerChunk != value)
            {
                _rowsPerChunk = value;
                OnPropertyChanged();
            }
        }
    }

    private string _csvColumns;
    public string CsvColumns
    {
        get => _csvColumns;
        set
        {
            if (_csvColumns != value)
            {
                _csvColumns = value;
                OnPropertyChanged();
            }
        }
    }

    private string _device;
    public string Device
    {
        get => _device;
        set
        {
            if (_device != value)
            {
                _device = value;
                OnPropertyChanged();
            }
        }
    }

    public Setting()
    {
        InitializeComponent();
        BindingContext = this;
        LoadSettings();
    }

    private void LoadSettings()
    {
        ApiKey = Preferences.Get("ApiKey", "");
        Location = Preferences.Get("Location", "eu-gb");
        ProjectId = Preferences.Get("ProjectId", "");
        UseChunking = Preferences.Get("UseChunking", true);
        ChunkSize = Preferences.Get("ChunkSize", "1000");
        ChunkOverlap = Preferences.Get("ChunkOverlap", "0");
        ChunkMethod = Preferences.Get("ChunkMethod", "fixed_length");
        RowsPerChunk = Preferences.Get("RowsPerChunk", "1");
        CsvColumns = Preferences.Get("CsvColumns", "");
        Device = Preferences.Get("Device", "cpu");
    }

    private void SaveSettings()
    {
        Preferences.Set("ApiKey", ApiKey);
        Preferences.Set("Location", Location);
        Preferences.Set("ProjectId", ProjectId);
        Preferences.Set("UseChunking", UseChunking);
        Preferences.Set("ChunkSize", ChunkSize);
        Preferences.Set("ChunkOverlap", ChunkOverlap);
        Preferences.Set("ChunkMethod", ChunkMethod);
        Preferences.Set("RowsPerChunk", RowsPerChunk);
        Preferences.Set("CsvColumns", CsvColumns);
        Preferences.Set("Device", Device);
    }

    private async void OnSaveClicked(object sender, EventArgs e)
    {
        bool answer = await DisplayAlert("Save Settings", "Are you sure you want to save these settings?", "Yes", "No");
        if (answer)
        {
            SaveSettings();
            await DisplayAlert("Success", "Settings saved successfully", "OK");
        }
    }

    private async void OnResetClicked(object sender, EventArgs e)
    {
        bool answer = await DisplayAlert("Reset Settings", "Are you sure you want to reset all settings to default values?", "Yes", "No");
        if (answer)
        {
            ApiKey = "";
            Location = "eu-gb";
            ProjectId = "";
            UseChunking = true;
            ChunkSize = "1000";
            ChunkOverlap = "0";
            ChunkMethod = "fixed_length";
            RowsPerChunk = "1";
            CsvColumns = "";
            Device = "cpu";

            SaveSettings();
            await DisplayAlert("Success", "Settings reset to default values", "OK");
        }
    }

    private void OnCopyApiKeyClicked(object sender, EventArgs e)
    {
        if (!string.IsNullOrEmpty(ApiKey))
        {
            Clipboard.SetTextAsync(ApiKey);
        }
    }

    private void OnCopyProjectIdClicked(object sender, EventArgs e)
    {
        if (!string.IsNullOrEmpty(ProjectId))
        {
            Clipboard.SetTextAsync(ProjectId);
        }
    }

    public ICommand ShowTooltipCommand => new Command<string>(async (param) =>
    {
        string message = param switch
        {
            "APIKeyInfo" => "Your Watson Cloud API Key is used to authenticate your requests.",
            "ChunkSizeInfo" => "Chunk size determines how many tokens are in each text chunk.",
            _ => "No information available."
        };
        await DisplayAlert("Info", message, "OK");
    });
}