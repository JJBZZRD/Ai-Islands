using System.Text.Json.Serialization;

namespace frontend.Models
{
    public class Playground
    {
        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("models")]
        public Dictionary<string, object>? ModelIds { get; set; }

        public Dictionary<string, Model>? Models { get; set; }

        [JsonPropertyName("chain")]
        public List<string>? Chain { get; set; }

        [JsonPropertyName("active_chain")]
        public bool ActiveChain { get; set; }

        [JsonPropertyName("playground_id")]
        public string? PlaygroundId { get; set; }

    }

}