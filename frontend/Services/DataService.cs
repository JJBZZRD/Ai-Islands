using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.IO;

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
        }

        public async Task<Dictionary<string, object>> UploadDataset(string filePath)
        {
            var request = new { file_path = filePath };
            var response = await _httpClient.PostAsJsonAsync("data/upload-dataset", request);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }

        public async Task<List<string>> ListDatasets()
        {
            var response = await _httpClient.GetAsync("data/list-datasets");
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<string>>>();
            return result["datasets"];
        }

        public async Task<Dictionary<string, List<string>>> GetAvailableModels()
        {
            var response = await _httpClient.GetAsync("data/available-models");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, List<string>>>();
        }

        public async Task<Dictionary<string, object>> ProcessDataset(string filePath, string modelName)
        {
            var request = new { file_path = filePath, model_name = modelName };
            var response = await _httpClient.PostAsJsonAsync("data/process-dataset", request);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }

        public async Task<string> GetDatasetPreview(string datasetName)
        {
            var response = await _httpClient.GetAsync($"data/preview-dataset?dataset_name={datasetName}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsStringAsync();
        }

        public async Task<Dictionary<string, bool>> GetDatasetProcessingStatus(string datasetName)
        {
            var response = await _httpClient.GetAsync($"data/dataset-processing-status?dataset_name={datasetName}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, bool>>();
        }

        public async Task<Dictionary<string, object>> DeleteDataset(string datasetName)
        {
            var response = await _httpClient.DeleteAsync($"data/delete-dataset?dataset_name={datasetName}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }

        public async Task<Dictionary<string, object>> GetDatasetProcessingInfo(string datasetName, string processingType)
        {
            var response = await _httpClient.GetAsync($"data/dataset-processing-info?dataset_name={datasetName}&processing_type={processingType}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        }
    }
}