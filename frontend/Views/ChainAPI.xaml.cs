namespace frontend.Views;

public partial class ChainAPI : ContentView
{
    public ChainAPI(frontend.entities.Playground playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }
}