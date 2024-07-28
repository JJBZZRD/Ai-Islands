using Microsoft.Maui.Controls;
using System.Windows.Input;

namespace frontend.Views
{
    public partial class AppShell : Shell
    {
        public ICommand NavigateCommand { get; }
        public AppShell()
        {
            InitializeComponent();
            Routing.RegisterRoute("MainPage", typeof(MainPage));
            Routing.RegisterRoute("Library", typeof(Library));
            Routing.RegisterRoute("Playground", typeof(Playground));
            Routing.RegisterRoute("Setting", typeof(Setting));
            NavigateCommand = new Command<string>(async (route) => await Shell.Current.GoToAsync(route));
            BindingContext = this;
        }
    }
}