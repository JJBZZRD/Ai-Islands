using Microsoft.Maui.Controls;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using frontend.Services;
using System.Text.Json;

namespace frontend.Views
{
    public partial class DataRefinery : ContentPage, INotifyPropertyChanged
    {
        private readonly DataService _dataService;
        private Dictionary<string, List<string>> _availableModels;

        private bool _defaultProcessed;
        public bool DefaultProcessed
        {
            get => _defaultProcessed;
            set => SetProperty(ref _defaultProcessed, value);
        }

        public bool IsNotDefaultProcessed => !DefaultProcessed;

        private bool _chunkedProcessed;
        public bool ChunkedProcessed
        {
            get => _chunkedProcessed;
            set => SetProperty(ref _chunkedProcessed, value);
        }

        public bool IsNotChunkedProcessed => !ChunkedProcessed;

        public DataRefinery()
        {
            InitializeComponent();
            _dataService = new DataService();
            BindingContext = this;
            InitializeAsync();
        }

        private async Task InitializeAsync()
        {
            await LoadDatasets();
            await LoadAvailableModels();
        }

        private async Task LoadDatasets()
        {
            var datasets = await _dataService.ListDatasets();
            DatasetPicker.ItemsSource = datasets;
        }

        private async Task LoadAvailableModels()
        {
            _availableModels = await _dataService.GetAvailableModels();
            EmbeddingTypePicker.ItemsSource = new List<string> { "Sentence Transformer", "Watson Embedder" };
        }

        private async void OnFindDatasetClicked(object sender, EventArgs e)
        {
            try
            {
                var result = await FilePicker.PickAsync();
                if (result != null)
                {
                    FilePathEntry.Text = result.FullPath;
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Unable to pick file: {ex.Message}", "OK");
            }
        }

        private async void OnUploadToAIIslandsClicked(object sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(FilePathEntry.Text))
            {
                await DisplayAlert("Error", "Please select a file first.", "OK");
                return;
            }

            try
            {
                var result = await _dataService.UploadDataset(FilePathEntry.Text);
                await DisplayAlert("Success", "Dataset uploaded successfully!", "OK");
                FilePathEntry.Text = string.Empty; // Clear the file path
                await LoadDatasets();
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to upload dataset: {ex.Message}", "OK");
            }
        }

        private async void OnDatasetPickerSelectedIndexChanged(object sender, EventArgs e)
        {
            if (DatasetPicker.SelectedItem is string selectedDataset)
            {
                var previewContent = await _dataService.GetDatasetPreview(selectedDataset);
                DatasetPreviewEditor.Text = FormatPreviewContent(previewContent);

                var processingStatus = await _dataService.GetDatasetProcessingStatus(selectedDataset);
                DefaultProcessed = processingStatus["default_processed"];
                ChunkedProcessed = processingStatus["chunked_processed"];
            }
        }

        private void OnEmbeddingTypePickerSelectedIndexChanged(object sender, EventArgs e)
        {
            if (EmbeddingTypePicker.SelectedItem is string selectedType)
            {
                ModelPicker.ItemsSource = null;
                ModelPicker.SelectedItem = null;

                string key = selectedType == "Sentence Transformer" ? "sentence_transformer" : "watson";
                if (_availableModels.ContainsKey(key))
                {
                    ModelPicker.ItemsSource = _availableModels[key];
                }
                else
                {
                    // Handle the case when the key doesn't exist (e.g., for Watson Embedder)
                    ModelPicker.ItemsSource = new List<string> { "Default Watson Model" };
                }
            }
        }

        private async void OnProcessClicked(object sender, EventArgs e)
        {
            if (DatasetPicker.SelectedItem is string selectedDataset &&
                ModelPicker.SelectedItem is string selectedModel)
            {
                string filePath = Path.Combine("Datasets", selectedDataset, $"{selectedDataset}.csv");
                try
                {
                    var result = await _dataService.ProcessDataset(filePath, selectedModel);
                    await DisplayAlert("Success", "Dataset processed successfully!", "OK");

                    // Update processing status
                    var processingStatus = await _dataService.GetDatasetProcessingStatus(selectedDataset);
                    DefaultProcessed = processingStatus["default_processed"];
                    ChunkedProcessed = processingStatus["chunked_processed"];
                }
                catch (Exception ex)
                {
                    await DisplayAlert("Error", $"Failed to process dataset: {ex.Message}", "OK");
                }
            }
            else
            {
                await DisplayAlert("Error", "Please select a dataset and a model.", "OK");
            }
        }

