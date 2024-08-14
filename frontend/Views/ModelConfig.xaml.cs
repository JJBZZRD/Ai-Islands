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
        private DataService _dataService;

        public ModelConfig(Model model)
        {
            InitializeComponent();
            _model = model;
            _configViewModel = new ConfigViewModel { Config = model.Config };
            _modelService = new ModelService();
            _dataService = new DataService();
            ModelIdLabel.Text = $"Model: {_model.ModelId}";
            Debug.WriteLine("===============watch me==============");
            Debug.WriteLine(_configViewModel.Config.ExampleConversation == null);
            if (_configViewModel.Config.PipelineConfig != null)
            {
                Debug.WriteLine(_configViewModel.Config.PipelineConfig.CandidateLabels == null);
            }
            if (_configViewModel.Config.Parameters != null)
            {   
            Debug.WriteLine(_configViewModel.Config.Parameters.StopSequences == null);
            }
            BindingContext = _configViewModel; // Set the BindingContext

            LoadDatasetNames();
        }

        private async void LoadDatasetNames()
        {
            try
            {
                var datasetNames = await _dataService.ListDatasetsNames();
                _configViewModel.DatasetNames = new List<string>(datasetNames);

                // Set the selected dataset name after populating the list
                if (_configViewModel.Config.RagSettings != null && 
                    !string.IsNullOrEmpty(_configViewModel.Config.RagSettings.DatasetName) &&
                    datasetNames.Contains(_configViewModel.Config.RagSettings.DatasetName))
                {
                    _configViewModel.SelectedDatasetName = _configViewModel.Config.RagSettings.DatasetName;
                }

                // Manually trigger UI update
                OnPropertyChanged(nameof(_configViewModel.SelectedDatasetName));
            }
            catch (Exception ex)
            {
                // Handle any errors, e.g., show an alert to the user
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to load dataset names: {ex.Message}", "OK");
            }
        }

        private async void OnSaveConfigClicked(object sender, EventArgs e)
        {

            // Update the _model's Config with the current ConfigViewModel's Config
            if (_configViewModel.ExampleConversation.Count != 0)
            {
                _configViewModel.Config.ExampleConversation = _configViewModel.ExampleConversation.ToList();
            }
            if (_configViewModel.CandidateLabels.Count != 0)
            {
                _configViewModel.Config.PipelineConfig.CandidateLabels = _configViewModel.CandidateLabels.Select(cl => cl.Value).ToList();
            }
            if (_configViewModel.StopSequences.Count != 0)
            {
                _configViewModel.Config.Parameters.StopSequences = _configViewModel.StopSequences.Select(ss => ss.Value).ToList();
            }
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
            _configViewModel.CandidateLabels.Add(new CandidateLabel(newLabel));

            // Clear the input field
            NewCandidateLabel.Text = string.Empty;
        }

        private void OnDeleteCandidateLabelClicked(object sender, EventArgs e)
        {
            var button = sender as Button;
            var label = button?.BindingContext as CandidateLabel;

            if (label != null)
            {
                _configViewModel.CandidateLabels.Remove(label);
            }
        }

        private void OnAddStopSequenceClicked(object sender, EventArgs e)
        {
            // Get the new stop sequence from the UI
            string newStopSequence = NewStopSequence.Text;

            // Validate input
            if (string.IsNullOrWhiteSpace(newStopSequence))
            {
                // Show an error message or handle the validation as needed
                return;
            }

            // Add the new stop sequence to the ObservableCollection
            _configViewModel.StopSequences.Add(new StopSequence(newStopSequence));

            // Clear the input field
            NewStopSequence.Text = string.Empty;
        }

        private void OnDeleteStopSequenceClicked(object sender, EventArgs e)
        {
            var button = sender as Button;
            var stopSequence = button?.BindingContext as StopSequence;

            if (stopSequence != null)
            {
                _configViewModel.StopSequences.Remove(stopSequence);
            }
        }
    }
}