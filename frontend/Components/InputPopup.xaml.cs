using System;
using Microsoft.Maui.Controls;
using Microsoft.Maui.ApplicationModel;

namespace frontend.Components
{
    public partial class InputPopup : ContentView
    {
        public event EventHandler<string> InputSubmitted;
        public event EventHandler InputCancelled;

        public static readonly BindableProperty TitleProperty =
            BindableProperty.Create(nameof(Title), typeof(string), typeof(InputPopup), string.Empty, propertyChanged: OnTitleChanged);

        public static readonly BindableProperty FieldLabelProperty =
            BindableProperty.Create(nameof(FieldLabel), typeof(string), typeof(InputPopup), string.Empty, propertyChanged: OnFieldLabelChanged);

        public static readonly BindableProperty IsPasswordProperty =
            BindableProperty.Create(nameof(IsPassword), typeof(bool), typeof(InputPopup), false, propertyChanged: OnIsPasswordChanged);

        public static readonly BindableProperty DescriptionProperty =
            BindableProperty.Create(nameof(Description), typeof(string), typeof(InputPopup), string.Empty, propertyChanged: OnDescriptionChanged);

        public string Title
        {
            get => (string)GetValue(TitleProperty);
            set => SetValue(TitleProperty, value);
        }

        public string FieldLabel
        {
            get => (string)GetValue(FieldLabelProperty);
            set => SetValue(FieldLabelProperty, value);
        }

        public bool IsPassword
        {
            get => (bool)GetValue(IsPasswordProperty);
            set => SetValue(IsPasswordProperty, value);
        }

        public string Description
        {
            get => (string)GetValue(DescriptionProperty);
            set => SetValue(DescriptionProperty, value);
        }

        public InputPopup()
        {
            InitializeComponent();
        }

        private static void OnTitleChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var popup = (InputPopup)bindable;
            popup.TitleLabel.Text = (string)newValue;
        }

        private static void OnFieldLabelChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var popup = (InputPopup)bindable;
            popup.InputEntry.Placeholder = (string)newValue;
        }

        private static void OnIsPasswordChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var popup = (InputPopup)bindable;
            popup.InputEntry.IsPassword = (bool)newValue;
        }

        private static void OnDescriptionChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var popup = (InputPopup)bindable;
            popup.DescriptionLabel.Text = (string)newValue;
        }

        private void OnSubmitClicked(object sender, EventArgs e)
        {
            InputSubmitted?.Invoke(this, InputEntry.Text);
            InputEntry.Text = string.Empty;
        }

        private void OnCancelClicked(object sender, EventArgs e)
        {
            InputCancelled?.Invoke(this, EventArgs.Empty);
            InputEntry.Text = string.Empty;
        }

        private async void OnDescriptionDoubleTapped(object sender, EventArgs e)
        {
            await Clipboard.SetTextAsync(Description);
            await Application.Current.MainPage.DisplayAlert("Copied", "Description copied to clipboard", "OK");
        }
    }
}