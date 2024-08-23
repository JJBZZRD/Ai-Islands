using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.ObjectModel;
using System.Diagnostics;

namespace frontend.Models.ViewModels
{
    internal partial class ConfigViewModel : ObservableObject
    {
        [ObservableProperty]
        private Config? config;

        public ObservableCollection<ConversationMessage> ExampleConversation { get; }
        public ObservableCollection<CandidateLabel> CandidateLabels { get; }
        public ObservableCollection<StopSequence> StopSequences { get; }
        public ObservableCollection<Language> LanguagesList { get; }

        [ObservableProperty]
        private List<string> datasetNames;

        [ObservableProperty]
        private string selectedDatasetName;

        [ObservableProperty]
        private Language selectedPipelineConfigSrcLang;

        [ObservableProperty]
        private Language selectedPipelineConfigTgtLang;

        [ObservableProperty]
        private Language selectedTranslationConfigSrcLang;

        [ObservableProperty]
        private Language selectedTranslationConfigTgtLang;

        [ObservableProperty]
        private Language selectedTransationConfigTargetLanguage;

        [ObservableProperty]
        private Language selectedGenerateKwargsLanguage;

        public ConfigViewModel()
        {
            ExampleConversation = new ObservableCollection<ConversationMessage>();
            CandidateLabels = new ObservableCollection<CandidateLabel>();
            StopSequences = new ObservableCollection<StopSequence>();
            LanguagesList = new ObservableCollection<Language>(); // Initialize LanguagesList
        }

        partial void OnConfigChanged(Config? oldValue, Config? newValue)
        {
            ExampleConversation.Clear();
            if (newValue?.ExampleConversation != null)
            {
                foreach (var message in newValue.ExampleConversation)
                {
                    ExampleConversation.Add(new ConversationMessage { Role = message.Role, Content = message.Content });
                }
            }

            CandidateLabels.Clear();
            if (newValue?.PipelineConfig?.CandidateLabels != null)
            {
                foreach (var label in newValue.PipelineConfig.CandidateLabels)
                {
                    CandidateLabels.Add(new CandidateLabel(label));
                }
            }

            StopSequences.Clear();
            if (newValue?.Parameters?.StopSequences != null)
            {
                foreach (var sequence in newValue.Parameters.StopSequences)
                {
                    StopSequences.Add(new StopSequence(sequence));
                }
            }

            InitialiseSelectedItemForPicker();
        }

        public void InitialiseSelectedItemForPicker()
        {
                        // Update the SelectedDatasetName
                        if (Config.RagSettings != null && 
                            !string.IsNullOrEmpty(Config.RagSettings.DatasetName))
                        {
                            SelectedDatasetName = Config.RagSettings.DatasetName;
                        }
                        else
                        {
                            SelectedDatasetName = null;
                        }

            if (Config.PipelineConfig != null)
            {
                SelectedPipelineConfigSrcLang = LanguagesList.FirstOrDefault(x => x.ShortForm == Config.PipelineConfig.SrcLang);
                SelectedPipelineConfigTgtLang = LanguagesList.FirstOrDefault(x => x.ShortForm == Config.PipelineConfig.TgtLang);
                if (Config.PipelineConfig.GenerateKwargs != null)
                {
                    SelectedGenerateKwargsLanguage = LanguagesList.FirstOrDefault(x => x.ShortForm == Config.PipelineConfig.GenerateKwargs.Language);
                }
            }

            if (Config.TranslationConfig != null)
            {
                SelectedTranslationConfigSrcLang = LanguagesList.FirstOrDefault(x => x.ShortForm == Config.TranslationConfig.SrcLang);
                SelectedTranslationConfigTgtLang = LanguagesList.FirstOrDefault(x => x.ShortForm == Config.TranslationConfig.TgtLang);
                SelectedTransationConfigTargetLanguage = LanguagesList.FirstOrDefault(x => x.ShortForm == Config.TranslationConfig.TargetLanguage);
                Debug.WriteLine($"target language = {SelectedTransationConfigTargetLanguage?.FullForm}");
            }
        }
    }

    public partial class CandidateLabel : ObservableObject
    {
        [ObservableProperty]
        private string value;

        public CandidateLabel(string value)
        {
            Value = value;
        }
    }

    public partial class StopSequence : ObservableObject
    {
        [ObservableProperty]
        private string value;

        public StopSequence(string value)
        {
            Value = value;
        }
    }

    public partial class Language : ObservableObject
    {
        [ObservableProperty]
        private string? fullForm;

        [ObservableProperty]
        private string? shortForm;
    }
}