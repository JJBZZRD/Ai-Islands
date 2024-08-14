using System;
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
        public ObservableCollection<string> CandidateLabels { get; }

        public ConfigViewModel()
        {
            ExampleConversation = new ObservableCollection<ConversationMessage>();
            CandidateLabels = new ObservableCollection<string>();

            if (config?.ExampleConversation != null)
            {
                foreach (var message in config.ExampleConversation)
                {
                    ExampleConversation.Add(new ConversationMessage { Role = message.Role, Content = message.Content });
                }
            }

            if (config?.PipelineConfig?.CandidateLabels != null)
            {
                foreach (var label in config.PipelineConfig.CandidateLabels)
                {
                    CandidateLabels.Add(label);
                }
            }
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
                    CandidateLabels.Add(label);
                }
            }
        }
    }
}