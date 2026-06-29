#Fernando Henrique M. Rossignolli e Jean Carlos Dantas
#Ciência de Dados para Negócios, 2° Semestre, 04/2026
#Prof. Rômulo Francisco

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import time
from datetime import datetime #pega a hora atual e calcula o tempo
import uuid #gera identificadores
import os #permite a interação do sistema com os arquivos
import atexit #executa o código quando o programa encerra

# CONTROLE DE USUÁRIO ---------------------------------------------

if "user_id" not in st.session_state:   #verifica se é a primeira vez que o usuário entra no site
    st.session_state.user_id = str(uuid.uuid4()) #cria um id único para o usuário
    st.session_state.entrada = datetime.now() #salva o momento em que o usuário entra no site
    st.session_state.pagina_atual = None #inicializa a página atual como vazia
    st.session_state.inicio_pagina = datetime.now() #marca o momento em que a página atual se inicializou
if "saida_registrada" not in st.session_state: #verifica se já existe controle de saída
    st.session_state.saida_registrada = False #verifica se já salvou a saída

#IMPORTAR E TRATAR tabela_covid MUNDO -----------------------------

@st.cache_data
def carregar_dados_mundo():

   url_dados_casos = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
   url_dados_mortes = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"

   dados_casos = pd.read_csv(url_dados_casos)
   dados_mortes = pd.read_csv(url_dados_mortes)

   dados_casos = dados_casos.melt(
       id_vars=["Province/State", "Country/Region", "Lat", "Long"],
       var_name="date",
       value_name="total_dados_casos") #formatar dados em linhas
   dados_mortes = dados_mortes.melt(
       id_vars=["Province/State", "Country/Region", "Lat", "Long"],
       var_name="date",
       value_name="total_dados_mortes")

   dados_casos["date"] = pd.to_datetime(dados_casos["date"], format="%m/%d/%y")  #arrumar datas
   dados_mortes["date"] = pd.to_datetime(dados_mortes["date"], format="%m/%d/%y")

   dados_casos = dados_casos.groupby(["Country/Region", "date"])["total_dados_casos"].sum().reset_index() #agrupar valores de estados e somar total
   dados_mortes = dados_mortes.groupby(["Country/Region", "date"])["total_dados_mortes"].sum().reset_index()

   tabela_covid = pd.merge(dados_casos, dados_mortes, on=["Country/Region", "date"]) #agrupar as duas tabela_covids

   tabela_covid = tabela_covid.rename(columns={"Country/Region": "País", "date": "Data", "total_dados_casos": "Casos",
                                   "total_dados_mortes": "Mortes"}) #renomear colunas

   tabela_covid = tabela_covid.sort_values(["País", "Data"]) #ordenar a tabela_covid em ordem crescente

   return tabela_covid

tabela_covid = carregar_dados_mundo() #atribui as variáveis para

tabela_covid.to_csv("covid_limpo.csv", index=False) #salvar csv limpo

#-------------------------------------------------
#IMPORTAR E TRATAR tabela_covid BRASIL
#-------------------------------------------------

@st.cache_data #cria um cachê no armaenamento do streamlit
def carregar_dados_brasil():   #"def" "coloca" um código em um só nome
   url = "https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-states.csv"

   tabela_covid_br = pd.read_csv(url) #ler dados

   tabela_covid_br = tabela_covid_br[["date", "state", "totalCases", "deaths"]] #selecionar apenas colunas essenciais

   tabela_covid_br = tabela_covid_br.rename(columns={
       "date": "Data Brasil",
       "state": "Estado",
       "totalCases": "Casos Brasil",
       "deaths": "Mortes Brasil"}) #renomear colunas

   tabela_covid_br = tabela_covid_br.sort_values(["Estado", "Data Brasil"]) #ordenar

   return tabela_covid_br #retona as variáveis ao acionar o def

tabela_covid_br = carregar_dados_brasil() #atribui as variáveis de dentro do def ao próprio def

#IMPORTAR E TRATAR tabela_covid VACINAS ----------------------------------

