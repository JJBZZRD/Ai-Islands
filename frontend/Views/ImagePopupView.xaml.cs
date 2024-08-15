using Microsoft.Maui.Controls;

namespace frontend.Views
{
    public partial class ImagePopupView : ContentView
    {
        private TaskCompletionSource<bool> _imageLoadedTcs;
        public ImagePopupView()
        {
            InitializeComponent();

            var tapGestureRecognizer = new TapGestureRecognizer();
            tapGestureRecognizer.Tapped += OnBackgroundTapped;
            BackgroundOverlay.GestureRecognizers.Add(tapGestureRecognizer);
        }

        public Task WaitForImageLoadAsync()
        {
            _imageLoadedTcs = new TaskCompletionSource<bool>();
            return _imageLoadedTcs.Task;
        }

        public void SetImage(ImageSource imageSource)
        {
            PopupImage.Source = imageSource;
        }

        private void OnCloseButtonClicked(object sender, EventArgs e)
        {
            IsVisible = false;
        }

        private void OnBackgroundTapped(object sender, EventArgs e)
        {
            IsVisible = false;
        }
    }
}