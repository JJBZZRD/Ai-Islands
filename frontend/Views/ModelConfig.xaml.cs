using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.Text.Json;
using frontend.Services;
using Microsoft.Maui.Graphics;
using System.Reflection;
using frontend.Models.ViewModels;
using System.Diagnostics;

namespace frontend.Views
{
    public partial class ModelConfig : ContentView
    {
        private Model _model;
        private ModelService _modelService;
        private ConfigViewModel _configViewModel;
        public ModelConfig(Model model)
        {
            InitializeComponent();
            _model = model;
            _configViewModel = new ConfigViewModel { Config = model.Config };
            _modelService = new ModelService();
            ModelIdLabel.Text = $"Model: {_model.ModelId}";
            Debug.WriteLine("===============watch me==============");
            Debug.WriteLine(_configViewModel.Config.ExampleConversation);
            Debug.WriteLine(_configViewModel.Config.ExampleConversation == null);
            BindingContext = _configViewModel; // Set the BindingContext
        }

        private async void OnSaveConfigClicked(object sender, EventArgs e)
        {
            // Update the _model's Config with the current ConfigViewModel's Config
            _configViewModel.Config.ExampleConversation = _configViewModel.ExampleConversation.ToList();
            _configViewModel.Config.PipelineConfig.CandidateLabels = _configViewModel.CandidateLabels.ToList();
            _model.Config = _configViewModel.Config;
            await _modelService.ConfigureModel(_model.ModelId, _model.Config);
        }

        private void OnAddExampleMessageClicked(object sender, EventArgs e)
        {
            // Get the role and content from the UI
            string role = NewMessageRole.Text;
            string content = NewMessageContent.Text;

            // Validate inputs
            if (string.IsNullOrWhiteSpace(role) || string.IsNullOrWhiteSpace(content))
            {
                // Show an error message or handle the validation as needed
                return;
            }

            // Add the new message to the ObservableCollection
            _configViewModel.ExampleConversation.Add(new ConversationMessage { Role = role, Content = content });

            // Clear the input fields
            NewMessageRole.Text = string.Empty;
            NewMessageContent.Text = string.Empty;
        }

        private void OnDeleteExampleMessageClicked(object sender, EventArgs e)
        {
            var button = sender as Button;
            var message = button?.BindingContext as ConversationMessage;

            if (message != null)
            {
                _configViewModel.ExampleConversation.Remove(message);
            }
        }

        private void OnAddCandidateLabelClicked(object sender, EventArgs e)
        {
            // Get the new label from the UI
            string newLabel = NewCandidateLabel.Text;

            // Validate input
            if (string.IsNullOrWhiteSpace(newLabel))
            {
                // Show an error message or handle the validation as needed
                return;
            }

            // Add the new label to the ObservableCollection
            _configViewModel.CandidateLabels.Add(newLabel);

            // Clear the input field
            NewCandidateLabel.Text = string.Empty;
        }

        private void OnDeleteCandidateLabelClicked(object sender, EventArgs e)
        {
            var button = sender as Button;
            var label = button?.BindingContext as string;

            if (label != null)
            {
                _configViewModel.CandidateLabels.Remove(label);
            }
        }
    }
}