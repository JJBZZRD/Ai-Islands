namespace frontend.Views;

public partial class Chain : ContentView
{
    public Chain(Dictionary<string, object> playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }
}