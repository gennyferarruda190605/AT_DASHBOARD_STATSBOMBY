import pandas as pd 
from mplsoccer import Pitch, VerticalPitch
from statsbombpy import sb
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def competicoes():
    return sb.competitions()


def partidas(competition_id: int, season_id: int):
    return sb.matches(competition_id=competition_id, season_id=season_id).sort_values('match_date')



def eventos(match_id):
    ev = sb.events(match_id=match_id)
    return ev



def tabela_eventos(ev):

    eventos_filtro = (ev['type'].isin(['Pass', 'Shot', 'Dribble']) | ((ev['type'] == 'Duel') & (ev['duel_type'] == 'Tackle')))
    eventos = ev[eventos_filtro].copy()
    eventos['Resultado'] = eventos['shot_outcome']
    eventos['Resultado'] = eventos['Resultado'].fillna(eventos['pass_outcome'])
    eventos['Resultado'] = eventos['Resultado'].fillna('Certo')

    if 'dribble_outcome' in eventos.columns:
         eventos['Resultado'] = eventos['Resultado'].fillna(eventos['dribble_outcome'])

    tabela = eventos[['timestamp', 'team', 'player', 'type', 'Resultado']]
    tabela['type'] = tabela['type'].replace({
        'Pass': 'Passe', 
        'Shot': 'Chute (finalização)', 
        'Duel': 'Desarme',
        'Dribble': 'Drible'})

    
    with st.expander('Ver tabela completa dos eventos'):
        st.dataframe(tabela)
    
    csv = tabela.to_csv(index=False).encode('utf-8')
    st.download_button(label='Baixar tabela completa dos eventos (CSV)', data=csv, file_name='tabela_eventos.csv')





def estatisticas_partida(ev, times):
    st.write(f'DEBUG times recebido: {list(times)} (tamanho: {len(times)})')
    dados = {}
    for time in times:

        eventos_time = ev[ev['team'] == time]
        adversario = [t for t in times if t != time][0]
        eventos_adversario = ev[ev['team'] == adversario]

        passes = eventos_time[eventos_time['type'] == 'Pass']
        chutes = eventos_time[eventos_time['type'] == 'Shot']
        desarmes = eventos_time[(eventos_time['type'] == 'Duel') & (eventos_time['duel_type'] == 'Tackle')]
        
        chutes_sofridos = eventos_adversario[eventos_adversario['type'] == 'Shot']
        defesas = chutes_sofridos['shot_outcome'].isin(['Saved']).sum()
        gols_sofridos = (chutes_sofridos['shot_outcome'] == 'Goal').sum()

        dados[time] = {
            'Gols': (chutes['shot_outcome'] == 'Goal').sum(),
            'Chutes': len(chutes),
            'Chutes_no_alvo': chutes['shot_outcome'].isin(['Goal', 'Saved']).sum(),
            'Passes': len(passes),
            'Passes_certos': passes['pass_outcome'].isna().sum(),
            'Desarmes': len(desarmes), 
            'Defesas': defesas,
            'Gols_sofridos': gols_sofridos}
        

    estatisticas = pd.DataFrame(dados)
    precisao_passe = estatisticas.loc['Passes_certos'] / estatisticas.loc['Passes']
    precisao_chute = estatisticas.loc['Chutes_no_alvo'] / estatisticas.loc['Chutes']
    total_chutes_sofridos = estatisticas.loc['Defesas'] + estatisticas.loc['Gols_sofridos']
    precisao_defesa = estatisticas.loc['Defesas'] / total_chutes_sofridos.replace(0, pd.NA)

    col1, col2 = st.columns(2)

    for coluna, time in zip([col1, col2], times):
        adversario = [t for t in times if t != time][0]


        with coluna.container(border=True, key=f'container_{time}'):
            st.markdown(f'**{time}**')
            m1, m2, m3, m4 = st.columns(4)
            m1.metric('Gols', int(estatisticas.loc['Gols', time])),
            m2.metric('Precisão de Chutes', f'{precisao_chute[time]*100:.1f}%',
                    delta=f'{(precisao_chute[time]-precisao_chute[adversario])*100:.1f}%')
            m3.metric('Precisão de Passes certos', f'{precisao_passe[time]*100:.1f}%',
                    delta=f'{(precisao_passe[time]-precisao_passe[adversario])*100:.1f}%')
            m4.metric('Precisão de Defesa (Goleiro)', f'{precisao_defesa[time]*100:.1f}%',
                    delta=f'{(precisao_defesa[time]-precisao_defesa[adversario])*100:.1f}%')

    st.dataframe(estatisticas)




