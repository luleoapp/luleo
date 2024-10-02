import pytest
from unittest.mock import patch, MagicMock
from src.function_map import function_map

# Mock imports
patch('utils.llm_utils.call_and_log_llm')
patch('utils.drive.write_daily_news_file')
patch('utils.drive.write_ai_newsletter_file')
patch('utils.drive.add_to_daily_update')
patch('utils.drive.get_reddit_tech_posts')
patch('utils.drive.get_reddit_events_posts')
patch('utils.spotify.add_to_spotify_playlist')
patch('src.scripts.start_of_day')
patch('src.scripts.hourly_update')
patch('utils.end_of_day_update.get_processed_events')
patch('utils.end_of_day_update.update_end_of_day')
patch('utils.end_of_day_update.update_summary')
patch('utils.wisdom.generate_wisdom_image')
patch('utils.wisdom.compute_wisdom_summary')
patch('utils.love.compute_love_summary')
patch('utils.luleo.get_luleo_prompt')
patch('utils.agi.scrape_metaculus_prediction_date')
patch('utils.agi.answer_agi_questions')  # Corrected typo here
patch('utils.agi.generate_agi_vision_image')
patch('utils.luleo.classify_user_input')
patch('utils.luleo.process_user_upload')

@pytest.fixture
def fm():
    return function_map()

def test_get_news(fm):
    with patch('utils.drive.write_daily_news_file') as mock_write:
        fm.func_map['GET_NEWS']()
        mock_write.assert_called_once()

def test_get_ai_news(fm):
    with patch('utils.drive.write_ai_newsletter_file') as mock_write:
        fm.func_map['GET_AI_NEWS']()
        mock_write.assert_called_once()

def test_add_to_daily_update(fm):
    with patch('utils.drive.add_to_daily_update') as mock_add:
        fm.func_map['ADD_TO_DAILY_UPDATE']()
        mock_add.assert_called_once()

def test_get_reddit_tech_posts(fm):
    with patch('utils.drive.get_reddit_tech_posts') as mock_get:
        fm.func_map['GET_REDDIT_TECH_POSTS']()
        mock_get.assert_called_once()

def test_get_reddit_events_posts(fm):
    with patch('utils.drive.get_reddit_events_posts') as mock_get:
        fm.func_map['GET_REDDIT_EVENTS_POSTS']()
        mock_get.assert_called_once()

def test_add_to_spotify_playlist(fm):
    with patch('utils.spotify.add_to_spotify_playlist') as mock_add:
        fm.func_map['ADD_TO_SPOTIFY_PLAYLIST']()
        mock_add.assert_called_once()

def test_start_of_day(fm):
    with patch('src.scripts.start_of_day') as mock_start:
        fm.func_map['START_OF_DAY']()
        mock_start.assert_called_once()

def test_qualia_update(fm):
    with patch('src.scripts.hourly_update') as mock_update:
        fm.func_map['QUALIA_UPDATE']()
        mock_update.assert_called_once()

def test_get_today_processed_events(fm):
    with patch('utils.end_of_day_update.get_processed_events') as mock_get:
        fm.func_map['GET_TODAY_PROCESSED_EVENTS']()
        mock_get.assert_called_once()

def test_update_end_of_day(fm):
    with patch('utils.end_of_day_update.update_end_of_day') as mock_update:
        fm.func_map['UPDATE_END_OF_DAY']()
        mock_update.assert_called_once()

def test_generate_wisdom_image(fm):
    with patch('utils.wisdom.generate_wisdom_image') as mock_generate:
        fm.func_map['GENERATE_WISDOM_IMAGE']()
        mock_generate.assert_called_once()

def test_get_wisdom_summary(fm):
    with patch('utils.wisdom.compute_wisdom_summary') as mock_compute:
        fm.func_map['GET_WISDOM_SUMMARY']()
        mock_compute.assert_called_once()

def test_get_love_summary(fm):
    with patch('utils.love.compute_love_summary') as mock_compute:
        fm.func_map['GET_LOVE_SUMMARY']()
        mock_compute.assert_called_once()

def test_update_end_of_day_summary(fm):
    with patch('utils.end_of_day_update.update_summary') as mock_update:
        fm.func_map['UPDATE_END_OF_DAY_SUMMARY']()
        mock_update.assert_called_once()

def test_get_luleo_prompt(fm):
    with patch('utils.luleo.get_luleo_prompt') as mock_get:
        fm.func_map['GET_LULEO_PROMPT']()
        mock_get.assert_called_once()

def test_scrape_metaculus_prediction_date(fm):
    with patch('utils.agi.scrape_metaculus_prediction_date') as mock_scrape:
        fm.func_map['SCRAPE_METACULUS_PREDICTION_DATE']()
        mock_scrape.assert_called_once()

def test_answer_agi_questions(fm):
    with patch('utils.agi.answer_agi_questions') as mock_answer:
        fm.func_map['ANSWER_AGI_QUESTIONS']()
        mock_answer.assert_called_once()

def test_generate_agi_vision_image(fm):
    with patch('utils.agi.generate_agi_vision_image') as mock_generate:
        fm.func_map['GENERATE_AGI_VISION_IMAGE']()
        mock_generate.assert_called_once()

def test_classify_user_input(fm):
    with patch('utils.luleo.classify_user_input') as mock_classify:
        fm.func_map['CLASSIFY_USER_INPUT']()
        mock_classify.assert_called_once()

def test_process_user_upload(fm):
    with patch('utils.luleo.process_user_upload') as mock_process:
        fm.func_map['PROCESS_USER_UPLOAD']()
        mock_process.assert_called_once()