@st.cache_data
def carregar_dados_vacinacao():
   url_vac = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"

   tabela_covid_vac = pd.read_csv(url_vac)

   tabela_covid_vac = tabela_covid_vac[[
       "location",
       "date",
       "total_vaccinations",
       "people_vaccinated",
       "people_fully_vaccinated",
       "people_vaccinated_per_hundred"]]  #adicionado para a porcentagem de primeira dose // #selecionar colunas principais

   tabela_covid_vac = tabela_covid_vac.rename(columns={
       "location": "País Vacina",
       "date": "Data Vacina",
       "total_vaccinations": "Total Vacinas",
       "people_vaccinated": "1ª Dose",
       "people_fully_vaccinated": "Total Imunizados",
       "people_vaccinated_per_hundred": "% 1ª Dose"})  #adicionado para porcentagem de primeira dose}) #renomear

   tabela_covid_vac["Data Vacina"] = pd.to_datetime(tabela_covid_vac["Data Vacina"])
   #ordenar
   tabela_covid_vac = tabela_covid_vac.sort_values(["País Vacina", "Data Vacina"]) #converter data

   excluir = [
       "World", "Europe", "Asia", "European Union",
       "High income", "Upper middle income",
       "Lower middle income", "Low income",
       "North America", "South America", "Africa", "Oceania"] #excluir agragados

   ultimo_vac = tabela_covid_vac.sort_values("Data Vacina") \
       .groupby("País Vacina").last().reset_index()  #pegar último registro de cada país para a soma

   ultimo_vac = ultimo_vac[
       ~ultimo_vac["País Vacina"].isin(excluir)] #remover agregados por lista

   ultimo_vac = ultimo_vac[
       ~ultimo_vac["País Vacina"].str.contains(
           "income|World|Asia|Europe|America|Africa|Oceania|Union",
           case=False)] #remover padrões

   ultimo_vac = ultimo_vac.fillna(0) #evitar NaN (nulos)

   return tabela_covid_vac, ultimo_vac

tabela_covid_vac, ultimo_vac = carregar_dados_vacinacao()

#cards
total_doses = ultimo_vac["Total Vacinas"].sum()
total_1_dose = ultimo_vac["1ª Dose"].sum()
total_imunizados = ultimo_vac["Total Imunizados"].sum()

top6_vac = ultimo_vac.sort_values(
   "Total Vacinas", ascending=False
).head(6)["País Vacina"]

dados_top6_vac = tabela_covid_vac[
   tabela_covid_vac["País Vacina"].isin(top6_vac)]

#CRIAÇÃO DO APP -----------------------------------------

st.set_page_config(layout="wide")      #diminuir bordas e aumentar área utilizável
st.markdown(""" ... """, unsafe_allow_html=True)

st.markdown("""
   <style>
       .main .block-container {
           max-width: 100%;
           padding-left: 0.5rem;
           padding-right: 0.5rem;
       }
   </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.block-container {
   padding-top: 1rem;
   padding-bottom: 0rem;
}
</style>
""", unsafe_allow_html=True)

ultima_data_mortes = tabela_covid.sort_values("Data").groupby("País").last().reset_index()  #soma de casos e mortes mundialmente
total_mortes = ultima_data_mortes["Mortes"].sum()
ultima_data_casos = tabela_covid.sort_values("Data").groupby("País").last().reset_index()
total_casos = ultima_data_casos["Casos"].sum()

#dia com mais casos e mortes (pico da pandemia)
global_diario = tabela_covid.groupby("Data")[["Casos", "Mortes"]].sum().reset_index() #agrupar por data e somando todos os países
dia_max_casos = global_diario.loc[global_diario["Casos"].idxmax()] #dia com mais casos
dia_max_mortes = global_diario.loc[global_diario["Mortes"].idxmax()]  #dia com mais mortes

ultimo_caso = tabela_covid.sort_values("Data").groupby("País").last().reset_index()

top6_casos = ultimo_caso.sort_values("Casos", ascending=False).head(6)

top6_casos["Taxa de Mortalidade (%)"] = (
   top6_casos["Mortes"] / top6_casos["Casos"]) * 100  #criar taxa de mortalidade

