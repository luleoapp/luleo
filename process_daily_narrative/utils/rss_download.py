import html2text
import feedparser
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
import textwrap
from utils.openai_api import get_article_summary
import traceback

def get_latest_article(rss_url):
    # Parse the RSS feed
    feed = feedparser.parse(rss_url)
    
    # Get the latest entry
    latest_entry = feed.entries[0]
    
    # Extract relevant information
    title = latest_entry.title
    date = latest_entry.published
    content = latest_entry.content[0].value
    
    # Convert HTML content to plain text
    h = html2text.HTML2Text()
    h.ignore_links = False
    plain_text_content = h.handle(content)
    
    return {
        "title": title,
        "date": date,
        "content": plain_text_content
    }

def get_feed_details_of_substack_sites():
    return {
        "Zvi" : {
            "feed_url" : "https://thezvi.substack.com/feed",
            "latest_article_retrieved" : ""
        }
    }

def create_pdf(title, summary, output_filename):
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


def write_substack_pdfs():
    d_substack_feeds_details = get_feed_details_of_substack_sites()
    for key,val in d_substack_feeds_details.items():
        try:
            print(val)
            article = get_latest_article(val["feed_url"])
            if article["title"].lower().strip() == val["latest_article_retrieved"].lower().strip():
                print("'{0}' already retrieved for {1} feed".format(article["title"], key))
            summary = get_article_summary(article["content"])
            create_pdf("Article Summary", summary, "article_summary.pdf")
        except Exception as e:
            print("ERROR in getting feed for {0} {1}".format(key,e))
            traceback.print_exc()
