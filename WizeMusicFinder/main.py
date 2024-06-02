import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
from datetime import datetime, timedelta
import pprint
import requests
import os
import psycopg2
from psycopg2 import sql



# Adjust the parameters
params = {
    'limit': 50,  # Adjust the number of albums to retrieve
    'offset': 5,
}


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
    client_id, client_secret = load_credentials()
    credentials = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=credentials)
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




def get_top_tracks(sp, genre):
    # Get current date
    current_date = datetime.now().date()
    
    # Calculate the date three months ago
    three_months_ago = current_date - timedelta(days=3 * 30)
    
    # Make the API call to retrieve new releases
    new_releases = sp.new_releases(country='US', limit=50, offset=0)
    
    top_tracks = []
    
    # Filter and process each album in the new releases
    for album in new_releases['albums']['items']:
        album_tracks = sp.album_tracks(album['id'])
        for track in album_tracks['items']:
            # Get track details
            track_details = sp.track(track['id'])
            # Check if the track's release date is within the last three months
            release_date = datetime.strptime(track_details['album']['release_date'], '%Y-%m-%d').date()
            if release_date >= three_months_ago:
                # Check if the track's genre matches the specified genre
                track_genres = [g.lower() for g in sp.artist(track_details['artists'][0]['id'])['genres']]
                if genre.lower() in track_genres:
                    song_info = {
                        'name': track_details['name'],
                        'artists': ', '.join([artist['name'] for artist in track_details['artists']]),
                        'album': track_details['album']['name'],
                        'release_date': track_details['album']['release_date'],
                        'popularity': track_details['popularity'],
                        'preview_url': track_details['preview_url'],
                    }
                    top_tracks.append(song_info)
    
    # Sort the tracks by popularity in descending order
    top_tracks.sort(key=lambda x: x['popularity'], reverse=True)
    
    # Return the top 20 tracks
    return top_tracks[:20]


def download_weekly_genre_playlist(genres):
    sp = authenticate_spotify()
    
    # Load PostgreSQL credentials
    postgres_host, postgres_port, postgres_db, postgres_user, postgres_password = load_credentials_postgres()

    # Connect to the database
    conn = psycopg2.connect(host=postgres_host, port=postgres_port, database=postgres_db, user=postgres_user, password=postgres_password)
    cur = conn.cursor()

    # Get current date and week number
    current_date = datetime.now()
    week_number = current_date.isocalendar()[1]
    
    for genre in genres:
        # Create folder for the playlist
        folder_name = f"Playlist_week_{week_number}_{genre}"
        os.makedirs(folder_name, exist_ok=True)
        
        # Get top tracks for the genre
        top_tracks = get_top_tracks(sp, genre)
        
        for track in top_tracks:
            # Insert track information into the database
            insert_query = sql.SQL("INSERT INTO wizeplaylist.weekly_playlist (name, album, release_date, popularity, artist, week_nb, genre) VALUES (%s, %s, %s, %s, %s, %s, %s)")
            cur.execute(insert_query, (track['name'], track['album'], track['release_date'], track['popularity'], track['artists'], week_number, genre))
            conn.commit()

            # Download the track
            track_name = track['name'] + '.mp3'
            track_url = track['preview_url']
            if track_url:
                track_path = os.path.join(folder_name, track_name)
                os.system(f"wget -O '{track_path}' '{track_url}'")

    # Close the database connection
    cur.close()
    conn.close()




#print(load_credentials_postgres(filename='postgres_cred.json'))






download_weekly_genre_playlist(['pop', 'rock', 'hip-hop'])






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