#casos e mortes por dia
tabela_covid["Novos Casos"] = tabela_covid.groupby("País")["Casos"].diff()
tabela_covid["Novas Mortes"] = tabela_covid.groupby("País")["Mortes"].diff()
global_diario = tabela_covid.groupby("Data")[["Novos Casos", "Novas Mortes"]].sum().reset_index()
global_diario = global_diario.fillna(0)

global_diario["Casos MM7"] = global_diario["Novos Casos"].rolling(7).mean()
global_diario["Mortes MM7"] = global_diario["Novas Mortes"].rolling(7).mean()

global_semanal = global_diario.resample("W", on="Data").sum().reset_index()

st.sidebar.title("Menu")

#diminuir grossura do menu
st.markdown("""
<style>
[data-testid="stSidebar"] {
   width: 100px !important;}
</style>
""", unsafe_allow_html=True)

pagina = st.sidebar.radio(
   "Escolha uma página:",
   ["Visão Geral", "Global", "Brasil", "Vacinação", "Filtro de Países", "Dados Brutos"])

st.sidebar.write("Criado por Fernando Henrique M. Rossignolli e Jean Carlos Dantas")
st.sidebar.write("Fontes: Johns Hopkins (CSSE), Wesley Cota (pesquisador brasileiro) e Our World in Data (OWID), respectivamente")

def card(titulo, valor):
   with st.container(border=True):
       st.metric(titulo, valor)

def marcacao_preta():
   st.markdown("""
       <hr style="border: 1px solid #444; margin-top: 20px; margin-bottom: 20px;">
       """, unsafe_allow_html=True)

def marcacao_cinza():
   st.markdown("""
       <hr style="border: 1px solid #dddddd; margin-top: 20px; margin-bottom: 20px;">
       """, unsafe_allow_html=True)
   
def adicionar_marcador(fig, dados, data_alvo, coluna_x, coluna_y, nome, texto):
    linha = dados.iloc[
        (dados[coluna_x] - pd.to_datetime(data_alvo)).abs().argsort()[:1]]

    fig.add_scatter(
        x=linha[coluna_x],
        y=linha[coluna_y],
        mode="markers",
        marker=dict(size=10, color="black"),
        name=nome,
        hovertext=[texto],
        hoverinfo="text")
   
def grafico_dois_eixos(
    dados,
    x,
    y1,
    y2,
    nome_y1="Casos",
    nome_y2="Mortes",
    cor_y1="#ff4d4d",
    cor_y2="#444444",
    titulo="Gráfico com Dois Eixos"):
    fig = go.Figure()

    #eixo esquerdo
    fig.add_trace(go.Scatter(
        x=dados[x],
        y=dados[y1],
        name=nome_y1,
        line=dict(color=cor_y1, width=2)))

    #eixo direito
    fig.add_trace(go.Scatter(
        x=dados[x],
        y=dados[y2],
        name=nome_y2,
        line=dict(color=cor_y2, width=2),
        yaxis="y2"))

    #layout
    fig.update_layout(
        title=titulo,
        xaxis=dict(title=x),
        yaxis=dict(
            title=dict(text=nome_y1, font=dict(color=cor_y1)),
            tickfont=dict(color=cor_y1)),
        yaxis2=dict(
            title=dict(text=nome_y2, font=dict(color=cor_y2)),
            tickfont=dict(color=cor_y2),
            overlaying="y",
            side="right"),
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99))
    return fig

def salvar_log(user_id, pagina, tempo):
    arquivo = "logs_usuarios.csv" #define o nome do arquivo onde as informações serão salvas

    novo_dado = pd.DataFrame([{
        "user_id": user_id,
        "pagina": pagina,
        "tempo_segundos": tempo,
        "timestamp": datetime.now()}]) #cria colunas

    try:
        if os.path.exists(arquivo): #verifica se o arquivo existe
            df = pd.read_csv(arquivo) #se existir, lê o arquivo atual
            df = pd.concat([df, novo_dado], ignore_index=True) #adiciona uma nova linha ao que já existia
        else: #se o arquivo não existe, cria um com a primeira linha
            df = novo_dado
        df.to_csv(arquivo, index=False) #salva tudo
    except Exception as e: #se der erro, não encerra o site, apenas mostra no terminal
        print("Erro ao salvar log:", e)

