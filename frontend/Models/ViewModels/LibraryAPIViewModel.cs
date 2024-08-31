using CommunityToolkit.Mvvm.ComponentModel;
using frontend.Models;
using System.Text.Json;

namespace frontend.ViewModels
{
    public partial class LibraryAPIViewModel : ObservableObject
    {
        [ObservableProperty]
        private string loadModelRequest;
        [ObservableProperty]
        private string loadModelResponse;
        [ObservableProperty]
        private string unloadModelRequest;
        [ObservableProperty]
        private string unloadModelResponse;
        [ObservableProperty]
        private string inferenceRequest;
        [ObservableProperty]
        private string inferenceResponse;
        [ObservableProperty]
        private string inferenceRequestBody;

        public LibraryAPIViewModel(Model model)
        {
            InitializeApiExamples(model);
        }

        private void InitializeApiExamples(Model model)
        {
            LoadModelRequest = $"POST http://127.0.0.1:8000/model/load?model_id={model.ModelId}";
            LoadModelResponse = $@"{{
    ""message"": ""Model {model.ModelId} loaded successfully"",
    ""data"": {{}}
}}";
            UnloadModelRequest = $"POST http://127.0.0.1:8000/model/unload?model_id={model.ModelId}";
            UnloadModelResponse = $@"{{
    ""message"": ""Model {model.ModelId} unloaded successfully"",
    ""data"": {{}}
}}";
            InferenceRequest = $"POST http://127.0.0.1:8000/model/inference";
            InferenceResponse = GetInferenceResponseExample();
            InferenceRequestBody = GetInferenceRequestBodyExample(model);
        }

        private string GetInferenceRequestBodyExample(Model model)
        {
            object data;
            switch (model.PipelineTag?.ToLower())
            {
                // Computer Vision Models
                case "object-detection":
                case "image-segmentation":
                    data = new { image_path = "/path/to/image.jpg" };
                    break;
                case "zero-shot-object-detection":
                    data = new { payload = new { image = "/path/to/image.jpg", text = new[] { "cat", "dog", "bird" } } };
                    break;

                // NLP Models
                case "text-classification":
                case "zero-shot-classification":
                case "feature-extraction":
                case "text-generation":
                    data = new { payload = "Your input text here" };
                    break;
                case "translation":
                    data = new { payload = new[] { "Translate this sentence.", "And this one too." } };
                    break;
                case "text-to-speech":
                    data = new { payload = "Text to be converted to speech" };
                    break;
                case "speech-to-text":
                case "automatic-speech-recognition":
                    data = new { file_path = "/path/to/audio.wav" };
                    break;

                default:
                    data = new { payload = "Example input for this model type" };
                    break;
            }

            var requestBody = new { model_id = model.ModelId, data = data };
            return JsonSerializer.Serialize(requestBody, new JsonSerializerOptions { WriteIndented = true });
        }

        private string GetInferenceResponseExample()
        {
            return @"{
    ""message"": ""Success"",
    ""data"": {
        ""output"": ""Model inference output""
    }
}";
        }
    }
}
