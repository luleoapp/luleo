import io
from googleapiclient.http import MediaIoBaseDownload
from utils.file_processing import process_file_content
import os 
from utils.pdf_generator import download_file, combine_pdfs, save_as_pdf
import tempfile 
from googleapiclient.http import MediaFileUpload
import datetime
import feedparser
from dateutil import parser as date_parser
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors    
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import textwrap
from github import Github 
from github import Auth
import base64
import json
from reportlab.lib.utils import ImageReader
import requests
from io import BytesIO
from bs4 import BeautifulSoup
from utils.openai_api import get_article_summary
from firebase_admin import firestore
import hashlib
from github.InputGitTreeElement import InputGitTreeElement  # Add this import
import random
import praw
from utils.db_init import drive_service, db, PROJECT_TIMEZONE




def list_files_in_folder(folder_id):
    try:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents",
            pageSize=1000,
            fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])
        if not items:
            print('No files found.')
        else:
            for item in items:
                print(f'{item["name"]} ({item["id"]}) - {item["mimeType"]}')
        return items
    except Exception as e:
        print(f'Error listing files in folder: {e}')
        return []

def download_and_process_file(file_id, file_name, mime_type, parent_path):
    try:
        if mime_type.startswith('application/vnd.google-apps.'):
            if mime_type == 'application/vnd.google-apps.document':
                request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                request = drive_service.files().export_media(fileId=file_id, mimeType='text/csv')
            elif mime_type == 'application/vnd.google-apps.presentation':
                request = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
            else:
                print(f'Cannot export file type: {mime_type}')
                return None, None
        else:
            request = drive_service.files().get_media(fileId=file_id)
        
        content = download_file(request)
        pdf_file = process_file_content(file_name, content)
        return pdf_file
    except Exception as e:
        print(f'Error downloading or processing file {file_name}: {e}')
        return None

def traverse_and_download(folder_id, parent_path, contents):
    files = list_files_in_folder(folder_id)
    lst_pdf_files = []
    for file in files:
        file_id = file['id']
        file_name = file['name']
        mime_type = file['mimeType']
        print(f'Processing {file_name} ({file_id})...')
        
        if mime_type == 'application/vnd.google-apps.folder':
            # Create local directory
            subfolder_path = os.path.join(parent_path, file_name)
            os.makedirs(subfolder_path, exist_ok=True)
            # Recursively traverse the subfolder
            traverse_and_download(file_id, subfolder_path, contents)
        else:
            tmp_pdf_file = download_and_process_file(file_id, file_name, mime_type, parent_path)
            if tmp_pdf_file:
                contents.append(tmp_pdf_file)
                print("PDF ",tmp_pdf_file)
    output_pdf = combine_pdfs([k[0] for k in contents])


def find_subfolder_id(root_folder_id, subfolder_name):
    files = list_files_in_folder(root_folder_id)
    for file in files:
        if file['name'] == subfolder_name and file['mimeType'] == 'application/vnd.google-apps.folder':
            return file['id']
    return None


def create_folder(folder_name, parent_id):
    curr_folder_id = find_subfolder_id(parent_id, folder_name)
    if curr_folder_id:
        print(f'Error : {folder_name} already exists under {parent_id} : {curr_folder_id}')
        return curr_folder_id
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id] if parent_id else []

    }
    folder = drive_service.files().create(body=file_metadata, fields='id').execute()
    return folder.get("id")

def create_initialize_subfolders(folder_id, lst_subfolders):
    if not folder_id:
        print("ERROR - Folder ID not found")
        return 
    #AI/ Luleo/ News/ Art/
    d_folders = {}
    for folder_name in lst_subfolders:
        d_folders[folder_name.lower()] = create_folder(folder_name, folder_id)
    
    return d_folders


