import pytest
from backend.controlers.library_control import LibraryControl
from unittest.mock import patch

@pytest.fixture
def library_control():
    return LibraryControl()

def test_merge_configs_basic(library_control):
    original_config = {"a": 1, "b": 2}
    new_config = {"b": 3, "c": 4}
    result = library_control._merge_configs(original_config, new_config)
    assert result == {"a": 1, "b": 3, "c": 4}

def test_merge_configs_nested_dict(library_control):
    original_config = {"a": 1, "b": {"x": 10, "y": 20}}
    new_config = {"b": {"y": 30, "z": 40}}
    result = library_control._merge_configs(original_config, new_config)
    assert result == {"a": 1, "b": {"x": 10, "y": 30, "z": 40}}

def test_merge_configs_none_values(library_control):
    original_config = {"a": 1, "b": 2, "c": 3}
    new_config = {"b": None, "d": 4}
    result = library_control._merge_configs(original_config, new_config)
    assert result == {"a": 1, "b": 2, "c": 3, "d": 4}

def test_merge_configs_null_string(library_control):
    original_config = {"a": 1, "b": 2}
    new_config = {"b": "null", "c": "NULL"}
    with patch('backend.controlers.library_control.logger') as mock_logger:
        result = library_control._merge_configs(original_config, new_config)
    assert result == {"a": 1, "b": None, "c": None}
    mock_logger.info.assert_any_call("Setting b to None")
    mock_logger.info.assert_any_call("Setting c to None")

def test_merge_configs_empty_dicts(library_control):
    original_config = {}
    new_config = {}
    result = library_control._merge_configs(original_config, new_config)
    assert result == {}

def test_merge_configs_new_nested_dict(library_control):
    original_config = {"a": 1}
    new_config = {"b": {"x": 10, "y": 20}}
    result = library_control._merge_configs(original_config, new_config)
    assert result == {"a": 1, "b": {"x": 10, "y": 20}}

def test_merge_configs_overwrite_non_dict_with_dict(library_control):
    original_config = {"a": 1, "b": 2}
    new_config = {"b": {"x": 10, "y": 20}}
    with pytest.raises(TypeError):
        library_control._merge_configs(original_config, new_config)

def test_merge_configs_mixed_types(library_control):
    original_config = {"a": 1, "b": {"x": 10}, "c": [1, 2, 3]}
    new_config = {"b": {"y": 20}, "c": 4, "d": {"z": 30}}
    result = library_control._merge_configs(original_config, new_config)
    assert result == {"a": 1, "b": {"x": 10, "y": 20}, "c": 4, "d": {"z": 30}}