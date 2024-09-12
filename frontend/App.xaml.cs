using Microsoft.Maui.Controls;
using Microsoft.Maui.Controls.Xaml;
using frontend.Views;
using System;
using System.Threading.Tasks;
using frontend.Services;
using static OpenCvSharp.ML.LogisticRegression;
using System.Security.Claims;

// Part of the code to check for active models before closing the app
// using frontend.Services;
// using System.Text.Json;

namespace frontend
{
    public partial class App : Application
    {
        private readonly PlaygroundService _playgroundService;
        private readonly List<string> _loadedChains;
        private List<PlaygroundInferenceView> _activeViews;
        public App()
        {
            InitializeComponent();
            // this.UserAppTheme = AppTheme.Light;
            _activeViews = new List<PlaygroundInferenceView>();
            Routing.RegisterRoute(nameof(ModelInfoPage), typeof(ModelInfoPage));
            MainPage = new AppShell();

            // Initialize PlaygroundService and list to track loaded chains
            _playgroundService = new PlaygroundService();
            _loadedChains = new List<string>();

            // add global exception handling
            AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;
            TaskScheduler.UnobservedTaskException += TaskScheduler_UnobservedTaskException;
        }

        private void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            System.Diagnostics.Debug.WriteLine($"Unhandled Exception: {e.ExceptionObject}");
        }

        private void TaskScheduler_UnobservedTaskException(object? sender, UnobservedTaskExceptionEventArgs e)
        {
            System.Diagnostics.Debug.WriteLine($"Unobserved Task Exception: {e.Exception}");
            e.SetObserved();
        }

        protected override Window CreateWindow(IActivationState activationState)
        {
            Window window = base.CreateWindow(activationState);
            window.Destroying += Window_Destroying;
            return window;
        }

        public void RegisterView(PlaygroundInferenceView view)
        {
            _activeViews.Add(view);
        }

        public void UnregisterView(PlaygroundInferenceView view)
        {
            _activeViews.Remove(view);
        }

        private async void Window_Destroying(object sender, EventArgs e)
        {
            System.Diagnostics.Debug.WriteLine("Window is closing. Attempting to stop all loaded chains.");
            await StopAllLoadedChainsAsync();
            System.Diagnostics.Debug.WriteLine("All chains stopped. Updating UI state.");
            foreach (var view in _activeViews)
            {
                view.IsChainLoaded = false; // Set state to reflect that chains are stopped
                view.UpdateOutputVisibility(); // Update UI elements
            }
        }


        private async Task StopAllLoadedChainsAsync()
        {
            try
            {
                foreach (var chainId in _loadedChains)
                {
                    await _playgroundService.StopPlaygroundChain(chainId);
                    System.Diagnostics.Debug.WriteLine($"Stopped chain: {chainId}");

                    // Update preferences to reflect the chain is no longer loaded
                    Preferences.Set($"{chainId}_isChainLoaded", false);
                    System.Diagnostics.Debug.WriteLine($"Preference set for chain {chainId}: false");
                }

                _loadedChains.Clear();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error stopping chains on app close: {ex.Message}");
            }
        }

        public void AddLoadedChain(string chainId)
        {
            if (!_loadedChains.Contains(chainId))
            {
                _loadedChains.Add(chainId);
            }
        }

        public void RemoveLoadedChain(string chainId)
        {
            if (_loadedChains.Contains(chainId))
            {
                _loadedChains.Remove(chainId);
            }
        }


        // CHECK FOR LOADED MODELS BEFORE CLOSING APP - future work needs to look at list active models in endpoint file for this to work!
        // protected override Window CreateWindow(IActivationState activationState)
        // {
        //     Window window = base.CreateWindow(activationState);

        //     window.Destroying += Window_Destroying;

        //     return window;
        // }

        // private async void Window_Destroying(object sender, EventArgs e)
        // {
        //     try
        //     {
        //         var modelService = new ModelService();
        //         List<string> activeModels;

        //         try
        //         {
        //             activeModels = await modelService.ListActiveModels();
        //             System.Diagnostics.Debug.WriteLine($"Active models: {string.Join(", ", activeModels)}");
        //         }
        //         catch (Exception ex)
        //         {
        //             System.Diagnostics.Debug.WriteLine($"Error listing active models: {ex.Message}");
        //             return;
        //         }

        //         if (activeModels.Count > 0)
        //         {
        //             bool unloadModels = await Current.MainPage.DisplayAlert(
        //                 "Models Still Loaded",
        //                 $"There are still {activeModels.Count} model(s) loaded in memory. Do you want to unload them before quitting?",
        //                 "Unload and Quit", "Quit Without Unloading");

        //             if (unloadModels)
        //             {
        //                 await UnloadAllModels(modelService, activeModels);
        //             }
        //         }
        //     }
        //     catch (Exception ex)
        //     {
        //         System.Diagnostics.Debug.WriteLine($"Error during window destruction: {ex.Message}");
        //     }
        // }

        // private async Task UnloadAllModels(ModelService modelService, List<string> modelsToUnload)
        // {
        //     foreach (var modelId in modelsToUnload)
        //     {
        //         try
        //         {
        //             await modelService.UnloadModel(modelId);
        //             System.Diagnostics.Debug.WriteLine($"Successfully unloaded model: {modelId}");
        //         }
        //         catch (Exception ex)
        //         {
        //             System.Diagnostics.Debug.WriteLine($"Error unloading model {modelId}: {ex.Message}");
        //         }
        //     }
        // }
    }
}