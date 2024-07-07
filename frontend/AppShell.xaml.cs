using Microsoft.Maui.Controls;
using System.Windows.Input;

namespace frontend
{
    public partial class AppShell : Shell
    {
        public ICommand NavigateCommand { get; }
        public AppShell()
        {
            InitializeComponent();
            Routing.RegisterRoute("AIIndexPage", typeof(AIIndexPage));
            Routing.RegisterRoute("LibraryPage", typeof(LibraryPage));
            Routing.RegisterRoute("PlaygroundPage", typeof(PlaygroundPage));
            Routing.RegisterRoute("SettingsPage", typeof(SettingsPage));
            NavigateCommand = new Command<string>(async (route) => await Shell.Current.GoToAsync(route));
            BindingContext = this;
        }
    }
}