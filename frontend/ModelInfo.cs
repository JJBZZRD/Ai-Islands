namespace frontend
{
    public class ModelInfo
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public string Finetune { get; set; } = string.Empty;
        public bool IsAddToLibraryEnabled { get; set; } = true; // New property to control button state
    }
}
