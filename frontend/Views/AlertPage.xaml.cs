using System;
using System.Threading.Tasks;
using Microsoft.Maui.Controls;
using Microsoft.Maui.Dispatching;

namespace frontend.Views
{
    public partial class AlertPage : ContentPage
    {
        public TaskCompletionSource<bool> CompletionSource { get; private set; }

        public AlertPage(string title, string message, bool showProgressBar = false)
        {
            InitializeComponent();
            TitleLabel.Text = title;
            MessageLabel.Text = message;
            DownloadProgressBar.IsVisible = showProgressBar;
            CompletionSource = new TaskCompletionSource<bool>();
        }

        public void UpdateDownloadProgress(double progress)
        {
            MainThread.BeginInvokeOnMainThread(() =>
            {
                DownloadProgressBar.Progress = progress;
                if (progress >= 1)
                {
                    MessageLabel.Text = "Download completed!";
                    OkButton.IsVisible = true;
                }
            });
        }

        private void OnOkButtonClicked(object sender, EventArgs e)
        {
            CompletionSource.SetResult(true);
        }
    }
}