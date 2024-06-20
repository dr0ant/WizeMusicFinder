# Spotify Playlist Downloader

This Python script interacts with the Spotify API to fetch and download top tracks from a specified genre. It also stores track metadata in a PostgreSQL database for further analysis.

## Features

- **Authentication**: Authenticates with the Spotify API using client credentials.
- **Top Tracks Retrieval**: Fetches the most popular tracks released in the last 3 months for a given genre.
- **Track Download**: Downloads tracks' preview audio files using `wget`.
- **Database Integration**: Stores track metadata (name, album, release date, duration, popularity, artist) in a PostgreSQL database.
- **Logging**: Logs actions and errors to facilitate troubleshooting and monitoring.

## Prerequisites

- Python 3.x
- `spotipy` library (`pip install spotipy`)
- `psycopg2` library (`pip install psycopg2`)
- `wget` command-line utility (if not installed, download from [eternallybored.org](https://eternallybored.org/misc/wget/))

## Workflow and Database Schema

```mermaid
graph TD;
    A[Start] --> B[Authenticate Spotify]
    B --> C[Retrieve New Releases]
    C --> D{Filter by Release Date}
    D -- Yes --> E{Filter by Genre}
    E -- Yes --> F[Fetch Artist Details]
    F --> G[Fetch Album Tracks]
    G --> H[Fetch Track Details]
    H --> I[Download Track]
    I --> J[Store in Database]
    J --> K[Loop to Next Track]
    E -- No --> D
    D -- No --> C
    C -- No --> B
    B --> L[End]

    A[Start] --> M[weekly_playlist]
    M --> id int
    M --> name varchar(255)
    M --> album varchar(255)
    M --> release_date date
    M --> duration_ms int
    M --> popularity int
    M --> artist varchar(255)
    M --> week_nb int
    M --> genre varchar(50)
