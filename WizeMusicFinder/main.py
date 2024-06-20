import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
from datetime import datetime, timedelta
import pprint
import requests
import os
import psycopg2
from psycopg2 import sql
import wget
from tqdm import tqdm
import logging
import concurrent.futures



# Adjust the parameters
params = {
    'limit': 50,  # Adjust the number of albums to retrieve
    'offset': 5,
}

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load credentials from the JSON file
def load_credentials(filename='spotify_cred.json'):
    with open(filename, 'r') as cred_file:
        creds = json.load(cred_file)
    return creds['client_ID'], creds['client_secret']

# Load credentials from the JSON file
def load_credentials_postgres(filename='postgres_cred.json'):
    with open(filename, 'r') as cred_file:
        creds_postgres = json.load(cred_file)

   # print (creds_postgres['host'], creds_postgres['port'],  creds_postgres['database'], creds_postgres['user'], creds_postgres['password'])
    return creds_postgres['host'], creds_postgres['port'],  creds_postgres['database'], creds_postgres['user'], creds_postgres['password']

def authenticate_spotify():
    logging.info("Authenticating Spotify...")
    
    # Load Spotify credentials
    client_id, client_secret = load_credentials()
    
    logging.info("Loaded Spotify credentials.")
    
    # Authenticate with Spotify API
    credentials = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=credentials)
    
    logging.info("Successfully authenticated with Spotify.")
    
    return sp











def get_top_playlists(limit=50):
    sp = authenticate_spotify()
    try:
        playlists = sp.featured_playlists(limit=limit)
        return playlists['playlists']['items']
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")
        return []



def get_genres():
    sp = authenticate_spotify()
    genres = set()

    # Retrieve available genres directly from the Spotify API
    response = sp.recommendation_genre_seeds()
    if 'genres' in response:
        genres.update(response['genres'])

    return sorted(genres)




# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_album_tracks(sp, album_id):
    logging.info(f"Fetching album tracks for album ID: {album_id}")
    return sp.album_tracks(album_id)

def fetch_track_details(sp, track_id):
    logging.info(f"Fetching track details for track ID: {track_id}")
    return sp.track(track_id)

def fetch_artist_details(artist_id):
    logging.info(f"Fetching artist details for artist ID: {artist_id}")
    
    # Authenticate with Spotify to get access token
    sp = authenticate_spotify()
    
    # Define the API endpoint
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    
    # Make the GET request to the API
    response = sp._get(url)  # Using internal method to access authenticated request
    #print(response)
    # Check if the request was successful

    artist_details = response
    return artist_details
    


def get_top_tracks(sp, genre):
    logging.info(f"Starting to get top tracks for genre: {genre}")

    # Get current date
    current_date = datetime.now().date()
    logging.info(f"Current date: {current_date}")
    
    # Calculate the date three months ago
    three_months_ago = current_date - timedelta(days=90)
    logging.info(f"Date three months ago: {three_months_ago}")
    
    # Make the API call to retrieve new releases
    logging.info("Retrieving new releases...")
    new_releases = sp.new_releases(country='US', limit=50, offset=0)

    top_tracks = []
    artist_genre_cache = {}
    
    # Filter albums by release date
    recent_albums = [album for album in new_releases['albums']['items'] 
                     if datetime.strptime(album['release_date'], '%Y-%m-%d').date() >= three_months_ago]
    
    logging.info(f"Filtered {len(recent_albums)} recent albums.")
    
    # Fetch artist genres sequentially
    for album in recent_albums:
        artist_id = album['artists'][0]['id']
        if artist_id not in artist_genre_cache:
            print(artist_genre_cache)
            artist_details = fetch_artist_details(sp, artist_id)
            artist_genre_cache[artist_id] = [g.lower() for g in artist_details['genres']]
    
    logging.info(f"Fetched genres for {len(artist_genre_cache)} artists.")
    
    # Filter albums by genre and collect tracks
    for album in recent_albums:
        artist_id = album['artists'][0]['id']
        if genre.lower() in artist_genre_cache.get(artist_id, []):
            logging.info(f"Fetching tracks for album: {album['name']} (ID: {album['id']})")
            album_tracks = sp.album_tracks(album['id'])
            for track in album_tracks['items']:
                song_info = {
                    'name': track['name'],
                    'artists': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': album['name'],
                    'release_date': album['release_date'],
                    'popularity': track['popularity'],
                    'preview_url': track['preview_url'],
                }
                top_tracks.append(song_info)
                logging.info(f"Added track: {track['name']} by {track['artists'][0]['name']}")

    # Sort the tracks by popularity in descending order
    top_tracks.sort(key=lambda x: x['popularity'], reverse=True)
    logging.info("Tracks sorted by popularity.")
    
    # Return the top 20 tracks
    top_20_tracks = top_tracks[:20]
    logging.info(f"Returning top {len(top_20_tracks)} tracks.")
    
    return top_20_tracks


