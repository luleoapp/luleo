import pytest
from unittest.mock import patch, MagicMock
from process_daily_narrative.utils.drive import (
    write_daily_news_file,
    write_ai_newsletter_file,
    add_to_daily_update,
    upload_file_to_github,
)
from process_daily_narrative.utils.string_utils import get_user_input_document_path
from process_daily_narrative.utils.github_utils import upload_file_to_github

# Sample data for testing
SAMPLE_CONTENT = "This is a sample news content."
GITHUB_UPLOAD_PATH = "/path/to/github/repo"

@pytest.fixture
def mock_upload():
    with patch('process_daily_narrative.utils.drive.upload_file_to_github') as mock_upload_fn:
        yield mock_upload_fn

@pytest.fixture
def mock_get_path():
    with patch('process_daily_narrative.utils.string_utils.get_user_input_document_path', return_value='/mock/path') as mock_path_fn:
        yield mock_path_fn

def test_get_user_input_document_path(mock_get_path):
    path = get_user_input_document_path()
    mock_get_path.assert_called_once()
    assert path == '/mock/path'

def test_write_daily_news_file(mock_upload, mock_get_path):
    with patch('process_daily_narrative.utils.drive.open', mock_open=True) as mock_file:
        write_daily_news_file(SAMPLE_CONTENT)
        mock_get_path.assert_called_once()
        # Assuming write_daily_news_file calls upload_file_to_github
        mock_upload.assert_called_once_with('/mock/path', SAMPLE_CONTENT)
        mock_file.assert_called_once_with('/mock/path', 'w')

def test_write_ai_newsletter_file(mock_upload, mock_get_path):
    with patch('process_daily_narrative.utils.drive.open', mock_open=True) as mock_file:
        write_ai_newsletter_file(SAMPLE_CONTENT)
        mock_get_path.assert_called_once()
        # Assuming write_ai_newsletter_file calls upload_file_to_github
        mock_upload.assert_called_once_with('/mock/path', SAMPLE_CONTENT)
        mock_file.assert_called_once_with('/mock/path', 'w')

def test_add_to_daily_update(mock_upload, mock_get_path):
    with patch('process_daily_narrative.utils.drive.open', mock_open=True) as mock_file:
        add_to_daily_update(SAMPLE_CONTENT)
        mock_get_path.assert_called_once()
        # Assuming add_to_daily_update calls upload_file_to_github
        mock_upload.assert_called_once_with('/mock/path', SAMPLE_CONTENT)
        mock_file.assert_called_once_with('/mock/path', 'a')

@patch('process_daily_narrative.utils.github_utils')
def test_upload_file_to_github(mock_github_api):
    mock_instance = mock_github_api.return_value
    upload_file_to_github('/fake/path', 'file content')
    mock_instance.upload_file.assert_called_once_with('/fake/path', 'file content')
