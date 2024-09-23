import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import json
from backend.utils.dataset_management import DatasetFileManagement

@pytest.fixture
def dataset_management():
    return DatasetFileManagement()

@patch('backend.utils.dataset_management.shutil.copy2')
@patch('backend.utils.dataset_management.Path.mkdir')
@patch('backend.utils.dataset_management.Path.exists')
def test_upload_dataset(mock_exists, mock_mkdir, mock_copy2, dataset_management):
    mock_exists.return_value = True
    result = dataset_management.upload_dataset('/path/to/dataset.csv')
    assert "Dataset uploaded successfully" in result['message']
    mock_copy2.assert_called_once()

@patch('backend.utils.dataset_management.FileTypeManager.read_file')
@patch('backend.utils.dataset_management.Path.exists')
@patch('backend.utils.dataset_management.Path.iterdir')
def test_preview_dataset(mock_iterdir, mock_exists, mock_read_file, dataset_management):
    mock_exists.return_value = True
    mock_file = MagicMock()
    mock_file.is_file.return_value = True
    mock_file.suffix = '.csv'
    mock_iterdir.return_value = [mock_file]
    mock_read_file.return_value = ['row1', 'row2', 'row3']

    result = dataset_management.preview_dataset('test_dataset')
    assert result['file_type'] == '.csv'
    assert len(result['content']) == 3

@patch('backend.utils.dataset_management.Path.exists')
def test_get_dataset_processing_status(mock_exists, dataset_management):
    mock_exists.side_effect = [True, True, False]
    result = dataset_management.get_dataset_processing_status('test_dataset')
    assert result['default_processed'] is True
    assert result['chunked_processed'] is False

@patch('backend.utils.dataset_management.shutil.rmtree')
@patch('backend.utils.dataset_management.Path.exists')
def test_delete_dataset(mock_exists, mock_rmtree, dataset_management):
    mock_exists.return_value = True
    result = dataset_management.delete_dataset('test_dataset')
    assert "deleted successfully" in result['message']
    mock_rmtree.assert_called_once()

@patch('backend.utils.dataset_management.json.load')
@patch('builtins.open', new_callable=mock_open)
@patch('backend.utils.dataset_management.Path.exists')
def test_get_dataset_processing_info(mock_exists, mock_file, mock_json_load, dataset_management):
    mock_exists.return_value = True
    mock_json_load.return_value = {
        "model_type": "sentence_transformer",
        "model_name": "all-MiniLM-L6-v2",
        "chunking_settings": {
            "use_chunking": True,
            "chunk_method": "fixed_length",
            "chunk_size": 1000,
            "chunk_overlap": 100
        }
    }
    result = dataset_management.get_dataset_processing_info('test_dataset', 'chunked')
    assert result['model_type'] == "sentence_transformer"
    assert result['chunking_settings']['chunk_method'] == "fixed_length"

@patch('backend.utils.dataset_management.Path.iterdir')
def test_list_datasets(mock_iterdir, dataset_management):
    mock_dir = MagicMock()
    mock_dir.is_dir.return_value = True
    mock_dir.name = 'test_dataset'
    mock_file = MagicMock()
    mock_file.is_file.return_value = True
    mock_file.suffix = '.csv'
    mock_dir.iterdir.return_value = [mock_file]
    mock_iterdir.return_value = [mock_dir]

    result = dataset_management.list_datasets()
    assert 'test_dataset.csv' in result['datasets']

@patch('backend.utils.dataset_management.json.load')
@patch('backend.utils.dataset_management.json.dump')
@patch('builtins.open', new_callable=mock_open)
def test_update_dataset_metadata(mock_file, mock_json_dump, mock_json_load, dataset_management):
    mock_json_load.return_value = {}
    dataset_management.update_dataset_metadata('test_dataset', {'default': True})
    mock_json_dump.assert_called_once()

@patch('backend.utils.dataset_management.json.load')
@patch('builtins.open', new_callable=mock_open)
def test_get_dataset_metadata(mock_file, mock_json_load, dataset_management):
    mock_json_load.return_value = {'test_dataset': {'default': True}}
    result = dataset_management.get_dataset_metadata('test_dataset')
    assert result == {'default': True}

@patch('backend.utils.dataset_management.DatasetFileManagement.get_dataset_metadata')
def test_check_rag_settings_feasibility(mock_get_metadata, dataset_management):
    mock_get_metadata.return_value = {'default': True, 'chunked': False}
    result, _ = dataset_management.check_rag_settings_feasibility('test_dataset', use_chunking=False)
    assert result is True

    result, _ = dataset_management.check_rag_settings_feasibility('test_dataset', use_chunking=True)
    assert result is False

@patch('backend.utils.dataset_management.json.load')
@patch('builtins.open', new_callable=mock_open)
def test_get_datasets_tracker_info(mock_file, mock_json_load, dataset_management):
    mock_json_load.return_value = {
        'dataset1': {'default': True},
        'dataset2': {'chunked': True},
        'dataset3': {'default': False, 'chunked': False}
    }
    result = dataset_management.get_datasets_tracker_info()
    assert len(result['datasets']) == 2
    assert 'dataset1' in result['datasets']
    assert 'dataset2' in result['datasets']
    assert 'dataset3' not in result['datasets']

@patch('backend.utils.dataset_management.Path.exists')
def test_get_dataset_report(mock_exists, dataset_management):
    mock_exists.return_value = True
    result = dataset_management.get_dataset_report('test_dataset', 'default')
    assert isinstance(result, Path)
    assert result.name == 'test_dataset_processing_report.html'

    mock_exists.return_value = False
    result = dataset_management.get_dataset_report('test_dataset', 'default')
    assert result is None