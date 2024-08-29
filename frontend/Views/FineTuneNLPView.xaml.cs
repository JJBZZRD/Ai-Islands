using frontend.Models;
using frontend.Models.ViewModels;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;

namespace frontend.Views;

public partial class FineTuneNLPView : ContentView
{
	public Model model { get; set; }
	private FineTuneNLPViewModel fineTuneNLPViewModel;

	public FineTuneNLPView(Model model)
	{
		InitializeComponent();
		this.model = model;
		fineTuneNLPViewModel = new FineTuneNLPViewModel(model);
		BindingContext = fineTuneNLPViewModel;
	}

	private async void OnBeginFineTuningClicked(object sender, EventArgs e)
	{
		var button = sender as Button;
		button.IsEnabled = false;

		try
		{
			string resultMessage = await fineTuneNLPViewModel.FineTune();
			
			if (resultMessage.StartsWith("error", StringComparison.OrdinalIgnoreCase))
			{
				await Application.Current.MainPage.DisplayAlert("Error", resultMessage, "OK");
			}
			else
			{
				await Application.Current.MainPage.DisplayAlert("Success", resultMessage, "OK");
			}
		}
		catch (Exception ex)
		{
			await Application.Current.MainPage.DisplayAlert("Error", $"An error occurred: {ex.Message}", "OK");
		}
		finally
		{
			button.IsEnabled = true;
		}
	}

	private async void OnSelectCsvFileClicked(object sender, EventArgs e)
	{
		try
		{
			var result = await FilePicker.PickAsync(new PickOptions
			{
				PickerTitle = "Please select a CSV file",
				FileTypes = new FilePickerFileType(new Dictionary<DevicePlatform, IEnumerable<string>>
				{
					{ DevicePlatform.iOS, new[] { "public.comma-separated-values-text" } },
					{ DevicePlatform.Android, new[] { "text/csv" } },
					{ DevicePlatform.WinUI, new[] { ".csv" } },
					{ DevicePlatform.Tizen, new[] { "text/csv" } },
				})
			});

			if (result != null)
			{
				fineTuneNLPViewModel.SelectedFilePath = result.FullPath;
			}
		}
		catch (Exception ex)
		{
			Debug.WriteLine($"Error selecting file: {ex.Message}");
		}
	}

	private async void OnDownloadExampleDatasetClicked(object sender, EventArgs e)
	{
		try
		{
			string fileName = "train_text_classification_dataset.csv";
			using var stream = await FileSystem.Current.OpenAppPackageFileAsync($"Resources/ExampleDataset/{fileName}");
			var downloadsFolder = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
			downloadsFolder = Path.Combine(downloadsFolder, "Downloads");
			var targetFile = Path.Combine(downloadsFolder, fileName);

			using (var fileStream = File.Create(targetFile))
			{
				await stream.CopyToAsync(fileStream);
			}

			await Application.Current.MainPage.DisplayAlert("Success", $"Example dataset downloaded to:\n{targetFile}", "OK");
		}
		catch (Exception ex)
		{
			await Application.Current.MainPage.DisplayAlert("Error", $"Failed to download example dataset: {ex.Message}", "OK");
		}
	}
}