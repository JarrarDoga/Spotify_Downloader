import os
import spotipy
import yt_dlp as youtube_dl
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading
import platform

# Define the Spotify API credentials
client_id = 'your_client_id'
client_secret = 'your_client_secret'
redirect_uri = 'http://localhost:8888/callback'

# Authenticate with the Spotify API
scope = 'user-read-private user-library-read playlist-read-private'
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))

# Global variables to store playlists and albums
playlists = []
albums = []
filtered_items = []
selected_item_index = None
current_view = "playlists"  # Track whether we're showing playlists or albums

def get_user_playlist():
    playlists = sp.current_user_playlists()
    return playlists['items']

def get_user_albums():
    albums = []
    results = sp.current_user_saved_albums()
    albums.extend(results['items'])
    
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    
    return albums

def get_playlist_songs(playlist_id):
    tracks = sp.playlist_tracks(playlist_id)
    return tracks['items']

def get_album_songs(album_id):
    tracks = sp.album_tracks(album_id)
    return [{'track': track} for track in tracks['items']]

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
        if 'entries' in info and len(info['entries']) > 0:
            return info['entries'][0]['id']
        else:
            return None

def download_audio_files(tracks, download_folder):
    os.chdir(download_folder)
    failed_songs = []
    total_tracks = len(tracks)

    for i, track in enumerate(tracks, 1):
        track_name = track['track']['name']
        artists = [artist['name'] for artist in track['track']['artists']]
        video_id = search_song_on_youtube(track_name, artists)

        status_var.set(f"Downloading {i}/{total_tracks}: {track_name}")
        progress_bar['value'] = (i / total_tracks) * 100
        root.update_idletasks()

        if video_id:
            with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
                try:
                    ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                except Exception as e:
                    failed_songs.append(track_name)
        else:
            failed_songs.append(track_name)

    status_var.set("Download completed")
    progress_bar['value'] = 100

    if failed_songs:
        messagebox.showwarning("Failed Downloads", f"Could not download the following songs: {', '.join(failed_songs)}")
    else:
        messagebox.showinfo("Success", "All songs downloaded successfully!")

def update_listbox(search_term=""):
    global selected_item_index, filtered_items
    items = playlists if current_view == "playlists" else albums
    filtered_items = [item for item in items if search_term.lower() in (item['name'].lower() if current_view == "playlists" else item['album']['name'].lower())]
    
    for widget in listbox_frame.winfo_children():
        widget.destroy()

    for index, item in enumerate(filtered_items, start=1):
        frame = tk.Frame(listbox_frame, bg="#191414")
        frame.pack(fill=tk.X, pady=2)

        if current_view == "playlists":
            image_url = item['images'][0]['url'] if item['images'] else None
            name = item['name']
        else:
            image_url = item['album']['images'][0]['url'] if item['album']['images'] else None
            name = item['album']['name']

        if image_url:
            img = load_image_from_url(image_url, (40, 40))
            img_label = tk.Label(frame, image=img, bg="#191414")
            img_label.image = img
            img_label.pack(side=tk.LEFT, padx=5)

        label = tk.Label(frame, text=name, bg="#191414", fg="white", anchor="w")
        label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        label.bind("<Button-1>", lambda e, idx=index - 1: on_item_click(idx))

    listbox_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    selected_item_index = None

def toggle_view():
    global current_view, filtered_items
    current_view = "albums" if current_view == "playlists" else "playlists"
    toggle_button.config(text="Show Playlists" if current_view == "albums" else "Show Albums")
    if current_view == "albums":
        albums.clear()
        albums.extend(get_user_albums())
    else:
        playlists.clear()
        playlists.extend(get_user_playlist())
    update_listbox()

def on_item_click(index):
    global selected_item_index
    selected_item_index = index

    for frame in listbox_frame.winfo_children():
        for child in frame.winfo_children():
            if isinstance(child, tk.Label) and child.cget("text"):
                child.configure(bg="#191414", fg="white", font=("TkDefaultFont", 9, "normal"))

    selected_frame = listbox_frame.winfo_children()[index]
    for child in selected_frame.winfo_children():
        if isinstance(child, tk.Label) and child.cget("text"):
            child.configure(bg="#191414", fg="#1DB954", font=("TkDefaultFont", 9, "underline"))

