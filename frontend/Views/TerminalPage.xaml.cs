using System;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Maui.Controls;

namespace frontend.Views
{
    public partial class TerminalPage : ContentPage
    {
        private ClientWebSocket _webSocket;
        private CancellationTokenSource _cts;
        private TaskCompletionSource<bool> _operationCompletionSource;

        public TerminalPage(string title)
        {
            InitializeComponent();
            TitleLabel.Text = title;
            _operationCompletionSource = new TaskCompletionSource<bool>();
        }

        public async Task ConnectAndStreamOutput(string modelId, string action)
        {
            _webSocket = new ClientWebSocket();
            _cts = new CancellationTokenSource();

            try
            {
                await _webSocket.ConnectAsync(new Uri($"ws://localhost:8000/ws/console-stream/{modelId}/{action}"), _cts.Token);
                AppendOutput($"Connected to WebSocket for {action} operation on model {modelId}");
                _ = ReceiveMessages();
            }
            catch (Exception ex)
            {
                AppendOutput($"WebSocket connection error: {ex.Message}");
                _operationCompletionSource.SetResult(false);
            }
        }

        private async Task ReceiveMessages()
        {
            var buffer = new byte[1024 * 4];
            bool taskComplete = false;

            try
            {
                while (_webSocket.State == WebSocketState.Open && !taskComplete)
                {
                    var result = await _webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), _cts.Token);

                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        string message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                        AppendOutput(message);

                        // Check for the "Task Completed" message sent from the backend
                        if (message.Contains("Task Completed"))
                        {
                            taskComplete = true;
                            _operationCompletionSource.SetResult(true);
                            AppendOutput("Operation completed successfully.");
                        }
                    }
                    else if (result.MessageType == WebSocketMessageType.Close)
                    {
                        AppendOutput("WebSocket connection closed by server.");
                        break;
                    }
                }
            }
            catch (WebSocketException ex)
            {
                AppendOutput($"WebSocket error: {ex.Message}");
                _operationCompletionSource.SetResult(false);
            }
            catch (Exception ex)
            {
                AppendOutput($"Error receiving message: {ex.Message}");
                _operationCompletionSource.SetResult(false);
            }
            finally
            {
                await CloseWebSocketAndTerminal();
            }
        }

        private async Task CloseWebSocketAndTerminal()
        {
            if (_webSocket.State == WebSocketState.Open)
            {
                await _webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, CancellationToken.None);
            }

            await Task.Delay(2000); // Give user time to read the output
            await Navigation.PopAsync();
        }

        public void AppendOutput(string text)
        {
            MainThread.BeginInvokeOnMainThread(() =>
            {
                OutputLabel.Text += text + Environment.NewLine;
                ((ScrollView)OutputLabel.Parent).ScrollToAsync(OutputLabel, ScrollToPosition.End, true);
            });
        }

        public Task<bool> WaitForCompletion()
        {
            return _operationCompletionSource.Task;
        }

        protected override async void OnDisappearing()
        {
            base.OnDisappearing();
            _cts?.Cancel();
            await CloseWebSocketAndTerminal();
        }
    }
}
