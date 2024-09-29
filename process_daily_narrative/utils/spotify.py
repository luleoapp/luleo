import os
import requests# Function to refresh the access token
from openai import OpenAI
import json
from google.cloud import firestore
from datetime import datetime, timedelta
import re

from utils.llm_utils import call_and_log_llm

# Initialize Firestore client
db = firestore.Client()


def refresh_access_token():
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    if response.status_code == 200:
        access_token = response.json()['access_token']
        print("New access token:", access_token)
        # Optionally store the new access token somewhere safe if needed
        return access_token
    else:
        print("Failed to refresh access token:", response.status_code, response.text)
        return None
        
def get_track_uri(access_token, track_name, artist_name):
    query = f"track:{track_name} artist:{artist_name}"
    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        params={
            "q": query,
            "type": "track",
            "limit": 1
        }
    )

    if response.status_code == 200 and response.json()['tracks']['items']:
        track_uri = response.json()['tracks']['items'][0]['uri']
        return track_uri
    else:
        print("Failed to find the track:", response.status_code, response.text)
        return None

def add_track_to_playlist(access_token, playlist_id, track_uri):
    response = requests.post(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "uris": [track_uri]
        }
    )

    if response.status_code == 201:
        print("Track added to playlist successfully!")
    else:
        print("Failed to add track to playlist:", response.status_code, response.text)



def add_song_to_playlist(mood, access_token, playlist_id, repeat_song_time=timedelta(days=30), list_seen_songs=None):
    # Get the current songs in the playlist
    current_songs = get_playlist_tracks(access_token, playlist_id)
    
    # Format the current playlist
    current_playlist = "Current playlist:\n"
    if not current_songs:
        current_playlist += "Empty\n"
    else:
        for song in current_songs[:10]:  # Limit to first 10 songs
            current_playlist += f"- {song['name']} by {', '.join(song['artists'])}\n"

    # Load the prompt template
    with open('prompts/spotify.prompt', 'r') as file:
        prompt_template = file.read()

    # Load the article
    with open('prompts/how_to_make_a_good_playlist.prompt', 'r') as file:
        article = file.read()

    #Load the luleo prompt
    from utils.luleo import get_luleo_prompt
    luleo_prompt = get_luleo_prompt()

    # Substitute variables into the prompt
    prompt = prompt_template.replace('{{MOOD}}', str(mood))
    prompt = prompt.replace('{{CURRENT_PLAYLIST}}', current_playlist)
    prompt = prompt.replace('{{ARTICLE}}', article)

    # Add the creativity patch if list_seen_songs is provided
    if list_seen_songs:
        creativity_patch = f"\n\nPlease be creative in your choices and ignore the following songs:\n{', '.join(list_seen_songs)}\n"
        prompt += creativity_patch

    response_json = call_and_log_llm(luleo_prompt, prompt, "gpt-4o-mini")
    suggestions = response_json['song_recommendation_list']

    print("\nParsed suggestions:")
    print(json.dumps(suggestions, indent=2))

    # Try to add songs, checking for recent additions
    songs_added = False
    if list_seen_songs is None:
        list_seen_songs = []

    for song_to_add in suggestions:
        track_name = song_to_add['title']
        artist_name = song_to_add['artist']
        
        if f"{track_name} - {artist_name}" in list_seen_songs:
            continue

        track_uri = get_track_uri(access_token, track_name, artist_name)
        
        if track_uri:
            track_id = track_uri.split(':')[-1]
            if not was_song_recently_added(track_id, playlist_id, repeat_song_time):
                remove_earliest_track_from_playlist(access_token, playlist_id)
                add_track_to_playlist(access_token, playlist_id, track_uri)
                add_song_to_firestore(track_id, track_name, artist_name, playlist_id)
                songs_added = True
                return f"Added '{track_name}' by {artist_name} to the playlist.", track_id, track_name, artist_name
            else:
                print(f"Skipped '{track_name}' by {artist_name} as it was recently added.")
        else:
            print(f"Couldn't find '{track_name}' by {artist_name} on Spotify.")
        
        list_seen_songs.append(f"{track_name} - {artist_name}")

    if not songs_added:
        if len(list_seen_songs) >= 20:
            return "No suitable songs were found after multiple attempts.", None, None, None
        else:
            return add_song_to_playlist(mood, access_token, playlist_id, repeat_song_time, list_seen_songs)

    return "No suitable songs were found to add to the playlist.", None, None, None


def get_playlist_tracks(access_token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        tracks = response.json()['items']
        return [{'name': track['track']['name'], 
                 'artists': [artist['name'] for artist in track['track']['artists']]} 
                for track in tracks]
    else:
        return []


def was_song_recently_added(track_id, playlist_id, repeat_song_time=timedelta(days=30)):
    doc_ref = db.collection('playlist_songs').document(track_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        if data['playlist_id'] == playlist_id:
            added_date = data['added_date'].replace(tzinfo=None)
            if datetime.utcnow() - added_date < repeat_song_time:
                return True
    
    return False

def add_song_to_firestore(track_id, track_name, artist_name, playlist_id):
    doc_ref = db.collection('playlist_songs').document(track_id)
    doc_ref.set({
        'track_name': track_name,
        'artist_name': artist_name,
        'playlist_id': playlist_id,
        'added_date': datetime.utcnow()
    })

def add_to_spotify_playlist(mood):
    playlist_id = os.environ.get("SPOTIFY_PLAYLIST_ID")
    
    if not playlist_id:
        print("Error: SPOTIFY_PLAYLIST_ID not found in environment variables.")
        return

    access_token = refresh_access_token()
    if not access_token:
        print("Error: Failed to refresh access token.")
        return
    
    result, track_id, track_name, artist_name = add_song_to_playlist(mood, access_token, playlist_id)
    print(result)
    return result, track_id, track_name, artist_name

def remove_earliest_track_from_playlist(access_token, playlist_id, max_tracks=23):
    # Get all tracks in the playlist
    tracks = get_all_playlist_tracks(access_token, playlist_id)
    
    # If the number of tracks is 23 or less, no action needed
    if len(tracks) <= max_tracks:
        return

    # Sort tracks by added_at date
    sorted_tracks = sorted(tracks, key=lambda x: x['added_at'])
    
    # Calculate how many tracks to remove
    tracks_to_remove = len(tracks) - max_tracks
    
    # Get the URIs of the tracks to remove
    tracks_to_remove_uris = [track['track']['uri'] for track in sorted_tracks[:tracks_to_remove]]
    
    # Remove tracks in batches of 100 (Spotify API limit)
    for i in range(0, len(tracks_to_remove_uris), 100):
        batch = tracks_to_remove_uris[i:i+100]
        remove_tracks_from_playlist(access_token, playlist_id, batch)

def get_all_playlist_tracks(access_token, playlist_id):
    tracks = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    
    while url:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code != 200:
            print(f"Failed to get playlist tracks: {response.status_code}, {response.text}")
            return tracks
        
        data = response.json()
        tracks.extend(data['items'])
        url = data['next']  # Get the next page URL, if any
    
    return tracks

def remove_tracks_from_playlist(access_token, playlist_id, track_uris):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    
    response = requests.delete(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={"tracks": [{"uri": uri} for uri in track_uris]}
    )
    
    if response.status_code != 200:
        print(f"Failed to remove tracks: {response.status_code}, {response.text}")
    else:
        print(f"Successfully removed {len(track_uris)} tracks from the playlist.")



