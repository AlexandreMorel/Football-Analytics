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

# List of games and JSON files as dictionary
games_dict = {
    'Barcelona - Huesca 4:1 (Round 27)': '3773369',
    'Barcelona - Real Madrid 1:3 (Round 7)': '3773585'
}

games_list = list(games_dict.keys())
games_id_list = list(games_dict.values())


# Set page config
st.set_page_config(page_title='Football Data Game', page_icon=':soccer:', initial_sidebar_state='expanded')

# Drop-down menu "Select Football Game"
st.sidebar.markdown('## Select Football Game')
menu_game = st.sidebar.selectbox('Select Game', games_list, index=0)

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
activities = ['Pass', 'Events Location', 'Ball Receipt', 'Carry', 'Pressure', 'Shot']


# Drop-down menus 'Select Team, Player and Activity'
st.sidebar.markdown('## Select Player and Activity')
menu_team = st.sidebar.selectbox('Select Team', (team_1, team_2))
if menu_team == team_1:
    menu_player = st.sidebar.selectbox('Select Player', player_names_1)
else:
    menu_player = st.sidebar.selectbox('Select Player', player_names_2)
menu_activity = st.sidebar.selectbox('Select Activity', activities)
st.sidebar.markdown('Select a player and activity. Statistics plot will appear on the pitch.')

# Titles and text above the pitch
st.title('Football Game Stats')
st.markdown("""
The knockout phase of UEFA Euro 2020 took place between 26 June 2021 and 11 July 2021. It consisted of 
15 matches between 16 teams successfully qualified from the group stage. In the final game in London Italy 
won England on penalty kicks and took the trophy second time in their history.
""")
st.write("""* Use dropdown-menus on the left side to select a game, team, player, and activity. 
Statistics plot will appear on the pitch below.""")
st.write('###', menu_activity, 'Map')
st.write('###### Game:', menu_game)
st.write('###### Player:', menu_player, '(', menu_team ,')')

def pass_map():
    df_pass = df_events.loc[(df_events['player'] == menu_player) & (df_events['type'] == 'Pass')]
    mask_complete = df_pass.pass_outcome.isnull()
    # Completed passes
    location = df_pass[mask_complete]['location'].tolist()
    pass_end_location = df_pass[mask_complete]['pass_end_location'].tolist()
    x1_completed = pd.Series([el[0] for el in location])
    y1_completed = pd.Series([el[1] for el in location])
    x2_completed = pd.Series([el[0] for el in pass_end_location])
    y2_completed = pd.Series([el[1] for el in pass_end_location])
    
    # Other passes
    location2 = df_pass[~mask_complete]['location'].tolist()
    pass_end_location2 = df_pass[~mask_complete]['pass_end_location'].tolist()
    x1_not_completed = pd.Series([el[0] for el in location2])
    y1_not_completed = pd.Series([el[1] for el in location2])
    x2_not_completed = pd.Series([el[0] for el in pass_end_location2])
    y2_not_completed = pd.Series([el[1] for el in pass_end_location2])
    
    # Assists
    location_assist = df_pass[df_pass["pass_goal_assist"] == True]["location"].tolist()
    pass_end_location_assist = df_pass[df_pass["pass_goal_assist"] == True]["pass_end_location"].tolist()
    x1_assist = pd.Series([el[0] for el in location_assist])
    y1_assist = pd.Series([el[1] for el in location_assist])
    x2_assist = pd.Series([el[0] for el in pass_end_location_assist])
    y2_assist = pd.Series([el[1] for el in pass_end_location_assist])
    
    # Setup the pitch
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#FFFFFF', line_color='#000000')
    fig, ax = pitch.draw(figsize=(12, 8))
    
    # Plot the completed passes
    pitch.arrows(x1_completed, y1_completed,
                 x2_completed, y2_completed, width=2,
                 headwidth=6, headlength=6, color='#3CD74A', ax=ax, label='Completed passes')
    
    pitch.arrows(x1_assist, y1_assist,
                 x2_assist, y2_assist, width=2,
                 headwidth=6, headlength=6, color='#F4D03F', ax=ax, label='Assists')
    
    # Plot the other passes
    pitch.arrows(x1_not_completed, y1_not_completed,
                 x2_not_completed, y2_not_completed, width=2,
                 headwidth=6, headlength=6, color='#F31515', ax=ax, label='Other passes')
    
    # Setup the legend
    ax.legend(facecolor='#D4DADC', handlelength=5, edgecolor='None', fontsize=14, loc='best')
    return fig, ax

def heatmap():
    df_heatmap = df_events.loc[(df_events['player'] == menu_player)]
    location = [item for item in df_heatmap["location"].tolist() if str(item) != 'nan']
    x = pd.Series([el[0] for el in location])
    y = pd.Series([el[1] for el in location])
    
    # setup pitch
    pitch = Pitch(pitch_type='statsbomb', line_zorder=2,
                  pitch_color='#22312b', line_color='#efefef')
    # draw
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor('#22312b')
    bin_statistic = pitch.bin_statistic(x, y, statistic='count', bins=(25, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot', edgecolors='#22312b') #YlOrRd
    # Add the colorbar and format off-white
    cbar = fig.colorbar(pcm, ax=ax, shrink=0.6)
    cbar.outline.set_edgecolor('#efefef')
    cbar.ax.yaxis.set_tick_params(color='#efefef')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#efefef')
    return fig, ax
    

# Get plot function based on selected activity
if menu_activity == 'Pass':
    fig, ax = pass_map()
elif menu_activity == "Events Location":
    fig, ax = heatmap()
    
st.pyplot(fig)