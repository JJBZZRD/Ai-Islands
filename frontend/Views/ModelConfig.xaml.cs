using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;
using frontend.Models;
using System.Text.Json;
using frontend.Services;
using Microsoft.Maui.Graphics;
using System.Reflection;
using frontend.Models.ViewModels;

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
            _configViewModel = new ConfigViewModel { Config = model.Config};
            _modelService = new ModelService();
            ModelIdLabel.Text = $"Model: {_model.ModelId}";
            BindingContext = _configViewModel; // Set the BindingContext
        }

        private async void OnSaveConfigClicked(object sender, EventArgs e)
        {
            // Update the _model's Config with the current ConfigViewModel's Config
            _model.Config = _configViewModel.Config;
            await _modelService.ConfigureModel(_model.ModelId, _model.Config);
        }
    }
}