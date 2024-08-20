using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.IO;
using System.Net;

namespace frontend.Services
{
    public class DataService
    {
        private readonly HttpClient _httpClient;
        private const string BaseUrl = "http://127.0.0.1:8000";

        public DataService()
        {
            _httpClient = new HttpClient();
            _httpClient.BaseAddress = new Uri(BaseUrl);
            _httpClient.Timeout = TimeSpan.FromMinutes(2);
        }

        // API Call: POST /data/upload-dataset
        // Request Body: { "file_path": "path/to/file.csv" }
        public async Task<Dictionary<string, object>> UploadDataset(string filePath)
        {
            var request = new { file_path = filePath };
            var response = await _httpClient.PostAsJsonAsync("data/upload-dataset", request);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }

        // API Call: GET /data/list-datasets
        // Response: { "datasets": ["dataset1.csv", "dataset2.csv"] }
        public async Task<List<string>> ListDatasets()
        {
            var response = await _httpClient.GetAsync("data/list-datasets");
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<string>>>();
            return result["datasets"];
        }

        public async Task<List<string>> ListDatasetsNames()
        {
            var response = await _httpClient.GetAsync("data/list-datasets-names");
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<string>>>();
            return result["datasets"];
        }

        // API Call: GET /data/available-models
        // Response: { "sentence_transformer": ["model1", "model2"], "watson": ["model3", "model4"] }
        public async Task<Dictionary<string, List<string>>> GetAvailableModels()
        {
            var response = await _httpClient.GetAsync("data/available-models");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, List<string>>>();
        }

        // API Call: POST /data/process-dataset
        // Request Body: { "file_path": "Datasets/dataset_name/dataset_name.extension", "model_name": "model1" }
        public async Task<Dictionary<string, object>> ProcessDataset(string datasetFileName, string modelName)
        {
            var datasetName = Path.GetFileNameWithoutExtension(datasetFileName);
            var request = new { file_path = $"Datasets/{datasetName}/{datasetFileName}", model_name = modelName };
            var response = await _httpClient.PostAsJsonAsync("data/process-dataset", request);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }

        // API Call: GET /data/preview-dataset?dataset_name=dataset
        // Note: Sends dataset name without extension
        public async Task<string> GetDatasetPreview(string datasetFileName)
        {
            var datasetName = Path.GetFileNameWithoutExtension(datasetFileName);
            var response = await _httpClient.GetAsync($"data/preview-dataset?dataset_name={datasetName}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsStringAsync();
        }

        // API Call: GET /data/dataset-processing-status?dataset_name=dataset
        // Note: Sends dataset name without extension
        public async Task<Dictionary<string, bool>> GetDatasetProcessingStatus(string datasetFileName)
        {
            var datasetName = Path.GetFileNameWithoutExtension(datasetFileName);
            var response = await _httpClient.GetAsync($"data/dataset-processing-status?dataset_name={datasetName}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, bool>>();
        }

        // API Call: DELETE /data/delete-dataset?dataset_name=dataset
        // Note: Sends dataset name without extension
        public async Task<Dictionary<string, object>> DeleteDataset(string datasetFileName)
        {
            var datasetName = Path.GetFileNameWithoutExtension(datasetFileName);
            var response = await _httpClient.DeleteAsync($"data/delete-dataset?dataset_name={datasetName}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }

        // API Call: GET /data/dataset-processing-info?dataset_name=dataset&processing_type=default
        // Note: Sends dataset name without extension
        public async Task<Dictionary<string, object>> GetDatasetProcessingInfo(string datasetFileName, string processingType)
        {
            var datasetName = Path.GetFileNameWithoutExtension(datasetFileName);
            var response = await _httpClient.GetAsync($"data/dataset-processing-info?dataset_name={datasetName}&processing_type={processingType}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }

        // API Call: POST /data/upload-image-dataset
        // Request Body: { "file_path": "path/to/dataset.zip", "model_name": "model1" }
        public async Task<Dictionary<string, object>> UploadImageDataset(string filePath, string modelId)
        {
            var request = new { file_path = filePath, model_name = modelId };
            var response = await _httpClient.PostAsJsonAsync("data/upload-image-dataset", request);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }
    }

    // public class ProgressableStreamContent : HttpContent
    // {
    //     private readonly HttpContent _content;
    //     private readonly Action<long, long> _progress;

    //     public ProgressableStreamContent(HttpContent content, Action<long, long> progress)
    //     {
    //         _content = content;
    //         _progress = progress;
    //         foreach (var header in _content.Headers)
    //         {
    //             Headers.TryAddWithoutValidation(header.Key, header.Value);
    //         }
    //     }

    //     protected override async Task SerializeToStreamAsync(Stream stream, TransportContext context)
    //     {
    //         var buffer = new byte[8192];
    //         TryComputeLength(out var size);
    //         var uploaded = 0L;

    //         using (var contentStream = await _content.ReadAsStreamAsync())
    //         {
    //             while (true)
    //             {
    //                 var length = await contentStream.ReadAsync(buffer, 0, buffer.Length);
    //                 if (length <= 0) break;
    //                 uploaded += length;
    //                 _progress?.Invoke(uploaded, size);
    //                 await stream.WriteAsync(buffer, 0, length);
    //                 await stream.FlushAsync();
    //             }
    //         }
    //     }

    //     protected override bool TryComputeLength(out long length)
    //     {
    //         length = _content.Headers.ContentLength ?? -1;
    //         return length != -1;
    //     }
    // }
}