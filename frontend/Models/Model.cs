using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Newtonsoft.Json.Linq;
using System.Windows.Input;
using System.Text.Json;

namespace frontend.Models
{
    public class Model
    {
        public string? ModelId { get; set; }

        [JsonPropertyName("base_model")]
        public string? BaseModel { get; set; }

        [JsonPropertyName("dir")]
        public string? Dir { get; set; }

        [JsonPropertyName("is_customised")]
        public bool? IsCustomised { get; set; }

        [JsonPropertyName("is_online")]
        public bool? IsOnline { get; set; }

        public string Status => IsOnline ?? false ? "Online" : "Offline";

        [JsonPropertyName("model_source")]
        public string? ModelSource { get; set; }

        [JsonPropertyName("tags")]
        public List<string>? Tags { get; set; }

        [JsonPropertyName("model_desc")]
        public string? ModelDesc { get; set; }

        [JsonPropertyName("model_detail")]
        public string? ModelDetail { get; set; }

        [JsonPropertyName("model_class")]
        public string? ModelClass { get; set; }

        [JsonPropertyName("pipeline_tag")]
        public string? PipelineTag { get; set; }

        [JsonPropertyName("model_card_url")]
        public string? ModelCardUrl { get; set; }

        [JsonPropertyName("requirements")]
        public Dictionary<string, JsonElement>? Requirements { get; set; }

        [JsonPropertyName("config")]
        public Dictionary<string, object>? Config { get; set; }

        [JsonPropertyName("auth_token")]
        public string? AuthToken { get; set; }

        public bool IsInLibrary { get; set; }

        [JsonIgnore]
        public ICommand? LoadOrStopCommand { get; set; }

        public string? DatasetFormat { get; set; }

        [JsonPropertyName("mapping")]
        public Mapping? Mapping { get; set; }

        [JsonPropertyName("languages")]
        public Dictionary<string,string>? Languages { get; set; }

    }    
    public class Mapping
    {
        [JsonPropertyName("input")]
        public string? Input { get; set; }

        [JsonPropertyName("output")]
        public string? Output { get; set; }

    }
}