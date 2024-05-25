# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 11:39:54 2022

@author: alexa
"""

import time
import streamlit as st
from statsbombpy import sb
from io import BytesIO
from helpers import passes_map, heatmap, shots_map, check_required_columns, try_read_json

# Set page config
st.set_page_config(page_title='Football Data Analysis', page_icon=':soccer:', initial_sidebar_state='expanded')

# Drop-down menu 1
st.sidebar.markdown('## Match Selection')

# Colonnes nécessaires définies pour les différentes analyses
required_columns = ['team', 'player', 'location', 
                    'pass_end_location', 'type', 'pass_outcome', 
                    'shot_outcome', 'shot_end_location', 'shot_statsbomb_xg']

# File upload
uploaded_file = st.sidebar.file_uploader("Upload your own data", type='json')
if uploaded_file is not None:
    df_uploaded = try_read_json(uploaded_file)

    if df_uploaded is not None:
        # Vérification des colonnes
        is_valid, missing_info = check_required_columns(df_uploaded, required_columns)

        if not is_valid:
            st.error(f"Data Error: {missing_info}")
            st.stop()  # Stop further execution if columns are missing
        else:
            # Extraction des équipes et joueurs
            teams_uploaded = df_uploaded['team'].dropna().unique()
            players_uploaded = df_uploaded[df_uploaded['team'] == teams_uploaded[0]]['player'].dropna().unique()

            # Choix de l'équipe et du joueur
            menu_team_uploaded = st.sidebar.selectbox('Select a Team', teams_uploaded)
            menu_player_uploaded = st.sidebar.selectbox('Select a Player', df_uploaded[df_uploaded['team'] == menu_team_uploaded]['player'].dropna().unique())

            # Données spécifiques pour les graphiques
            activities_uploaded = ['Passes', 'Shots', 'Heatmap']
            menu_activity = st.sidebar.selectbox('Select a Statistic', activities_uploaded)
            df_events = df_uploaded
            menu_team = menu_team_uploaded
            menu_player = menu_player_uploaded
            menu_game = "Uploaded Data" 

else: 
    # List of games and JSON files as dictionary
    games_dict = {
        'Barcelona - Huesca 4:1 (Round 27)': '3773369',
        'Barcelona - Real Madrid 1:3 (Round 7)': '3773585'
    }

    games_list = list(games_dict.keys())
    games_id_list = list(games_dict.values())

    menu_game = st.sidebar.selectbox('Or use our samples data', games_list, index=0)

    # Get Statsbomb events data based on selected game
    df_events = sb.events(match_id=games_dict.get(menu_game))
    df_events.to_json("df_test.json")

    # Get teams and players names
    team_1 = df_events['team'].unique()[0]
    team_2 = df_events['team'].unique()[1]
    mask_1 = df_events.loc[df_events['team'] == team_1]
    mask_2 = df_events.loc[df_events['team'] == team_2]
    player_names_1 = mask_1['player'].dropna().unique()
    player_names_2 = mask_2['player'].dropna().unique()

    # List of activities for drop-down menus
    activities = ['Passes', 'Shots', 'Heatmap']

    # Drop-down menu 2
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
st.write("""* Events data have been labelled by StastBomb according to the following [specification](https://github.com/statsbomb/statsbombpy/blob/master/doc/Open%20Data%20Events%20v4.0.0.pdf).""")
st.write("""* Use the dropdown-menus on the left sidebar to select a football match, a player, and a statistic to plot.""")
st.divider()
if menu_activity != "Heatmap":
    st.write('###', menu_activity, 'Map')
else:
    st.write('###', menu_activity)
if menu_game != "Uploaded Data": 
    st.write('###### Match:', menu_game)
st.write('###### Player:', menu_player, '(', menu_team ,')') 

# Get plot function based on selected activity
if menu_activity == 'Passes':
    if menu_game != "Uploaded Data": 
        fig, ax = passes_map(player=menu_player, df=df_events, team=menu_team, match=menu_game)
    else:
        fig, ax = passes_map(player=menu_player, df=df_events, team=menu_team)
elif menu_activity == "Heatmap":
    if menu_game != "Uploaded Data": 
        fig, ax = heatmap(player=menu_player, df=df_events, team=menu_team, match=menu_game)
    else:
        fig, ax = heatmap(player=menu_player, df=df_events, team=menu_team)
elif menu_activity == "Shots":
    if menu_game != "Uploaded Data":
        fig, ax = shots_map(player=menu_player, df=df_events, team=menu_team, match=menu_game)
    else:
        fig, ax = shots_map(player=menu_player, df=df_events, team=menu_team)
    
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