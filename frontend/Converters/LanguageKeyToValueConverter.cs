using System.Globalization;

namespace frontend.Converters
{
    public class LanguageKeyToValueConverter : IValueConverter
    {
        public Dictionary<string, string> LanguagesDict = new Dictionary<string, string>{ {"English", "en"}, {"Zulu", "zu"}};

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string key && LanguagesDict != null && LanguagesDict.ContainsKey(key))
            {
                return LanguagesDict[key];
            }
            return null;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string val && LanguagesDict != null)
            {
                return LanguagesDict.FirstOrDefault(x => x.Value == val).Key;
            }
            return null;
        }
    }
}