#páginas ---------------------------------------------

#MONITORAMENTO DE NAVEGAÇÃO -------------------------------------------

agora = datetime.now() #pega o horário atual

if st.session_state.pagina_atual != pagina: #verifica se o usuário mudou de página
    if st.session_state.pagina_atual is not None: #se mudou, entra aqui
        tempo_pagina = (agora - st.session_state.inicio_pagina).total_seconds() #calcula quanto tempo o usuário ficou na página anterior

        salvar_log(
            st.session_state.user_id,
            st.session_state.pagina_atual,
            tempo_pagina) #salva no csv
        
    st.session_state.pagina_atual = pagina #atualiza a página atual para a nova
    st.session_state.inicio_pagina = agora #marca o início da nova página


if pagina == "Visão Geral":
   st.title("Valores Totais e Resumo:")
   #colunas e cards
   col3, col4 = st.columns(2)
   with col3:
       card("Primeira Data Documentada", "22/01/2020")
       card("Dia Com Maior Número de Casos Confirmados", "23/01/2022 (~4,08 Milhões)")

   with col4:
       card("Última Data Documentada", "09/03/2023")
       card("Dia Com Maior Número de Mortes", "20/01/2021 (~17,5 Mil)")

   marcacao_preta()

   col1, col2 = st.columns(2) #divide a página em dois
   with col1: #na coluna 1:
       card("Total de Casos", f"{total_casos:,}")

   with col2:
       card("Total de Mortes", f"{total_mortes:,}")

   ultimo_caso = tabela_covid.sort_values("Data").groupby("País").last().reset_index() #gráfico casos e mortes

   st.subheader("Mapa Global")
   tipo = st.radio("Escolha o indicador:", ["Casos", "Mortes"], horizontal=True) #botão de escolha
   fig_mapa_casos_mortes = px.choropleth( #criação do mapa
       ultimo_caso,
       locations="País",
       locationmode="country names",
       color=tipo,
       hover_name="País",      #oque aparece quando passa o mouse
       hover_data={tipo: ":,."},
       color_continuous_scale="OrRd" if tipo == "Casos" else "Greys")   #mudança de cores (preto ou vermelho)

   fig_mapa_casos_mortes.update_layout(    #personalia o layout
       geo=dict(showframe=False, showcoastlines=False),  #remove borda e linhas do fundo do gráfico
       margin=dict(l=0, r=0, t=0, b=0),   #tamanho
       height=400)
   st.plotly_chart(fig_mapa_casos_mortes, use_container_width=True)  #expõe no app

   #----------------------------------------------------------

   col5, col6, col7 = st.columns([1, 1, 1], gap="small")
   with col5:
       card("País mais afetado", "EUA (USA)")
   with col6:
       card("Casos EUA", "103.802.702")
   with col7:
       card("Mortes EUA", "1.123.836")

