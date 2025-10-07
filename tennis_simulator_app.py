import streamlit as st
import pandas as pd
import numpy as np
import random

# --- CONFIG ---
st.set_page_config(layout="wide")
st.title("🎾 Monte Carlo Tennis Match Simulator (Monte7)")

# --- Load Player Stats ---
@st.cache_data
def load_stats():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte7/main/player_surface_stats_master.csv"
    df = pd.read_csv(url)
    return df

stats_df = load_stats()

# --- Match Settings ---
col1, col2 = st.columns(2)
with col1:
    match_format = st.radio("Match Format", [3, 5], index=0)
    surface = st.selectbox("Surface", ["Hard", "Clay", "Grass"], index=0)
    tour = st.radio("Tour", ["ATP", "WTA"], index=0)

# --- Select Players ---
players = sorted(stats_df['player'].unique())
player_a = st.selectbox("Select Player A", players, key="player_a")
player_b = st.selectbox("Select Player B", players, key="player_b")

# --- Scoreboard Input ---
st.markdown("### 🟩 Live Scoreboard")
score_col1, score_col2 = st.columns(2)
with score_col1:
    sets_a = st.number_input("Sets Won (A)", min_value=0, max_value=match_format, value=0, key="sets_a")
    games_a = st.number_input("Games in Current Set (A)", min_value=0, max_value=7, value=0, key="games_a")
    points_a = st.number_input("Points (A)", min_value=0, max_value=4, value=0, key="points_a")
with score_col2:
    sets_b = st.number_input("Sets Won (B)", min_value=0, max_value=match_format, value=0, key="sets_b")
    games_b = st.number_input("Games in Current Set (B)", min_value=0, max_value=7, value=0, key="games_b")
    points_b = st.number_input("Points (B)", min_value=0, max_value=4, value=0, key="points_b")

# --- Odds and Bankroll Input ---
st.markdown("### 💰 Odds & Betting Setup")
col3, col4, col5 = st.columns(3)
with col3:
    odds_a = st.number_input(f"Back Odds for {player_a}", value=2.0, step=0.01)
    lay_odds_a = st.number_input(f"Lay Odds for {player_a}", value=2.2, step=0.01)
with col4:
    odds_b = st.number_input(f"Back Odds for {player_b}", value=2.0, step=0.01)
    lay_odds_b = st.number_input(f"Lay Odds for {player_b}", value=2.2, step=0.01)
with col5:
    bankroll = st.number_input("Bankroll (£)", value=1000.0, step=10.0)
    kelly_toggle = st.selectbox("Stake Mode", ["Full Kelly", "Half Kelly"], index=1)

# --- Get Stats for Simulation ---
def get_player_stats(player_name):
    row = stats_df[stats_df["player"] == player_name]
    serve_win = row[f"{surface.lower()}_serve_win"].values[0]
    return_win = row[f"{surface.lower()}_return_win"].values[0]
    return serve_win, return_win

sa_serve, sa_return = get_player_stats(player_a)
sb_serve, sb_return = get_player_stats(player_b)

# --- Pressure Multiplier ---
def get_pressure_multiplier(sets_a, sets_b, games_a, games_b, points_a, points_b):
    # Example logic
    if abs(sets_a - sets_b) == match_format - 1 and abs(games_a - games_b) >= 5:
        return 1.25  # match point scenario
    elif abs(games_a - games_b) >= 3:
        return 1.15  # break point
    else:
        return 1.0

# --- Monte Carlo Simulation ---
def monte_carlo_sim(serve_win_a, serve_win_b, n=100000):
    wins_a = 0
    for _ in range(n):
        p1, p2 = sets_a, sets_b
        while p1 < match_format and p2 < match_format:
            # Simplified: Each set is best-of-7 games
            g1 = g2 = 0
            while g1 < 6 and g2 < 6:
                if random.random() < serve_win_a:
                    g1 += 1
                else:
                    g2 += 1
            if g1 > g2:
                p1 += 1
            else:
                p2 += 1
        if p1 > p2:
            wins_a += 1
    return wins_a / n

# --- Calculate Implied Probability & EV ---
pressure_mult = get_pressure_multiplier(sets_a, sets_b, games_a, games_b, points_a, points_b)
adjusted_serve = sa_serve * pressure_mult
adjusted_return = sa_return * pressure_mult

sim_prob = monte_carlo_sim(adjusted_serve, sb_serve)
implied_odds = 1 / sim_prob if sim_prob > 0 else float('inf')
edge_a = (1 / odds_a) - (1 / implied_odds)
edge_b = (1 / odds_b) - (1 / (1 - sim_prob))

# --- Betting Logic ---
def calc_kelly(edge, odds, bankroll):
    if edge <= 0:
        return 0
    kelly = ((odds - 1) * edge) / (odds - 1)
    kelly_stake = bankroll * kelly
    return max(2, round(kelly_stake, 2))  # Enforce £2 min

stake_a = calc_kelly(edge_a, odds_a, bankroll) if kelly_toggle == "Full Kelly" else calc_kelly(edge_a, odds_a, bankroll) / 2
stake_b = calc_kelly(edge_b, odds_b, bankroll) if kelly_toggle == "Full Kelly" else calc_kelly(edge_b, odds_b, bankroll) / 2

# --- Display Results ---
st.markdown("### 📊 Simulation Output")
col6, col7 = st.columns(2)
with col6:
    st.metric("Match Win % (A)", f"{sim_prob*100:.2f}%")
    st.metric("Implied Odds (A)", f"{implied_odds:.2f}")
    st.metric("Edge vs Back Odds (A)", f"{edge_a*100:.2f}%")
    st.metric("Suggested Stake (A)", f"£{stake_a:.2f}")
with col7:
    st.metric("Match Win % (B)", f"{(1-sim_prob)*100:.2f}%")
    st.metric("Implied Odds (B)", f"{1/(1-sim_prob):.2f}")
    st.metric("Edge vs Back Odds (B)", f"{edge_b*100:.2f}%")
    st.metric("Suggested Stake (B)", f"£{stake_b:.2f}")

st.success("✅ Simulation complete — trade decisions based on positive EV are now visible.")

