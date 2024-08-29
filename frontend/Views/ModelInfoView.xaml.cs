using System;
using System.Threading.Tasks;
using System.Collections.Generic;
using frontend.Models;
using frontend.Services;
using Microsoft.Maui.Controls;
using System.Diagnostics;

namespace frontend.Views
{
    public partial class ModelInfoView : ContentView
    {
        private Model _model;
        private ModelService _modelService;
        private bool _isUpdatingHardwareUsage = true;

        public ModelInfoView()
        {
            InitializeComponent();
            _modelService = new ModelService();
            Debug.WriteLine("ModelInfoView constructor called");
        }

        protected override void OnBindingContextChanged()
        {
            base.OnBindingContextChanged();
            _model = BindingContext as Model;
            Debug.WriteLine($"OnBindingContextChanged called. Model: {_model?.ModelId ?? "null"}");
            if (_model != null)
            {
                _isUpdatingHardwareUsage = true;
                Task.Run(UpdateHardwareUsageAsync);
            }
            else
            {
                _isUpdatingHardwareUsage = false;
            }
        }

        private async Task UpdateHardwareUsageAsync()
        {
            Debug.WriteLine("UpdateHardwareUsageAsync started");
            while (_isUpdatingHardwareUsage)
            {
                try
                {
                    Debug.WriteLine($"Fetching hardware usage for model: {_model.ModelId}");
                    var usage = await _modelService.GetModelHardwareUsage(_model.ModelId);
                    Debug.WriteLine($"Hardware usage received: {string.Join(", ", usage)}");

                    MainThread.BeginInvokeOnMainThread(() =>
                    {
                        UpdateUsageLabels(usage);
                    });
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"Error updating hardware usage: {ex.Message}");
                    Debug.WriteLine($"Stack trace: {ex.StackTrace}");
                    await Task.Delay(10000); // Wait 10 seconds before retrying
                }

                await Task.Delay(5000); // Update every 5 seconds
            }
            Debug.WriteLine("UpdateHardwareUsageAsync ended");
        }

        private void UpdateUsageLabels(Dictionary<string, object> usage)
        {
            try
            {
                CpuUsageLabel.Text = $"CPU Usage: {usage["cpu_percent"]}%";
                MemoryUsageLabel.Text = $"Memory Usage: {usage["memory_used_mb"]} MB ({usage["memory_percent"]}%)";

                if (usage["gpu_memory_used_mb"] != null)
                {
                    GpuUsageLabel.Text = $"GPU Memory Usage: {usage["gpu_memory_used_mb"]} MB ({usage["gpu_memory_percent"]}%)";
                    GpuUsageLabel.IsVisible = true;
                }
                else
                {
                    GpuUsageLabel.IsVisible = false;
                }
                Debug.WriteLine("Usage labels updated successfully");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error updating usage labels: {ex.Message}");
            }
        }

        public void StopUpdatingHardwareUsage()
        {
            _isUpdatingHardwareUsage = false;
            Debug.WriteLine("StopUpdatingHardwareUsage called");
        }
    }
}