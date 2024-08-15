using frontend.Models;

namespace frontend.Views;

public partial class ChainAPI : ContentView
{
    public ChainAPI(Playground playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }
}