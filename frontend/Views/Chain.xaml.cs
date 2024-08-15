using frontend.Models;
using frontend.Models;


namespace frontend.Views;

public partial class Chain : ContentView
{
    public Chain(Playground playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }
}