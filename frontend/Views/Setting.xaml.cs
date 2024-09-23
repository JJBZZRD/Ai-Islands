using System.ComponentModel;
using System.Windows.Input;
using frontend.Services;
using System.Collections.Generic;
using System.Text.Json;

namespace frontend.Views;

public partial class Setting : ContentPage, INotifyPropertyChanged
{
    private readonly SettingsService _settingsService;

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
                UpdateChunkingFieldsState();
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
                UpdateChunkingFieldsState();
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

    private bool _cudaAvailable;
    public bool CudaAvailable
    {
        get => _cudaAvailable;
        set
        {
            if (_cudaAvailable != value)
            {
                _cudaAvailable = value;
                OnPropertyChanged();
            }
        }
    }

    private string _cudaVersion;
    public string CudaVersion
    {
        get => _cudaVersion;
        set
        {
            if (_cudaVersion != value)
            {
                _cudaVersion = value;
                OnPropertyChanged();
            }
        }
    }

    private string _cudnnVersion;
    public string CudnnVersion
    {
        get => _cudnnVersion;
        set
        {
            if (_cudnnVersion != value)
            {
                _cudnnVersion = value;
                OnPropertyChanged();
            }
        }
    }

    private bool _isChunkSizeEnabled;
    public bool IsChunkSizeEnabled
    {
        get => _isChunkSizeEnabled;
        set
        {
            if (_isChunkSizeEnabled != value)
            {
                _isChunkSizeEnabled = value;
                OnPropertyChanged();
            }
        }
    }

    private bool _isChunkOverlapEnabled;
    public bool IsChunkOverlapEnabled
    {
        get => _isChunkOverlapEnabled;
        set
        {
            if (_isChunkOverlapEnabled != value)
            {
                _isChunkOverlapEnabled = value;
                OnPropertyChanged();
            }
        }
    }

    private bool _isRowsPerChunkEnabled;
    public bool IsRowsPerChunkEnabled
    {
        get => _isRowsPerChunkEnabled;
        set
        {
            if (_isRowsPerChunkEnabled != value)
            {
                _isRowsPerChunkEnabled = value;
                OnPropertyChanged();
            }
        }
    }

    private bool _isCsvColumnsEnabled;
    public bool IsCsvColumnsEnabled
    {
        get => _isCsvColumnsEnabled;
        set
        {
            if (_isCsvColumnsEnabled != value)
            {
                _isCsvColumnsEnabled = value;
                OnPropertyChanged();
            }
        }
    }

    public Setting()
    {
        InitializeComponent();
        _settingsService = new SettingsService();
        BindingContext = this;
        LoadSettings();
    }

    private void LoadSettings()
    {
        Task.Run(async () =>
        {
            await LoadSettingsAsync();
        });
    }

    private async Task LoadSettingsAsync()
    {
        try
        {
            var watsonSettings = await _settingsService.GetWatsonSettings();
            ApiKey = watsonSettings.TryGetValue("api_key", out var apiKey) ? apiKey?.ToString() : string.Empty;
            Location = watsonSettings.TryGetValue("location", out var location) ? location?.ToString() : string.Empty;
            ProjectId = watsonSettings.TryGetValue("project", out var project) ? project?.ToString() : string.Empty;

            var chunkingSettings = await _settingsService.GetChunkingSettings();
            UseChunking = chunkingSettings.TryGetValue("use_chunking", out var useChunking) && bool.TryParse(useChunking?.ToString(), out var uc) ? uc : false;
            ChunkSize = chunkingSettings.TryGetValue("chunk_size", out var chunkSize) ? chunkSize?.ToString() : string.Empty;
            ChunkOverlap = chunkingSettings.TryGetValue("chunk_overlap", out var chunkOverlap) ? chunkOverlap?.ToString() : string.Empty;
            ChunkMethod = chunkingSettings.TryGetValue("chunk_method", out var chunkMethod) ? chunkMethod?.ToString() : string.Empty;
            RowsPerChunk = chunkingSettings.TryGetValue("rows_per_chunk", out var rowsPerChunk) ? rowsPerChunk?.ToString() : string.Empty;
            
            if (chunkingSettings.TryGetValue("csv_columns", out var csvColumns) && csvColumns is JsonElement jsonElement && jsonElement.ValueKind == JsonValueKind.Array)
            {
                CsvColumns = string.Join(",", jsonElement.EnumerateArray().Select(e => e.ToString()));
            }
            else
            {
                CsvColumns = string.Empty;
            }

            var hardwareSettings = await _settingsService.GetHardware();
            Device = hardwareSettings.TryGetValue("hardware", out var hardware) ? hardware?.ToString() : string.Empty;

            var gpuInfo = await _settingsService.CheckGpu();
            CudaAvailable = gpuInfo.TryGetValue("CUDA available", out var cudaAvailable) && bool.TryParse(cudaAvailable?.ToString(), out var ca) ? ca : false;
            CudaVersion = gpuInfo.TryGetValue("CUDA version", out var cudaVersion) ? cudaVersion?.ToString() ?? "N/A" : "N/A";
            CudnnVersion = gpuInfo.TryGetValue("cuDNN version", out var cudnnVersion) ? cudnnVersion?.ToString() ?? "N/A" : "N/A";

            InitializeChunkingFields();
        }
        catch (Exception ex)
        {
            await Dispatcher.DispatchAsync(async () =>
            {
                await DisplayAlert("Error", $"Failed to load settings: {ex.Message}", "OK");
            });
        }
    }

