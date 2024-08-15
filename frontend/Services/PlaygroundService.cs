using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using frontend.Models;
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
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri(BaseUrl),
                Timeout = TimeSpan.FromSeconds(30)
            };
            _httpClient.DefaultRequestHeaders.Accept.Add(new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));
        }

        public async Task<Dictionary<string, object>> CreatePlayground(string? playgroundId = null, string? description = null)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(playgroundId))
                {
                    throw new ArgumentException("Playground name cannot be empty", nameof(playgroundId));
                }

                // Ensure description is not null
                description ??= string.Empty;

                var request = new { playground_id = playgroundId, description = description };
                var response = await _httpClient.PostAsJsonAsync("playground/create", request);
                
                if (!response.IsSuccessStatusCode)
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    throw new HttpRequestException($"Error creating playground. Status: {response.StatusCode}, Content: {errorContent}");
                }
                
                var result = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
                
                // Log the result for debugging
                System.Diagnostics.Debug.WriteLine($"Create Playground Result: {JsonSerializer.Serialize(result)}");
                
                return result!;
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HTTP Request Error: {ex.Message}");
                if (ex.InnerException != null)
                {
                    System.Diagnostics.Debug.WriteLine($"Inner Exception: {ex.InnerException.Message}");
                }
                throw;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Unexpected error in CreatePlayground: {ex.Message}");
                throw;
            }
        }

        public async Task<Dictionary<string, object>> UpdatePlayground(string playgroundId, string? newPlaygroundId = null, string? description = null)
        {
            var request = new { playground_id = playgroundId, new_playground_id = newPlaygroundId, description = description };
            var response = await _httpClient.PutAsJsonAsync("playground/update", request);
            response.EnsureSuccessStatusCode();
            return (await response.Content.ReadFromJsonAsync<Dictionary<string, object>>())!;
        }

        public async Task DeletePlayground(string playgroundId)
        {
            var response = await _httpClient.DeleteAsync($"playground/delete?playground_id={Uri.EscapeDataString(playgroundId)}");
            response.EnsureSuccessStatusCode();
            // No need to return anything for a successful delete
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
            try
            {
                var request = new { playground_id = playgroundId, model_id = modelId };
                var response = await _httpClient.PostAsJsonAsync("playground/remove-model", request);
                response.EnsureSuccessStatusCode();
                
                var content = await response.Content.ReadAsStringAsync();
                System.Diagnostics.Debug.WriteLine($"RemoveModelFromPlayground raw response: {content}");

                if (string.IsNullOrWhiteSpace(content))
                {
                    return new Dictionary<string, object> { { "message", "Success" } };
                }

                return JsonSerializer.Deserialize<Dictionary<string, object>>(content) ?? 
                       new Dictionary<string, object> { { "message", "Success" } };
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HTTP Request Exception in RemoveModelFromPlayground: {ex.Message}");
                throw;
            }
            catch (JsonException ex)
            {
                System.Diagnostics.Debug.WriteLine($"JSON parsing error in RemoveModelFromPlayground: {ex.Message}");
                return new Dictionary<string, object> { { "message", "Error" }, { "error", "Unable to parse response" } };
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Unexpected error in RemoveModelFromPlayground: {ex.Message}");
                throw;
            }
        }

        public async Task<List<Playground>> ListPlaygrounds()
        {
            try
            {
                var response = await _httpClient.GetAsync("playground/list");
                response.EnsureSuccessStatusCode();

                var content = await response.Content.ReadAsStringAsync();
                System.Diagnostics.Debug.WriteLine($"API Response: {content}");

                var jsonResponse = JsonSerializer.Deserialize<Dictionary<string, object>>(content);

                if (jsonResponse != null && jsonResponse.ContainsKey("data"))
                {
                    var playgroundsDict = JsonSerializer.Deserialize<Dictionary<string, Playground>>(jsonResponse["data"].ToString()) ?? new Dictionary<string, Playground>();
                    
                    var libraryService = new LibraryService();
                    var playgroundList = new List<Playground>();

                    foreach (var kvp in playgroundsDict)
                    {
                        var playground = kvp.Value;
                        playground.PlaygroundId = kvp.Key;

                        // Initialize the Models dictionary if it's null
                        playground.Models ??= new Dictionary<string, Model>();

                        // Populate the Models dictionary with actual Model objects
                        if (playground.ModelIds != null)
                        {
                            foreach (var modelKvp in playground.ModelIds)
                            {
                                try
                                {
                                    var modelInfo = await libraryService.GetModelInfoLibrary(modelKvp.Key);
                                    playground.Models[modelKvp.Key] = modelInfo;
                                }
                                catch (Exception ex)
                                {
                                    System.Diagnostics.Debug.WriteLine($"Error fetching model info for {modelKvp.Key}: {ex.Message}");
                                    // If we can't fetch the model info, we'll create a basic Model object with the available information
                                    playground.Models[modelKvp.Key] = new Model
                                    {
                                        ModelId = modelKvp.Key,
                                        // You can add more properties here if they're available in modelKvp.Value
                                    };
                                }
                            }
                        }

                        playgroundList.Add(playground);
                    }
                    return playgroundList;
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

        public async Task<Playground> GetPlaygroundInfo(string playgroundId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"playground/info?playground_id={playgroundId}");
                response.EnsureSuccessStatusCode();

                var content = await response.Content.ReadAsStringAsync();
                System.Diagnostics.Debug.WriteLine($"API Response for playground {playgroundId}: {content}");

                var jsonResponse = JsonSerializer.Deserialize<Dictionary<string, object>>(content);

                if (jsonResponse != null && jsonResponse.ContainsKey("data"))
                {
                    var playgroundData = JsonSerializer.Deserialize<Playground>(jsonResponse["data"].ToString());
                    
                    if (playgroundData != null)
                    {
                        playgroundData.PlaygroundId = playgroundId;

                        // Initialize the Models dictionary if it's null
                        playgroundData.Models ??= new Dictionary<string, Model>();

                        var libraryService = new LibraryService();

                        // Populate the Models dictionary with actual Model objects
                        if (playgroundData.ModelIds != null)
                        {
                            foreach (var modelKvp in playgroundData.ModelIds)
                            {
                                try
                                {
                                    var modelInfo = await libraryService.GetModelInfoLibrary(modelKvp.Key);
                                    playgroundData.Models[modelKvp.Key] = modelInfo;
                                }
                                catch (Exception ex)
                                {
                                    System.Diagnostics.Debug.WriteLine($"Error fetching model info for {modelKvp.Key}: {ex.Message}");
                                    // If we can't fetch the model info, we'll create a basic Model object with the available information
                                    playgroundData.Models[modelKvp.Key] = new Model
                                    {
                                        ModelId = modelKvp.Key,
                                        // You can add more properties here if they're available in modelKvp.Value
                                    };
                                }
                            }
                        }

                        return playgroundData;
                    }
                    else
                    {
                        throw new JsonException($"Failed to deserialize playground data for playground ID: {playgroundId}");
                    }
                }
                else
                {
                    throw new JsonException($"Unexpected JSON structure for playground ID: {playgroundId}");
                }
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HTTP error in GetPlaygroundInfo: {ex.Message}");
                throw;
            }
            catch (JsonException ex)
            {
                System.Diagnostics.Debug.WriteLine($"JSON parsing error in GetPlaygroundInfo: {ex.Message}");
                throw;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Unexpected error in GetPlaygroundInfo: {ex.Message}");
                throw;
            }
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