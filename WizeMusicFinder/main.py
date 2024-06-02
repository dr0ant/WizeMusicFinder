import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json

# Load credentials from the JSON file
with open('spotify_cred.json', 'r') as cred_file:
    creds = json.load(cred_file)

client_id = creds['client_ID']
client_secret = creds['client_secret']

# Authenticate with Spotify
credentials = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=credentials)

def get_top_playlists(limit=50):
    try:
        playlists = sp.featured_playlists(limit=limit)
        return playlists['playlists']['items']
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")
        return []

def main():
    top_playlists = get_top_playlists()
    if not top_playlists:
        print("No playlists found or there was an error.")
        return

    for idx, playlist in enumerate(top_playlists, start=1):
        print(f"{idx}. {playlist['name']} by {playlist['owner']['display_name']}")
        print(f"   URL: {playlist['external_urls']['spotify']}")
        print(f"   Description: {playlist['description']}")
        print(f"   Tracks: {playlist['tracks']['total']}")
        print()

if __name__ == '__main__':
    main()
