using frontend.Models;

namespace frontend.Views;

public partial class PlaygroundAPIView : ContentView
{
    public PlaygroundAPIView(Playground playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }
}