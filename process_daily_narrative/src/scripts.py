from utils.drive import write_daily_news_file, write_ai_newsletter_file
from utils.drive import get_reddit_tech_posts, get_reddit_events_posts
from utils.qualia import update_qualia
from utils.logger_config import system_logger


def start_of_day():
    system_logger.info("Starting the day...")
    write_daily_news_file()
    write_ai_newsletter_file()
    get_reddit_tech_posts()
    get_reddit_events_posts()


def hourly_update():
    system_logger.info("Updating hourly...")
    #TODO process files from daily folder
    update_qualia()
    
def end_of_day():
    system_logger.info("Ending the day...")
    #todo get learnings
    