        private void OnModelPickerSelectedIndexChanged(object sender, EventArgs e)
        {
            ProcessButton.BackgroundColor = ModelPicker.SelectedItem != null ? Colors.Green : Colors.Red;
        }

        private void OnClearClicked(object sender, EventArgs e)
        {
            DatasetPicker.SelectedItem = null;
            EmbeddingTypePicker.SelectedItem = null;
            ModelPicker.SelectedItem = null;
            DefaultProcessed = false;
            ChunkedProcessed = false;
            DatasetPreviewEditor.Text = string.Empty;
            ProcessButton.BackgroundColor = Colors.Red;
        }

        private async void OnRemoveDatasetsClicked(object sender, EventArgs e)
        {
            var datasets = await _dataService.ListDatasets();
            var result = await DisplayActionSheet("Select dataset to delete", "Cancel", null, datasets.ToArray());

            if (result != null && result != "Cancel")
            {
                bool confirm = await DisplayAlert("Confirm Deletion", $"Are you sure you want to delete the dataset '{result}'?", "Yes", "No");
                if (confirm)
                {
                    try
                    {
                        await _dataService.DeleteDataset(result);
                        await DisplayAlert("Success", $"Dataset '{result}' deleted successfully", "OK");
                        await LoadDatasets(); // Refresh the dataset list
                    }
                    catch (Exception ex)
                    {
                        await DisplayAlert("Error", $"Failed to delete dataset: {ex.Message}", "OK");
                    }
                }
            }
        }

        private async void OnDefaultInfoClicked(object sender, EventArgs e)
        {
            if (DatasetPicker.SelectedItem is string selectedDataset)
            {
                var info = await _dataService.GetDatasetProcessingInfo(selectedDataset, "default");
                await DisplayAlert("Default Processing Info", FormatProcessingInfo(info), "OK");
            }
        }

        private async void OnChunkedInfoClicked(object sender, EventArgs e)
        {
            if (DatasetPicker.SelectedItem is string selectedDataset)
            {
                var info = await _dataService.GetDatasetProcessingInfo(selectedDataset, "chunked");
                await DisplayAlert("Chunked Processing Info", FormatProcessingInfo(info), "OK");
            }
        }

        private string FormatProcessingInfo(Dictionary<string, object> info)
        {
            var formattedInfo = new List<string>();
            foreach (var kvp in info)
            {
                if (kvp.Key == "chunking_settings" && kvp.Value is JsonElement jsonElement)
                {
                    formattedInfo.Add($"{kvp.Key}:");
                    foreach (var property in jsonElement.EnumerateObject())
                    {
                        formattedInfo.Add($"  {property.Name}: {property.Value}");
                    }
                }
                else if (kvp.Value is JsonElement element)
                {
                    formattedInfo.Add($"{kvp.Key}: {JsonSerializer.Serialize(element)}");
                }
                else
                {
                    formattedInfo.Add($"{kvp.Key}: {kvp.Value}");
                }
            }
            return string.Join("\n", formattedInfo);
        }

        private string FormatPreviewContent(string content)
        {
            try
            {
                var previewData = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(content);
                if (previewData != null && previewData.TryGetValue("content", out var contentObj))
                {
                    if (contentObj is System.Text.Json.JsonElement jsonElement && jsonElement.ValueKind == System.Text.Json.JsonValueKind.Array)
                    {
                        var formattedContent = jsonElement.EnumerateArray()
                            .Select(item => item.GetString())
                            .Where(item => item != null)
                            .Select(item => item.Replace(": ", ","));

                        return string.Join("\n", formattedContent);
                    }
                }
            }
            catch (System.Text.Json.JsonException)
            {
                // If it's not JSON, assume it's raw CSV content
                return content;
            }

            return "Error: Unable to format preview content";
        }

        protected virtual bool SetProperty<T>(ref T storage, T value, [CallerMemberName] string propertyName = null)
        {
            if (EqualityComparer<T>.Default.Equals(storage, value)) return false;
            storage = value;
            OnPropertyChanged(propertyName);
            OnPropertyChanged($"IsNot{propertyName}");
            return true;
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}