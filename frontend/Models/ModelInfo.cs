using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace frontend.Models
{
    public class ModelInfo
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty;
        
        [JsonPropertyName("is_online")]
        public bool IsOnline { get; set; }

        [JsonPropertyName("pipeline_tag")]
        public string PipelineTag { get; set; } = string.Empty;
        public string Finetune { get; set; } = string.Empty;
        public bool IsAddToLibraryEnabled { get; set; } = true;
        public string Description { get; set; } = string.Empty;
        public List<string> Tags { get; set; } = new List<string>();
    }
}