elif pagina == "Global":
   st.title("Dados Globais")
   st.write("Evolução da COVID-19 no Brasil e no mundo.")

   #informações casos---------------

   col1, col2 = st.columns([2, 2])

   with col1:
       ultimo_caso = tabela_covid.sort_values("Data").groupby("País").last().reset_index()  #mostrar os países com maiores valores
       top10_caso = ultimo_caso.sort_values("Casos", ascending=False).head(10)["País"]   #top10 desses países

       tabela_covid1_plot_casos = tabela_covid[tabela_covid["País"].isin(top10_caso)] #filtrar

       forma_casos = px.line(
           tabela_covid1_plot_casos,
           x="Data",
           y="Casos",
           color="País",
           title="Top 10 Países com Mais Casos de COVID-19")  #criar o gráfico
       st.plotly_chart(forma_casos, use_container_width=True)

   with col2:
       st.subheader("Top 6 Países com Mais Casos")
       colunas = st.columns(2)
       top6_casos = ultimo_caso.sort_values("Casos", ascending=False).head(6)

       for i, (_, row) in enumerate(top6_casos.iterrows()):
           with colunas[i % 2]:
               card(
                   row["País"],
                   f"{row['Casos']:,}".replace(",", "."))

   marcacao_cinza()

   #informações mortes
   col3, col4 = st.columns([2, 2])

   with col3:
       ultima_mortes= tabela_covid.sort_values("Data").groupby("País").last().reset_index()  #mostrar os países com maiores valores
       top10_mortes = ultima_mortes.sort_values("Mortes", ascending=False).head(10)["País"]   #top10 desses países

       tabela_covid1_plot_mortes = tabela_covid[tabela_covid["País"].isin(top10_mortes)] #filtrar

       forma_mortes = px.line(
           tabela_covid1_plot_mortes,
           x="Data",
           y="Mortes",
           color="País",
           title="Top 10 Países com Mais Mortes Causadas pela COVID-19")  #criar gráfico
       st.plotly_chart(forma_mortes, use_container_width=True)

   with col4:
       st.subheader("Top 6 Países com Mais Mortes")
       colunas = st.columns(2)
       top6_mortes = ultima_mortes.sort_values("Mortes", ascending=False).head(6)

       for i, (_, row) in enumerate(top6_mortes.iterrows()):
           with colunas[i % 2]:
               card(row["País"], f"{row['Mortes']:,}".replace(",", "."))

   marcacao_preta()

   #mapa casos e mortes------------

   col5, col6, col7 = st.columns(3)

   with col5:
       st.subheader("Mapa Global de Casos")
       fig_mapa_casos = px.choropleth(
           ultimo_caso,
           locations="País",
           locationmode="country names",
           color="Casos",
           hover_name="País",
           color_continuous_scale="Reds",
           title="Casos de COVID-19 por País")
       fig_mapa_casos.update_layout(
           geo=dict(
               showframe=False,
               showcoastlines=False,
               projection_type="natural earth"),
       margin=dict(l=0, r=0, t=50, b=0))
       st.plotly_chart(fig_mapa_casos, use_container_width=True)

   with col6:
       st.subheader("Mapa Global de Mortes")
       fig_mapa_mortes = px.choropleth(
           ultima_mortes,
           locations="País",
           locationmode="country names",
           color="Mortes",
           hover_name="País",
           color_continuous_scale="Greys",
           title="Mortes de COVID-19 por País")
       fig_mapa_mortes.update_layout(
           geo=dict(
               showframe=False,
               showcoastlines=False,
               projection_type="natural earth"),
       margin=dict(l=0, r=0, t=50, b=0))
       st.plotly_chart(fig_mapa_mortes, use_container_width=True)

   top6_casos["Taxa de Mortalidade (%)"] = (
       top6_casos["Mortes"] / top6_casos["Casos"]) * 100  #criar taxa

   with col7:
       #gráfico taxa de mortalidade
       grafico_taxa_mortalidade = px.bar(
           top6_casos.sort_values("Taxa de Mortalidade (%)", ascending=False),
           x="País",
           y="Taxa de Mortalidade (%)",
           title="Top 6 - Taxa de Mortalidade (A Cada 100 Habitantes)",
           color="Taxa de Mortalidade (%)",
           color_continuous_scale="Reds",
           labels={"Taxa de Mortalidade (%)": "Taxa (%)"})
       #deixar valores visíveis nas barras
       grafico_taxa_mortalidade.update_traces(
           texttemplate="%{y:.2f}%",
           textposition="outside")
       st.plotly_chart(grafico_taxa_mortalidade, use_container_width=True)

   col8, col9 = st.columns(2)
   with col8:
       #gráfico de linha pico de casos
       fig_casos_semana = px.line(
           global_semanal,
           x="Data",
           y="Novos Casos",
           title="Casos por Semana (Mundo)",
           color_discrete_sequence=["#ff6b6b"])

       adicionar_marcador(fig_casos_semana, global_semanal, "2020-01-26", "Data", "Novos Casos",
                           "Emergência", "OMS decreta emergência de saúde pública mundial.")
       adicionar_marcador(fig_casos_semana, global_semanal, "2020-03-11", "Data", "Novos Casos",
                           "Início Pandemia", "OMS anuncia decreto de pandemia.")
       adicionar_marcador(fig_casos_semana, global_semanal, "2020-12-08", "Data", "Novos Casos",
                           "1ª Vacina", "Primeira vacina aplicada fora de testes clínicos, no Reino Unido.")
       adicionar_marcador(fig_casos_semana, global_semanal, "2021-11-26", "Data", "Novos Casos",
                           "Ômicron", "Variante Ômicron é vista como preocupante.")
       adicionar_marcador(fig_casos_semana, global_semanal, "2023-05-05", "Data", "Novos Casos",
                           "Fim Pandemia", "OMS decreta o fim da pandemia.")
       
       st.plotly_chart(fig_casos_semana, use_container_width=True)

   with col9:
       #gráfico de linha pico de mortes
       global_semanal["Mortes MM"] = global_semanal["Novas Mortes"].rolling(2).mean()
       fig_mortes_semana = px.line(
           global_semanal,
           x="Data",
           y="Novas Mortes",
           title="Mortes por Semana (Mundo)",
           color_discrete_sequence=["#555555"])

       adicionar_marcador(fig_mortes_semana, global_semanal, "2020-01-26", "Data", "Novas Mortes",
                    "Emergência", "OMS decreta emergência de saúde pública mundial.")
       adicionar_marcador(fig_mortes_semana, global_semanal, "2020-03-11", "Data", "Novas Mortes",
                    "Início Pandemia", "OMS anuncia decreto de pandemia.")
       adicionar_marcador(fig_mortes_semana, global_semanal, "2020-12-08", "Data", "Novas Mortes",
                    "1ª Vacina", "Primeira vacina aplicada fora de testes clínicos, no Reino Unido.")
       adicionar_marcador(fig_mortes_semana, global_semanal, "2021-11-26", "Data", "Novas Mortes",
                    "Ômicron", "Variante Ômicron é vista como preocupante.")
       adicionar_marcador(fig_mortes_semana, global_semanal, "2023-05-05", "Data", "Novas Mortes",
                    "Fim Pandemia", "OMS decreta o fim da pandemia.")
       st.plotly_chart(fig_mortes_semana, use_container_width=True)

       st.write(
           "Nota: alguns picos podem indicar atrasos nas notificações dos dados da "
           "Johns Hopkins Coronavirus Resource Center (CRC), especialmente em 2023.")

