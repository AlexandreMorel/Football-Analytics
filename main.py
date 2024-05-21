# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 11:39:54 2022

@author: alexa
"""

import streamlit as st
from statsbombpy import sb
import pandas as pd
from mplsoccer import Pitch
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from io import BytesIO

# List of games and JSON files as dictionary
games_dict = {
    'Barcelona - Huesca 4:1 (Round 27)': '3773369',
    'Barcelona - Real Madrid 1:3 (Round 7)': '3773585'
}

games_list = list(games_dict.keys())
games_id_list = list(games_dict.values())

# Set page config
st.set_page_config(page_title='Football Data Analysis', page_icon=':soccer:', initial_sidebar_state='expanded')

# Drop-down menu "Select Football Game"
st.sidebar.markdown('## Match Selection')
menu_game = st.sidebar.selectbox('Select a Match', games_list, index=0)

# Get Statsbomb events data based on selected game
df_events = sb.events(match_id=games_dict.get(menu_game))

# Get teams and players names
team_1 = df_events['team'].unique()[0]
team_2 = df_events['team'].unique()[1]
mask_1 = df_events.loc[df_events['team'] == team_1]
mask_2 = df_events.loc[df_events['team'] == team_2]
player_names_1 = mask_1['player'].dropna().unique()
player_names_2 = mask_2['player'].dropna().unique()

# List of activities for drop-down menus
activities = ['Passes', 'Shots', 'Heatmap']

# Drop-down menus 'Select Team, Player and Activity'
st.sidebar.markdown('## Player and Statistic selection')
menu_team = st.sidebar.selectbox('Select a Team', (team_1, team_2))
if menu_team == team_1:
    menu_player = st.sidebar.selectbox('Select a Player', player_names_1)
else:
    menu_player = st.sidebar.selectbox('Select a Player', player_names_2)
menu_activity = st.sidebar.selectbox('Select a Statistic', activities)

st.sidebar.divider()
st.sidebar.markdown('### Made with :heart: by [Alexandre Morel](https://fr.linkedin.com/in/alexandre-morel-38590am)')
st.sidebar.markdown('#### [View source](https://github.com/AlexandreMorel/Football-Analytics):computer:')

# Titles and text above the pitch
st.header('Welcome to my Performance Analysis tool!:dart:', divider='red')
st.write("""* Freshly designed to assess players' individual performance over the course of a match.""")
st.write("""* Event data have been labelled by StastBomb according to the following [specification](https://github.com/statsbomb/statsbombpy/blob/master/doc/Open%20Data%20Events%20v4.0.0.pdf).""")
st.write("""* Use the dropdown-menus on the left sidebar to select a football match, a player, and a statistic to plot.""")
st.divider()
st.write('###', menu_activity, 'Map')
st.write('###### Game:', menu_game)
st.write('###### Player:', menu_player, '(', menu_team ,')')

def passes_map(player, df):
    df_pass = df.loc[(df['player'] == player) & (df['type'] == 'Pass')].dropna(subset=['location', 'pass_end_location'])
    mask_complete = df_pass.pass_outcome.isnull()

    # Créer des séries de données pour chaque type de passe
    pass_types = {
        'Completed': df_pass[mask_complete],
        'Assist': df_pass[df_pass["pass_goal_assist"] == True],
        'Missed': df_pass[~mask_complete]
    }

    total_completed_passes = len(pass_types['Completed'])
    total_missed_passes = len(pass_types['Missed'])
    percentage_completed_passes = round((total_completed_passes / (total_completed_passes + total_missed_passes)) * 100)

    # Setup the pitch
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#FFFFFF', line_color='#000000')
    fig, ax = pitch.draw(figsize=(12, 8))

    # Variables pour stocker les totaux des passes vers l'avant
    forward_passes_completed = 0
    forward_passes_missed = 0

    # Parcourir chaque type de passe et tracer les flèches correspondantes
    for label, data in pass_types.items():
        if not data.empty:
            location = data['location'].tolist()
            pass_end_location = data['pass_end_location'].tolist()
            x1 = pd.Series([el[0] for el in location])
            y1 = pd.Series([el[1] for el in location])
            x2 = pd.Series([el[0] for el in pass_end_location])
            y2 = pd.Series([el[1] for el in pass_end_location])
            color = '#3CD74A' if label == 'Completed' else '#F4D03F' if label == 'Assist' else '#F31515'

            # Compter le nombre de passes vers l'avant
            if label == 'Completed':
                forward_passes_completed += ((x2 > x1)).sum()
            elif label == 'Missed':
                forward_passes_missed += ((x2 > x1)).sum()

            pitch.arrows(x1, y1, x2, y2, width=2, headwidth=6, headlength=6, color=color, ax=ax, label=label)

    # Calcul du pourcentage de passes vers l'avant
    total_forward_passes = forward_passes_completed + forward_passes_missed
    percentage_forward_passes = round((total_forward_passes / (total_completed_passes + total_missed_passes)) * 100)

    percentage_completed_forward_passes = round(forward_passes_completed / total_forward_passes * 100)
 
    col1, col2, col3 = st.columns(3)
    col1.metric("Completed passes", f"{total_completed_passes}/{total_completed_passes + total_missed_passes} ({percentage_completed_passes}%)")
    col2.metric("Completed forward passes", f"{forward_passes_completed}/{total_forward_passes} ({percentage_completed_forward_passes}%)")
    col3.metric("Forward play", f"{percentage_forward_passes}%")

    # Setup the legend
    ax.legend(facecolor='#D4DADC', handlelength=5, edgecolor='None', fontsize=14, loc='upper left')
    return fig, ax