def format_news_json_for_pdf(news_json):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=12)
    source_style = ParagraphStyle('Source', parent=styles['Italic'], alignment=TA_CENTER)
    url_style = ParagraphStyle('URL', parent=styles['BodyText'], textColor='blue', alignment=TA_CENTER)
    summary_style = ParagraphStyle('Summary', parent=styles['BodyText'], alignment=TA_JUSTIFY, firstLineIndent=20, spaceBefore=12, spaceAfter=12)
    date_style = ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER)

    formatted_content = []
    for i, article in enumerate(news_json["articles"]):
        title = article.get("title", "No Title")
        link = article.get("link", "No URL")
        content = article.get("summary", "No Summary")
        published = article.get("published", "No Date")
        source = article.get("source", "Unknown Source")
        
        try:
            date = datetime.datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z').strftime("%B %d, %Y %H:%M")
        except ValueError:
            date = published
        
        print(f"Formatting article {i+1}:")
        print(f"  Title: {title}")
        print(f"  Source: {source}")
        print(f"  Date: {date}")
        
        # Clean the content HTML, removing images and keeping only text
        soup = BeautifulSoup(content, 'html.parser')
        for img in soup.find_all('img'):
            img.decompose()
        clean_content = soup.get_text()
        
        # Get article summary
        summary = get_article_summary(clean_content)
        
        formatted_content.append(Paragraph(title, title_style))
        formatted_content.append(Paragraph(f"Source: {source}", source_style))
        formatted_content.append(Paragraph(f"Published: {date}", date_style))
        formatted_content.append(Paragraph(f"URL: {link}", url_style))
        formatted_content.append(Paragraph(f"Summary: {summary}", summary_style))
        formatted_content.append(Spacer(1, 20))  # Add extra space between entries
    
    return formatted_content

def write_daily_news_file(overwrite=False, max_articles=None):
    # Generate the filename and paths with the current date
    current_date = datetime.datetime.now(PROJECT_TIMEZONE).strftime("%Y-%m-%d")
    filename = f"{current_date}_news.pdf"
    outputs_dir = os.path.join(os.getcwd(), 'outputs')
    local_filepath = os.path.join(outputs_dir, filename)
    github_file_path = f"daily_data/{current_date}/inputs/news_and_events/{filename}"
    if not overwrite:
        #check if file exists in github
        file_exists =  check_if_file_exists_in_github(github_file_path)
        if file_exists:
            print(f"File {github_file_path} already exists in GitHub.")
            return {"message": f"File {github_file_path} already exists in GitHub."}
    
    
    news_json = get_daily_news(github_file_path, max_articles)
    if len(news_json['articles']) == 0:
        print("ERROR: No news articles were retrieved.")
        return {"error": "No news articles were retrieved."}
    
    # Create the outputs directory if it doesn't exist
    os.makedirs(outputs_dir, exist_ok=True)
    
    # Create the PDF document
    doc = SimpleDocTemplate(local_filepath, pagesize=letter)
    
    # Define styles
    styles = getSampleStyleSheet()
    headline_style = ParagraphStyle(
        'Headline',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=12,
        underline=True
    )
    
    # Create the content
    content = []
    
    # Add the headline
    content.append(Paragraph("Today's News", headline_style))
    content.append(Spacer(1, 12))  # Add some space after the headline
    
    # Add the news content
    formatted_news = format_news_json_for_pdf(news_json)
    
    # Debug: Print out formatted news
    print(f"Number of formatted news items: {len(formatted_news)}")
    
    if len(formatted_news) == 0:
        print("ERROR: No news items were formatted for PDF.")
        return {"error": "No news items were formatted for PDF."}
    
    content.extend(formatted_news)
    
    # Build the PDF
    doc.build(content)
    
    print(f"Daily news saved as {local_filepath}")

    # Define the GitHub file path
    
    # Upload the file to GitHub
    result = upload_file_to_github(local_filepath, github_file_path)
    
    return result

