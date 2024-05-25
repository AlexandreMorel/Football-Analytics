import streamlit as st
from mplsoccer import Pitch
import matplotlib.pyplot as plt
import pandas as pd
from scipy.ndimage import gaussian_filter

def passes_map(player, df, team, match=None):
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
    fig, axs = pitch.grid(endnote_height=0.03, endnote_space=0, figheight=12,
                      title_height=0.06, title_space=0, grid_height=0.86,
                      # Turn off the endnote/title axis. I usually do this after
                      # I am happy with the chart layout and text placement
                      axis=False)

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

            pitch.arrows(x1, y1, x2, y2, width=2, headwidth=6, headlength=6, color=color, ax=axs['pitch'], label=label)

    # Calcul du pourcentage de passes vers l'avant
    total_forward_passes = forward_passes_completed + forward_passes_missed
    percentage_forward_passes = round((total_forward_passes / (total_completed_passes + total_missed_passes)) * 100)

    percentage_completed_forward_passes = round(forward_passes_completed / total_forward_passes * 100)
 
    col1, col2, col3 = st.columns(3)
    col1.metric("Completed passes", f"{total_completed_passes}/{total_completed_passes + total_missed_passes} ({percentage_completed_passes}%)")
    col2.metric("Completed forward passes", f"{forward_passes_completed}/{total_forward_passes} ({percentage_completed_forward_passes}%)")
    col3.metric("Forward play", f"{percentage_forward_passes}%")

    # Setup the legend
    axs['pitch'].legend(facecolor='#D4DADC', handlelength=5, edgecolor='None', fontsize=16, loc='upper left')

    # endnote and title
    axs['endnote'].text(1, 0.5, '@alex.mrl38', va='center', ha='right', fontsize=20, color='#000000')
    TITLE_TEXT = f'Passes of {player} ({team})'
    axs['title'].text(0.5, 0.7, TITLE_TEXT, color='#000000',
                    va='center', ha='center', fontsize=25)
    axs['title'].text(0.5, 0.25, match, color='#000000',
                    va='center', ha='center', fontsize=18)
    
    return fig, axs

def heatmap(player, df, team, match=None):

    # Filtrer les données du joueur spécifié
    df_heatmap = df.loc[df['player'] == player]

    # Récupérer les coordonnées des emplacements non nuls
    location = df_heatmap["location"].dropna().tolist()
    x = pd.Series([el[0] for el in location])
    y = pd.Series([el[1] for el in location])

    # Setup pitch
    pitch = Pitch(pitch_type='statsbomb', line_zorder=2, pitch_color='#22312b', line_color='#efefef')

    # Pitch with title
    fig, axs = pitch.grid(figheight=10, title_height=0.08, endnote_space=0,
                      grid_width=0.88, left=0.025, title_space=0,
                      axis=False, grid_height=0.82, endnote_height=0.05)
    
    fig.set_facecolor('#22312b')

    # Générer la heatmap
    bin_statistic = pitch.bin_statistic(x, y, statistic='count', bins=(25, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=axs['pitch'], cmap='hot', edgecolors='#22312b')  # YlOrRd

    # Ajouter la barre de couleur et formater en blanc cassé
    ax_cbar = fig.add_axes((0.915, 0.093, 0.03, 0.786))
    cbar = plt.colorbar(pcm, cax=ax_cbar)
    cbar.outline.set_edgecolor('#efefef')
    cbar.ax.yaxis.set_tick_params(color='#efefef')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#efefef')

    # endnote /title
    axs['endnote'].text(1, 0.5, '@alex.mrl38', color='#ffffff',
                        va='center', ha='right', fontsize=15)
    TITLE_TEXT = f'Heatmap of {player} ({team})'
    axs['title'].text(0.5, 0.7, TITLE_TEXT, color='#ffffff',
                    va='center', ha='center', fontsize=25)
    axs['title'].text(0.5, 0.25, match, color='#ffffff',
                    va='center', ha='center', fontsize=18)

    return fig, axs

def shots_map(player, df, team, match=None):
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
    fig, axs = pitch.grid(endnote_height=0.03, endnote_space=0, figheight=12,
                      title_height=0.06, title_space=0, grid_height=0.86,
                      # Turn off the endnote/title axis. I usually do this after
                      # I am happy with the chart layout and text placement
                      axis=False)
    
    # Parcourir la liste et tracer les flèches pour chaque type de tir
    for x1, y1, x2, y2, color, label in series_to_plot:
        pitch.arrows(x1, y1, x2, y2, width=2, headwidth=6, headlength=6, color=color, ax=axs['pitch'], label=label)

    # Setup the legend
    axs['pitch'].legend(facecolor='#D4DADC', handlelength=5, edgecolor='None', fontsize=16, loc='upper left')

    # endnote and title
    axs['endnote'].text(1, 0.5, '@alex.mrl38', va='center', ha='right', fontsize=20, color='#000000')
    TITLE_TEXT = f'Shots of {player} ({team})'
    axs['title'].text(0.5, 0.7, TITLE_TEXT, color='#000000',
                    va='center', ha='center', fontsize=25)
    axs['title'].text(0.5, 0.25, match, color='#000000',
                    va='center', ha='center', fontsize=18)
    
    return fig, axs

# Fonction pour vérifier les colonnes requises
def check_required_columns(df, required_cols):
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, missing_detail(missing_cols)
    return True, None

# Fonction pour détailler les colonnes manquantes
def missing_detail(cols):
    return f"Missing columns: {', '.join(cols)}"

def try_read_json(uploaded_file):
    """ Tente de lire un fichier JSON et gère les erreurs potentielles. """
    try:
        df = pd.read_json(uploaded_file)
        return df
    except ValueError as e:
        # Gestion d'erreurs spécifiques à la lecture JSON, e.g., données malformées
        st.error(f"Failed to read JSON file. The file format might be incorrect. Error: {e}")
        st.stop()  # Stop further execution if columns are missing
    except Exception as e:
        # Gestion de toute autre exception non prévue
        st.error(f"An unexpected error occurred: {e}")
        st.stop()  # Stop further execution if columns are missing