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
        public Config? Config { get; set; }

        [JsonPropertyName("auth_token")]
        public string? AuthToken { get; set; }

        public bool IsInLibrary { get; set; }

        [JsonIgnore]
        public ICommand? LoadOrStopCommand { get; set; }

        public string? DatasetFormat { get; set; }

        [JsonPropertyName("mapping")]
        public Dictionary<string, object>? Mapping { get; set; }

        [JsonPropertyName("languages")]
        public Dictionary<string, string>? Languages { get; set; }
    }

    public class Config
    {
        [JsonPropertyName("model_config")]
        public ModelConfig? ModelConfig { get; set; }

        [JsonPropertyName("tokenizer_config")]
        public TokenizerConfig? TokenizerConfig { get; set; }

        [JsonPropertyName("processor_config")]
        public ProcessorConfig? ProcessorConfig { get; set; }

        [JsonPropertyName("pipeline_config")]
        public PipelineConfig? PipelineConfig { get; set; }

        [JsonPropertyName("device_config")]
        public DeviceConfig? DeviceConfig { get; set; }

        [JsonPropertyName("quantization_config")]
        public QuantizationConfig? QuantizationConfig { get; set; }

        [JsonPropertyName("quantization_config_options")]
        public QuantizationConfigOptions? QuantizationConfigOptions { get; set; }

        [JsonPropertyName("system_prompt")]
        public Prompt? SystemPrompt { get; set; }

        [JsonPropertyName("user_prompt")]
        public Prompt? UserPrompt { get; set; }

        [JsonPropertyName("assistant_prompt")]
        public Prompt? AssistantPrompt { get; set; }

        [JsonPropertyName("example_conversation")]
        public List<Conversation>? ExampleConversation { get; set; }

        [JsonPropertyName("embedding_dimensions")]
        public int? EmbeddingDimensions { get; set; }

        [JsonPropertyName("max_input_tokens")]
        public int? MaxInputTokens { get; set; }

        [JsonPropertyName("supported_languages")]
        public List<string>? SupportedLanguages { get; set; }

        [JsonPropertyName("speaker_embedding_config")]
        public string? SpeakerEmbeddingConfig { get; set; }
    }

    public class ModelConfig
    {
        [JsonPropertyName("torch_dtype")]
        public string? TorchDtype { get; set; }

        [JsonPropertyName("use_auth_token")]
        public string? UseAuthToken { get; set; }

        [JsonPropertyName("use_cache")]
        public bool? UseCache { get; set; }

        [JsonPropertyName("trust_remote_code")]
        public bool? TrustRemoteCode { get; set; }
    }

    public class TokenizerConfig
    {
        [JsonPropertyName("use_auth_token")]
        public string? UseAuthToken { get; set; }

        [JsonPropertyName("do_lower_case")]
        public bool? DoLowerCase { get; set; }

        [JsonPropertyName("eos_token")]
        public string? EosToken { get; set; }

        [JsonPropertyName("unk_token")]
        public string? UnkToken { get; set; }

        [JsonPropertyName("trust_remote_code")]
        public bool? TrustRemoteCode { get; set; }
    }

    public class ProcessorConfig
    {
        // Add properties as needed
    }

    public class PipelineConfig
    {
        [JsonPropertyName("max_length")]
        public int? MaxLength { get; set; }

        [JsonPropertyName("max_new_tokens")]
        public int? MaxNewTokens { get; set; }

        [JsonPropertyName("num_beams")]
        public int? NumBeams { get; set; }

        [JsonPropertyName("use_cache")]
        public bool? UseCache { get; set; }
    }

    public class DeviceConfig
    {
        [JsonPropertyName("device")]
        public string? Device { get; set; }
    }

    public class QuantizationConfig
    {
        [JsonPropertyName("current_mode")]
        public string? CurrentMode { get; set; }
    }

    public class QuantizationConfigOptions
    {
        [JsonPropertyName("4-bit")]
        public FourBitConfig? FourBit { get; set; }

        [JsonPropertyName("8-bit")]
        public EightBitConfig? EightBit { get; set; }

        [JsonPropertyName("bfloat16")]
        public Bfloat16Config? Bfloat16 { get; set; }
    }

    public class FourBitConfig
    {
        [JsonPropertyName("load_in_4bit")]
        public bool? LoadIn4Bit { get; set; }

        [JsonPropertyName("bnb_4bit_use_double_quant")]
        public bool? Bnb4BitUseDoubleQuant { get; set; }

        [JsonPropertyName("bnb_4bit_quant_type")]
        public string? Bnb4BitQuantType { get; set; }

        [JsonPropertyName("bnb_4bit_compute_dtype")]
        public string? Bnb4BitComputeDtype { get; set; }
    }

    public class EightBitConfig
    {
        [JsonPropertyName("load_in_8bit")]
        public bool? LoadIn8Bit { get; set; }
    }

    public class Bfloat16Config
    {
        // Add properties as needed
    }

    public class Prompt
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }
    }

    public class Conversation
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }
    }
}