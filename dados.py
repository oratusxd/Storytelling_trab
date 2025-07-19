import pandas as pd
import geopandas as gpd
import streamlit as st
import geopandas as gpd
from shapely.geometry import Polygon
import folium
from folium.plugins import MarkerCluster
import plotly.graph_objects as go
import plotly.express as px
import requests
import io
from streamlit.web.cli import main


# Instalar Python mais atualizado e rodar esse comando para instalar as bibliotecas : pip install pandas geopandas streamlit shapely folium plotly 
# rodar esse comando no terminal: streamlit run dados.py

df = pd.read_feather("dados_156.feather") 
print(df.head())
colunas_para_frequencia_individual = [
    'Tipo', 'Orgao', 'MesCriacao', 'Assunto', 'Subdivisao', 'Situacao',
    'Bairro', 'Regional', 'MesResposta', 'Origem'
]

# Armazenar os resumos de frequência em um dicionário
frequencias_por_coluna = {}

for coluna in colunas_para_frequencia_individual:
    print(f"\n--- Frequência para a coluna: '{coluna}' ---")
    
   
    frequencia_coluna = df[coluna].value_counts().reset_index(name='Frequencia')
    frequencia_coluna.rename(columns={'index': coluna}, inplace=True)
    frequencias_por_coluna[coluna] = frequencia_coluna
    
    print(frequencia_coluna)
    print("-" * 30)


print("\n--- Acessando a frequência do 'Tipo' do dicionário ---")
print(frequencias_por_coluna['Tipo'])

gdf_bairros = gpd.read_file('DIVISA_DE_BAIRROS.shp')
print("\n--- GeoDataFrame de Bairros ---")
print(gdf_bairros.head())

print(frequencias_por_coluna['Bairro'])

bairro_frequencia = frequencias_por_coluna['Bairro'].set_index('Bairro').join(
    gdf_bairros.set_index('NOME'), how='right'
).reset_index()

bairro_frequencia['Frequencia'] = bairro_frequencia['Frequencia'].fillna(0)

bairro_frequencia = bairro_frequencia.rename(columns={'index': 'Bairro'})

st.set_page_config(page_title="Análise Central 156",page_icon="logo_prefeitura_branco", layout="wide")
st.image("logo_prefeitura_branco.png", width=75)
st.title("Análise das solicitações geradas na Central 156")

st.markdown("""
**A Central 156** é um canal de atendimento ao cidadão que permite registrar solicitações, reclamações e sugestões relacionadas a serviços públicos. A análise dos dados gerados por essa central pode fornecer insights valiosos sobre as demandas da população e a eficiência dos serviços prestados.

Um dos pontos centrais de uma gestão pública seria possibilitar uma gestão mais participativa, seja para dar voz aos diferentes setores privados, interesses do próprio poder público e bem como dar voz à população. Nesse último caso, é que entram centrais de atendimento, ao serem a ponte entre a população e a Prefeitura.

Nesse contexto, que em 1984 emerge a Central 156 em Curitiba, nascendo para diminuir as filas no balcão de atendimento na Prefeitura, sendo assim, uma ferramenta para aproximar a população da administração municipal. Hoje, a Central é a porta de entrada para diferentes solicitações repassadas para as devidas Secretarias ou órgãos da Prefeitura que possam as resolver.

Hoje, existem diferentes meios para fazer uma solicitação à central 156, como telefone celular, internet, chat online, aplicativo e até atendimento presencial. Como a Central recebe muitas solicitações, ela acaba por disponibilizar uma série de compilados estatísticos, podendo ser organizados por mês ou ano.
""")
dfResumo_frequencias = pd.DataFrame({
    'Tipo': frequencias_por_coluna['Tipo']['Frequencia'],
    'Orgao': frequencias_por_coluna['Orgao']['Frequencia'],
    'MesCriacao': frequencias_por_coluna['MesCriacao']['Frequencia'],
    'Assunto': frequencias_por_coluna['Assunto']['Frequencia'],
    'Subdivisao': frequencias_por_coluna['Subdivisao']['Frequencia'],
    'Situacao': frequencias_por_coluna['Situacao']['Frequencia'], }) 

@st.cache_data
def carregar_dados():
    return df


# Converter para GeoDataFrame
gdf_frequencia = gpd.GeoDataFrame(
    bairro_frequencia, 
    geometry='geometry'
).dropna(subset=['geometry'])

# Mapa das solicitações por bairro
st.subheader("Mapa de Solicitações por Bairro")
fig = px.choropleth_map(
    gdf_frequencia,
    geojson=gdf_frequencia.geometry,
    locations=gdf_frequencia.index,
    color='Frequencia',
    hover_name='NOME',
    #hover_data=['Frequencia'],
    color_continuous_scale=
    "Sunsetdark",
    zoom=10,
    center={"lat": gdf_frequencia.geometry.centroid.y.mean(), 
            "lon": gdf_frequencia.geometry.centroid.x.mean()},
    opacity=0.7,
    labels={'Frequencia': 'Número de Solicitações'}
)

fig.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    height=500
)


st.plotly_chart(fig, use_container_width=True, key="tipo_mapa")


st.write("")
st.write("")
st.write("")
st.subheader("Top 10 Bairros com Mais Solicitações")
top_bairros = bairro_frequencia.sort_values('Frequencia', ascending=False)
fig_bairros = px.bar(
        top_bairros.head(10),
        x='NOME',
        y='Frequencia',
        labels={'NOME': 'Bairro', 'Frequencia': 'Solicitações'}
    )
st.plotly_chart(fig_bairros, use_container_width=True)


fig_tipo = px.bar(
        frequencias_por_coluna['Tipo'], 
            x='Tipo',
            y='Frequencia',
            color='Tipo', # Corrigido: Colorindo as barras pelo 'Tipo'
            title='Frequência de Solicitações por Tipo'
    )
st.plotly_chart(fig_tipo, use_container_width=True)

fig_tipo_solicitacao = px.bar(
    frequencias_por_coluna['Situacao'], 
    x='Situacao',  
    y='Frequencia',
    color='Situacao',
    title='Contagem da situação das solicitações'
)
st.plotly_chart(fig_tipo_solicitacao, use_container_width=True, key="tipo_situacao")

fig_tipo_solicitacao = px.bar(
    frequencias_por_coluna['Orgao'], 
    x='Orgao',  
    y='Frequencia',
    color='Orgao',
    title='Contagem das solicitações por órgão'
)
st.plotly_chart(fig_tipo_solicitacao, use_container_width=True, key="tipo_orgao")


st.subheader("Frequência de Solicitações por Mês de Criação")

meses_map = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }

freq_mes_criacao = frequencias_por_coluna['MesCriacao'].copy()
freq_mes_criacao['Mes'] = freq_mes_criacao['MesCriacao'].map(meses_map)
    

freq_mes_criacao_sorted = freq_mes_criacao.sort_values(by='MesCriacao')

fig_mes_criacao = px.bar(
        freq_mes_criacao_sorted,
        x='Mes', 
        y='Frequencia',
        title='Solicitações por Mês de Criação'
    )
st.plotly_chart(fig_mes_criacao, use_container_width=True, key="grafico_mes_criacao")


st.markdown("---")
st.caption("Dashboard desenvolvido com dados da Central 156 de Curitiba.")

