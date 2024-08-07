using System.Windows.Input;
using Microsoft.Maui.Controls;
using frontend.Services;
 
namespace frontend.Views
{
    public partial class AppShell : Shell
    {
        public ICommand NavigateCommand { get; }
        private Library libraryPage;
        public AppShell()
        {
            InitializeComponent();
            Routing.RegisterRoute("MainPage", typeof(MainPage));
            var libraryService = new LibraryService(); // Create an instance of LibraryService
            libraryPage = new Library(libraryService);
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
            Routing.RegisterRoute("Playground", typeof(Playground));
            Routing.RegisterRoute("DataRefinery", typeof(DataRefinery));
            Routing.RegisterRoute("Setting", typeof(Setting));
            Routing.RegisterRoute(nameof(LibraryTabbedPage), typeof(LibraryTabbedPage));
            NavigateCommand = new Command<string>(async (route) => await Shell.Current.GoToAsync(route));
            BindingContext = this;
        }
    }
}