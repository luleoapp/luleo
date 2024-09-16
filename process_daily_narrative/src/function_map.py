from utils.file_processing import create_daily_folder
from utils.drive import write_daily_news_file, write_ai_newsletter_file, add_to_daily_update
from utils.drive import get_reddit_tech_posts, get_reddit_events_posts
from utils.spotify import add_to_spotify_playlist
from src.scripts import start_of_day, hourly_update

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
    }   