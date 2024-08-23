using System.Globalization;

namespace frontend.Converters
{
    public class BoolToImageConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool isCustomised)
            {
                return isCustomised ? "check.png" : "cross.png";
            }
            return "cross.png"; // Default to cross if the value is not a boolean
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}