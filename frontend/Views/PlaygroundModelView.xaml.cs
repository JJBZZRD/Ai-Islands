namespace frontend.Views;

public partial class PlaygroundModelView : ContentView
{
    public PlaygroundModelView(Dictionary<string, object> playground)
    {
        InitializeComponent();
        BindingContext = playground;

        // Example of accessing data
        //DescriptionLabel.Text = playground["Description"] as string;
    }
}