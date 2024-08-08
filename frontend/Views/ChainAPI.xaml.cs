namespace frontend.Views;

public partial class ChainAPI : ContentView
{
    public ChainAPI(Dictionary<string, object> playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }
}