using System;
using System.Globalization;
using Microsoft.Maui.Controls;

namespace frontend.Converters
{
    public class LoadUnloadTextConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool isLoaded)
            {
                return isLoaded ? "Unload" : "Load";
            }
            return "Unknown state"; 
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}