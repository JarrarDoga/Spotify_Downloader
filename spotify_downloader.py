# Step 2: Import necessary libraries
import os
import spotipy
import youtube_dl
from spotipy.oauth2 import SpotifyOAuth

# Step 3: Define the Spotify API credentials
client_id = 'your_client_id'
client_secret = 'your_client_secret'
redirect_uri = 'your_redirect_uri'

# Step 4: Authenticate with the Spotify API
scope = 'playlist-read-private'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri=redirect_uri,scope=scope))

# Step 5: Retrieve the user's playlists
def get_user_playlist():
    playlists =sp.current_user_playlists()
    return playlists['items']

# Step 6: Display the user's playlists
def select_playlist(playlists):
    print("Your Spotify Playlists: ")
    for index, playlist in enumerate(playlists, start=1):
        print(f"{index}. {playlist['name']}")
    
    while True:
        try:
            choice = int(input("\nPlease enter the number of the playlist you want to select: "))
            if 1 <= choice <= len(playlists):
                return playlists[choice -1]
            else:
                print("Invalid choice. Please enter a number corresponding to the playlist.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
# Step 7: Main function
def main():
    playlists = get_user_playlist()
    selected_playlist = select_playlist(playlists)
    display_playlist_info(selected_playlist)
    playlist_tracks = get_playlist_tracks(selected_playlist['id'])
    display_track_info(playlist_tracks)
    download_folder = download_audio_files(playlist_tracks)  # Capture the value returned by download_audio_files()
    list_downloaded_songs(download_folder)  # Call the function to list downloaded songs


if __name__ == '__main__':
    main()

# Step 8: Display information about the selected playlist
def display_playlist_info(playlist):
    print("\nPlaylist Infomration: ")
    print(f"Name: {playlist['name']}")
    print(f"Number of Tracks: {playlist['tracks']['total']}")

# Step 9: Retrieve information about each song in the playlist
def get_playlist_tracks(playlist_id):
    tracks = sp.playlist_tracks(playlist_id)
    return tracks['items']

# Step 10: Display information about each song
def display_track_info(tracks):
    print("\nTrack Information:")
    for index, track in enumerate(tracks, start=1):
        track_name = track['track']['name']
        artists = ', '.join([artist['name'] for artist in track['track']['artists']])
        print(f"{index}. {track_name} - {artists}")

# Step 11: Search for each song on Youtube
def search_song_on_youtube(song_name, artist_names):
    search_query = f"{song_name} {', '.join(artist_names)} audio"
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
        if 'entries' in info:
            return info['entries'][0]['id']
        else:
            return None

# Step 12: Download audio files for each song
def download_audio_files(tracks):
    download_folder = prompt_for_download_folder()
    os.chdir(download_folder) # Change current working directory to the download folder
    failed_songs = []  # List to keep track of failed songs
    for track in tracks:
        track_name = track['track']['name']
        artists = [artist['name'] for artist in track['track']['artists']]
        video_id = search_song_on_youtube(track_name, artists)
        if video_id:
            print(f"Downloading {track_name}...")
            with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
                try:
                    ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                except Exception as e:
                    print(f"Failed to download {track_name}: {str(e)}")
                    failed_songs.append(track_name)
        else:
            print(f"No audio found for {track_name}")
            failed_songs.append(track_name)
    
    if failed_songs:
        print("\nFailed to download the following songs:")
        for song in failed_songs:
            print(song)

    return download_folder # Return the download folder


# Step 13.1: Prompt the user for folder and set download location
def prompt_for_download_folder():
    while True:
        folder_path = input("Enter the folder path where you want to save the downloaded songs: ")
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            return folder_path
        else: 
            print("Invalid folder path. Please enter a valid directory.")


# Step 13.2: Create a folder to store downloaded songs
def create_download_folder():
    folder_path = prompt_for_download_folder()
    return folder_path

# Step 14: List downloaded songs in the specified folder
def list_downloaded_songs(folder_path):
    print("\nDownloaded Songs: ")
    songs = os.listdir(folder_path)
    for song in songs:
        print(song)