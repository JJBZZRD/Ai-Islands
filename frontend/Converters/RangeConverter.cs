using System;
using System.Globalization;
using System.Linq;
using Microsoft.Maui.Controls;

namespace frontend.Converters
{
    public class RangeConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value == null || parameter == null)
                return 0;

            var paramDict = ParseParameters(parameter.ToString());

            if (paramDict.TryGetValue("val", out var valString))
            {
                var values = ParseValues(valString);
                if (values.Contains(value))
                {
                    return (double)Array.IndexOf(values, value);
                }
                return 0;
            }
            else if (paramDict.TryGetValue("min", out var minString) &&
                     paramDict.TryGetValue("max", out var maxString) &&
                     paramDict.TryGetValue("step", out var stepString))
            {
                if (!double.TryParse(minString, out double min) ||
                    !double.TryParse(maxString, out double max) ||
                    !double.TryParse(stepString, out double step))
                    return value;

                if (paramDict["type"] == "float" && value is float floatValue)
                {
                    return (floatValue - min) / step;
                }
                else if (paramDict["type"] == "int" && value is int intValue)
                {
                    return (intValue - min) / step;
                }
            }

            return value;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value == null || parameter == null)
                return 0;

            var paramDict = ParseParameters(parameter.ToString());

            if (paramDict.TryGetValue("val", out var valString))
            {
                var values = ParseValues(valString);
                if (value is double doubleValue)
                {
                    int index = (int)Math.Round(doubleValue);
                    if (index >= 0 && index < values.Length)
                    {
                        return values[index];
                    }
                }
                return values[0];
            }
            else if (paramDict.TryGetValue("min", out var minString) &&
                     paramDict.TryGetValue("max", out var maxString) &&
                     paramDict.TryGetValue("step", out var stepString))
            {
                if (!double.TryParse(minString, out double min) ||
                    !double.TryParse(maxString, out double max) ||
                    !double.TryParse(stepString, out double step))
                    return value;

                if (value is double doubleValue)
                {
                    double result = min + (Math.Round(doubleValue) * step);
                    result = Math.Clamp(result, min, max);

                    if (paramDict["type"] == "float")
                    {
                        return (float)result;
                    }
                    else if (paramDict["type"] == "int")
                    {
                        return (int)Math.Round(result);
                    }
                }
            }

            return value;
        }

        private Dictionary<string, string> ParseParameters(string paramString)
        {
            return paramString.Split(',')
                .Select(p => p.Split('='))
                .Where(p => p.Length == 2)
                .ToDictionary(p => p[0].Trim(), p => p[1].Trim());
        }

        private object[] ParseValues(string valString)
        {
            return valString.Trim('(', ')')
                .Split(',')
                .Select(v => 
                {
                    if (int.TryParse(v, out int intVal))
                        return (object)intVal;
                    if (float.TryParse(v, out float floatVal))
                        return (object)floatVal;
                    return (object)v.Trim();
                })
                .ToArray();
        }
    }
}