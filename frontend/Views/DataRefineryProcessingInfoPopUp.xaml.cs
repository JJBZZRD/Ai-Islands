using System;
using System.Collections.Generic;
using CommunityToolkit.Maui.Views;
using System.Text.Json;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace frontend.Views
{
    public partial class DataRefineryProcessingInfoPopUp : Popup, INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler PropertyChanged;

        public string Title { get; set; }
        public string ModelType { get; set; }
        public string ModelName { get; set; }
        public int EmbeddingDimensions { get; set; }
        public int MaxInputTokens { get; set; }
        private bool _hasChunkingSettings;
        public bool HasChunkingSettings
        {
            get => _hasChunkingSettings;
            set
            {
                if (_hasChunkingSettings != value)
                {
                    _hasChunkingSettings = value;
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
                    OnPropertyChanged(nameof(IsCsvRowMethod));
                    OnPropertyChanged(nameof(IsNotCsvRowMethod));
                }
            }
        }
        public bool IsCsvRowMethod => ChunkMethod == "csv_row";
        public bool IsNotCsvRowMethod => !IsCsvRowMethod;
        public int RowsPerChunk { get; set; }
        public string CsvColumns { get; set; }
        public int ChunkSize { get; set; }
        public int ChunkOverlap { get; set; }

        public DataRefineryProcessingInfoPopUp(Dictionary<string, object> processingInfo, string title)
        {
            InitializeComponent();
            Title = title;

            if (processingInfo.TryGetValue("model_type", out var modelType))
                ModelType = modelType.ToString();

            if (processingInfo.TryGetValue("model_name", out var modelName))
                ModelName = modelName.ToString();

            if (processingInfo.TryGetValue("embedding_dimensions", out var embeddingDimensions))
            {
                if (embeddingDimensions is JsonElement jsonElement)
                {
                    EmbeddingDimensions = jsonElement.GetInt32();
                }
                else if (int.TryParse(embeddingDimensions.ToString(), out int result))
                {
                    EmbeddingDimensions = result;
                }
            }

            if (processingInfo.TryGetValue("max_input_tokens", out var maxInputTokens))
            {
                if (maxInputTokens is JsonElement jsonElement)
                {
                    MaxInputTokens = jsonElement.GetInt32();
                }
                else if (int.TryParse(maxInputTokens.ToString(), out int result))
                {
                    MaxInputTokens = result;
                }
            }

            if (processingInfo.TryGetValue("chunking_settings", out var chunkingSettingsObj) && chunkingSettingsObj is JsonElement chunkingSettingsElement)
            {
                if (chunkingSettingsElement.ValueKind == JsonValueKind.Object)
                {
                    HasChunkingSettings = true;
                    var settings = chunkingSettingsElement.EnumerateObject();

                    foreach (var setting in settings)
                    {
                        switch (setting.Name)
                        {
                            case "chunk_method":
                                ChunkMethod = setting.Value.GetString();
                                break;
                            case "rows_per_chunk":
                                RowsPerChunk = setting.Value.GetInt32();
                                break;
                            case "chunk_size":
                                ChunkSize = setting.Value.GetInt32();
                                break;
                            case "chunk_overlap":
                                ChunkOverlap = setting.Value.GetInt32();
                                break;
                            case "csv_columns":
                                CsvColumns = string.Join(", ", setting.Value.EnumerateArray().Select(v => v.GetString()));
                                break;
                        }
                    }

                    System.Diagnostics.Debug.WriteLine($"Chunking settings: ChunkMethod={ChunkMethod}, RowsPerChunk={RowsPerChunk}, ChunkSize={ChunkSize}, ChunkOverlap={ChunkOverlap}, CsvColumns={CsvColumns}");
                }
                else
                {
                    HasChunkingSettings = false;
                    System.Diagnostics.Debug.WriteLine("Chunking settings is not an object");
                }
            }
            else
            {
                HasChunkingSettings = false;
                System.Diagnostics.Debug.WriteLine("No chunking settings found");
            }

            OnPropertyChanged(nameof(HasChunkingSettings));

            BindingContext = this;
        }

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        private void OnCloseButtonClicked(object sender, EventArgs e)
        {
            Close();
        }
    }
}