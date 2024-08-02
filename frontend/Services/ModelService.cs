using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace frontend.Services
{
    public class ModelService
    {
        private readonly HttpClient _httpClient;
        private const string BaseUrl = "http://127.0.0.1:8000/model"; // Updated base URL

        public ModelService()
        {
            _httpClient = new HttpClient();
            _httpClient.BaseAddress = new Uri(BaseUrl);
        }

        public async Task<List<string>> ListActiveModels()
        {
            var response = await _httpClient.GetAsync("/active");
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<string>>>();
            return result?["active_models"] ?? new List<string>();
        }

        public async Task<bool> LoadModel(string modelId)
        {
            var response = await _httpClient.PostAsync($"/load?model_id={modelId}", null);
            return response.IsSuccessStatusCode;
        }

        public async Task<bool> UnloadModel(string modelId)
        {
            var response = await _httpClient.PostAsync($"/unload?model_id={modelId}", null);
            return response.IsSuccessStatusCode;
        }

        public async Task<bool> DownloadModel(string modelId, string? authToken = null)
        {
            var url = $"/download-model?model_id={modelId}";
            if (!string.IsNullOrEmpty(authToken))
            {
                url += $"&auth_token={authToken}";
            }
            var response = await _httpClient.PostAsync(url, null);
            return response.IsSuccessStatusCode;
        }

        public async Task<bool> IsModelLoaded(string modelId)
        {
            var response = await _httpClient.GetAsync($"/is-model-loaded?model_id={modelId}");
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, string>>();
            return result?["message"]?.Contains("is loaded") ?? false;
        }

        public async Task<object> Inference(string modelId, object data)
        {
            var request = new { model_id = modelId, data = data };
            var response = await _httpClient.PostAsJsonAsync("/inference", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<object>())!;
        }

        public async Task<object> TrainModel(string modelId, object data)
        {
            var request = new { model_id = modelId, data = data };
            var response = await _httpClient.PostAsJsonAsync("/train", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<object>())!;
        }

        public async Task<object> ConfigureModel(string modelId, object data)
        {
            var request = new { model_id = modelId, data = data };
            var response = await _httpClient.PostAsJsonAsync("/configure", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<object>())!;
        }

        // Note: File upload methods (upload_image, upload_video, upload_dataset) are not included
        // as they require special handling in C# for file uploads.

        public async Task<bool> DeleteModel(string modelId)
        {
            var response = await _httpClient.DeleteAsync($"/delete-model?model_id={modelId}");
            return response.IsSuccessStatusCode;
        }
    }
}