def jogadores_estatisticas(ev, jogador, exibir=True):

    ev_filtrado = ev[ev['player'] == jogador]

    if ev_filtrado.empty:
        st.warning(f'Não há dados registrados de {jogador} nesta partida.')
        return
    
    time = ev_filtrado['team'].iloc[0]

    passes = ev_filtrado[ev_filtrado['type'] == 'Pass']
    passes_certos = passes['pass_outcome'].isna().sum()
    chutes = ev_filtrado[ev_filtrado['type'] == 'Shot']
    gols = (chutes['shot_outcome'] == 'Goal').sum()
    desarmes = ev_filtrado[(ev_filtrado['type'] == 'Duel') & (ev_filtrado['duel_type'] == 'Tackle')]


    dribles = ev_filtrado[ev_filtrado['type'] == 'Dribble']
    if 'dribble_outcome' in dribles.columns:
        dribles_certos = (dribles['dribble_outcome'] == 'Complete').sum()
    else:
        dribles_certos = 0


    precisao_chutes = 100 * gols / len(chutes) if len(chutes) > 0 else 0
    precisao_passe = 100 * passes_certos / len(passes)if len(passes) > 0 else 0

    dados_jogador = { 
            'Gols': gols,
            'Chutes': len(chutes),
            'Passes': len(passes),
            'Passes_certos': passes_certos,
            'Desarmes': len(desarmes),
            'Dribles': dribles_certos,
            'Precisão_chutes': precisao_chutes,
            'Precisão_passe': precisao_passe}


    if exibir:

        with st.container(border=True):

            st.subheader(jogador)
            st.caption(f'Time - {time}')
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric('Precisão de passe', f'{precisao_passe:.1f}%')
            c2.metric('Precisão de chutes (para gols)', f'{precisao_chutes:.1f}%')
            c3.metric('Chutes', len(chutes))
            c4.metric('Gols', gols)
            c5.metric('Dribles', dribles_certos)

        estatisticas_jogador = pd.DataFrame(dados_jogador, index=[0])
        st.dataframe(estatisticas_jogador)

        csv = estatisticas_jogador.to_csv(index=False).encode('utf-8')
        st.download_button(label='Baixar estatísticas (CSV)', data=csv, file_name=f'estatisticas_{jogador}.csv')

    return dados_jogador




def mapa_passes(ev, time):

    passes = ev[(ev['type'] == 'Pass') & (ev['team'] == time)]
    passes[['x', 'y']] = passes['location'].tolist()
    passes[['end_x', 'end_y']] = passes['pass_end_location'].tolist()

    certos = passes[passes['pass_outcome'].isna()]

    campo = Pitch(pitch_type='statsbomb')
    fig, ax = campo.draw(figsize=(10, 7))
    campo.arrows(passes['x'], passes['y'], passes['end_x'], passes['end_y'], color='red', width=2, ax=ax)
    campo.arrows(certos['x'], certos['y'], certos['end_x'], certos['end_y'], color='green', width=2, ax=ax, label=f' Passes certos ({len(certos)})')
    ax.legend()
    return fig




def mapa_chutes(ev, time):
    
    chutes = ev[(ev['type'] == 'Shot') & (ev['team'] == time)]
    chutes[['x', 'y']] = chutes['location'].tolist()
    gols = chutes[chutes['shot_outcome'] == 'Goal']
    pitch = Pitch(pitch_type='statsbomb')
    fig, ax = pitch.draw(figsize=(10, 7))
    ax.scatter(chutes['x'], chutes['y'])
    ax.scatter(gols['x'], gols['y'], color='gold', label=f'Total de Gol(s) = ({len(gols)})')
    ax.legend()
    return fig




def mapa_passe_jogador(ev, jogador):

    passes = ev[(ev['type'] == 'Pass') & (ev['player'] == jogador)]

    if passes.empty:

        st.info(f'{jogador} não tem passes registrados nesta partida.')

    passes[['x', 'y']] = passes['location'].tolist()
    passes[['end_x', 'end_y']] = passes['pass_end_location'].tolist()
    certos = passes[passes['pass_outcome'].isna()]

    campo = Pitch(pitch_type='statsbomb')
    fig, ax = campo.draw(figsize=(10, 7))
    campo.arrows(passes['x'], passes['y'], passes['end_x'], passes['end_y'], color='red', width=2, ax=ax)
    campo.arrows(certos['x'], certos['y'], certos['end_x'], certos['end_y'], color='green', width=2, ax=ax, label=f' Passes certos ({len(certos)})')
    ax.legend()
    return fig




