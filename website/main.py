from flask import Flask, render_template
import os
from src.qualia import get_latest_event
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

print(f"Secret Key: {os.getenv('FIREBASE_APP_NAME')}")

@app.route("/")
def index():
    image_url, summary, qualia = get_latest_event()
    spotify_playlist_uri = os.environ.get(
        'SPOTIFY_PLAYLIST_ID', 'spotify:playlist:5SCYMGXrvwRtlCe9sTC7m7')

    return render_template("index.html",
                           image_url=image_url,
                           spotify_playlist_uri=spotify_playlist_uri,
                           image_description=summary)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
