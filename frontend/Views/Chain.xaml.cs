namespace frontend.Views;

public partial class Chain : ContentView
{
    public Chain(frontend.entities.Playground playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }
}