elif pagina == "Brasil":
   st.title("Brasil")
   st.write("Resumo da COVID-19 no Brasil")

   #CASOS E MORTES NO BRASIL ----------------------------------

   ultimo_br = tabela_covid_br.sort_values("Data Brasil").groupby("Estado").last().reset_index()

   total_casos_br = ultimo_br["Casos Brasil"].sum()
   total_mortes_br = ultimo_br["Mortes Brasil"].sum()

   #VACINAÇÃO NO BRASIL ---------------------------------------

   vac_br = tabela_covid_vac[
       tabela_covid_vac["País Vacina"] == "Brazil"
   ].sort_values("Data Vacina")

   if not vac_br.empty:
       ultimo_vac_br = vac_br.iloc[-1]
       total_doses_br = ultimo_vac_br["Total Vacinas"]
       total_1dose_br = ultimo_vac_br["1ª Dose"]
       total_imunizados_br = ultimo_vac_br["Total Imunizados"]
   else:
       total_doses_br = total_1dose_br = total_imunizados_br = 0

   #CARDS --------------------------

   col1, col2 = st.columns(2)

   with col1:
       card("Casos Totais", "37.076.053")
   with col2:
       card("Mortes Totais", "699.276")

   # vacinação
   col3, col4, col5 = st.columns(3)

   with col3:
           card("Total de Doses", f"{int(total_doses_br):,}".replace(",", "."))
   with col4:
           card("1ª Dose", f"{int(total_1dose_br):,}".replace(",", "."))
   with col5:
           card("Total Imunizados", f"{int(total_imunizados_br):,}".replace(",", "."))

   marcacao_cinza()

   #gráfico Brasil (casos e mortes) -------------

   dados_br = tabela_covid[
       tabela_covid["País"] == "Brazil"
   ].sort_values("Data") #filtrar apenas Brasil da tabela global

   col10, col11 = st.columns(2) #criar gráfico com 2 eixos

   with col10:
       fig = grafico_dois_eixos(
        dados_br,
        "Data",
        "Casos",
        "Mortes",
        titulo="Evolução da COVID-19 no Brasil")
       st.plotly_chart(fig, use_container_width=True)

   #gráfico de vacinação

   vac_br = tabela_covid_vac[
       tabela_covid_vac["País Vacina"] == "Brazil"
   ].sort_values("Data Vacina") #filtrar Brasil

   vac_br = vac_br.dropna(subset=["Total Vacinas"]) #remover valores nulos

   #criar gráfico
   with col11:
       grafico_vac_br = go.Figure()
       grafico_vac_br.add_trace(go.Scatter(
           x=vac_br["Data Vacina"],
           y=vac_br["Total Vacinas"],
           name="Total de Vacinas",
           line=dict(color="blue", width=2)))

       #layout
       grafico_vac_br.update_layout(
           title="Evolução da Vacinação no Brasil",
           xaxis=dict(title="Data"),
           yaxis=dict(title="Total de Vacinas Aplicadas"),
           hovermode="x unified")
       st.plotly_chart(grafico_vac_br, use_container_width=True)

   marcacao_preta()

   st.subheader("Análise por Estado")

   #filtros por estado
   estados = tabela_covid_br["Estado"].unique() #cards de estados
   estados = [e for e in estados if e != "TOTAL"]

   #lista de estados (sem TOTAL)
   estados = tabela_covid_br["Estado"].unique()
   estados = [e for e in estados if e != "TOTAL"]
   estado_selecionado = st.selectbox(
       "Escolha um estado:",
       sorted(estados))

   dados_estado = tabela_covid_br[
       tabela_covid_br["Estado"] == estado_selecionado
   ].sort_values("Data Brasil") #filtrar dados do estado

   ultimo_estado = dados_estado.iloc[-1]
   casos_estado = ultimo_estado["Casos Brasil"]
   mortes_estado = ultimo_estado["Mortes Brasil"] #pegar último valor (mais recente)

   #cards
   col1, col2 = st.columns(2)
   with col2:
           card(f"Casos em {estado_selecionado}", f"{int(casos_estado):,}".replace(",", "."))
           card(f"Mortes em {estado_selecionado}", f"{int(mortes_estado):,}".replace(",", "."))
           st.write("A soma de casos e mortes dos estados brasileiros podem divergir do total real.")

   with col1:
        fig = grafico_dois_eixos(
            dados_estado,
            "Data Brasil",
            "Casos Brasil",
            "Mortes Brasil",
            titulo=f"Evolução em {estado_selecionado}")
        st.plotly_chart(fig, use_container_width=True) #gráfico de casos e mortes por estado filtrado

