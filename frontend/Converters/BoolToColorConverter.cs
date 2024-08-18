using System;
using System.Globalization;
using Microsoft.Maui.Controls;

namespace frontend.Converters
{
    public class BoolToColorConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool boolValue)
            {
                return boolValue ? Color.FromArgb("D4002E") : Color.FromArgb("3366FF"); // False (not loaded) is blue, true (loaded) is red
            }
            return Color.FromArgb("000000"); 
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}