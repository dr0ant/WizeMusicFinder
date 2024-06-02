import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Replace these with your Spotify developer credentials


client_id = 'YOUR_CLIENT_ID'
client_secret = 'YOUR_CLIENT_SECRET'

# Authenticate with Spotify
credentials = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=credentials)

def get_top_playlists(limit=100):
    playlists = sp.featured_playlists(limit=limit)
    return playlists['playlists']['items']

def main():
    top_playlists = get_top_playlists()
    for idx, playlist in enumerate(top_playlists, start=1):
        print(f"{idx}. {playlist['name']} by {playlist['owner']['display_name']}")
        print(f"   URL: {playlist['external_urls']['spotify']}")
        print(f"   Description: {playlist['description']}")
        print(f"   Tracks: {playlist['tracks']['total']}")
        print()

if __name__ == '__main__':
    main()
