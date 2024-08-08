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


        public async Task<ObservableCollection<Model>> GetLibrary()
        {
            var response = await _httpClient.GetAsync("library/get-full-library");
            response.EnsureSuccessStatusCode();
            var jsonString = await response.Content.ReadAsStringAsync();
            
            // Parse the JSON string into a JObject
            var libraryJson = JObject.Parse(jsonString);
            
            var modelCollection = new ObservableCollection<Model>();

            // Iterate through each key-value pair in the JObject
            foreach (var pair in libraryJson)
            {
                if (pair.Value is JObject modelData)
                {
                    // Create a new JObject for each model, including the key as "ModelId"
                    var modelJson = new JObject(modelData);
                    modelJson["ModelId"] = pair.Key;

                    // Create a new Model instance and add it to the collection
                    var model = new Model(modelJson);
                    modelCollection.Add(model);
                }
            }

            return modelCollection;
        }

        public async Task<Dictionary<string, Dictionary<string, object>>> GetModelIndex()
        {
            var response = await _httpClient.GetAsync("library/get-full-model-index");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, Dictionary<string, object>>>())!;
        }

        
        public async Task<Dictionary<string, object>> UpdateLibrary(string modelId, Dictionary<string, object> newEntry)
        {
            var response = await _httpClient.PostAsJsonAsync($"library/update?model_id={modelId}", newEntry);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> GetModelInfoLibrary(string modelId)
        {
            var response = await _httpClient.GetAsync($"library/get-model-info-library?model_id={modelId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task<Dictionary<string, object>> GetModelInfoIndex(string modelId)
        {
            var response = await _httpClient.GetAsync($"library/get-model-index?model_id={modelId}");
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
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