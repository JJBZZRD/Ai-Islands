using System.Globalization;
using frontend.Models;

namespace frontend.Views;


public partial class PlaygroundConfigView : ContentView
{
    private List<string> _models = new List<string> { "Model 1", "Model 2", "Model 3", "Model 4", "Model 5", "Model 6", "Model 7" };

    public PlaygroundConfigView(Playground playground)
    {
        InitializeComponent();
        BindingContext = playground;
    }

    private void OnDropdownClicked(object sender, EventArgs e)
    {
        DropdownPopup.IsVisible = !DropdownPopup.IsVisible;
    }

    private void OnModelSelected(object sender, SelectionChangedEventArgs e)
    {
        if (e.CurrentSelection.FirstOrDefault() is string selectedModel)
        {
            ModelEntry.Text = selectedModel;
            DropdownPopup.IsVisible = false;
        }
    }

    public class PercentageConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is double width && parameter is string percentageString)
            {
                if (double.TryParse(percentageString, out double percentage))
                {
                    return width * percentage;
                }
            }
            return value;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

}