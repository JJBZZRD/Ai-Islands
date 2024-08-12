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
            var response = await _httpClient.PostAsJsonAsync("settings/update-watson-settings", settings);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> GetWatsonSettings()
        {
            var response = await _httpClient.GetAsync("settings/get-watson-settings");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> UpdateChunkingSettings(Dictionary<string, object> settings)
        {
            var response = await _httpClient.PostAsJsonAsync("settings/update-chunking-settings", settings);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> GetChunkingSettings()
        {
            var response = await _httpClient.GetAsync("settings/get-chunking-settings");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> SetHardware(string device)
        {
            var response = await _httpClient.PostAsJsonAsync("settings/set-hardware", new { device });
            
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>() ?? new Dictionary<string, object>();
            }
            else
            {
                var errorContent = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
                return errorContent ?? new Dictionary<string, object> { { "detail", "An unknown error occurred" } };
            }
        }

        public async Task<Dictionary<string, object>> GetHardware()
        {
            var response = await _httpClient.GetAsync("settings/get-hardware");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> CheckGpu()
        {
            var response = await _httpClient.GetAsync("settings/check-gpu");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }
    }
}