namespace frontend.Views;

public partial class TerminalPage : ContentPage
{
    public void SetTitle(string title)
    {
        Title = title;
    }

    public TerminalPage(string title)
    {
        InitializeComponent();
        TitleLabel.Text = title;
    }

    public void AppendOutput(string text)
    {
        OutputLabel.Text += text + Environment.NewLine;
    }
}