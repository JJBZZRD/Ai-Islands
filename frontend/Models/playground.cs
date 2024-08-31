using System.Text.Json.Serialization;

namespace frontend.Models
{
    public class Playground
    {
        [JsonPropertyName("playground_id")]
        public string? PlaygroundId { get; set; }

        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("models")]
        public Dictionary<string, object>? ModelIds { get; set; }

        public Dictionary<string, Model>? Models { get; set; }

        [JsonPropertyName("chain")]
        public List<string>? Chain { get; set; }

        [JsonPropertyName("active_chain")]
        public bool ActiveChain { get; set; }

        public string SelectedFilePath { get; set; }

        public string InputText { get; set; }

        public bool IsChainLoaded { get; set; }

        public string PipelineTag { get; set; }

    }

}