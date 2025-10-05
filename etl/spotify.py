import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv(dotenv_path="../.env")

mongo_url = os.getenv("MONGO_URL")

def get_dados_spotify():
    # Ler o CSV ignorando apenas a primeira linha (extra de info)
    df = pd.read_csv("./semana_global.csv", sep=",")
    df.set_index("rank", inplace=True)
    # Limpeza básica
    df.dropna(subset=["track_name", "artist_names"], inplace=True)  # remover nulos críticos
    df["streams"] = pd.to_numeric(df["streams"], errors="coerce")  # garantir numérico
    df["weeks_on_chart"] = pd.to_numeric(df["weeks_on_chart"], errors="coerce")

    # Padronização de nomes
    df["track_name"] = df["track_name"].str.strip()
    df["artist_names"] = df["artist_names"].str.strip()
    
    df["avg_streams_per_week"] = df["streams"] / df["weeks_on_chart"]

    df = df.rename(columns={
        "rank": "RANK",
        "track_name": "NOME_MUSICA",
        "artist_names": "ARTISTA",
        "source": "FONTE",
        "peak_rank": "MELHOR_RANK",
        "previous_rank": "RANK_ANTERIOR",
        "weeks_on_chart": "SEMANAS_NO_RANK",
        "uri": "URL",
        "streams": "ACESSOS",
        "avg_streams_per_week": "MEDIA_ACESSOS_SEMANA",
    })
    df = df.head(50)
    return df

def salvar_no_mongo(df):
    # Conexão com o MongoDB Atlas (substitua pela sua URI)
    client = MongoClient(mongo_url, server_api=ServerApi('1'))
    db = client["midia_db"]  # nome do banco
    colecao = db["spotify_music"]     # nome da coleção

    # Converte o DataFrame em dicionários (formato JSON)
    dados = df.to_dict(orient="records")

    # Insere todos os documentos na coleção
    colecao.insert_many(dados)
    print(f"{len(dados)} vídeos inseridos no MongoDB com sucesso!")
    
if __name__ == "__main__":
    df_spotify = get_dados_spotify()
    salvar_no_mongo(df_spotify)
    
# # carregar variáveis do .env
# load_dotenv()

# # cria auth_manager
# auth_manager = SpotifyClientCredentials(
#     client_id=os.getenv("SPOTIPY_CLIENT_ID"),
#     client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
# )

# sp = spotipy.Spotify(auth_manager=auth_manager)
# # pegar token atual
# # token = auth_manager.get_access_token()
# # print("Access Token gerado:", token)

# # https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=5f83hgvfQVWx7moTvgsxUw# Exemplo: pegar faixas de uma playlist
# playlist_id = "37i9dQZF1DX0FOF1IUWK1W"  # Pop Brasil
# results = sp.playlist_items(playlist_id, market="BR")

# tracks_data = []
# for item in results["items"]:
#     track = item["track"]
#     if track:
#         tracks_data.append({
#             "nome": track["name"],
#             "artista": track["artists"][0]["name"],
#             "album": track["album"]["name"],
#             "popularidade": track["popularity"],
#             "duracao_min": round(track["duration_ms"]/60000, 2)
#         })

# df = pd.DataFrame(tracks_data)
# print(df.head())