elif pagina == "Vacinação":
   st.title("Vacinação")
   st.write("Dados sobre a vacinação no Brasil e no mundo")

   #cards
   col1, col2, col3 = st.columns(3)

   with col1:
       card("Total de Doses Aplicadas", f"{int(total_doses):,}".replace(",", "."))
   with col2:
       card("Pessoas com pelo menos 1 dose", f"{int(total_1_dose):,}".replace(",", "."))
   with col3:
       card("Total de Imunizados", f"{int(total_imunizados):,}".replace(",", "."))

   #gráfico de evolução -------------------------

   col4, col5 = st.columns(2)

   dados_top6_vac = dados_top6_vac.sort_values("Data Vacina") #garantir dados limpos
   dados_top6_vac = dados_top6_vac.dropna(subset=["Total Vacinas"])

   with col4:
       fig_vac = px.line(
           dados_top6_vac,
           x="Data Vacina",
           y="Total Vacinas",
           color="País Vacina",
           title="Evolução da Vacinação - Top 6 Países com Mais Doses Aplicadas")
       st.plotly_chart(fig_vac, use_container_width=True)

   #gráfico de porcentagem --------------------------

   top6_percentual = ultimo_vac[
       ultimo_vac["País Vacina"].isin(top6_vac)
   ][["País Vacina", "% 1ª Dose"]] #filtro pegar último valor dos top 6

   with col5:
       fig_percentual = px.bar(
       top6_percentual.sort_values("% 1ª Dose", ascending=False),
       x="País Vacina",
       y="% 1ª Dose",
       title="Percentual da População com Pelo Menos 1 Dose (Top 6)",
       text="% 1ª Dose")
       fig_percentual.update_traces(
           texttemplate="%{y:.2f}%",
           textposition="outside")
       st.plotly_chart(fig_percentual, use_container_width=True)


