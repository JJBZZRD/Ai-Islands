using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Collections.ObjectModel;
using Newtonsoft.Json.Linq;
using frontend.Models;

namespace frontend.Services
{
    public class LibraryService
    {
        private readonly HttpClient _httpClient;
        private const string BaseUrl = "http://127.0.0.1:8000"; // Updated base URL

        public LibraryService()
        {
            _httpClient = new HttpClient();
            _httpClient.BaseAddress = new Uri(BaseUrl);
        }


        public async Task<List<Model>> GetLibrary()
        {
            System.Diagnostics.Debug.WriteLine("GetLibrary method started");
            try
            {
                var response = await _httpClient.GetAsync("library/get-full-library");
                response.EnsureSuccessStatusCode();
                var jsonString = await response.Content.ReadAsStringAsync();
                System.Diagnostics.Debug.WriteLine($"Received JSON string of length: {jsonString.Length}");

                var modelList = new List<Model>();

                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };
                
                var modelDictionary = JsonSerializer.Deserialize<Dictionary<string, Model>>(jsonString, options);
                System.Diagnostics.Debug.WriteLine($"Deserialized model dictionary. Count: {modelDictionary?.Count ?? 0}");

                if (modelDictionary != null)
                {
                    foreach (var pair in modelDictionary)
                    {
                        string modelId = pair.Key;
                        Model model = pair.Value;
                        model.ModelId = modelId;
                        modelList.Add(model);
                        System.Diagnostics.Debug.WriteLine($"Added model to list: {modelId}");
                    }
                }

                System.Diagnostics.Debug.WriteLine($"GetLibrary completed. Returning {modelList.Count} models");
                return modelList;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error in GetLibrary: {ex.Message}");
                throw;
            }
        }

 

        public async Task<List<Model>> GetModelIndex()
        {
            System.Diagnostics.Debug.WriteLine("GetModelIndex method started");
            try
            {
                var response = await _httpClient.GetAsync("library/get-full-model-index");
                response.EnsureSuccessStatusCode();
                var jsonString = await response.Content.ReadAsStringAsync();
                System.Diagnostics.Debug.WriteLine($"Received JSON string of length: {jsonString.Length}");

                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };
                
                var modelDictionary = JsonSerializer.Deserialize<Dictionary<string, Model>>(jsonString, options);
                System.Diagnostics.Debug.WriteLine($"Deserialized model dictionary. Count: {modelDictionary?.Count ?? 0}");

                var modelList = new List<Model>();

                if (modelDictionary != null)
                {
                    foreach (var pair in modelDictionary)
                    {
                        string modelId = pair.Key;
                        Model model = pair.Value;
                        model.ModelId = modelId;
                        modelList.Add(model);
                        System.Diagnostics.Debug.WriteLine($"Added model to list: {modelId}");
                    }
                }

                System.Diagnostics.Debug.WriteLine($"GetModelIndex completed. Returning {modelList.Count} models");
                return modelList;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error in GetModelIndex: {ex.Message}");
                throw;
            }
        }

        
        public async Task<Dictionary<string, object>> UpdateLibrary(string modelId, Dictionary<string, object> newEntry)
        {
            var response = await _httpClient.PostAsJsonAsync($"library/update?model_id={modelId}", newEntry);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Model> GetModelInfoLibrary(string modelId)
        {
            var response = await _httpClient.GetAsync($"library/get-model-info-library?model_id={modelId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Model>())!;
        }

        public async Task<Model> GetModelInfoIndex(string modelId)
        {
            var response = await _httpClient.GetAsync($"library/get-model-index?model_id={modelId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Model>())!;
        }

        public async Task<Dictionary<string, object>> DeleteModel(string modelId)
        {
            var response = await _httpClient.DeleteAsync($"library/delete-model?model_id={modelId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> AddFineTunedModel(Dictionary<string, object> newEntry)
        {
            var response = await _httpClient.PostAsJsonAsync("library/add-fine-tuned-model", newEntry);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> UpdateModelConfig(string modelId, Dictionary<string, object> newConfig)
        {
            var request = new { model_id = modelId, new_config = newConfig };
            var response = await _httpClient.PostAsJsonAsync("library/update-model-config", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> SaveNewModel(string modelId, string newModelId, Dictionary<string, object> newConfig)
        {
            var request = new { model_id = modelId, new_model_id = newModelId, new_config = newConfig };
            var response = await _httpClient.PostAsJsonAsync("library/save-new-model", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> UpdateModelId(string modelId, string newModelId)
        {
            var request = new { model_id = modelId, new_model_id = newModelId };
            var response = await _httpClient.PostAsJsonAsync("library/update-model-id", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }
    }
}