def mapa_chutes_jogador (ev, jogador):

    chutes = ev[(ev['type'] == 'Shot') & (ev['player'] == jogador)]

    if chutes.empty:
        st.info(f'{jogador} não teve chutes registrados nesta partida.')
        return None
    
    chutes[['x', 'y']] = chutes['location'].tolist()

    gols = chutes[chutes['shot_outcome'] == 'Goal']

    pitch = Pitch(pitch_type='statsbomb')
    fig, ax = pitch.draw()
    ax.scatter(chutes['x'], chutes['y'])
    ax.scatter(gols['x'], gols['y'], color='gold', label=f'Total de Gol(s) = ({len(gols)})')
    ax.legend()
    return fig




def comparar_jogadores(ev, jogador1, jogador2):

    stats1 = jogadores_estatisticas(ev, jogador1, exibir=False)
    stats2 = jogadores_estatisticas(ev, jogador2, exibir=False)
    
    if not stats1 or not stats2:
        st.warning('Um dos jogadores não possui dados nesta partida.')
        return

    
    df_grafico = pd.DataFrame({
        jogador1: [stats1['Gols'], stats1['Passes'], stats1['Passes_certos'], stats1['Dribles'], stats1['Chutes'], stats1['Desarmes']],
        jogador2: [stats2['Gols'], stats2['Passes'], stats2['Passes_certos'], stats2['Dribles'], stats2['Chutes'], stats2['Desarmes']]}, index=['Gols', 'Passes', 'Passes_certos', 'Dribles', 'Chutes', 'Desarmes'])


    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown(f'### **{jogador1}**')
            c1, c2, c3 = st.columns(3)
            c1.metric('Precisão de passe certos', f'{stats1['Precisão_passe']:.1f}%',
                    delta=f'{stats1['Precisão_passe'] - stats2['Precisão_passe']:.1f}%')
            c2.metric('Precisão de chutes (para gols)', f'{stats1['Precisão_chutes']:.1f}%',
                    delta=f'{stats1['Precisão_chutes'] - stats2['Precisão_chutes']:.1f}%')
            c3.metric('Gols', stats1['Gols'])

    with col2:
        with st.container(border=True):
            st.markdown(f'### **{jogador2}**')
            c1, c2, c3 = st.columns(3)
            c1.metric('Precisão de passe certos', f'{stats2['Precisão_passe']:.1f}%',
                    delta=f'{stats2['Precisão_passe'] - stats1['Precisão_passe']:.1f}%')
            c2.metric('Precisão de chutes (para gols)', f'{stats2['Precisão_chutes']:.1f}%',
                    delta=f'{stats2['Precisão_chutes'] - stats1['Precisão_chutes']:.1f}%')
            c3.metric('Gols', stats2['Gols'])


    fig, ax = plt.subplots(figsize=(8, 3))

    df_grafico.plot.bar(ax=ax, rot=0) 
    ax.set_title('Comparação entre jogadores')
    ax.legend(title='jogador')
    ax.grid(axis='y', color='#e0e0e0', linestyle='-')
    ax.set_axisbelow(True)
    st.pyplot(fig, use_container_width=False)
    
    st.divider()

    st.subheader('Tabela de eventos comparação 📋')
    st.dataframe(df_grafico)
    csv = df_grafico.to_csv(index=False).encode('utf-8')
    st.download_button(label='Baixar comparação (CSV)', data=csv, file_name='Comparação_jogadores.csv')




def mapa_calor_chutes(ev, time):

    chutes = ev[(ev['type'] == 'Shot') & (ev['team'] == time)]
    chutes[['x', 'y']] = chutes['location'].tolist()

    pitch = Pitch(pitch_type='statsbomb')
    bin_estatisticas = pitch.bin_statistic(chutes['x'], chutes['y'], statistic='count', bins=(10, 8))
    
    fig, ax = pitch.draw(figsize=(4, 2))
    mapa = pitch.heatmap(bin_estatisticas, ax=ax)
    regua = fig.colorbar(mapa, ax=ax, shrink=0.6)
    regua.set_label('Quantidade de chutes')

    return fig



def mapa_calor_chutes_jogador(ev, jogador):

    chutes = ev[(ev['type'] == 'Shot') & (ev['player'] == jogador)]

    if chutes.empty:
        st.info(f'{jogador} não teve chutes registrados nesta partida.')
        return None
    
    chutes[['x', 'y']] = chutes['location'].tolist()

    pitch = Pitch(pitch_type='statsbomb')
    bin_estatisticas = pitch.bin_statistic(chutes['x'], chutes['y'], statistic='count', bins=(10, 8))

    fig, ax = pitch.draw(figsize=(4, 2))
    mapa = pitch.heatmap(bin_estatisticas, ax=ax, cmap='viridis', edgecolors='#22312b')
    regua = fig.colorbar(mapa, ax=ax, shrink=0.6)
    regua.set_label('Quantidade de ações')

    return fig