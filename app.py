import streamlit as st
import pandas as pd
from pymongo import MongoClient
import unidecode  # para remover acentos
import plotly.express as px
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# 🔧 Configuração
st.set_page_config(page_title="Spotify & YouTube Dashboard", layout="wide")
st.title("🎵📺 Dashboard Spotify & YouTube")
mongo_url = os.getenv("MONGO_URL")
# 📦 Conexão com MongoDB
def conectar_mongo():
    client = MongoClient(mongo_url)
    db = client["midia_db"]
    return db

db = conectar_mongo()

# 🎶 Spotify
# st.header("🎶 Top Semanal Brasil do Spotify")
colecao_spotify = db["spotify_music"]  # nome que usou quando salvou
dados_spotify = list(colecao_spotify.find({}, {"_id": 0}))  # exclui o campo _id
df_spotify = pd.DataFrame(dados_spotify)
df_spotify['RANK'] = df_spotify.index + 1  # +1 para começar do 1

# ▶️ YouTube
# st.header("▶️ Vídeos em Alta do YouTube no Brasil")
colecao_youtube = db["youtube_videos"]
dados_youtube = list(colecao_youtube.find({}, {"_id": 0}))
df_youtube = pd.DataFrame(dados_youtube)
df_youtube['RANK'] = df_youtube.index + 1

    
# 🧹 Tratamento básico
if not df_spotify.empty and not df_youtube.empty:
    # Normalização de texto
    df_spotify["musica_norm"] = df_spotify["NOME_MUSICA"].str.lower().apply(unidecode.unidecode)
    df_spotify["artista_norm"] = df_spotify["ARTISTA"].str.lower().apply(unidecode.unidecode)
    df_youtube["titulo_norm"] = df_youtube["TITULO"].str.lower().apply(unidecode.unidecode)

    # 🔗 Cruzamento: se o título do vídeo contém nome da música OU do artista
    cruzamentos = []
    for _, row_sp in df_spotify.iterrows():
        for _, row_yt in df_youtube.iterrows():
            if (row_sp["musica_norm"] in row_yt["titulo_norm"]) or (row_sp["artista_norm"] in row_yt["titulo_norm"]):
                cruzamentos.append({
                    "Rank_Spotify": row_sp["RANK"],
                    "Musica_Spotify": row_sp["NOME_MUSICA"],
                    "Artista_Spotify": row_sp["ARTISTA"],
                    "Rank_Youtube": row_yt["RANK"],
                    "Titulo_Video": row_yt["TITULO"],
                    "Canal_YouTube": row_yt["CANAL"],
                    "Views_YouTube": row_yt["VIEWS"],
                    "Likes_YouTube": row_yt["LIKES"]
                })

    df_cruzado = pd.DataFrame(cruzamentos)
        
st.set_page_config(page_title="Spotify & YouTube Dashboard", layout="wide")

