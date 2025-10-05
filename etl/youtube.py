from googleapiclient.discovery import build
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

mongo_url = os.getenv("MONGO_URL")

def get_dados_youtube():
    # Configura credenciais do YouTube
    api_key = os.getenv("YOUTUBE_KEY")
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Exemplo: vídeos em alta no Brasil
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode="BR",
        maxResults=199
    )
    response = request.execute()

    # Transformação: cria DataFrame
    videos = []
    for item in response['items']:
        videos.append({
            'titulo': item['snippet']['title'],
            'canal': item['snippet']['channelTitle'],
            'categoria': item['snippet'].get('categoryId'),
            'views': item['statistics'].get('viewCount'),
            'likes': item['statistics'].get('likeCount'),
            'comentarios': item['statistics'].get('commentCount')
        })

    df = pd.DataFrame(videos)
    
    # Conversão para tipos corretos
    df["views"] = pd.to_numeric(df["views"], errors="coerce")
    df["likes"] = pd.to_numeric(df["likes"], errors="coerce")
    df["comentarios"] = pd.to_numeric(df["comentarios"], errors="coerce")

    # Tratar nulos
    df.fillna(0, inplace=True)

    # Padronização de nomes
    df["titulo"] = df["titulo"].str.strip()
    df["canal"] = df["canal"].str.strip()

    df["engajamento"] = (df["likes"] + df["comentarios"]) / df["views"]
    
    df = df.rename(columns={
        "titulo": "TITULO",
        "canal": "CANAL",
        "categoria": "CATEGORIA",
        "views": "VIEWS",
        "likes": "LIKES",
        "comentarios": "COMENTARIOS",
    })
    return df

def salvar_no_mongo(df):
    # Conexão com o MongoDB Atlas (substitua pela sua URI)
    client = MongoClient(mongo_url, server_api=ServerApi('1'))
    db = client["midia_db"]  # nome do banco
    colecao = db["youtube_videos"]     # nome da coleção

    # Converte o DataFrame em dicionários (formato JSON)
    dados = df.to_dict(orient="records")

    # Insere todos os documentos na coleção
    colecao.insert_many(dados)
    print(f"{len(dados)} vídeos inseridos no MongoDB com sucesso!")
    
if __name__ == "__main__":
    df_youtube = get_dados_youtube()
    salvar_no_mongo(df_youtube)