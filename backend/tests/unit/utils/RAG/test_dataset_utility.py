import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import numpy as np
import pandas as pd
from backend.utils.dataset_utility import DatasetManagement
from backend.core.exceptions import ModelError
from langchain_ibm import WatsonxEmbeddings

@pytest.fixture
def dataset_management():
    return DatasetManagement()

def test_get_available_models():
    models = DatasetManagement.get_available_models()
    assert 'sentence_transformer' in models
    assert 'watson' in models
    assert len(models['sentence_transformer']) > 0
    assert len(models['watson']) > 0

@patch('backend.utils.dataset_utility.SentenceTransformer')
def test_generate_embeddings_sentence_transformer(mock_sentence_transformer, dataset_management):
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[1.0, 2.0], [3.0, 4.0]])
    mock_sentence_transformer.return_value = mock_model

    texts = ["Hello", "World"]
    model_info = {'model_type': 'sentence_transformer', 'model_name': 'all-MiniLM-L6-v2'}
    embeddings = dataset_management.generate_embeddings(texts, model_info)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (2, 2)
    mock_model.encode.assert_called_once_with(texts, show_progress_bar=True)

@patch('backend.utils.dataset_utility.WatsonxEmbeddings')
def test_generate_embeddings_watson(mock_watsonx_embeddings, dataset_management):
    mock_model = mock_watsonx_embeddings.return_value
    mock_model.embed_documents.return_value = [[1.0, 2.0], [3.0, 4.0]]

    texts = ["Hello", "World"]
    model_info = {'model_type': 'watson', 'model_name': 'ibm/slate-30m-english-rtrvr'}
    
    with patch.object(dataset_management, '_initialize_embedding_model', return_value=mock_model):
        with patch('backend.utils.dataset_utility.isinstance', return_value=True):
            embeddings = dataset_management.generate_embeddings(texts, model_info)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (2, 2)

@patch('backend.utils.dataset_utility.DatasetManagement._initialize_watson_embeddings')
def test_generate_embeddings_watson_error(mock_initialize_watson, dataset_management):
    mock_initialize_watson.side_effect = ModelError("Watson error")

    texts = ["Hello", "World"]
    model_info = {'model_type': 'watson', 'model_name': 'ibm/slate-30m-english-rtrvr'}

    with pytest.raises(ModelError, match="Watson error"):
        dataset_management.generate_embeddings(texts, model_info)

@patch('backend.utils.dataset_utility.pd.read_csv')
@patch('backend.utils.dataset_utility.DatasetManagement.generate_embeddings')
@patch('backend.utils.dataset_utility.faiss')
@patch('backend.utils.dataset_utility.pickle.dump')
@patch('backend.utils.dataset_utility.json.dump')
@patch('backend.utils.dataset_utility.Path')
@patch('builtins.open', new_callable=mock_open)
@patch('backend.utils.dataset_utility.DatasetFileManagement')
@patch('backend.utils.dataset_utility.shutil.copy2')
@patch('backend.utils.dataset_utility.DatasetManagement.generate_processing_report')
def test_process_dataset(mock_generate_report, mock_copy2, mock_dataset_file_management, mock_open, mock_path, mock_json_dump, mock_pickle_dump, mock_faiss, mock_generate_embeddings, mock_read_csv, dataset_management):
    mock_read_csv.return_value = pd.DataFrame({'col1': ['text1', 'text2'], 'col2': ['text3', 'text4']})
    mock_generate_embeddings.return_value = np.array([[1.0, 2.0], [3.0, 4.0]])
    mock_faiss.IndexFlatIP.return_value = MagicMock()
    mock_path.return_value.exists.return_value = False  # Change this to False
    mock_path.return_value.__truediv__.return_value = mock_path.return_value
    mock_dataset_file_management.return_value.update_dataset_metadata.return_value = None
    mock_generate_report.return_value = "report_path"

    file_path = Path('test.csv')
    result = dataset_management.process_dataset(file_path)

    assert result['message'] == "Dataset processed successfully"
    assert 'model_info' in result
    assert result['report_generated'] is True

    # Verify that all expected file operations were mocked
    mock_open.assert_called()
    mock_copy2.assert_called_once()
    mock_pickle_dump.assert_called()
    mock_json_dump.assert_called()
    mock_generate_report.assert_called_once()

@patch('backend.utils.dataset_utility.faiss')
@patch('backend.utils.dataset_utility.pickle.load')
@patch('backend.utils.dataset_utility.json.load')
@patch('backend.utils.dataset_utility.DatasetManagement.generate_embeddings')
@patch('backend.utils.dataset_utility.Path')
@patch('builtins.open', new_callable=mock_open)
def test_find_relevant_entries(mock_open, mock_path, mock_generate_embeddings, mock_json_load, mock_pickle_load, mock_faiss, dataset_management):
    mock_path.return_value.exists.return_value = True
    mock_json_load.return_value = {'model_type': 'sentence_transformer', 'model_name': 'all-MiniLM-L6-v2'}
    mock_pickle_load.side_effect = [
        np.array([[1.0, 2.0], [3.0, 4.0]]),  # embeddings
        ['text1', 'text2']  # original data
    ]
    mock_generate_embeddings.return_value = np.array([[0.5, 0.5]])
    mock_index = MagicMock()
    mock_index.search.return_value = (np.array([[0.9, 0.8]]), np.array([[0, 1]]))
    mock_faiss.read_index.return_value = mock_index

    result = dataset_management.find_relevant_entries('query', 'dataset_name', use_chunking=False)

    assert len(result) == 2
    assert 'text1' in result
    assert 'text2' in result