if pagina == "Filtro de Países":
   st.title("Escolha um país e uma data para filtragem específica:")

   #filtragens
   paises = tabela_covid["País"].unique()  #lista de países
   pais_selecionado = st.selectbox("Escolha um país:", sorted(paises))  #filtro de país
   data_min = tabela_covid["Data"].min()  #filtro de período
   data_max = tabela_covid["Data"].max()
   periodo = st.date_input(
       "Escolha o período:",
       [data_min, data_max])   #lista de datas

   if len(periodo) == 2:
    inicio, fim = periodo
   else:
    st.warning("Selecione um intervalo válido")
    st.stop()

   dados_filtrados = tabela_covid[
       (tabela_covid["País"] == pais_selecionado) &
       (tabela_covid["Data"] >= pd.to_datetime(inicio)) &
       (tabela_covid["Data"] <= pd.to_datetime(fim))] #garantir que o usuário escolheu intervalo válido

   #criar os cards
   total_casos = dados_filtrados["Casos"].max()
   total_mortes = dados_filtrados["Mortes"].max()

   col1, col2 = st.columns(2)

   with col1:
       card("Casos Totais", f"{int(total_casos):,}".replace(",", "."))
   with col2:
       card("Mortes Totais", f"{int(total_mortes):,}".replace(",", "."))

   marcacao_cinza()

   #gráfico mortes e casos em diferentes eixos(filtragem)
   fig = grafico_dois_eixos(
        dados_filtrados,
        "Data",
        "Casos",
        "Mortes",
        titulo=f"Evolução da COVID-19 em {pais_selecionado}")
   st.plotly_chart(fig, use_container_width=True)

   #vacinação (filtragem)
   vac_filtrado = tabela_covid_vac[
       tabela_covid_vac["País Vacina"] == pais_selecionado
   ].sort_values("Data Vacina") #pegar dados de vacinação do país selecionado

   if not vac_filtrado.empty:
       ultimo_vac_pais = vac_filtrado.iloc[-1] # pegar último registro (mais recente)
       vac_total = ultimo_vac_pais["Total Vacinas"]
       vac_1dose = ultimo_vac_pais["1ª Dose"]
       vac_imunizados = ultimo_vac_pais["Total Imunizados"]

       st.markdown("Vacinação")

       col3, col4, col5 = st.columns(3)
       with col3:
           card("Doses Aplicadas",f"{int(vac_total):,}".replace(",", "."))
       with col4:
           card("Pelo menos 1 dose", f"{int(vac_1dose):,}".replace(",", "."))
       with col5:
           card("Total Imunizados", f"{int(vac_imunizados):,}".replace(",", "."))

elif pagina == "Dados Brutos":
   st.title("DataBases")
   st.write("Aqui, você encontra as 3 tabelas principais.")

   st.dataframe(tabela_covid)
   st.dataframe(tabela_covid_br)
   st.dataframe(tabela_covid_vac)

#REGISTRAR SAÍDA DO USUÁRIO -----------------------------

def salvar_saida():
    try:
        agora = datetime.now()  #pega a hora de entrada
        tempo_pagina = (agora - st.session_state.inicio_pagina).total_seconds() #calcula o tempo de permanência na página

        salvar_log(
            st.session_state.user_id,
            st.session_state.pagina_atual,
            tempo_pagina) #salva no csv
    except:
        pass

atexit.register(salvar_saida) #registra a função para rodar quando o site encerrar

tempo_total = (datetime.now() - st.session_state.entrada).total_seconds() #calcula o tempo total
st.caption(f"Tempo no site: {tempo_total:.1f} segundos") #mostra o tempo total no site

salvar_log(
    st.session_state.user_id,
    "SAIDA_TOTAL",
    tempo_total)