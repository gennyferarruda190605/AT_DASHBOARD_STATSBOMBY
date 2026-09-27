import streamlit as st
from mplsoccer import Pitch, VerticalPitch
from funcoes import competicoes, partidas, eventos, estatisticas_partida, mapa_chutes, mapa_passes, jogadores_estatisticas, mapa_passe_jogador, mapa_chutes_jogador, tabela_eventos, comparar_jogadores, mapa_calor_chutes, mapa_calor_chutes_jogador
import time


@st.cache_data(ttl=3600)
def carregar_dados():
    return competicoes()

@st.cache_data(ttl=3600)
def carregar_eventos(match_id):
    return eventos(match_id)

competicoes = carregar_dados()

st.set_page_config(page_title='Dashboard de Futebol', page_icon='⚽', layout='wide')

with st.sidebar:

    with st.form('filtro_jogos'):

        st.header('Seleção de Filtros 🔎')

        competicoes = competicoes.assign(nome_pais=competicoes['competition_name'] + ' - ' + competicoes['country_name'])
        campeonato = st.selectbox('Campeonato', sorted(competicoes['nome_pais'].unique()) ,key='campeonato')

        temp = competicoes[competicoes['nome_pais'] == campeonato].sort_values('season_name', ascending=False)
        temporada = st.selectbox('Temporada', temp['season_name'].tolist(), key='temporada')

        info = temp[temp['season_name'] == temporada].iloc[0]

        part = partidas(int(info['competition_id']), int(info['season_id']))
        part = part.assign(partida=part['home_team']  + '  x  ' + part['away_team'] + '  |  ' + part['match_date'].astype(str))
        
        partida = st.selectbox('Partida', part['partida'].tolist(), key='partida')

        jogo = part[part['partida'] == partida].iloc[0] 
        ev = carregar_eventos(int(jogo['match_id']))
        times = [jogo['home_team'], jogo['away_team']]

        st.divider()

        foco = st.radio('Foco da Análise Exploratoria🎯', ['Partida ⚽', 'Jogador👤'] , key='foco')

        if foco == 'Jogador👤':

            lista_jogadores = ev['player'].dropna().unique()
            lista_jogadores = sorted(lista_jogadores)
            
            jogador = st.selectbox('Selecione o Jogador', lista_jogadores, key='jogador')

        st.form_submit_button('Aplicar filtros')





st.title('⚽ Dashboard de Futebol ')

times = [jogo['home_team'], jogo['away_team']]

tab1, tab2, tab3, tab4 = st.tabs(['Visão geral📋', 'Mapas🗺️', 'Comparar jogadores👥', 'Explorar Eventos🔍'])

with tab1:
    st.header(f'{jogo['home_team']} {jogo['home_score']} X {jogo['away_score']} {jogo['away_team']}')
    st.caption(f'🏆 {campeonato} · 📅 Temporada {temporada}')

    area_tab1 = st.empty()

    with area_tab1.container():
        with st.spinner('Processando o arquivo...', show_time=True):
            time.sleep(4)

        barra = st.progress(0.2, 'Aguarde mais um pouco...')
        for i in range(0, 101, 5):
            time.sleep(0.3)
            barra.progress(i, f'Processando {i}%')


    with area_tab1.container():

        if foco == 'Partida ⚽':
            estatisticas_partida(ev, times)
            st.subheader('Tabela com todos os Eventos📋')
            tabela_eventos(ev)

        else:
            jogadores_estatisticas(ev, jogador)

with tab2:

    if foco == 'Partida ⚽':

        time = st.radio('Time', times, horizontal=True, key='time_mapa')

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f'Mapa de Passes - {time}')
            st.pyplot(mapa_passes(ev, time))

        with col2:
            st.subheader(f'Mapa de Chutes - {time}')
            st.pyplot(mapa_chutes(ev, time))

        col1.subheader(f'Mapa de Calor de Chutes - {time}')
        st.pyplot(mapa_calor_chutes(ev, time))

    else:
        
        col1, col2 = st.columns(2)

        map_passe = mapa_passe_jogador(ev, jogador)
        col1.subheader(f'Mapa de Passes - {jogador}')
        if map_passe:
            col1.pyplot(map_passe)

        map_chutes = mapa_chutes_jogador(ev, jogador)
        col2.subheader(f'Mapa de Chutes - {jogador}')
        if map_chutes:
            col2.pyplot(map_chutes)

        mapa_calor = mapa_calor_chutes_jogador(ev, jogador)
        st.subheader(f'Mapa de Calor de Chutes - {jogador}')
        if map_chutes:
            st.pyplot(mapa_calor)



with tab3:

    lista_todos_jogadores = sorted(ev['player'].dropna().unique())

    st.markdown(' #### Selecione dois jogadores para comparar')
    col1, col2 = st.columns(2)

    with col1:
        jogador_a = st.selectbox('Jogador 1', lista_todos_jogadores, key='jog_a')
    with col2:
        jogador_b = st.selectbox('Jogador 2', lista_todos_jogadores, key='jog_b')

    if jogador_a and jogador_b:
        if jogador_a != jogador_b:
            st.divider()
            comparar_jogadores(ev, jogador_a, jogador_b)
        else:
            st.info('Selecione dois jogadores diferentes para ver a comparação.')


with tab4:

    with st.form('filtro_eventos'):
        st.markdown('**Filtrar tabela de eventos 📋🔍**')

        c1, c2 = st.columns(2)
        qtde = c1.number_input('Quantidade de eventos', min_value=5, max_value=500, value=50, step=5)
        intervalo = c2.slider('Intervalo de tempo (minutos)', 0, 120, (0, 45))

        tipos_disponiveis = sorted(ev['type'].dropna().unique())
        tipos_escolhidos = st.multiselect('Tipos de evento', tipos_disponiveis, default=['Pass', 'Shot'])

        ordenar_desc = st.checkbox('Ordenar por recentes primeiro')
        enviado = st.form_submit_button('Aplicar filtros')

if enviado:

    filtro = ev[ev['minute'].between(intervalo[0], intervalo[1]) & ev['type'].isin(tipos_escolhidos)]
    filtro = filtro.sort_values('minute', ascending=not ordenar_desc)
    filtro = filtro.head(int(qtde))

    st.dataframe(filtro[['minute', 'team', 'player', 'type']], use_container_width=True)