col1, col2 = st.columns(2)
with col1:  # Spotify
    st.header("Top Semanal Brasil no Spotify")
    # KPI 1: Total de visualizações
    total_acessos = df_spotify['ACESSOS'].sum()
    # KPI 2: Média de engajamento (%)
    media_semanal = df_spotify['MEDIA_ACESSOS_SEMANA'].mean()
    
    total_acessos_fmt = f"{total_acessos:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    media_semanal_fmt = f"{media_semanal:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # Mostrando os KPIs lado a lado
    col_kp1, col_kp2= st.columns(2)

    col_kp1.metric("👁 Total de Acessos", total_acessos_fmt)
    col_kp2.metric("📊 Média de Acessos por Semana", f"{media_semanal:.0f}")
    
    # Criar abas
    tabs = st.tabs(["Gráficos", "Relatório"])
    with tabs[1]:
        # Calcula variação de rank
        # df_spotify['VARIACAO'] = df_spotify['RANK_ANTERIOR'] - df_spotify['RANK']
        # Filtros
        artista_filter = st.multiselect("Selecione artista", df_spotify["ARTISTA"].unique())
        semanas_filter = st.slider("Semanas no ranking", 
                                int(df_spotify["SEMANAS_NO_RANK"].min()), 
                                int(df_spotify["SEMANAS_NO_RANK"].max()), 
                                (int(df_spotify["SEMANAS_NO_RANK"].min()), int(df_spotify["SEMANAS_NO_RANK"].max())))

        # Aplicando filtros
        df_filtered = df_spotify.copy()
        df_filtered = df_filtered.drop(columns=["URL", "musica_norm", "artista_norm"])
        if artista_filter:
            df_filtered = df_filtered[df_filtered["ARTISTA"].isin(artista_filter)]
        df_filtered = df_filtered[(df_filtered["SEMANAS_NO_RANK"] >= semanas_filter[0]) &
                                (df_filtered["SEMANAS_NO_RANK"] <= semanas_filter[1])]
        st.dataframe(df_filtered)
    
    with tabs[0]:
        rank_acesso = px.bar(
            df_filtered.sort_values('ACESSOS', ascending=True),
            y="NOME_MUSICA",
            x="ACESSOS",
            color="ACESSOS",
            hover_data=["NOME_MUSICA","ACESSOS", "RANK", "MEDIA_ACESSOS_SEMANA"],
            title="Top Músicas com Mais Acessos",
            height=800
        )
        
        rank_media = px.scatter(
            df_filtered,
            x='MEDIA_ACESSOS_SEMANA',
            y='SEMANAS_NO_RANK',
            hover_data=["NOME_MUSICA","ACESSOS", "RANK", "MEDIA_ACESSOS_SEMANA", "SEMANAS_NO_RANK"],
            # size='ENGAJAMENTO',
            # color_continuous_scale='Viridis',
            title='Semanas no Ranking vs Média de Acessos Semanal',
            # labels={'ENGAJAMENTO':'Engajamento (%)', 'RANK':'Rank'}
        )
        rank_media.update_traces(marker=dict(size=12))  # ajuste o valor conforme quiser
        
        # rank_media = px.bar(
        #     df_filtered.sort_values('MEDIA_ACESSOS_SEMANA', ascending=False).head(10),
        #     x="NOME_MUSICA",
        #     y="MEDIA_ACESSOS_SEMANA",
        #     color="MEDIA_ACESSOS_SEMANA",
        #     hover_data=["NOME_MUSICA","ACESSOS", "RANK", "MEDIA_ACESSOS_SEMANA"],
        #     title="Top 10 Músicas com Maior Média de Acessos por Semana"
        # )
        
        # Gráfico de barras horizontal mostrando a subida
        fig_semanal = px.bar(
            df_filtered.sort_values('SEMANAS_NO_RANK', ascending=False).head(10),
            x="SEMANAS_NO_RANK",
            y="NOME_MUSICA",
            orientation='h',
            color="SEMANAS_NO_RANK",
            hover_data=["RANK_ANTERIOR", "RANK", "ACESSOS", "MEDIA_ACESSOS_SEMANA"],
            title="Top 10 Músicas com Mais Semanas no Ranking",
            text="SEMANAS_NO_RANK",
            color_continuous_scale=px.colors.sequential.Viridis  # degrade da cor
        )
        fig_semanal.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)  # melhor visual

        with st.container(height=500):
            st.plotly_chart(rank_acesso, use_container_width=True)
        with st.container(height=500):
            st.plotly_chart(fig_semanal, use_container_width=True)
        with st.container(height=500):
            st.plotly_chart(rank_media, use_container_width=True)

    # fig_eng = px.line(df_filtered, x="RANK", y="ENGAJAMENTO", color="ARTISTA",
    #               title="Engajamento por Música")
    # st.plotly_chart(fig_eng, use_container_width=True)
    