def download_weekly_genre_playlist(genres):
    sp = authenticate_spotify()
    
    # Load PostgreSQL credentials
    print("Loading PostgreSQL credentials...")
    postgres_host, postgres_port, postgres_db, postgres_user, postgres_password = load_credentials_postgres()
    print("PostgreSQL credentials loaded.")
    
    # Connect to the database
    print("Connecting to the database...")
    conn = psycopg2.connect(host=postgres_host, port=postgres_port, database=postgres_db, user=postgres_user, password=postgres_password)
    cur = conn.cursor()
    print("Connected to the database.")

    # Get current date and week number
    current_date = datetime.now()
    week_number = current_date.isocalendar()[1]
    
    for genre in genres:
        print(f"Processing genre: {genre}")
        
        # Create folder for the playlist
        folder_name = f"Playlist_week_{week_number}_{genre}"
        os.makedirs(folder_name, exist_ok=True)
        print(f"Created folder: {folder_name}")
        
        # Get top tracks for the genre
        print(f"Retrieving top tracks for genre: {genre}")
        top_tracks = get_top_tracks(sp, genre)
        
        for track in top_tracks:
            # Insert track information into the database
            insert_query = sql.SQL("INSERT INTO wizeplaylist.weekly_playlist (name, album, release_date, popularity, artist, week_nb, genre) VALUES (%s, %s, %s, %s, %s, %s, %s)")
            cur.execute(insert_query, (track['name'], track['album'], track['release_date'], track['popularity'], track['artists'], week_number, genre))
            conn.commit()
            print(f"Inserted track into database: {track['name']}")

            # Download the track
            track_name = track['name'] + '.mp3'
            track_url = track['preview_url']
            if track_url:
                track_path = os.path.join(folder_name, track_name)
                print(f"Downloading track: {track['name']}")
                wget.download(track_url, track_path)
                print(f"Downloaded track to: {track_path}")

    # Close the database connection
    print("Closing database connection...")
    cur.close()
    conn.close()
    print("Database connection closed.")





#print(load_credentials_postgres(filename='postgres_cred.json'))






#download_weekly_genre_playlist(['pop'])

#fetch_artist_details('5slpk6nu2IwwKx0EHe3GcL')






""""

def main():
    print("Top Playlists on Spotify:")
    playlists = get_top_playlists()
    if not playlists:
        print("No playlists found or there was an error.")
    else:
        for idx, playlist in enumerate(playlists, start=1):
            print(f"{idx}. {playlist['name']} by {playlist['owner']['display_name']}")
            print(f"   URL: {playlist['external_urls']['spotify']}")
            print(f"   Description: {playlist['description']}")
            print(f"   Tracks: {playlist['tracks']['total']}")
            print()

    print("\nGenres of music available on Spotify:")
    genres = get_genres()
    for genre in genres:
        print(genre)
    





    genre = 'pop'
    print(f"Most Listened Songs in the {genre.capitalize()} Genre Released in the Last 3 Months on Spotify:")
    top_songs = get_top_tracks(genre)
    if not top_songs:
        print(f"No songs found in the {genre.capitalize()} genre released in the last 3 months or there was an error.")
    else:
        for idx, song in enumerate(top_songs, start=1):
            print(f"{idx}. {song['name']} by {song['artists']}")
            print(f"   Album: {song['album']}")
            print(f"   Release Date: {song['release_date']}")
            print(f"   Popularity: {song['popularity']}")
            print(f"   Preview URL: {song['preview_url']}")
            print()

if __name__ == '__main__':
    main()

"""
