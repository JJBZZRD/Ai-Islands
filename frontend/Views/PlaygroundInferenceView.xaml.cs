using frontend.Models;


namespace frontend.Views;

public partial class PlaygroundInferenceView : ContentView
{
    public PlaygroundInferenceView(Playground playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }
}