with col2:
    st.header("Vídeos em Alta no Youtube")
    df_youtube = df_youtube.rename(columns={
        "engajamento": "ENGAJAMENTO"
    })
    df_youtube = df_youtube.drop(columns=["titulo_norm", "CATEGORIA"])
    df_youtube['ENGAJAMENTO'] = df_youtube['ENGAJAMENTO'] * 100
    
    # KPI 1: Total de visualizações
    total_views = df_youtube['VIEWS'].sum()
    # KPI 2: Média de engajamento (%)
    avg_engagement = df_youtube['ENGAJAMENTO'].mean()
    
    total_views_fmt = f"{total_views:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    avg_engagement_fmt = f"{avg_engagement:.1f}".replace(".", ",")

    # Mostrando os KPIs lado a lado
    col_kp1, col_kp2= st.columns(2)

    col_kp1.metric("👁 Total de Visualizações", total_views_fmt)
    col_kp2.metric("📊 Engajamento Médio (%)", f"{avg_engagement:.1f}%")
    st.info("Engajamento = (Likes + Comentários) / Visualizações")
    
    # Criar abas
    tabs = st.tabs(["Gráficos", "Relatório"])
    with tabs[1]:
        st.write(df_youtube)
    with tabs[0]:
        df_top10 = df_youtube.head(10).sort_values('RANK', ascending=True)
        df_top10['Ranking'] = df_top10['RANK'].max() - df_top10['RANK'] + 1

        fig_alta = px.bar(
            df_top10,
            x='Ranking',
            y='TITULO',
            orientation='h',
            # color='RANK',
            # color_continuous_scale='Viridis',
            hover_data=['TITULO', 'CANAL', 'VIEWS', 'LIKES', 'COMENTARIOS', 'ENGAJAMENTO'],
            text='RANK',
            title='Top 10 Vídeos em Alta - Ranking'
        )
        fig_alta.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        with st.container(height=500):
            st.plotly_chart(fig_alta, use_container_width=True)
        
        fig_scatter = px.scatter(
            df_youtube,
            x='RANK',
            y='ENGAJAMENTO',
            hover_data=['TITULO', 'CANAL', 'LIKES', 'COMENTARIOS', 'VIEWS', "ENGAJAMENTO"],
            # size='ENGAJAMENTO',
            # color_continuous_scale='Viridis',
            title='Engajamento (%) vs Ranking dos vídeos',
            labels={'ENGAJAMENTO':'Engajamento (%)', 'RANK':'Rank'}
        )
        fig_scatter.update_traces(marker=dict(size=15))  # ajuste o valor conforme quiser
        
        rank_views = px.scatter(
            df_youtube,
            x='RANK',
            y='VIEWS',
            hover_data=['TITULO', 'CANAL', 'LIKES', 'COMENTARIOS', 'VIEWS', 'ENGAJAMENTO'],
            # size='ENGAJAMENTO',
            # color_continuous_scale='Viridis',
            title='Visualizações vs Em Alta',
            labels={'VIEWS':'Views', 'RANK':'Rank'}
        )
        rank_views.update_traces(marker=dict(size=15))  # ajuste o valor conforme quiser
        with st.container(height=500):
            st.plotly_chart(fig_scatter, use_container_width=True)
        with st.container(height=430):
            st.plotly_chart(rank_views, use_container_width=True)
    
    
st.header("🎵 Musicas do Spotify presentes nos vídeos em alta do YouTube")
df_cross_filtered = df_cruzado.copy()
# Criar abas
tabs = st.tabs(["Gráficos", "Relatório"])
with tabs[1]:
    st.dataframe(df_cross_filtered)
with tabs[0]:
    fig_cross = px.scatter(df_cross_filtered,
                            x="Rank_Spotify", y="Rank_Youtube",
                            color="Artista_Spotify", hover_data=["Musica_Spotify", "Titulo_Video"],
                            title="Posição Spotify x YouTube")
    fig_cross.update_traces(marker=dict(size=15))  # ajuste o valor conforme quiser
    with st.container(height=500):
        st.plotly_chart(fig_cross, use_container_width=True)