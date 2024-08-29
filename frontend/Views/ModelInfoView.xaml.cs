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
                    Debug.WriteLine($"Checking if model is loaded: {_model.ModelId}");
                    bool isLoaded = await _modelService.IsModelLoaded(_model.ModelId);
                    
                    if (isLoaded)
                    {
                        Debug.WriteLine($"Fetching hardware usage for model: {_model.ModelId}");
                        var usage = await _modelService.GetModelHardwareUsage(_model.ModelId);
                        Debug.WriteLine($"Hardware usage received: {string.Join(", ", usage)}");

                        MainThread.BeginInvokeOnMainThread(() =>
                        {
                            UpdateUsageLabels(usage);
                        });
                    }
                    else
                    {
                        Debug.WriteLine($"Model {_model.ModelId} is not loaded. Skipping hardware usage update.");
                        MainThread.BeginInvokeOnMainThread(() =>
                        {
                            ResetUsageLabels();
                        });
                    }
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"Error updating hardware usage: {ex.Message}");
                    Debug.WriteLine($"Stack trace: {ex.StackTrace}");
                }

                await Task.Delay(5000); // Update every 5 seconds
            }
            Debug.WriteLine("UpdateHardwareUsageAsync ended");
        }

        private void ResetUsageLabels()
        {
            UpdateUsageBar(CpuUsageBar, CpuUsageLabel, "CPU", 0);
            UpdateUsageBar(MemoryUsageBar, MemoryUsageLabel, "Memory", 0);
            GpuUsageStack.IsVisible = false;
        }

        private void UpdateUsageLabels(Dictionary<string, object> usage)
        {
            try
            {
                UpdateUsageBar(CpuUsageBar, CpuUsageLabel, "CPU", usage["cpu_percent"]);
                UpdateUsageBar(MemoryUsageBar, MemoryUsageLabel, "Memory", usage["memory_percent"], $"{usage["memory_used_mb"]} MB");

                if (usage["gpu_memory_used_mb"] != null)
                {
                    UpdateUsageBar(GpuUsageBar, GpuUsageLabel, "GPU Memory", usage["gpu_memory_percent"], $"{usage["gpu_memory_used_mb"]} MB");
                    GpuUsageStack.IsVisible = true;
                }
                else
                {
                    GpuUsageStack.IsVisible = false;
                }
                Debug.WriteLine("Usage bars updated successfully");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error updating usage bars: {ex.Message}");
            }
        }

        private void UpdateUsageBar(ProgressBar bar, Label label, string resourceName, object percentValue, string additionalInfo = null)
        {
            if (double.TryParse(percentValue.ToString(), out double percent))
            {
                bar.Progress = percent / 100;
                label.Text = additionalInfo != null
                    ? $"{resourceName}: {percent:F1}% ({additionalInfo})"
                    : $"{resourceName}: {percent:F1}%";
            }
            else
            {
                bar.Progress = 0;
                label.Text = $"{resourceName}: N/A";
            }
        }

        public void StopUpdatingHardwareUsage()
        {
            _isUpdatingHardwareUsage = false;
            Debug.WriteLine("StopUpdatingHardwareUsage called");
        }
    }
}