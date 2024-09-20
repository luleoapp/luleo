from flask import Flask, render_template
import os
from src.qualia import get_latest_event
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    image_url, summary, qualia = get_latest_event()
    spotify_playlist_uri = os.environ.get(
        'SPOTIFY_PLAYLIST_ID', 'spotify:playlist:5SCYMGXrvwRtlCe9sTC7m7')

    print(f"Debug - Image URL: {image_url}")  # Add this line
    print(f"Debug - Summary: {summary}")      # Add this line

    return render_template("index.html",
                           image_url=image_url,
                           spotify_playlist_uri=spotify_playlist_uri,
                           image_description=summary)


if __name__ == "__main__":
    
    app.run(host="0.0.0.0", port=8080, debug=True)
