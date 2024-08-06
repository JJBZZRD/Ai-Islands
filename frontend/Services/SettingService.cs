using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace frontend.Services
{
    public class SettingsService
    {
        private readonly HttpClient _httpClient;
        private const string BaseUrl = "http://127.0.0.1:8000";

        public SettingsService()
        {
            _httpClient = new HttpClient();
            _httpClient.BaseAddress = new Uri(BaseUrl);
        }

        public async Task<Dictionary<string, object>> UpdateWatsonSettings(Dictionary<string, string> settings)
        {
            var response = await _httpClient.PostAsJsonAsync("/update-watson-settings", settings);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> GetWatsonSettings()
        {
            var response = await _httpClient.GetAsync("/get-watson-settings");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> UpdateChunkingSettings(Dictionary<string, object> settings)
        {
            var response = await _httpClient.PostAsJsonAsync("/update-chunking-settings", settings);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> GetChunkingSettings()
        {
            var response = await _httpClient.GetAsync("/get-chunking-settings");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> SetHardware(string device)
        {
            var response = await _httpClient.PostAsJsonAsync("/set-hardware", new { device });
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> GetHardware()
        {
            var response = await _httpClient.GetAsync("/get-hardware");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> CheckGpu()
        {
            var response = await _httpClient.GetAsync("/check-gpu");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }
    }
}