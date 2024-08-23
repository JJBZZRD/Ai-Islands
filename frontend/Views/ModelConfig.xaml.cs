using frontend.Models;
using System.Text.Json;
using frontend.Services;
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
        private bool _isExampleConversationNull;
        private bool _isCandidateLabelsNull;
        private bool _isStopSequencesNull;

        private DataService _dataService;

        // Add these fields at the class level
        private bool _areExpandersExpanded = false;
        private List<BindableObject> _expanders;

        public ModelConfig(Model model)
        {
            InitializeComponent();
            _model = model;
            _configViewModel = new ConfigViewModel
            {
                Config = model.Config,
            };

            if (_model.Languages != null)
            {
                foreach (var lang in _model.Languages)
                {
                    _configViewModel.LanguagesList.Add(new Language { FullForm = lang.Key, ShortForm = lang.Value });
                }
            }

            BindingContext = _configViewModel;

            _isExampleConversationNull = _configViewModel.Config.ExampleConversation == null;
            _isCandidateLabelsNull = _configViewModel.Config.PipelineConfig == null || _configViewModel.Config.PipelineConfig.CandidateLabels == null;
            _isStopSequencesNull = _configViewModel.Config.Parameters == null || _configViewModel.Config.Parameters.StopSequences == null;
            _modelService = new ModelService();
            _dataService = new DataService();


            ModelIdLabel.Text = $"Model: {_model.ModelId}";
            Debug.WriteLine("===============watch me==============");
            Debug.WriteLine(_isExampleConversationNull);
            Debug.WriteLine(_isCandidateLabelsNull);
            Debug.WriteLine(_isStopSequencesNull);

            LoadDatasetNames();

            // Find all Expanders in the view
            _expanders = FindExpanders(this);

            InitializeAsync();
        }

        private async Task InitializeAsync()
        {
            // dealy 500ms to make sure the picker is loaded
            // the delay time might have to be longer, depending on the time taken to load the picker
            await Task.Delay(500);
            _configViewModel.InitialiseSelectedItemForPicker();
        }

        private async Task LoadDatasetNames()
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
            }
            catch (Exception ex)
            {
                // Handle any errors, e.g., show an alert to the user
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to load dataset names: {ex.Message}", "OK");
            }
        }

        private async void OnSaveConfigClicked(object sender, EventArgs e)
        {
            // Disable the button to prevent multiple clicks
            SaveConfigButton.IsEnabled = false;

            try
            {
                // Update the _model's Config with the current ConfigViewModel's Config
                UpdateModelConfig();

                await _modelService.ConfigureModel(_model.ModelId, _model.Config);

                // Show success popup
                await Application.Current.MainPage.DisplayAlert("Success", "Configuration saved successfully!", "OK");
            }
            catch (Exception ex)
            {
                // Show error popup if something goes wrong
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save configuration: {ex.Message}", "OK");
            }
            finally
            {
                // Re-enable the button
                SaveConfigButton.IsEnabled = true;
            }
        }

        private void UpdateModelConfig()
        {
            if (_configViewModel.ExampleConversation.Count != 0 && !_isExampleConversationNull)
            {
                _configViewModel.Config.ExampleConversation = _configViewModel.ExampleConversation.ToList();
            }
            else if (_configViewModel.ExampleConversation.Count == 0 && !_isExampleConversationNull)
            {
                _configViewModel.Config.ExampleConversation = new List<ConversationMessage>();
            }
            if (_configViewModel.CandidateLabels.Count != 0 && !_isCandidateLabelsNull)
            {
                _configViewModel.Config.PipelineConfig.CandidateLabels = _configViewModel.CandidateLabels.Select(cl => cl.Value).ToList();
            }
            else if (_configViewModel.CandidateLabels.Count == 0 && !_isCandidateLabelsNull)
            {
                _configViewModel.Config.PipelineConfig.CandidateLabels = new List<string>();
            }
            if (_configViewModel.StopSequences.Count != 0 && !_isStopSequencesNull)
            {
                _configViewModel.Config.Parameters.StopSequences = _configViewModel.StopSequences.Select(ss => ss.Value).ToList();
            }
            else if (_configViewModel.StopSequences.Count == 0 && !_isStopSequencesNull)
            {
                _configViewModel.Config.Parameters.StopSequences = new List<string>();
            }

            if (_configViewModel.SelectedDatasetName != null)
            {
                _configViewModel.Config.RagSettings.DatasetName = _configViewModel.SelectedDatasetName;
            }

            if (_configViewModel.SelectedPipelineConfigSrcLang != null)
            {
                _configViewModel.Config.PipelineConfig.SrcLang = _configViewModel.SelectedPipelineConfigSrcLang.ShortForm;
            }

            if (_configViewModel.SelectedPipelineConfigTgtLang != null)
            {
                _configViewModel.Config.PipelineConfig.TgtLang = _configViewModel.SelectedPipelineConfigTgtLang.ShortForm;
            }

            if (_configViewModel.SelectedTranslationConfigSrcLang != null)
            {
                _configViewModel.Config.TranslationConfig.SrcLang = _configViewModel.SelectedTranslationConfigSrcLang.ShortForm;
            }

            if (_configViewModel.SelectedTranslationConfigTgtLang != null)
            {
                _configViewModel.Config.TranslationConfig.TgtLang = _configViewModel.SelectedTranslationConfigTgtLang.ShortForm;
            }

            if (_configViewModel.SelectedTransationConfigTargetLanguage != null)
            {
                _configViewModel.Config.TranslationConfig.TargetLanguage = _configViewModel.SelectedTransationConfigTargetLanguage.ShortForm;
            }

            if (_configViewModel.SelectedGenerateKwargsLanguage != null)
            {
                _configViewModel.Config.PipelineConfig.GenerateKwargs.Language = _configViewModel.SelectedGenerateKwargsLanguage.ShortForm;
            }

            _model.Config = _configViewModel.Config;
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
        private void OnRandomSeedTextChanged(object sender, TextChangedEventArgs e)
        {
            if (sender is Entry entry)
            {
                if (int.TryParse(e.NewTextValue, out int result))
                {
                    if (result >= 0 && result <= 2147483647)
                    {
                        entry.TextColor = Colors.Black;
                    }
                    else
                    {
                        entry.TextColor = Colors.Red;
                    }
                }
                else if (!string.IsNullOrEmpty(e.NewTextValue))
                {
                    entry.TextColor = Colors.Red;
                }
                else
                {
                    entry.TextColor = Colors.Black;
                }
            }
        }

        // Add these new methods
        private void OnToggleExpandersClicked(object sender, EventArgs e)
        {
            _areExpandersExpanded = !_areExpandersExpanded;
            foreach (var expander in _expanders)
            {
                if (expander.GetType().GetProperty("IsExpanded") is PropertyInfo prop)
                {
                    prop.SetValue(expander, _areExpandersExpanded);
                }
            }
            ToggleExpandersButton.Text = _areExpandersExpanded ? "Collapse All" : "Expand All";
        }

        private List<BindableObject> FindExpanders(Element element)
        {
            var expanders = new List<BindableObject>();

            if (element.GetType().Name == "Expander")
            {
                expanders.Add((BindableObject)element);
            }

            foreach (var child in element.LogicalChildren)
            {
                if (child is Element childElement)
                {
                    expanders.AddRange(FindExpanders(childElement));
                }
            }

            return expanders;
        }

        // Add this method to the ModelConfig class
        private async void OnResetDefaultsClicked(object sender, EventArgs e)
        {
            // Disable the button to prevent multiple clicks
            ResetDefaultsButton.IsEnabled = false;

            try
            {
                // Show confirmation popup
                bool shouldRestore = await Application.Current.MainPage.DisplayAlert(
                    "Warning",
                    "Are you sure you want to restore default configurations from library?",
                    "Restore",
                    "Abort");

                if (shouldRestore)
                {
                    await _modelService.ResetDefaultConfig(_model.ModelId);

                    // Show success popup
                    await Application.Current.MainPage.DisplayAlert("Success", "Configuration reset to defaults successfully!", "OK");

                    // Fetch the updated library data
                    var libraryService = new LibraryService();
                    var updatedModels = await libraryService.GetLibrary();

                    // Find the updated model in the list
                    var updatedModel = updatedModels.FirstOrDefault(m => m.ModelId == _model.ModelId);

                    if (updatedModel != null)
                    {
                        // Update the local model
                        _model = updatedModel;

                        // Create a new ConfigViewModel with the updated data
                        _configViewModel = new ConfigViewModel
                        {
                            Config = _model.Config,
                        };

                        // Reinitialize other properties
                        _isExampleConversationNull = _configViewModel.Config.ExampleConversation == null;
                        _isCandidateLabelsNull = _configViewModel.Config.PipelineConfig == null || _configViewModel.Config.PipelineConfig.CandidateLabels == null;
                        _isStopSequencesNull = _configViewModel.Config.Parameters == null || _configViewModel.Config.Parameters.StopSequences == null;

                        // Reload the dataset names
                        await LoadDatasetNames();

                        _configViewModel.LanguagesList.Clear();
                        if (_model.Languages != null)
                        {
                            foreach (var lang in _model.Languages)
                            {
                                _configViewModel.LanguagesList.Add(new Language { FullForm = lang.Key, ShortForm = lang.Value });
                            }
                        }
                        // Update the BindingContext to refresh the UI
                        BindingContext = _configViewModel;

                        await InitializeAsync();
                    }
                    else
                    {
                        await Application.Current.MainPage.DisplayAlert("Error", "Failed to find updated model data", "OK");
                    }
                }
            }
            catch (Exception ex)
            {
                // Show error popup if something goes wrong
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to reset configuration: {ex.Message}", "OK");
            }
            finally
            {
                // Re-enable the button
                ResetDefaultsButton.IsEnabled = true;
            }
        }

        private async void OnSaveAsNewModelClicked(object sender, EventArgs e)
        {
            // Disable the button to prevent multiple clicks
            SaveAsNewModelButton.IsEnabled = false;

            try
            {
                // Prompt the user for a new model name
                string newModelId = await Application.Current.MainPage.DisplayPromptAsync(
                    "Save As New Model",
                    "Enter a name for the new model:",
                    "Save",
                    "Cancel",
                    "New Model Name");

                if (string.IsNullOrWhiteSpace(newModelId))
                {
                    // User cancelled or didn't enter a name
                    return;
                }

                // Update the _model's Config with the current ConfigViewModel's Config
                UpdateModelConfig();

                // Create a new LibraryService instance
                var libraryService = new LibraryService();

                // Convert Config to Dictionary<string, object>
                var configDict = JsonSerializer.Deserialize<Dictionary<string, object>>(JsonSerializer.Serialize(_model.Config));

                // Call the SaveNewModel method
                var result = await libraryService.SaveNewModel(_model.ModelId, newModelId, configDict);

                // Show success popup
                await Application.Current.MainPage.DisplayAlert("Success", $"New model '{newModelId}' saved successfully!", "OK");

                // Ask user if they want to go to the Library page or stay on the current page
                bool goToLibrary = await Application.Current.MainPage.DisplayAlert(
                    "Navigation",
                    "Do you want to go to the Library page?",
                    "Yes, go to Library",
                    "No, stay here");

                if (goToLibrary)
                {
                    // Navigate to Library page
                    // await Shell.Current.GoToAsync("//Library");
                    // Use the existing navigation stack to go back to the Library page
                    await Navigation.PopToRootAsync();
                }
                else
                {
                    // Refresh the current page with the original model's data
                    await RefreshModelConfig();
                }
            }
            catch (Exception ex)
            {
                // Show error popup if something goes wrong
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to save new model: {ex.Message}", "OK");
            }
            finally
            {
                // Re-enable the button
                SaveAsNewModelButton.IsEnabled = true;
            }
        }

        private async Task RefreshModelConfig()
        {
            try
            {
                var libraryService = new LibraryService();
                var updatedModels = await libraryService.GetLibrary();
                var updatedModel = updatedModels.FirstOrDefault(m => m.ModelId == _model.ModelId);

                if (updatedModel != null)
                {
                    _model = updatedModel;
                    _configViewModel = new ConfigViewModel
                    {
                        Config = _model.Config,
                    };

                    _isExampleConversationNull = _configViewModel.Config.ExampleConversation == null;
                    _isCandidateLabelsNull = _configViewModel.Config.PipelineConfig == null || _configViewModel.Config.PipelineConfig.CandidateLabels == null;
                    _isStopSequencesNull = _configViewModel.Config.Parameters == null || _configViewModel.Config.Parameters.StopSequences == null;

                    _configViewModel.LanguagesList.Clear();
                    if (_model.Languages != null)
                    {
                        foreach (var lang in _model.Languages)
                        {
                            _configViewModel.LanguagesList.Add(new Language { FullForm = lang.Key, ShortForm = lang.Value });
                        }
                    }
                    // Update the SelectedDatasetName from the library data
                    _configViewModel.SelectedDatasetName = _configViewModel.Config.RagSettings?.DatasetName;

                    // Reload the dataset names
                    await LoadDatasetNames();
                    
                    BindingContext = _configViewModel;
                    InitializeAsync();

                }
                else
                {
                    await Application.Current.MainPage.DisplayAlert("Error", "Failed to find updated model data", "OK");
                }
            }
            catch (Exception ex)
            {
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to refresh configuration: {ex.Message}", "OK");
            }
        }

        // Add this method to the ModelConfig class
        private async void OnResetClicked(object sender, EventArgs e)
        {
            // Disable the button to prevent multiple clicks
            ResetButton.IsEnabled = false;

            try
            {
                // Show warning popup
                bool shouldReset = await Application.Current.MainPage.DisplayAlert(
                    "Warning",
                    "Are you sure you want to discard your changes?",
                    "Yes, discard changes",
                    "No, keep changes");

                if (shouldReset)
                {
                    // Fetch the original model data from the library
                    var libraryService = new LibraryService();
                    var updatedModels = await libraryService.GetLibrary();
                    var originalModel = updatedModels.FirstOrDefault(m => m.ModelId == _model.ModelId);

                    if (originalModel != null)
                    {
                        // Reset the model and ConfigViewModel to the original state
                        _model = originalModel;
                        _configViewModel.Config = _model.Config;

                        _configViewModel.LanguagesList.Clear();
                                                if (_model.Languages != null)
                        {
                        foreach (var lang in _model.Languages)
                        {
                            _configViewModel.LanguagesList.Add(new Language { FullForm = lang.Key, ShortForm = lang.Value });
                        }}

                        // Reinitialize other properties
                        _isExampleConversationNull = _configViewModel.Config.ExampleConversation == null;
                        _isCandidateLabelsNull = _configViewModel.Config.PipelineConfig == null || _configViewModel.Config.PipelineConfig.CandidateLabels == null;
                        _isStopSequencesNull = _configViewModel.Config.Parameters == null || _configViewModel.Config.Parameters.StopSequences == null;

                        // Reset collections
                        _configViewModel.ExampleConversation.Clear();
                        foreach (var message in _configViewModel.Config.ExampleConversation ?? new List<ConversationMessage>())
                        {
                            _configViewModel.ExampleConversation.Add(message);
                        }

                        _configViewModel.CandidateLabels.Clear();
                        foreach (var label in _configViewModel.Config.PipelineConfig?.CandidateLabels ?? new List<string>())
                        {
                            _configViewModel.CandidateLabels.Add(new CandidateLabel(label));
                        }

                        _configViewModel.StopSequences.Clear();
                        foreach (var sequence in _configViewModel.Config.Parameters?.StopSequences ?? new List<string>())
                        {
                            _configViewModel.StopSequences.Add(new StopSequence(sequence));
                        }

                        // Update the BindingContext to refresh the UI
                        BindingContext = _configViewModel;

                        // Show success popup
                        await Application.Current.MainPage.DisplayAlert("Success", "Changes discarded successfully!", "OK");
                    }
                    else
                    {
                        await Application.Current.MainPage.DisplayAlert("Error", "Failed to find original model data", "OK");
                    }
                }
            }
            catch (Exception ex)
            {
                // Show error popup if something goes wrong
                await Application.Current.MainPage.DisplayAlert("Error", $"Failed to reset: {ex.Message}", "OK");
            }
            finally
            {
                // Re-enable the button
                ResetButton.IsEnabled = true;
            }
        }
    }
}