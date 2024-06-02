import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def load_credentials():
    # Load Spotify API credentials from a file or environment variables
    client_id = 'your_client_id'
    client_secret = 'your_client_secret'
    return client_id, client_secret

def authenticate_spotify():
    logging.info("Authenticating Spotify...")
    
    # Load Spotify credentials
    client_id, client_secret = load_credentials()
    
    logging.info("Loaded Spotify credentials.")
    
    try:
        # Authenticate with Spotify API
        credentials = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=credentials)
        logging.info("Successfully authenticated with Spotify.")
        return sp
    except Exception as e:
        logging.error("Failed to authenticate with Spotify: %s", str(e))
        return None

def get_artist_details(sp, artist_id):
    try:
        # Get artist details
        artist = sp.artist(artist_id)
        
        # Print artist details
        print("Name:", artist['name'])
        print("Genres:", ', '.join(artist['genres']))
        print("Followers:", artist['followers']['total'])
        print("Popularity:", artist['popularity'])
        print("URL:", artist['external_urls']['spotify'])
    except Exception as e:
        logging.error("Failed to fetch artist details. Error: %s", str(e))

if __name__ == "__main__":
    sp = authenticate_spotify()
    if sp:
        print("Successfully authenticated with Spotify.")
        artist_id = input("Enter the artist ID: ")
        get_artist_details(sp, artist_id)
    else:
        print("Failed to authenticate with Spotify.")
