using Microsoft.Maui.Controls;
using Microsoft.Maui.Controls.Xaml;
using frontend.Views;

namespace frontend
{
    public partial class App : Application
    {
        public App()
        {
            InitializeComponent();
            MainPage = new AppShell();
        }
    }
}