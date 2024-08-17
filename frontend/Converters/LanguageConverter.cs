using System.Globalization;
using System.Collections.Generic;
using System.Linq;

namespace frontend.Converters
{
    public class LanguageConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string languageCode && parameter is IEnumerable<KeyValuePair<string, string>> languages)
            {
                return languages.FirstOrDefault(kvp => kvp.Key == languageCode);
            }
            return null;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is KeyValuePair<string, string> kvp)
            {
                return kvp.Key;
            }
            return null;
        }
    }
}