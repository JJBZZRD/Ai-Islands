using System;
using System.Threading.Tasks;
using System.Collections.Generic;
using frontend.Models;
using frontend.Services;
using Microsoft.Maui.Controls;
using System.Diagnostics;

namespace frontend.Views
{
    public partial class ModelInfoView : ContentView, IDisposable
    {
        private Model _model;
        private ModelService _modelService;
        private bool _isUpdatingHardwareUsage = false;
        private CancellationTokenSource _cts;

        public ModelInfoView()
        {
            InitializeComponent();
            _modelService = new ModelService();
            _cts = new CancellationTokenSource();
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
            while (_isUpdatingHardwareUsage && !_cts.Token.IsCancellationRequested)
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

                try
                {
                    await Task.Delay(5000, _cts.Token); // Update every 5 seconds
                }
                catch (TaskCanceledException)
                {
                    // Task was canceled, exit the loop
                    break;
                }
            }
            Debug.WriteLine("UpdateHardwareUsageAsync ended");
        }

        private void ResetUsageLabels()
        {
            UpdateUsageBar(CpuUsageBar, CpuUsageLabel, "CPU", 0);
            UpdateUsageBar(MemoryUsageBar, MemoryUsageLabel, "Memory", 0);
            GpuFrame.IsVisible = false;
        }

        private void UpdateUsageLabels(Dictionary<string, object> usage)
        {
            try
            {
                Debug.WriteLine($"Updating usage labels with data: {string.Join(", ", usage.Select(kvp => $"{kvp.Key}: {kvp.Value}"))}");

                UpdateUsageBar(CpuUsageBar, CpuUsageLabel, "CPU Utilisation", usage["cpu_percent"]);
                UpdateUsageBar(MemoryUsageBar, MemoryUsageLabel, "Memory", usage["memory_percent"], $"{usage["memory_used_mb"]} MB");

                bool showGpuFrame = false;

                Debug.WriteLine($"GPU Utilisation: {usage["gpu_utilization_percent"]}");
                if (usage["gpu_utilization_percent"] != null)
                {
                    UpdateUsageBar(GpuUtilisationBar, GpuUtilisationLabel, "GPU Utilisation", usage["gpu_utilization_percent"]);
                    showGpuFrame = true;
                    Debug.WriteLine("GPU Utilisation updated");
                }

                Debug.WriteLine($"GPU Memory Used: {usage["gpu_memory_used_mb"]}");
                if (usage["gpu_memory_used_mb"] != null)
                {
                    UpdateUsageBar(GpuUsageBar, GpuUsageLabel, "GPU Memory", usage["gpu_memory_percent"], $"{usage["gpu_memory_used_mb"]} MB");
                    showGpuFrame = true;
                    Debug.WriteLine("GPU Memory Usage updated");
                }

                GpuFrame.IsVisible = showGpuFrame;
                Debug.WriteLine($"GPU Frame visibility set to: {showGpuFrame}");

                Debug.WriteLine("Usage bars updated successfully");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error updating usage bars: {ex.Message}");
                Debug.WriteLine($"Stack trace: {ex.StackTrace}");
            }
        }

        private void UpdateUsageBar(ProgressBar bar, Label label, string resourceName, object percentValue, string additionalInfo = null)
        {
            Debug.WriteLine($"Updating {resourceName} bar with value: {percentValue}");
            if (double.TryParse(percentValue?.ToString(), out double percent))
            {
                bar.Progress = percent / 100;
                label.Text = additionalInfo != null
                    ? $"{resourceName}: {percent:F1}% ({additionalInfo})"
                    : $"{resourceName}: {percent:F1}%";
                Debug.WriteLine($"{resourceName} bar updated: Progress = {bar.Progress}, Label = {label.Text}");
            }
            else
            {
                bar.Progress = 0;
                label.Text = $"{resourceName}: N/A";
                Debug.WriteLine($"{resourceName} bar reset due to invalid value");
            }
        }

        public void Dispose()
        {
            _isUpdatingHardwareUsage = false;
            _cts.Cancel();
            _cts.Dispose();
        }
    }
}