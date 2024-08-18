using Microsoft.Maui.Controls;
using System.Windows.Input;

namespace frontend.Views
{
    public partial class AppShell : Shell
    {
        public ICommand NavigateCommand { get; }
        private Library libraryPage;
        public AppShell()
        {
            InitializeComponent();
            Routing.RegisterRoute("ModelIndex", typeof(ModelIndex));
            libraryPage = new Library();
            Routing.RegisterRoute("Library", typeof(Library));

            NavigateCommand = new Command<string>(async (route) =>
            {
                if (route == "LibraryPage")
                {
                    // Use the existing Library instance
                    await Navigation.PushAsync(libraryPage);
                }
                else
                {
                    await Shell.Current.GoToAsync(route);
                }
            });
            Routing.RegisterRoute("Playground", typeof(PlaygroundPage));
            Routing.RegisterRoute("DataRefinery", typeof(DataRefinery));
            Routing.RegisterRoute("Setting", typeof(Setting));
            Routing.RegisterRoute(nameof(LibraryTabbedPage), typeof(LibraryTabbedPage));
            NavigateCommand = new Command<string>(async (route) => await Shell.Current.GoToAsync(route));
            BindingContext = this;
        }
    }
}