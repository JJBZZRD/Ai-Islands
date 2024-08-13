using System.Collections.Generic;
using System.Text.Json.Serialization;
using frontend.entities;
using frontend.Models;
namespace frontend.entities
{
    public class Playground
    {
        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("models")]
        public Dictionary<string, Model>? Models { get; set; }

        [JsonPropertyName("chain")]
        public List<string>? Chain { get; set; }

        [JsonPropertyName("active_chain")]
        public bool ActiveChain { get; set; }

        [JsonPropertyName("id")]
        public string? Id { get; set; }

    }

}