using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using frontend.Models;

namespace frontend.Services
{
    public class ModelService
    {
        private readonly HttpClient _httpClient;
        private const string BaseUrl = "http://127.0.0.1:8000"; // Updated base URL

        public ModelService()
        {
            _httpClient = new HttpClient();
            _httpClient.BaseAddress = new Uri(BaseUrl);
            _httpClient.DefaultRequestHeaders.Accept.Add(new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));
        }
        
        public async Task<List<string>> ListActiveModels()
        {
            var response = await _httpClient.GetAsync("model/active");
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<string>>>();
            return result?["active_models"] ?? new List<string>();
        }

        public async Task<bool> LoadModel(string modelId)
        {
            var response = await _httpClient.PostAsync($"model/load?model_id={modelId}", null);
            return response.IsSuccessStatusCode;
        }

        public async Task<bool> UnloadModel(string modelId)
        {
            var response = await _httpClient.PostAsync($"model/unload?model_id={modelId}", null);
            return response.IsSuccessStatusCode;
        }

        public async Task<bool> DownloadModel(string modelId, string? authToken = null)
        {
            var url = $"model/download-model?model_id={modelId}";
            if (!string.IsNullOrEmpty(authToken))
            {
                url += $"&auth_token={authToken}";
            }
            var response = await _httpClient.PostAsync(url, null);
            return response.IsSuccessStatusCode;
        }

        public async Task<bool> IsModelLoaded(string modelId)
        {
            var response = await _httpClient.GetAsync($"model/is-model-loaded?model_id={modelId}");
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, string>>();
            return result?["message"]?.Contains("is loaded") ?? false;
        }

        public async Task<object> Inference(string modelId, object data)
        {
            var request = new { model_id = modelId, data = data };
            var response = await _httpClient.PostAsJsonAsync("model/inference", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<object>())!;
        }

        public async Task<object> TrainModel(string modelId, object data)
        {
            var request = new { model_id = modelId, data = data };
            var response = await _httpClient.PostAsJsonAsync("model/train", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<object>())!;
        }

        public async Task<object> ConfigureModel(string modelId, object payload)
        {
            var request = new { model_id = modelId, data = payload };
            var response = await _httpClient.PostAsJsonAsync("model/configure", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<object>())!;
        }

        // public async Task<Dictionary<string, Model>> GetModelDetails(List<string> modelIds)
        // {
        //     var response = await _httpClient.PostAsJsonAsync("model/details", modelIds);
        //     response.EnsureSuccessStatusCode();
        //     return await response.Content.ReadFromJsonAsync<Dictionary<string, Model>>() ?? new Dictionary<string, Model>();
        // }

        // Note: File upload methods (upload_image, upload_video, upload_dataset) are not included
        // as they require special handling in C# for file uploads.

        public async Task<bool> DeleteModel(string modelId)
        {
            var response = await _httpClient.DeleteAsync($"model/delete-model?model_id={modelId}");
            return response.IsSuccessStatusCode;
        }
    }
}