using System;
using System.Globalization;
using Microsoft.Maui.Controls;

namespace frontend.Converters
{
    public class TabToColorConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value == null || parameter == null)
                return Colors.White;

            return value.ToString() == parameter.ToString() ? Colors.Gray : Colors.White;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}