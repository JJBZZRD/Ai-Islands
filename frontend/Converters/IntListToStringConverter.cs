using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Microsoft.Maui.Controls;

namespace frontend.Converters
{
    public class IntListToStringConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is List<int> list)
            {
                return string.Join(",", list);
            }
            return string.Empty;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string str)
            {
                var result = new List<int>();
                var tokens = str.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);

                foreach (var token in tokens)
                {
                    if (int.TryParse(token.Trim(), out int number))
                    {
                        result.Add(number);
                    }
                    else
                    {
                        // Handle invalid input gracefully, e.g., log the error or ignore the invalid token
                        // For now, we'll just ignore invalid tokens
                    }
                }

                return result;
            }
            return new List<int>();
        }
    }
}