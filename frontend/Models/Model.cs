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

        [JsonPropertyName("is_reranker")]
        public bool IsReranker { get; set; } = false;

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

        public bool IsLoaded { get; set; }

        [JsonIgnore]
        public ICommand? LoadOrStopCommand { get; set; }

        // public bool IsButtonEnabled { get; set; } = true;

        public string? DatasetFormat { get; set; }

        [JsonPropertyName("mapping")]
        public Mapping? Mapping { get; set; }

        [JsonPropertyName("languages")]
        public Dictionary<string, string>? Languages { get; set; }

        public Dictionary<string, string> FineTuningParameters { get; set; } = new Dictionary<string, string>();
    }

        public class Mapping
    {
        [JsonPropertyName("input")]
        public string? Input { get; set; }

        [JsonPropertyName("output")]
        public string? Output { get; set; }

    }
    
    public class Config
    {
        [JsonPropertyName("prompt")]
        public PromptConfig? Prompt { get; set; }

        [JsonPropertyName("parameters")]
        public ParametersConfig? Parameters { get; set; }

        [JsonPropertyName("rag_settings")]
        public RagSettings? RagSettings { get; set; }

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

        [JsonPropertyName("translation_config")]
        public TranslationConfig? TranslationConfig { get; set; }

        [JsonPropertyName("quantization_config")]
        public QuantizationConfig? QuantizationConfig { get; set; }

        [JsonPropertyName("quantization_config_options")]
        public QuantizationConfigOptions? QuantizationConfigOptions { get; set; }

        [JsonPropertyName("system_prompt")]
        public SystemPrompt? SystemPrompt { get; set; }

        [JsonPropertyName("user_prompt")]
        public UserPrompt? UserPrompt { get; set; }

        [JsonPropertyName("assistant_prompt")]
        public AssistantPrompt? AssistantPrompt { get; set; }

        [JsonPropertyName("example_conversation")]
        public List<ConversationMessage>? ExampleConversation { get; set; }

        [JsonPropertyName("service_name")]
        public string? ServiceName { get; set; }

        [JsonPropertyName("features")]
        public Features? Features { get; set; }

        [JsonPropertyName("voice")]
        public string? Voice { get; set; }

        [JsonPropertyName("pitch")]
        public int? Pitch { get; set; }

        [JsonPropertyName("speed")]
        public int? Speed { get; set; }

        [JsonPropertyName("model")]
        public string? Model { get; set; }

        [JsonPropertyName("content_type")]
        public string? ContentType { get; set; }

        [JsonPropertyName("embedding_dimensions")]
        public int? EmbeddingDimensions { get; set; }

        [JsonPropertyName("max_input_tokens")]
        public int? MaxInputTokens { get; set; }

        [JsonPropertyName("supported_languages")]
        public List<string>? SupportedLanguages { get; set; }

        [JsonPropertyName("speaker_embedding_config")]
        public string? SpeakerEmbeddingConfig { get; set; }

        [JsonPropertyName("chat_history")]
        public bool? ChatHistory { get; set; }
    }

    public class ConversationMessage
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }
    }

    public class PromptConfig
    {
        [JsonPropertyName("system_prompt")]
        public string? SystemPrompt { get; set; }

        [JsonPropertyName("example_conversation")]
        public string? ExampleConversation { get; set; }
    }

    public class ParametersConfig
    {
        [JsonPropertyName("temperature")]
        public float? Temperature { get; set; }

        [JsonPropertyName("top_p")]
        public float? TopP { get; set; }

        [JsonPropertyName("top_k")]
        public float? TopK { get; set; }

        [JsonPropertyName("max_new_tokens")]
        public int? MaxNewTokens { get; set; }

        [JsonPropertyName("min_new_tokens")]
        public int? MinNewTokens { get; set; }

        [JsonPropertyName("repetition_penalty")]
        public float? RepetitionPenalty { get; set; }

        [JsonPropertyName("random_seed")]
        public int? RandomSeed { get; set; }

        [JsonPropertyName("stop_sequences")]
        public List<string>? StopSequences { get; set; }
    }

    public class RagSettings
    {
        [JsonPropertyName("use_dataset")]
        public bool? UseDataset { get; set; }

        [JsonPropertyName("dataset_name")]
        public string? DatasetName { get; set; }

        [JsonPropertyName("similarity_threshold")]
        public float? SimilarityThreshold { get; set; }

        [JsonPropertyName("use_chunking")]
        public bool? UseChunking { get; set; }
    }

    public class ModelConfig
    {
        [JsonPropertyName("torch_dtype")]
        public string? TorchDtype { get; set; }

        [JsonPropertyName("use_cache")]
        public bool? UseCache { get; set; }

        [JsonPropertyName("trust_remote_code")]
        public bool? TrustRemoteCode { get; set; }
    }

    public class TokenizerConfig
    {
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

        [JsonPropertyName("src_lang")]
        public string? SrcLang { get; set; }

        [JsonPropertyName("tgt_lang")]
        public string? TgtLang { get; set; }

        [JsonPropertyName("chunk_length_s")]
        public int? ChunkLengthS { get; set; }

        [JsonPropertyName("batch_size")]
        public int? BatchSize { get; set; }

        [JsonPropertyName("return_timestamps")]
        public bool? ReturnTimestamps { get; set; }

        [JsonPropertyName("candidate_labels")]
        public List<string>? CandidateLabels { get; set; }

        [JsonPropertyName("trust_remote_code")]
        public bool? TrustRemoteCode { get; set; }

        [JsonPropertyName("generate_kwargs")]
        public GenerateKwargs? GenerateKwargs { get; set; }

        [JsonPropertyName("forward_params")]
        public ForwardParams? ForwardParams { get; set; }

        // New properties based on the provided JSON
        [JsonPropertyName("min_new_tokens")]
        public int? MinNewTokens { get; set; }

        [JsonPropertyName("num_beam_groups")]
        public int? NumBeamGroups { get; set; }

        [JsonPropertyName("diversity_penalty")]
        public float? DiversityPenalty { get; set; }

        [JsonPropertyName("temperature")]
        public float? Temperature { get; set; }

        [JsonPropertyName("top_k")]
        public int? TopK { get; set; }

        [JsonPropertyName("top_p")]
        public float? TopP { get; set; }

        [JsonPropertyName("repetition_penalty")]
        public float? RepetitionPenalty { get; set; }

        [JsonPropertyName("length_penalty")]
        public float? LengthPenalty { get; set; }

        [JsonPropertyName("no_repeat_ngram_size")]
        public int? NoRepeatNgramSize { get; set; }

        [JsonPropertyName("early_stopping")]
        public bool? EarlyStopping { get; set; }

        [JsonPropertyName("typical_p")]
        public float? TypicalP { get; set; }

        [JsonPropertyName("epsilon_cutoff")]
        public float? EpsilonCutoff { get; set; }

        [JsonPropertyName("eta_cutoff")]
        public float? EtaCutoff { get; set; }

        [JsonPropertyName("do_sample")]
        public bool? DoSample { get; set; }

        [JsonPropertyName("renormalize_logits")]
        public bool? RenormalizeLogits { get; set; }

        [JsonPropertyName("exponential_decay_length_penalty")]
        public float? ExponentialDecayLengthPenalty { get; set; }

        // [JsonPropertyName("suppress_tokens")]
        // public List<int>? SuppressTokens { get; set; }

        // [JsonPropertyName("begin_suppress_tokens")]
        // public List<int>? BeginSuppressTokens { get; set; }

        [JsonPropertyName("forced_bos_token_id")]
        public int? ForcedBosTokenId { get; set; }

        [JsonPropertyName("forced_eos_token_id")]
        public int? ForcedEosTokenId { get; set; }

        [JsonPropertyName("remove_invalid_values")]
        public bool? RemoveInvalidValues { get; set; }

        [JsonPropertyName("num_return_sequences")]
        public int? NumReturnSequences { get; set; }

        [JsonPropertyName("output_attentions")]
        public bool? OutputAttentions { get; set; }

        [JsonPropertyName("output_hidden_states")]
        public bool? OutputHiddenStates { get; set; }

        [JsonPropertyName("output_scores")]
        public bool? OutputScores { get; set; }

        [JsonPropertyName("pad_token_id")]
        public int? PadTokenId { get; set; }

        [JsonPropertyName("bos_token_id")]
        public int? BosTokenId { get; set; }

        [JsonPropertyName("eos_token_id")]
        public int? EosTokenId { get; set; }

        [JsonPropertyName("encoder_no_repeat_ngram_size")]
        public int? EncoderNoRepeatNgramSize { get; set; }

        [JsonPropertyName("decoder_start_token_id")]
        public int? DecoderStartTokenId { get; set; }
    }

    public class GenerateKwargs
    {
        [JsonPropertyName("language")]
        public string? Language { get; set; }

        [JsonPropertyName("task")]
        public string? Task { get; set; }
    }

    public class ForwardParams
    {
        [JsonPropertyName("do_sample")]
        public bool? DoSample { get; set; }
    }

    public class DeviceConfig
    {
        [JsonPropertyName("device")]
        public string? Device { get; set; }
    }

    public class TranslationConfig
    {
        [JsonPropertyName("src_lang")]
        public string? SrcLang { get; set; }

        [JsonPropertyName("tgt_lang")]
        public string? TgtLang { get; set; }

        [JsonPropertyName("target_language")]
        public string? TargetLanguage { get; set; }

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

    public class SystemPrompt
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }

    }

    public class UserPrompt
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }
    }

    public class AssistantPrompt
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }
    }

    public class Features
    {
        [JsonPropertyName("sentiment")]
        public bool? Sentiment { get; set; }

        [JsonPropertyName("emotion")]
        public bool? Emotion { get; set; }

        [JsonPropertyName("entities")]
        public bool? Entities { get; set; }

        [JsonPropertyName("keywords")]
        public bool? Keywords { get; set; }

        [JsonPropertyName("categories")]
        public bool? Categories { get; set; }

        [JsonPropertyName("concepts")]
        public bool? Concepts { get; set; }

        [JsonPropertyName("relations")]
        public bool? Relations { get; set; }

        [JsonPropertyName("semantic_roles")]
        public bool? SemanticRoles { get; set; }
    }
}