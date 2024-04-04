# Step 2: Import necessary libraries
import spotipy
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
def display_playlists(playlists):
    print("Your Spotify Playlists: ")
    for index, playlist in enumerate(playlists, start=1):
        print(f"{index}. {playlist['name']}")
    
# Step 7: Main function
def main():
    playlists = get_user_playlist()
    display_playlists(playlists)

if __name__ == '__main__':
    main()