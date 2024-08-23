using System;
using System.Globalization;
using Microsoft.Maui.Controls;
using frontend.Models;

namespace frontend.Converters
{
    public class AnyPropertyExistsConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is Config config)
            {
                return !string.IsNullOrEmpty(config.Voice) ||
                       config.Pitch.HasValue ||
                       config.Speed.HasValue ||
                       !string.IsNullOrEmpty(config.Model) ||
                       !string.IsNullOrEmpty(config.ContentType) ||
                       config.EmbeddingDimensions != null ||
                       config.MaxInputTokens != null ||
                       !string.IsNullOrEmpty(config.SpeakerEmbeddingConfig) ||
                       config.ChatHistory.HasValue;
            }
            return false;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}