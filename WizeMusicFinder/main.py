import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
from datetime import datetime, timedelta
import pprint
import os
import psycopg2
from psycopg2 import sql
import wget
import logging


# Adjust the parameters
params = {
    'limit': 50,  # Adjust the number of albums to retrieve
    'offset': 5,
}

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_credentials(filename='spotify_cred.json'):
    with open(filename, 'r') as cred_file:
        creds = json.load(cred_file)
    return creds['client_ID'], creds['client_secret']


def load_credentials_postgres(filename='postgres_cred.json'):
    with open(filename, 'r') as cred_file:
        creds_postgres = json.load(cred_file)
    return creds_postgres['host'], creds_postgres['port'], creds_postgres['database'], creds_postgres['user'], \
           creds_postgres['password']


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


def fetch_artist_details(sp, artist_id):
    logging.info(f"Fetching artist details for artist ID: {artist_id}")
    return sp.artist(artist_id)


def fetch_track_details(sp, track_id):
    logging.info(f"Fetching track details for track ID: {track_id}")
    return sp.track(track_id)


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

    pprint.pprint(recent_albums)

    # Fetch artist genres sequentially
    for album in recent_albums:
        artist_id = album['artists'][0]['id']
        if artist_id not in artist_genre_cache:
            artist_details = fetch_artist_details(sp, artist_id)
            artist_genre_cache[artist_id] = [g.lower() for g in artist_details['genres']]

    logging.info(f"Fetched genres for {len(artist_genre_cache)} artists.")

    # Fetch tracks and populate top_tracks list
    for album in recent_albums:
        artist_id = album['artists'][0]['id']
        if genre.lower() in artist_genre_cache.get(artist_id, []):
            logging.info(f"Fetching tracks for album: {album['name']} (ID: {album['id']})")
            album_tracks = sp.album_tracks(album['id'])
            for track in album_tracks['items']:
                track_details = fetch_track_details(sp, track['id'])
                song_info = {
                    'name': track_details['name'],
                    'artists': ', '.join([artist['name'] for artist in track_details['artists']]),
                    'album': album['name'],
                    'release_date': album['release_date'],
                    'duration_ms': track_details['duration_ms'],
                    'popularity': track_details['popularity'],
                    'preview_url': track_details['preview_url'],
                }
                top_tracks.append(song_info)
                logging.info(f"Added track: {track_details['name']} by {track_details['artists'][0]['name']}")

    # Sort the tracks by popularity in descending order
    top_tracks.sort(key=lambda x: x['popularity'], reverse=True)

    logging.info("Tracks sorted by popularity.")
    return top_tracks


def download_weekly_genre_playlist(genres):
    sp = authenticate_spotify()

    # Load PostgreSQL credentials
    postgres_host, postgres_port, postgres_db, postgres_user, postgres_password = load_credentials_postgres()

    # Connect to the database
    conn = psycopg2.connect(host=postgres_host, port=postgres_port, database=postgres_db, user=postgres_user,
                            password=postgres_password)
    cur = conn.cursor()

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
            insert_query = sql.SQL(
                "INSERT INTO wizeplaylist.weekly_playlist (name, album, release_date, duration_ms, popularity, artist, week_nb, genre) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            cur.execute(insert_query, (
                track['name'], track['album'], track['release_date'], track['duration_ms'], track['popularity'],
                track['artists'], week_number, genre))
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
    cur.close()
    conn.close()
    print("Database connection closed.")


def main():
    genre = 'pop'
    sp = authenticate_spotify()
    print(f"Most Listened Songs in the {genre.capitalize()} Genre Released in the Last 3 Months on Spotify:")
    print(genre)
    top_songs = get_top_tracks(sp=sp, genre=genre)
    if not top_songs:
        print(
            f"No songs found in the {genre.capitalize()} genre released in the last 3 months or there was an error.")
    else:
        for idx, song in enumerate(top_songs, start=1):
            print(f"{idx}. {song['name']} by {song['artists']}")
            print(f"   Album: {song['album']}")
            print(f"   Release Date: {song['release_date']}")
            print(f"   Duration (ms): {song['duration_ms']}")
            print(f"   Popularity: {song['popularity']}")
            print(f"   Preview URL: {song['preview_url']}")
            print()


if __name__ == '__main__':
    main()