    private void OnChunkMethodChanged(object sender, EventArgs e)
    {
        UpdateChunkingFieldsState();
    }

    private void UpdateChunkingFieldsState()
    {
        bool isCsvRow = ChunkMethod == "csv_row";
        IsChunkSizeEnabled = !isCsvRow && UseChunking;
        IsChunkOverlapEnabled = !isCsvRow && UseChunking;
        IsRowsPerChunkEnabled = isCsvRow && UseChunking;
        IsCsvColumnsEnabled = isCsvRow && UseChunking;
    }

    private void InitializeChunkingFields()
    {
        UpdateChunkingFieldsState();
    }

    private async void OnSaveWatsonCloudClicked(object sender, EventArgs e)
    {
        bool answer = await DisplayAlert("Save Watson Cloud Settings", "Are you sure you want to save these settings?", "Yes", "No");
        if (answer)
        {
            try
            {
                var settings = new Dictionary<string, string>
                {
                    ["api_key"] = ApiKey,
                    ["location"] = Location,
                    ["project_id"] = ProjectId
                };
                await _settingsService.UpdateWatsonSettings(settings);
                await DisplayAlert("Success", "Watson Cloud settings saved successfully", "OK");
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to save Watson Cloud settings: {ex.Message}", "OK");
            }
        }
    }

    private async void OnSaveChunkingClicked(object sender, EventArgs e)
    {
        bool answer = await DisplayAlert("Save Chunking Settings", "Are you sure you want to save these settings?", "Yes", "No");
        if (answer)
        {
            try
            {
                var settings = new Dictionary<string, object>
                {
                    ["use_chunking"] = UseChunking,
                    ["chunk_size"] = int.Parse(ChunkSize),
                    ["chunk_overlap"] = int.Parse(ChunkOverlap),
                    ["chunk_method"] = ChunkMethod,
                    ["rows_per_chunk"] = int.Parse(RowsPerChunk),
                    ["csv_columns"] = CsvColumns.Split(',', StringSplitOptions.RemoveEmptyEntries).ToList()
                };
                await _settingsService.UpdateChunkingSettings(settings);
                await DisplayAlert("Success", "Chunking settings saved successfully", "OK");
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to save Chunking settings: {ex.Message}", "OK");
            }
        }
    }

    private async void OnSaveHardwareClicked(object sender, EventArgs e)
    {
        bool answer = await DisplayAlert("Save Hardware Settings", "Are you sure you want to save these settings?", "Yes", "No");
        if (answer)
        {
            try
            {
                var result = await _settingsService.SetHardware(Device);
                if (result.ContainsKey("detail"))
                {
                    // This means there was an error, likely GPU not available
                    await DisplayAlert("Hardware Settings", result["detail"].ToString(), "OK");
                    // Optionally, reset the Device selection to CPU
                    Device = "cpu";
                }
                else
                {
                    await DisplayAlert("Success", "Hardware settings saved successfully", "OK");
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to save Hardware settings: {ex.Message}", "OK");
            }
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
            "APIKeyInfo" => "Your IBM Cloud API Key is used to authenticate your watsonx requests.",
            "ProjectIDInfo" => "Your Project ID is the environment used for watsonx Foundation Models and Embedders. If no project ID entered, AI Islands will fetch your first Watson Studio project from your account.",
            "ChunkSizeInfo" => "Chunk size determines how many tokens are in each text chunk.",
            "ChunkOverlapInfo" => "Chunk overlap specifies how many tokens should overlap between chunks.",
            "ChunkMethodInfo" => "Chunk method determines how the text is split into chunks.",
            "RowsPerChunkInfo" => "Rows per chunk specifies how many CSV rows should be in each chunk.",
            "CsvColumnsInfo" => "CSV columns to include in the chunking process, comma-separated.",
            "HardwareInfo" => "Choose between CPU and GPU for processing.",
            _ => "No information available."
        };
        await DisplayAlert("Info", message, "OK");
    });
}