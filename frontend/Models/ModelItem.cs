using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Text.Json.Serialization;
namespace frontend.Models
{
    public class ModelItem
    {
        public string Name { get; set; } = string.Empty;

        public string PipelineTag { get; set; } = string.Empty;

        [JsonPropertyName("is_online")]
        public bool IsOnline { get; set; }

        public string Status => IsOnline ? "Online" : "Offline";
        public string Description { get; set; } = string.Empty;
        public string Tags { get; set; } = string.Empty;
        public ICommand LoadOrStopCommand { get; set; }

        public ModelItem()
        {
            LoadOrStopCommand = new Command(() => { });
        }
    }
}
