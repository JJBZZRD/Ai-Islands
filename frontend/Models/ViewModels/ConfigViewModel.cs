﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.ObjectModel;

namespace frontend.Models.ViewModels
{
    internal partial class ConfigViewModel : ObservableObject
    {
        [ObservableProperty]
        private Config? config;

        public ObservableCollection<ConversationMessage> ExampleConversation { get; }
        public ObservableCollection<CandidateLabel> CandidateLabels { get; }
        public ObservableCollection<StopSequence> StopSequences { get; }
        public Dictionary<string, string> Languages { get; set; } = new Dictionary<string, string>();

        private List<string> _datasetNames;
        public List<string> DatasetNames
        {
            get => _datasetNames;
            set
            {
                if (_datasetNames != value)
                {
                    _datasetNames = value;
                    OnPropertyChanged(nameof(DatasetNames));
                }
            }
        }

        private string _selectedDatasetName;
        public string SelectedDatasetName
        {
            get => _selectedDatasetName;
            set
            {
                if (_selectedDatasetName != value)
                {
                    _selectedDatasetName = value;
                    if (config?.RagSettings != null)
                    {
                        config.RagSettings.DatasetName = value;
                    }
                    OnPropertyChanged(nameof(SelectedDatasetName));
                }
            }
        }

        public IEnumerable<KeyValuePair<string, string>> LanguageList => Languages?.ToList() ?? new List<KeyValuePair<string, string>>();

        public ConfigViewModel()
        {
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