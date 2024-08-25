using System.Globalization;

namespace frontend.Converters
{
    public class DoubleListToStringConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is List<double> list)
            {
                return string.Join(",", list);
            }
            return string.Empty;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string str)
            {
                var result = new List<double>();
                var tokens = str.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);

                foreach (var token in tokens)
                {
                    if (double.TryParse(token.Trim(), out double number))
                    {
                        result.Add(number);
                    }
                }

                return result;
            }
            return new List<double>();
        }
    }
}