def get_daily_news(github_file_path, max_articles=None):
    # Read RSS feed URLs from file
    with open('files/news_rss_feeds.txt', 'r') as f:
        rss_feeds = [line.strip() for line in f]

    print(rss_feeds)
    
    news_items = []
    
    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            article = check_and_store_article(github_file_path, entry, feed.feed.get('title', ''))
            if article:
                news_items.append(article)
    
    # Sort news items by publication date (newest first)
    news_items.sort(key=lambda x: date_parser.parse(x['published']), reverse=True)
    
    # Randomly select max_articles if specified
    if max_articles and max_articles < len(news_items):
        news_items = random.sample(news_items, max_articles)
    
    # Create the final JSON structure
    news_json = {
        'date': datetime.datetime.now(PROJECT_TIMEZONE).strftime('%Y-%m-%d'),
        'articles': news_items
    }
    
    return news_json
    

def check_and_store_article(github_file_path, article, source):
    # Create a unique identifier for the article
    article_id = hashlib.md5(f"{source}_{article.get('id', article.get('link', ''))}".encode()).hexdigest()

    # Check if this article already exists in Firestore
    doc_ref = db.collection('retrieved_articles').document(article_id)
    
    try:
        doc = doc_ref.get()
        if not doc.exists:
            # Article doesn't exist in the database, so it's new
            article_data = {
                'title': article.get('title', ''),
                'link': article.get('link', ''),
                'published': article.get('published', ''),
                'summary': article.get('summary', ''),
                'source': source,
                'retrieved_at': firestore.SERVER_TIMESTAMP,
                'github_file_path' : github_file_path,
                'processed_for_qualia' : False,
                'qualia_event_id' : ''
            }

            # Add the article to Firestore
            doc_ref.set(article_data)
            print(f"New article found: {article_data['title']}")
            return article_data
        else:
            print(f"Article already retrieved: {article.get('title', '')}")
            return None
    except Exception as e:
        print(f"Error processing article: {e}")
        return None

