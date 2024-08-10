using System.Text.Json.Serialization;
using System.Windows.Input;

public class ModelItem
{
    public string? ModelId { get; set; }
    public string? PipelineTag { get; set; }
    public bool IsOnline { get; set; }
    public string Status => IsOnline ? "Online" : "Offline";
    public string? Description { get; set; }
    public string? ModelDesc { get; set; }
    public string? ModelDetail { get; set; }
    public List<string>? Tags { get; set; }
    public bool IsInLibrary { get; set; }
    [JsonIgnore]
    public ICommand? LoadOrStopCommand { get; set; }
    public string? ModelSource { get; set; }
    public string? ModelClass { get; set; }
    public string? ModelCardUrl { get; set; }
    public string? DatasetFormat { get; set; }
}