def on_item_select():
    global selected_item_index
    if selected_item_index is not None:
        selected_item = filtered_items[selected_item_index]
        
        if current_view == "playlists":
            tracks = get_playlist_songs(selected_item['id'])
        else:
            tracks = get_album_songs(selected_item['album']['id'])

        download_folder = filedialog.askdirectory(title="Select Download Folder")

        if download_folder:
            threading.Thread(target=download_audio_files, args=(tracks, download_folder)).start()
    else:
        messagebox.showerror("No Selection", "Please select a playlist or album to download songs from.")

def load_image_from_url(url, size):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img = img.resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)

# Tkinter Setup
root = tk.Tk()
root.title("Spotify Downloader")
root.geometry("300x600")
root.configure(bg="#191414")

# Create and configure widgets
label = tk.Label(root, text="Select Music to Download", bg="#191414", fg="white",
                 padx=5, pady=5, font=("TkDefaultFont", 10, "bold"))
label.pack(pady=10)

# Add the toggle button after root is created
toggle_button = ttk.Button(root, text="Show Albums", command=toggle_view, style="TButton")
toggle_button.pack(pady=5)

# Create a frame for the listbox and scrollbar
list_frame = tk.Frame(root, bg="#191414", bd=0)
list_frame.pack(pady=10, fill=tk.BOTH, expand=True)

# Create a canvas to hold the listbox frame
canvas = tk.Canvas(list_frame, bg="#191414", highlightthickness=0, width=280)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Add a scrollbar to the canvas
scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.configure(yscrollcommand=scrollbar.set)

# Create a frame inside the canvas to hold the listbox items
listbox_frame = tk.Frame(canvas, bg="#191414")
canvas_window = canvas.create_window((0, 0), window=listbox_frame, anchor="nw", width=280)

# Configure the canvas scrolling
def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    
listbox_frame.bind("<Configure>", on_frame_configure)

# Configure mouse wheel scrolling
def on_mousewheel(event):
    if platform.system() == "Windows":
        canvas.yview_scroll(int(-1 * (event.delta/120)), "units")
    elif platform.system() == "Darwin":  # macOS
        canvas.yview_scroll(int(-1 * event.delta), "units")
    else:  # Linux
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

# Bind mouse wheel for Windows and macOS
canvas.bind_all("<MouseWheel>", on_mousewheel)
# Bind mouse wheel for Linux
canvas.bind_all("<Button-4>", on_mousewheel)
canvas.bind_all("<Button-5>", on_mousewheel)

# Configure canvas scrolling with scrollbar
def on_canvas_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

canvas.bind("<Configure>", on_canvas_configure)

# Make sure the listbox frame expands to fill the canvas width
def on_canvas_configure(event):
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", on_canvas_configure)
# Create a custom style for buttons
style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", padding=6, relief="flat", background="#1DB954", foreground="white")
style.configure("TProgressbar", troughcolor='#191414', background='#1db1b9', thickness=20)
style.map("TButton",
          foreground=[('pressed', 'white'), ('active', 'white')],
          background=[('pressed', '#1ED760'), ('active', '#1ED760')]
          )

# Add a custom button with style
download_button = ttk.Button(root, text="Download Selected Music", command=on_item_select, style="TButton")
download_button.pack(pady=10)

# Add a search bar
search_frame = tk.Frame(root, bg="#191414")
search_frame.pack(pady=5)

search_var = tk.StringVar()
search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20)
search_entry.pack(side=tk.LEFT, padx=5)

search_button = ttk.Button(search_frame, text="Search", command=lambda: update_listbox(search_var.get()), style="TButton", width=10)
search_button.pack(side=tk.LEFT)

# Add a progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=280, mode="determinate")
progress_bar.pack(pady=10)

status_var = tk.StringVar()
status_label = tk.Label(root, textvariable=status_var, bg="#191414", fg="#fae22a")
status_label.pack(pady=10)

# Load the user's playlists at startup
playlists.extend(get_user_playlist())
update_listbox()

# Run the Tkinter event loop
root.mainloop()
