using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace frontend.Services
{
    public class PlaygroundService
    {
        private readonly HttpClient _httpClient;
        private const string BaseUrl = "http://127.0.0.1:8000/playground"; // Base URL for playground routes

        public PlaygroundService()
        {
            _httpClient = new HttpClient();
            _httpClient.BaseAddress = new Uri(BaseUrl);
        }

        public async Task<Dictionary<string, object>> CreatePlayground(string? playgroundId = null, string? description = null)
        {
            var request = new { playground_id = playgroundId, description = description };
            var response = await _httpClient.PostAsJsonAsync("/create", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> UpdatePlayground(string playgroundId, string? newPlaygroundId = null, string? description = null)
        {
            var request = new { playground_id = playgroundId, new_playground_id = newPlaygroundId, description = description };
            var response = await _httpClient.PutAsJsonAsync("/update", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> DeletePlayground(string playgroundId)
        {
            var response = await _httpClient.DeleteAsync($"/delete?playground_id={playgroundId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> AddModelToPlayground(string playgroundId, string modelId)
        {
            var request = new { playground_id = playgroundId, model_id = modelId };
            var response = await _httpClient.PostAsJsonAsync("/add-model", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> RemoveModelFromPlayground(string playgroundId, string modelId)
        {
            var request = new { playground_id = playgroundId, model_id = modelId };
            var response = await _httpClient.PostAsJsonAsync("/remove-model", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<List<Dictionary<string, object>>> ListPlaygrounds()
        {
            var response = await _httpClient.GetAsync("/list");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<List<Dictionary<string, object>>>())!;
        }

        public async Task<Dictionary<string, object>> GetPlaygroundInfo(string playgroundId)
        {
            var response = await _httpClient.GetAsync($"/info?playground_id={playgroundId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> ConfigureChain(string playgroundId, List<string> chain)
        {
            var request = new { playground_id = playgroundId, chain = chain };
            var response = await _httpClient.PostAsJsonAsync("/configure-chain", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> LoadPlaygroundChain(string playgroundId)
        {
            var response = await _httpClient.PostAsync($"/load-chain?playground_id={playgroundId}", null);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> StopPlaygroundChain(string playgroundId)
        {
            var response = await _httpClient.PostAsync($"/stop-chain?playground_id={playgroundId}", null);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> Inference(string playgroundId, Dictionary<string, object> data)
        {
            var request = new { playground_id = playgroundId, data = data };
            var response = await _httpClient.PostAsJsonAsync("/inference", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }
    }
}
