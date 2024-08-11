using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace frontend.entities
{
    public class Playground
    {
        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("models")]
        public Dictionary<string, Mapping>? Models { get; set; }

        [JsonPropertyName("chain")]
        public List<string>? Chain { get; set; }

        [JsonPropertyName("active_chain")]
        public bool ActiveChain { get; set; }

        [JsonPropertyName("id")]
        public string? Id { get; set; }
    }

    public class Mapping
    {
        [JsonPropertyName("input")]
        public string? Input { get; set; }

        [JsonPropertyName("output")]
        public string? Output { get; set; }
    }
}


