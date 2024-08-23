using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.Generic;
using frontend.Converters;
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
        public Dictionary<string, string> LanguagesDict { get; set; } = new Dictionary<string, string>();
        public List<string> LanguagesList { get; }

        [ObservableProperty]
        private List<string> datasetNames;

        [ObservableProperty]
        private string selectedDatasetName;

        [ObservableProperty]
        private string selectedPipelineConfigSrcLang;

        [ObservableProperty]
        private string selectedPipelineConfigTgtLang;

        [ObservableProperty]
        private string selectedTranslationConfigSrcLang;

        [ObservableProperty]
        private string selectedTranslationConfigTgtLang;

        [ObservableProperty]
        private string selectedTransationConfigTargetLanguage;

        [ObservableProperty]
        private string selectedGenerateKwargsLanguage;

        public ConfigViewModel(Dictionary<string, string> languagesDict)
        {
            LanguagesDict = languagesDict;
            LanguagesList = LanguagesDict.Keys.ToList();

            ExampleConversation = new ObservableCollection<ConversationMessage>();
            CandidateLabels = new ObservableCollection<CandidateLabel>();
            StopSequences = new ObservableCollection<StopSequence>();
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
        }

        public void InitialiseSelectedItemForPicker()
        {
            if (Config.RagSettings != null)
            {
                SelectedDatasetName = Config.RagSettings.DatasetName;
            }

            if (Config.PipelineConfig != null)
            {
                SelectedPipelineConfigSrcLang = LanguagesDict.FirstOrDefault(x => x.Value == Config.PipelineConfig.SrcLang).Key;
                SelectedPipelineConfigTgtLang = LanguagesDict.FirstOrDefault(x => x.Value == Config.PipelineConfig.TgtLang).Key;
                SelectedGenerateKwargsLanguage = LanguagesDict.FirstOrDefault(x => x.Value == Config.PipelineConfig.GenerateKwargs.Language).Key;
            }

            if (Config.TranslationConfig != null)
            {
                SelectedTranslationConfigSrcLang = LanguagesDict.FirstOrDefault(x => x.Value == Config.TranslationConfig.SrcLang).Key;
                SelectedTranslationConfigTgtLang = LanguagesDict.FirstOrDefault(x => x.Value == Config.TranslationConfig.TgtLang).Key;
                SelectedTransationConfigTargetLanguage = LanguagesDict.FirstOrDefault(x => x.Value == Config.TranslationConfig.TargetLanguage).Key;
                Debug.WriteLine($"target language = {SelectedTransationConfigTargetLanguage}");
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
}