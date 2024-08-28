using CommunityToolkit.Mvvm.ComponentModel;
using System.Diagnostics;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using frontend.Services;
using Microsoft.Maui.Storage;

namespace frontend.Models.ViewModels
{
    public partial class FineTuneNLPViewModel : ObservableObject
    {
        [ObservableProperty]
        private string modelId;

        [ObservableProperty]
        private string learningRate = "1E-05";
        [ObservableProperty]
        private string numTrainEpochs = "10";
        [ObservableProperty]
        private string weightDecay = "0.01";
        [ObservableProperty]
        private string saveTotalLimit = "3";
        [ObservableProperty]
        private string maxLength = "128";

        [ObservableProperty]
        private string selectedFilePath;

        private readonly ModelService _modelService;

        public FineTuneNLPViewModel(Model model)
        {
            ModelId = model.ModelId;
            _modelService = new ModelService();
        }

        public async Task<string> FineTune()
        {
            if (string.IsNullOrEmpty(SelectedFilePath))
                return "Error: No CSV file selected";

            if (!double.TryParse(LearningRate, out double learningRateValue))
                return "Error: Invalid Learning Rate";

            if (!double.TryParse(NumTrainEpochs, out double numTrainEpochsValue))
                return "Error: Invalid Number of Train Epochs";

            if (!double.TryParse(WeightDecay, out double weightDecayValue))
                return "Error: Invalid Weight Decay";

            if (!double.TryParse(SaveTotalLimit, out double saveTotalLimitValue))
                return "Error: Invalid Save Total Limit";

            if (!double.TryParse(MaxLength, out double maxLengthValue))
                return "Error: Invalid Max Length";

            Debug.WriteLine($"Model Name: {ModelId}");
            Debug.WriteLine($"Learning Rate: {learningRateValue}");
            Debug.WriteLine($"Number of Train Epochs: {numTrainEpochsValue}");
            Debug.WriteLine($"Weight Decay: {weightDecayValue}");
            Debug.WriteLine($"Save Total Limit: {saveTotalLimitValue}");
            Debug.WriteLine($"Max Length: {maxLengthValue}");
            Debug.WriteLine($"Selected File Path: {SelectedFilePath}");

            var tokenizerArgs = new Dictionary<string, double>
            {
                { "max_length", maxLengthValue }
            };

            var trainingArgs = new Dictionary<string, double>
            {
                { "learning_rate", learningRateValue },
                { "num_train_epochs", numTrainEpochsValue },
                { "weight_decay", weightDecayValue },
                { "save_total_limit", saveTotalLimitValue }
            };

            var response = await _modelService.FineTuneModel(ModelId, SelectedFilePath, tokenizerArgs, trainingArgs);

            if (response.IsSuccessStatusCode)
            {
                return "Fine-tuning started successfully";
            }
            else
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                    var errorJson = JsonDocument.Parse(errorContent);
                    if (errorJson.RootElement.TryGetProperty("error", out JsonElement errorElement) &&
                        errorElement.TryGetProperty("message", out JsonElement messageElement))
                    {
                        var errorMessage = messageElement.GetString();
                        return $"Error: {errorMessage}";
                    }
                    else
                    {
                        return $"Error: {response.ReasonPhrase}, Content: {errorContent}";
                    }
                
            }
        }
    }
}
