# DagsterSpotify

## A New Way to Discover Music

DagsterSpotify is a project aimed at enhancing how users discover music by leveraging Spotify's API and Dagster for data orchestration.

### Features:

- **Select Genre:** Choose your favorite music genre to explore.
- **Subscribe to Popular Playlists:** Stay updated with curated playlists.
- **Download Selected Songs:** Save your favorite tracks locally.
- **Get New Releases:** Discover the latest music releases.
- **Web UI Display:** User-friendly interface to interact with the features.

### Workflow Schema (using Mermaid syntax):

```mermaid
graph TD;
    selectGenre --> getTop100NewRelease;
    getTop100NewRelease --> randomlySelect50Songs;
    randomlySelect50Songs --> randomlySelect10Songs;
    randomlySelect10Songs --> insertAndDownload;
    insertAndDownload --> |Insert in DB and Download| storeAndDownloadSongs;
    storeAndDownloadSongs --> |Downloaded songs in folder| weekNumberGendraFolder;
