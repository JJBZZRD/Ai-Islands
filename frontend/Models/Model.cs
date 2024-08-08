using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using frontend.Models;
using Newtonsoft.Json.Linq;
using System.Reflection;

namespace frontend.Models
{
    public class Model
    {
        // Define instance variables with all possible first order keys from library.json
        public string? ModelId { get; set; }
        public string? BaseModel { get; set; }
        public string? Dir { get; set; }
        public bool? IsCustomised { get; set; }
        public bool? IsOnline { get; set; }
        public string? ModelSource { get; set; }
        public List<string>? Tags { get; set; }
        public List<string>? RequiredClasses { get; set; }
        public string? ModelDesc { get; set; }
        public string? ModelDetail { get; set; }
        public string? ModelClass { get; set; }
        public string? PipelineTag { get; set; }
        public string? ModelCardUrl { get; set; }
        public JObject? Requirements { get; set; }
        public JObject? Config { get; set; }
        public string? AuthToken { get; set; }

        public Model(JObject json)
        {
            ProcessJson(json);
        }

        private void ProcessJson(JObject json)
        {
            foreach (var pair in json)
            {
                string propertyName = ToPascalCase(pair.Key);
                var property = GetType().GetProperty(propertyName, BindingFlags.IgnoreCase | BindingFlags.Public | BindingFlags.Instance);
                if (property != null && pair.Value != null)
                {
                    Type propertyType = Nullable.GetUnderlyingType(property.PropertyType) ?? property.PropertyType;

                    if (propertyType == typeof(List<string>))
                    {
                        property.SetValue(this, pair.Value.ToObject<List<string>>());
                    }
                    else if (propertyType == typeof(JObject))
                    {
                        property.SetValue(this, pair.Value.ToObject<JObject>());
                    }
                    else
                    {
                        property.SetValue(this, pair.Value.ToObject(propertyType));
                    }
                }
            }
        }

        private static string ToPascalCase(string name)
        {
            string camelCase = JsonNamingPolicy.CamelCase.ConvertName(name);
            return char.ToUpper(camelCase[0]) + camelCase.Substring(1);
        }
    }
}