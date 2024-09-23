from utils.file_processing import create_daily_folder
from utils.drive import write_daily_news_file, write_ai_newsletter_file, add_to_daily_update
from utils.drive import get_reddit_tech_posts, get_reddit_events_posts
from utils.spotify import add_to_spotify_playlist
from src.scripts import start_of_day, hourly_update
from utils.end_of_day_update import get_processed_events, update_end_of_day, update_summary
from utils.wisdom import generate_wisdom_image, compute_wisdom_summary
from utils.love import compute_love_summary
from utils.luleo import get_luleo_prompt
from utils.agi import scrape_metaculus_prediction_date, answer_agi_questions, generate_agi_vision_image

class function_map:
    func_map = {
        "CREATE_DAILY_FOLDER" : create_daily_folder,
        "GET_NEWS" : write_daily_news_file,
        "GET_AI_NEWS": write_ai_newsletter_file,
        "ADD_TO_DAILY_UPDATE": add_to_daily_update,
        "GET_REDDIT_TECH_POSTS": get_reddit_tech_posts,
        "GET_REDDIT_EVENTS_POSTS": get_reddit_events_posts,
        "ADD_TO_SPOTIFY_PLAYLIST": add_to_spotify_playlist,
        "START_OF_DAY" : start_of_day,
        "QUALIA_UPDATE": hourly_update,
        "GET_TODAY_PROCESSED_EVENTS": get_processed_events,
        "UPDATE_END_OF_DAY": update_end_of_day,
        "GENERATE_WISDOM_IMAGE": generate_wisdom_image,
        "GET_WISDOM_SUMMARY": compute_wisdom_summary,
        "GET_LOVE_SUMMARY": compute_love_summary,
        "UPDATE_END_OF_DAY_SUMMARY": update_summary,
        "GET_LULEO_PROMPT": get_luleo_prompt,
        "SCRAPE_METACULUS_PREDICTION_DATE": scrape_metaculus_prediction_date,
        "ANSWER_AGI_QUESTIONS": answer_agi_questions,
        "GENERATE_AGI_VISION_IMAGE": generate_agi_vision_image,
    }