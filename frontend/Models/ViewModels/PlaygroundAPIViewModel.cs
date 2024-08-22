using CommunityToolkit.Mvvm.ComponentModel;

namespace frontend.Models.ViewModels
{
    public partial class PlaygroundAPIViewModel : ObservableObject
    {
        [ObservableProperty]
        private string infoRequest;
        [ObservableProperty]
        private string infoResponse;
        [ObservableProperty]
        private string listRequest;
        [ObservableProperty]
        private string listResponse;
        [ObservableProperty]
        private string loadChainRequest;
        [ObservableProperty]
        private string loadChainResponse;
        [ObservableProperty]
        private string stopChainRequest;
        [ObservableProperty]
        private string stopChainResponse;
        [ObservableProperty]
        private string inferenceRequest;
        [ObservableProperty]
        private string inferenceResponse;
        [ObservableProperty]
        private string loadChainRequestBody;
        [ObservableProperty]
        private string stopChainRequestBody;
        [ObservableProperty]
        private string inferenceRequestBody;

        public PlaygroundAPIViewModel(PlaygroundViewModel playgroundViewModel)
        {
            InitializeApiExamples(playgroundViewModel.Playground.PlaygroundId);
        }

        private void InitializeApiExamples(string playgroundId)
        {
            ListRequest = "http://127.0.0.1:8000/playground/list";
            ListResponse = GetListResponseExample();
            InfoRequest = $"http://127.0.0.1:8000/playground/info?playground_id={playgroundId}";
            InfoResponse = GetInfoResponseExample();
            LoadChainRequest = $"http://127.0.0.1:8000/playground/load-chain";
            LoadChainResponse = GetLoadChainResponseExample();
            StopChainRequest = $"http://127.0.0.1:8000/playground/stop-chain";
            StopChainResponse = "On success, the server will return 204 No Content as status code";
            InferenceRequest = $"http://127.0.0.1:8000/playground/inference";
            InferenceResponse = GetInferenceResponseExample();
            LoadChainRequestBody = GetLoadChainRequestBodyExample(playgroundId);
            StopChainRequestBody = GetStopChainRequestBodyExample(playgroundId);
            InferenceRequestBody = GetInferenceRequestBodyExample(playgroundId);
        }

        private string GetListResponseExample()
        {
            return @"{
    ""message"": ""Success"",
    ""data"": {
        ""playground1"": {
            ""description"": ""I am description 1"",
            ""models"": {
                ""cardiffnlp/twitter-roberta-base-sentiment-latest"": {
                    ""input"": ""text"",
                    ""output"": ""text"",
                    ""pipeline_tag"": ""text-classification"",
                    ""is_online"": false
                },
                ""suno/bark-small"": {
                    ""input"": ""text"",
                    ""output"": ""audio"",
                    ""pipeline_tag"": ""text-to-speech"",
                    ""is_online"": false
                }
            },
            ""chain"": [
                ""cardiffnlp/twitter-roberta-base-sentiment-latest"",
                ""suno/bark-small""
            ],
            ""active_chain"": false
        },
        ""playground2"": {
            ""description"": ""..."",
            ""models"": {...},
            ""chain"": [...],
            ""active_chain"": bool
        }
    }
}";
        }

        private string GetInfoResponseExample()
        {
            return @"{
    ""message"": ""Success"",
    ""data"": {
        ""myPlayground"": {
            ""description"": ""I am description for myPlayground"",
            ""models"": {
                ""cardiffnlp/twitter-roberta-base-sentiment-latest"": {
                    ""input"": ""text"",
                    ""output"": ""text"",
                    ""pipeline_tag"": ""text-classification"",
                    ""is_online"": false
                },
                ""suno/bark-small"": {
                    ""input"": ""text"",
                    ""output"": ""audio"",
                    ""pipeline_tag"": ""text-to-speech"",
                    ""is_online"": false
                }
            },
            ""chain"": [
                ""cardiffnlp/twitter-roberta-base-sentiment-latest"",
                ""suno/bark-small""
            ],
            ""active_chain"": false
        }
    }
}";
        }


        private string GetLoadChainResponseExample()
        {
            return @"{
    ""message"": ""Playground chain loaded successfully"",
    ""data"": {
        ""playground_id"": ""myPlayground"",
        ""chain"": [
            ""cardiffnlp/twitter-roberta-base-sentiment-latest"",
            ""suno/bark-small""
        ]
    }
}";
        }

        private string GetInferenceResponseExample()
        {
            return @$"{{
    ""message"": ""Success"",
    ""data"": [
        {{
            ""label"": ""positive"",
            ""score"": 1.0
        }}
    ]
}}";
        }

        private string GetLoadChainRequestBodyExample(string playgroundId)
        {
            return @$"{{
    ""playground_id"": ""{playgroundId}""
}}";
        }

        private string GetStopChainRequestBodyExample(string playgroundId)
        {
            return @$"{{
    ""playground_id"": ""{playgroundId}""
}}";
        }

        private string GetInferenceRequestBodyExample(string playgroundId)
        {
            return @$"{{
    ""playground_id"": ""{playgroundId}"",
    ""data"": {{
        ""payload"": ""'Ai Islands' is the best application i have ever used!""
    }}
}}";
        }
    }
}