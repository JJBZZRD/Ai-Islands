using frontend.Models;
using System;
using Microsoft.Maui.Controls;

namespace frontend.Views
{
    [QueryProperty(nameof(ModelJson), "ModelJson")]
    public partial class ModelInfoPage : ContentPage
    {
        public string ModelJson { get; set; }

        public ModelItem Model { get; set; }

        public ModelInfoPage(ModelItem model)
        {
            InitializeComponent();
            Model = model;
            BindingContext = this;
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            if (Model != null)
            {
                ModelNameLabel.Text = Model.Name ?? "Unknown Model";
                ModelDescriptionLabel.Text = Model.Description ?? "No description available";
                LoadTags();
            }
        }

        private void LoadTags()
        {
            TagsContainer.Children.Clear();
            if (Model.Tags != null && Model.Tags.Any())
            {
                foreach (var tag in Model.Tags)
                {
                    AddTagToContainer(tag);
                }
            }
            else
            {
                TagsContainer.Children.Add(new Label { Text = "No tags available" });
            }
        }

        private void LoadModelInfo()
        {
            try
            {
                System.Diagnostics.Debug.WriteLine($"LoadModelInfo started. ModelJson: {ModelJson}");

                if (string.IsNullOrEmpty(ModelJson))
                {
                    throw new ArgumentNullException(nameof(ModelJson), "Model data is null or empty");
                }

                System.Diagnostics.Debug.WriteLine("Attempting to deserialize ModelJson");
                var model = System.Text.Json.JsonSerializer.Deserialize<ModelItem>(ModelJson);

                System.Diagnostics.Debug.WriteLine($"Deserialized model: {System.Text.Json.JsonSerializer.Serialize(model)}");

                if (model == null)
                {
                    throw new InvalidOperationException("Failed to deserialize model data");
                }

                System.Diagnostics.Debug.WriteLine("Setting ModelNameLabel");
                ModelNameLabel.Text = model.Name ?? "Unknown Model";

                System.Diagnostics.Debug.WriteLine("Setting ModelDescriptionLabel");
                ModelDescriptionLabel.Text = model.Description ?? model.ModelDesc ?? "No description available";

                System.Diagnostics.Debug.WriteLine($"Model Name: {ModelNameLabel.Text}");
                System.Diagnostics.Debug.WriteLine($"Model Description: {ModelDescriptionLabel.Text}");

                System.Diagnostics.Debug.WriteLine("Clearing TagsContainer");
                TagsContainer.Children.Clear();

                if (model.Tags != null && model.Tags.Any())
                {
                    System.Diagnostics.Debug.WriteLine($"Adding {model.Tags.Count} tags");
                    foreach (var tag in model.Tags)
                    {
                        AddTagToContainer(tag);
                    }
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine("No tags available for this model");
                    TagsContainer.Children.Add(new Label { Text = "No tags available" });
                }

                System.Diagnostics.Debug.WriteLine($"ModelInfoPage loaded successfully for {model.Name}");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error in LoadModelInfo: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"StackTrace: {ex.StackTrace}");

                ModelNameLabel.Text = "Error Loading Model Information";
                ModelDescriptionLabel.Text = $"An error occurred: {ex.Message}";
                TagsContainer.Children.Clear();
            }
        }

        private void AddTagToContainer(string tag)
        {
            var tagFrame = new Frame
            {
                BackgroundColor = Colors.LightGray,
                Padding = new Thickness(10, 5),
                CornerRadius = 20,
                Margin = new Thickness(0, 0, 5, 5),
                HasShadow = false,
                BorderColor = Colors.Gray
            };

            var tagLabel = new Label
            {
                Text = tag.ToUpper(),
                TextColor = Colors.Black,
                FontSize = 12,
                FontAttributes = FontAttributes.Bold
            };

            tagFrame.Content = tagLabel;
            TagsContainer.Children.Add(tagFrame);
        }
    }
}