def heatmap(player, df):
    # Filtrer les données du joueur spécifié
    df_heatmap = df.loc[df['player'] == player]

    # Récupérer les coordonnées des emplacements non nuls
    location = df_heatmap["location"].dropna().tolist()
    x = pd.Series([el[0] for el in location])
    y = pd.Series([el[1] for el in location])

    # Setup pitch
    pitch = Pitch(pitch_type='statsbomb', line_zorder=2, pitch_color='#22312b', line_color='#efefef')
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor('#22312b')

    # Générer la heatmap
    bin_statistic = pitch.bin_statistic(x, y, statistic='count', bins=(25, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot', edgecolors='#22312b')  # YlOrRd

    # Ajouter la barre de couleur et formater en blanc cassé
    cbar = fig.colorbar(pcm, ax=ax, shrink=0.6)
    cbar.outline.set_edgecolor('#efefef')
    cbar.ax.yaxis.set_tick_params(color='#efefef')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#efefef')

    return fig, ax

def shots_map(player, df):
    # Filtrer les tirs du joueur spécifié
    shots = df.loc[(df['player'] == player) & (df['type'] == 'Shot')]
    
    # Définir les différents types de tirs
    shot_outcomes = {
        'On target': ['Saved', 'Saved To Post'],
        'Goal': ['Goal'],
        'Blocked': ['Blocked'],
        'Off target': ['Off T', 'Post', 'Wayward', 'Saved Off T']
    }
    
    # Préparer une liste pour stocker les séries de données de chaque type de tir
    series_to_plot = []

    # Parcourir les différents types de tirs et stocker les données correspondantes
    for label, outcomes in shot_outcomes.items():
        data = shots[shots["shot_outcome"].isin(outcomes)]
        if not data.empty:
            location = shots[shots["shot_outcome"].isin(outcomes)]['location'].tolist()
            end_location = shots[shots["shot_outcome"].isin(outcomes)]['shot_end_location'].tolist()
            x1 = pd.Series([el[0] for el in location])
            y1 = pd.Series([el[1] for el in location])
            x2 = pd.Series([el[0] for el in end_location])
            y2 = pd.Series([el[1] for el in end_location])
            color = '#F39C12' if label == 'Blocked' else '#3CD74A' if label == 'Goal' else '#F4D03F' if label == 'On target' else '#F31515'
            series_to_plot.append((x1, y1, x2, y2, color, label))

    # Calculer la somme des expected goals (xG) pour chaque tir
    total_xG = shots['shot_statsbomb_xg'].sum()
    total_goals = len(shots[shots['shot_outcome'] == 'Goal'])
    # Calculer la différence entre le nombre de buts marqués et la somme des expected goals
    goal_difference = total_goals - total_xG

    col1, col2 = st.columns(2)
    col1.metric("Goals", total_goals) 
    col2.metric("Expected goals (xG)", round(total_xG, 2), round(goal_difference, 2))
    
    # Setup the pitch
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#FFFFFF', line_color='#000000')
    fig, ax = pitch.draw(figsize=(12, 8))
    
    # Parcourir la liste et tracer les flèches pour chaque type de tir
    for x1, y1, x2, y2, color, label in series_to_plot:
        pitch.arrows(x1, y1, x2, y2, width=2, headwidth=6, headlength=6, color=color, ax=ax, label=label)

    # Setup the legend
    ax.legend(facecolor='#D4DADC', handlelength=5, edgecolor='None', fontsize=14, loc='best')
   
    return fig, ax 

# Get plot function based on selected activity
if menu_activity == 'Passes':
    fig, ax = passes_map(player=menu_player, df=df_events)
elif menu_activity == "Heatmap":
    fig, ax = heatmap(player=menu_player, df=df_events)
elif menu_activity == "Shots":
    fig, ax = shots_map(player=menu_player, df=df_events)
    
st.pyplot(fig)

# Sauvegarder le graphique au format PNG
buffer = BytesIO()
fig.savefig(buffer, format="png")
buffer.seek(0)

# Afficher une boîte de dialogue pour télécharger le fichier PNG
st.download_button(
    label="Export as PNG",
    data=buffer,
    file_name="soccer_plot.png",
    mime="image/png",
)

    # st.success(f"Graphique exporté avec succès en tant que {filename}")

# st.markdown("""
#     <span title="Message à afficher dans la popup">&#9888;</span>
# """, unsafe_allow_html=True)