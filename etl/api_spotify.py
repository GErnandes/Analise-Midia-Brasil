import os
import pandas as pd
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv(dotenv_path="../.env")

# Autenticação
auth_manager = SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
)
sp = Spotify(auth_manager=auth_manager)

# Top 50 Brasil (playlist oficial do Spotify)
# playlist_id = "37i9dQZF1DX0FOF1IUWK1W"
# results = sp.playlist_items(playlist_id, market="BR")

artist_id = "1uNFoZAHBGtllmzznpCI3s"  # Justin Bieber
top_tracks = sp.artist_top_tracks(artist_id, country="US")

for track in top_tracks['tracks']:
    print(track['name'], "-", track['popularity'])