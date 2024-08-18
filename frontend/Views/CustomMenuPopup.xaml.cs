using System;
using Microsoft.Maui.Controls;

namespace frontend.Views
{
    public partial class CustomMenuPopup : ContentView
    {
        public event EventHandler<string> MenuItemClicked;

        public CustomMenuPopup()
        {
            InitializeComponent();
        }

        private void OnStartTutorialClicked(object sender, EventArgs e) => MenuItemClicked?.Invoke(this, "StartTutorial");
        private void OnGoToIBMCloudClicked(object sender, EventArgs e) => MenuItemClicked?.Invoke(this, "GoToIBMCloud");
        private void OnHelpClicked(object sender, EventArgs e) => MenuItemClicked?.Invoke(this, "Help");
        private void OnSettingsClicked(object sender, EventArgs e) => MenuItemClicked?.Invoke(this, "Settings");
        private void OnAboutClicked(object sender, EventArgs e) => MenuItemClicked?.Invoke(this, "About");
    }
}