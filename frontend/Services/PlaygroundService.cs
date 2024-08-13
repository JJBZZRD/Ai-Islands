using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using frontend.entities;
using System.Text.Json;
using frontend.Models;
using frontend.Services;

namespace frontend.Services
{
    public class PlaygroundService
    {
        private readonly HttpClient _httpClient;
        private const string BaseUrl = "http://127.0.0.1:8000"; // Base URL for playground routes

        public PlaygroundService()
        {
            _httpClient = new HttpClient();
            _httpClient.BaseAddress = new Uri(BaseUrl);
        }

        public async Task<Dictionary<string, object>> CreatePlayground(string? playgroundId = null, string? description = null)
        {
            var request = new { playground_id = playgroundId, description = description };
            var response = await _httpClient.PostAsJsonAsync("playground/create", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> UpdatePlayground(string playgroundId, string? newPlaygroundId = null, string? description = null)
        {
            var request = new { playground_id = playgroundId, new_playground_id = newPlaygroundId, description = description };
            var response = await _httpClient.PutAsJsonAsync("playground/update", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> DeletePlayground(string playgroundId)
        {
            var response = await _httpClient.DeleteAsync($"playground/delete?playground_id={playgroundId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> AddModelToPlayground(string playgroundId, string modelId)
        {
            var request = new { playground_id = playgroundId, model_id = modelId };
            var response = await _httpClient.PostAsJsonAsync("playground/add-model", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> RemoveModelFromPlayground(string playgroundId, string modelId)
        {
            var request = new { playground_id = playgroundId, model_id = modelId };
            var response = await _httpClient.PostAsJsonAsync("playground/remove-model", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        //public async Task<List<Dictionary<string, object>>> ListPlaygrounds()
        //{
        // var response = await _httpClient.GetAsync("playground/list");
        //response.EnsureSuccessStatusCode();
        //return (await response.Content.ReadFromJsonAsync<List<Dictionary<string, object>>>())!;
        //}
           public async Task<Dictionary<string, Playground>> ListPlaygrounds()
           {
               try
               {
                   var response = await _httpClient.GetAsync("playground/list");
                   response.EnsureSuccessStatusCode();

                   var content = await response.Content.ReadAsStringAsync();
                   System.Diagnostics.Debug.WriteLine($"API Response: {content}");

                   // deserialize the response into a dynamic object to check its structure
                   var jsonResponse = JsonSerializer.Deserialize<Dictionary<string, object>>(content);
           
                   if (jsonResponse != null && jsonResponse.ContainsKey("data"))
                   {
                       // deserialize the 'data' field into the expected structure
                       return JsonSerializer.Deserialize<Dictionary<string, Playground>>(jsonResponse["data"].ToString()) ?? new Dictionary<string, Playground>();
                   }
                   else
                   {
                       throw new JsonException("Unexpected JSON structure: " + content);
                   }
               }
               catch (HttpRequestException ex)
               {
                   System.Diagnostics.Debug.WriteLine($"HTTP error in ListPlaygrounds: {ex.Message}");
                   throw;
               }
               catch (JsonException ex)
               {
                   System.Diagnostics.Debug.WriteLine($"JSON parsing error in ListPlaygrounds: {ex.Message}");
                   throw;
               }
               catch (Exception ex)
               {
                   System.Diagnostics.Debug.WriteLine($"Unexpected error in ListPlaygrounds: {ex.Message}");
                   throw;
               }
           }

        public async Task<Dictionary<string, object>> GetPlaygroundInfo(string playgroundId)
        {
            var response = await _httpClient.GetAsync($"playground/info?playground_id={playgroundId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> ConfigureChain(string playgroundId, List<string> chain)
        {
            var request = new { playground_id = playgroundId, chain = chain };
            var response = await _httpClient.PostAsJsonAsync("playground/configure-chain", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> LoadPlaygroundChain(string playgroundId)
        {
            var response = await _httpClient.PostAsync($"playground/load-chain?playground_id={playgroundId}", null);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> StopPlaygroundChain(string playgroundId)
        {
            var response = await _httpClient.PostAsync($"playground/stop-chain?playground_id={playgroundId}", null);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> Inference(string playgroundId, Dictionary<string, object> data)
        {
            var request = new { playground_id = playgroundId, data = data };
            var response = await _httpClient.PostAsJsonAsync("playground/inference", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, Model>> GetPlaygroundModels(Playground playground)
        {
            LibraryService libraryService = new LibraryService();
            ModelService modelService = new ModelService();
            var modelList = await libraryService.GetLibrary();
            var playgroundModels = new Dictionary<string, Model>();
            foreach (var model in modelList)
            {
                if (playground.Models.ContainsKey(model.ModelId))
                {
                    playgroundModels[model.ModelId] = model;
                }
            }
            return playgroundModels;
        }
    }
}