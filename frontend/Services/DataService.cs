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

        public async Task<string> GetDatasetPreview(string filePath)
        {
            if (!File.Exists(filePath))
            {
                return "File not found.";
            }

            using (var reader = new StreamReader(filePath))
            {
                var preview = await reader.ReadToEndAsync();
                return preview.Length > 1000 ? preview.Substring(0, 1000) + "..." : preview;
            }
        }
    }
}