def create_article_pdf(title, summary, output_filename):
    doc = SimpleDocTemplate(output_filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

    content = []
    
    # Add title
    content.append(Paragraph(title, styles['Title']))
    content.append(Spacer(1, 12))
    
    # Add summary
    wrapped_text = textwrap.fill(summary, width=80)
    for para in wrapped_text.split('\n'):
        content.append(Paragraph(para, styles['Justify']))
        content.append(Spacer(1, 12))
    
    doc.build(content)
    print("PDF created successfully.")


def check_if_file_exists_in_github(github_file_path):
    github_token = os.environ.get('GITHUB_TOKEN')
    repo_name = os.environ.get('GITHUB_REPO_NAME')
    
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    if not repo_name:
        raise ValueError("GITHUB_REPO_NAME environment variable is not set")

    g = Github(github_token)
    
    try:
        repo = g.get_repo(repo_name)
        try:
            # Try to get the file contents
            repo.get_contents(github_file_path)
            return True
        except Exception:
            # If an exception is raised, the file doesn't exist
            return False
    except Exception as e:
        print(f"Error checking if file exists in GitHub: {str(e)}")
        return False
    
def upload_file(file_path, parent_id, upload_file_name=None):
    file_metadata = {
        'name': upload_file_name or os.path.basename(file_path),
        'parents': [parent_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def upload_file_to_github(file_path, github_file_path):
    try:
        # Read the file in binary mode
        with open(file_path, 'rb') as file:
            content = file.read()

        # Initialize the GitHub client
        github_token = os.environ.get('GITHUB_TOKEN')
        repo_name = os.environ.get('GITHUB_REPO_NAME')
        
        print(f"Attempting to upload to GitHub repository: {repo_name}")
        
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        if not repo_name:
            raise ValueError("GITHUB_REPO_NAME environment variable is not set")
        
        g = Github(github_token)
        
        try:
            repo = g.get_repo(repo_name)
        except Exception as repo_error:
            print(f"Error accessing repository: {str(repo_error)}")
            raise

        # Get the latest commit
        master_ref = repo.get_git_ref('heads/main')
        master_sha = master_ref.object.sha
        base_tree = repo.get_git_tree(master_sha)

        # Create a new blob with the file content
        blob = repo.create_git_blob(base64.b64encode(content).decode(), "base64")

        # Create a new tree with the new blob
        element = InputGitTreeElement(path=github_file_path, mode='100644', type='blob', sha=blob.sha)
        new_tree = repo.create_git_tree([element], base_tree)

        # Create a new commit
        parent = repo.get_git_commit(master_sha)
        commit = repo.create_git_commit(f"Update {github_file_path}", new_tree, [parent])

        # Update the reference
        master_ref.edit(commit.sha)

        print(f"File {github_file_path} uploaded to GitHub successfully.")
        return {"message": f"File {github_file_path} uploaded to GitHub successfully."}

    except Exception as e:
        error_message = f"Error uploading file to GitHub: {str(e)}"
        print(error_message)
        print(f"GitHub Token (first 10 chars): {github_token[:10] if github_token else 'Not set'}")
        print(f"Repo Name: {repo_name}")
        print(f"GitHub File Path: {github_file_path}")
        return {"error": error_message}




def get_latest_ai_articles(github_file_path, max_articles=None):
    # Read RSS feed URLs from file
    with open('files/ai_newsletter_rss_feeds.txt', 'r') as f:
        rss_feeds = [line.strip() for line in f]

    all_articles = []

    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            print(f"No entries found for feed: {feed_url}")
            continue

        for entry in feed.entries:
            article = check_and_store_article(github_file_path, entry, feed.feed.get('title', ''))
            if article:
                all_articles.append(article)

    # Randomly select max_articles if specified
    if max_articles and max_articles < len(all_articles):
        selected_articles = random.sample(all_articles, max_articles)
    else:
        selected_articles = all_articles

    return selected_articles

def format_ai_articles_for_pdf(articles):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=12)
    source_style = ParagraphStyle('Source', parent=styles['Italic'], alignment=TA_CENTER)
    url_style = ParagraphStyle('URL', parent=styles['BodyText'], textColor='blue', alignment=TA_CENTER)
    summary_style = ParagraphStyle('Summary', parent=styles['BodyText'], alignment=TA_JUSTIFY, firstLineIndent=20, spaceBefore=12, spaceAfter=12)
    date_style = ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER)

    formatted_content = []
    for article in articles:
        title = article.get('title', 'No Title')
        link = article.get('link', 'No URL')
        published = article.get('published', 'No Date')
        content = article.get('summary', 'No Summary')
        source = article.get('source', 'Unknown Source')

        # Get article summary
        summary = get_article_summary(content)
        summary_text = summary if isinstance(summary, str) else summary[0].text if summary else "No summary available."

        formatted_content.append(Paragraph(title, title_style))
        formatted_content.append(Paragraph(f"Source: {source}", source_style))
        formatted_content.append(Paragraph(f"Published: {published}", date_style))
        formatted_content.append(Paragraph(f"URL: {link}", url_style))
        formatted_content.append(Paragraph(f"Summary: {summary_text}", summary_style))
        formatted_content.append(Spacer(1, 20))  # Add extra space between entries

    return formatted_content


def write_ai_newsletter_file(max_articles=None):
    # Generate the filename with the current date
    current_date = datetime.datetime.now(PROJECT_TIMEZONE).strftime("%Y-%m-%d")
    filename = f"{current_date}_ai_newsletter.pdf"
    outputs_dir = os.path.join(os.getcwd(), 'outputs')
    filepath = os.path.join(outputs_dir, filename)
    github_file_path = f"daily_data/{current_date}/inputs/AI_updates/{filename}"

    articles = get_latest_ai_articles(github_file_path, max_articles)
    
    if not articles:
        print("No new AI articles found.")
        return {"message": "No new AI articles found."}

    # Create the outputs directory if it doesn't exist
    os.makedirs(outputs_dir, exist_ok=True)
    

    # Create the PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    
    # Define styles
    styles = getSampleStyleSheet()
    headline_style = ParagraphStyle(
        'Headline',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=12,
        underline=True
    )
    
    # Create the content
    content = []
    
    # Add the headline
    content.append(Paragraph("Latest AI News", headline_style))
    content.append(Spacer(1, 12))  # Add some space after the headline
    
    # Add the news content
    formatted_news = format_ai_articles_for_pdf(articles)
    content.extend(formatted_news)
    
    # Build the PDF
    doc.build(content)
    
    print(f"AI newsletter saved as {filepath}")

    # Define the GitHub file path
    
    # Upload the file to GitHub
    result = upload_file_to_github(filepath, github_file_path)
    
    return result

def add_to_daily_update(update_text):
    # Get current date
    curr_dt = datetime.datetime.now(PROJECT_TIMEZONE).strftime("%Y-%m-%d")
    
    # Reference to the daily_updates collection
    daily_updates_ref = db.collection('daily_updates').document(curr_dt)
    
    # Add the update to Firestore
    daily_updates_ref.set({
        'updates': firestore.ArrayUnion([update_text])
    }, merge=True)
    
    # Retrieve all updates for the day
    doc = daily_updates_ref.get()
    updates = doc.to_dict().get('updates', []) if doc.exists else []
    
    # Create PDF
    outputs_dir = os.path.join(os.getcwd(), 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    pdf_path = os.path.join(outputs_dir, f"{curr_dt}_daily_update.pdf")
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'], leftIndent=20, firstLineIndent=-20, spaceAfter=10)
    
    story = [Paragraph("Daily Updates", styles['Title']), Spacer(1, 12)]
    for update in updates:
        story.append(Paragraph(f"• {update}", bullet_style))
    
    doc.build(story)
    
    # Upload PDF to GitHub
    github_file_path = f"daily_data/{curr_dt}/inputs/luleo/daily_update.pdf"
    upload_result = upload_file_to_github(pdf_path, github_file_path)
    
    return {
        "message": "Update added successfully",
        "pdf_upload": upload_result
    }


def check_and_store_reddit_post(github_file_path, post):
    # Use the Reddit post ID as the document name
    doc_ref = db.collection('retrieved_reddit_posts').document(post.id)
    
    try:
        doc = doc_ref.get()
        if not doc.exists:
            # Post doesn't exist in the database, so it's new
            post_data = {
                'title': post.title,
                'url': f'https://www.reddit.com{post.permalink}',
                'author': post.author.name if post.author else '[deleted]',
                'score': post.score,
                'num_comments': post.num_comments,
                'subreddit': post.subreddit.display_name,
                'retrieved_at': firestore.SERVER_TIMESTAMP,
                'github_file_path' : github_file_path,
                'processed_for_qualia' : False,
                'qualia_event_id' : '',
                'summary' : generate_reddit_post_summary(post)
            }   


            # Add the post to Firestore
            doc_ref.set(post_data)
            print(f"New Reddit post found: {post_data['title']}")
            return post_data
        else:
            print(f"Reddit post already retrieved: {post.title}")
            return None
    except Exception as e:
        print(f"Error processing Reddit post: {e}")
        return None
    
def generate_reddit_post_summary(submission):
    description = []
    # Basic post info
    description.append(f"Title: {submission.title}")
    description.append(f"Posted by u/{submission.author} in r/{submission.subreddit}")
    
    # Check if it's a text post or link/media
    if submission.is_self:
        if submission.selftext:
            description.append(f"Text post: {submission.selftext[:200]}...")  # Short snippet of the body
        else:
            description.append("Text post with no content.")
    elif submission.url:
        description.append(f"Link post: {submission.url}")
    else:
        description.append("Media post.")

    # Engagement and status details
    description.append(f"Upvote score: {submission.score}")
    description.append(f"Number of comments: {submission.num_comments}")
    description.append(f"Upvote ratio: {submission.upvote_ratio:.2f}")
    
    # NSFW and lock status
    if submission.over_18:
        description.append("⚠️ NSFW content.")
    if submission.locked:
        description.append("This post is locked.")
    
    return "\n".join(description)


def scrape_reddit_posts(github_file_path, max_posts=None, category='tech'):
    # Initialize Reddit API client
    reddit = praw.Reddit(
        client_id=os.environ.get('REDDIT_CLIENT_ID'),
        client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
        user_agent=os.environ.get('REDDIT_USER_AGENT', 'MyBot/1.0')
    )

    # Determine which file to read based on the category
    filename = f'files/subreddits_{category}.txt'

    # Read subreddits from file
    with open(filename, 'r') as f:
        subreddits = [line.strip() for line in f if line.strip()]

    all_posts = {}
    total_posts = 0

    for subreddit_name in subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts = []
            for post in subreddit.hot(limit=10):  # Fetch more than needed to account for duplicates
                post_data = check_and_store_reddit_post(github_file_path, post)
                if post_data:
                    posts.append(post_data)
                    total_posts += 1
                    if max_posts and total_posts >= max_posts:
                        break
            if posts:
                all_posts[subreddit_name] = posts
            if max_posts and total_posts >= max_posts:
                break
        except Exception as e:
            print(f"Error scraping r/{subreddit_name}: {str(e)}")

    return all_posts

def create_reddit_pdf(pdf_filename, posts, category):
    outputs_dir = os.path.join(os.getcwd(), 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    pdf_path = os.path.join(outputs_dir, pdf_filename)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], spaceAfter=12)
    subreddit_style = ParagraphStyle('Subreddit', parent=styles['Heading2'], spaceAfter=6, spaceBefore=12)
    post_title_style = ParagraphStyle('PostTitle', parent=styles['Heading3'], spaceAfter=3)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], spaceAfter=6)
    
    story = [Paragraph(f"Latest Reddit {category.capitalize()} Posts", styles['Title']), Spacer(1, 12)]
    
    for subreddit, subreddit_posts in posts.items():
        story.append(Paragraph(f"r/{subreddit}", subreddit_style))
        for post in subreddit_posts:
            story.append(Paragraph(post['title'], post_title_style))
            story.append(Paragraph(f"URL: {post['url']}", normal_style))
            story.append(Paragraph(f"Author: {post['author']} | Score: {post['score']} | Comments: {post['num_comments']}", normal_style))
        story.append(Spacer(1, 12))
    
    doc.build(story)
    return pdf_path

def get_reddit_posts(category, overwrite=False, max_posts=10):
    curr_dt = datetime.datetime.now(PROJECT_TIMEZONE).strftime("%Y-%m-%d")
    pdf_filename = f"{curr_dt}_reddit_{category}_posts.pdf"
    input_folder = "AI_updates" if category == 'tech' else "news_and_events"

    github_file_path = f"daily_data/{curr_dt}/inputs/{input_folder}/{pdf_filename}"

    file_exists =  check_if_file_exists_in_github(github_file_path)
    if file_exists:
        print(f"File {github_file_path} already exists in GitHub.")
        return {"message": f"File {github_file_path} already exists in GitHub."}

    posts = scrape_reddit_posts(github_file_path,max_posts, category)
    pdf_path = create_reddit_pdf(pdf_filename, posts, category)
    upload_result = upload_file_to_github(pdf_path, github_file_path)
    
    return {
        "message": f"Reddit {category} posts scraped (max: {max_posts}) and PDF created successfully",
        "pdf_upload": upload_result
    }


def get_reddit_tech_posts(max_posts=10):
    return get_reddit_posts('tech', max_posts)

def get_reddit_events_posts(max_posts=10):
    return get_reddit_posts('events', max_posts)
