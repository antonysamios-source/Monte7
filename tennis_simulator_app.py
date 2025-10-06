import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- App Config ---
st.set_page_config(page_title="Tennis EV Simulator", layout="wide")

# --- Load Data ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte7/main/player_surface_stats_master.csv"
    return pd.read_csv(url)

stats_df = load_data()

# --- UI Layout ---
st.markdown("## 🎾 Tennis Live Match Simulator with EV and Monte Carlo")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    player_a = st.selectbox("Player A", sorted(stats_df["player"].unique()))
with col2:
    player_b = st.selectbox("Player B", sorted(stats_df["player"].unique()))
with col3:
    surface = st.selectbox("Surface", ["Hard", "Clay", "Grass"])

tour = st.radio("Tour", ["ATP", "WTA"], horizontal=True)

# --- Match State ---
scoreboard = st.container()
with scoreboard:
    st.markdown("### 🎯 Compact Match Scoreboard")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"#### {player_a}")
        sets_a = st.number_input("Sets Won", min_value=0, max_value=5, key="sets_a")
        games_a = st.number_input("Games (Current Set)", min_value=0, max_value=7, key="games_a")
        points_a = st.number_input("Points", min_value=0, max_value=4, key="points_a")

    with col_b:
        st.markdown(f"#### {player_b}")
        sets_b = st.number_input("Sets Won", min_value=0, max_value=5, key="sets_b")
        games_b = st.number_input("Games (Current Set)", min_value=0, max_value=7, key="games_b")
        points_b = st.number_input("Points", min_value=0, max_value=4, key="points_b")

    server = st.radio("Who is serving?", [player_a, player_b])

# --- Odds + Toggles ---
st.markdown("---")
st.markdown("### 💸 Odds & Simulation")

bankroll = st.number_input("Your Bankroll (£)", min_value=0.0, value=1000.0)
kelly_toggle = st.radio("Stake Strategy", ["Full Kelly", "0.5 Kelly"])
commission = st.number_input("Betfair Commission (%)", min_value=0.0, value=5.0)

col_odds1, col_odds2 = st.columns(2)
with col_odds1:
    odds_a = st.number_input(f"Back Odds for {player_a}", min_value=1.01, value=2.0, key="odds_a_input")
with col_odds2:
    odds_b = st.number_input(f"Back Odds for {player_b}", min_value=1.01, value=2.0, key="odds_b_input")

# --- Get Player Stats ---
def get_player_stats(name):
    row = stats_df[(stats_df['player'] == name) & (stats_df['surface'] == surface) & (stats_df['tour'] == tour)]
    if row.empty:
        return 0.62, 0.38  # default average
    return float(row['serve_win_pct'].values[0]), float(row['return_win_pct'].values[0])

sa_serve, sa_return = get_player_stats(player_a)
sb_serve, sb_return = get_player_stats(player_b)

# --- Pressure Point Logic ---
def is_pressure_point(points_a, points_b, games_a, games_b):
    if points_a == 3 and points_b == 3:
        return True
    if abs(games_a - games_b) == 1 and max(games_a, games_b) >= 5:
        return True
    return False

pressure = is_pressure_point(points_a, points_b, games_a, games_b)
pressure_multiplier = 1.05 if pressure else 1.0

# --- Monte Carlo Simulation ---
def simulate_win_prob(serve_pct, return_pct, n_sim=100000, pressure=1.0):
    results = np.random.binomial(1, serve_pct * pressure, size=n_sim)
    return np.mean(results)

with st.spinner("Running 100,000 Monte Carlo simulations..."):
    win_prob_a = simulate_win_prob(sa_serve, sb_return, pressure=pressure_multiplier)
    win_prob_b = 1 - win_prob_a

# --- EV + Kelly Stake Calculation ---
def kelly_stake(prob, odds, bankroll, min_bet=2.0, fraction=1.0):
    edge = (odds * prob - 1) / (odds - 1)
    stake = edge * bankroll * fraction
    return max(min_bet, stake) if stake > 0 else 0

edge_a = win_prob_a - 1 / odds_a
edge_b = win_prob_b - 1 / odds_b

st.markdown("---")
st.markdown("### 📈 Results")

col1, col2 = st.columns(2)
with col1:
    st.metric(f"{player_a} Win Prob", f"{win_prob_a:.2%}")
    st.metric(f"{player_a} Edge", f"{edge_a:.2%}")
with col2:
    st.metric(f"{player_b} Win Prob", f"{win_prob_b:.2%}")
    st.metric(f"{player_b} Edge", f"{edge_b:.2%}")

# --- Stake Logic ---
fraction = 1.0 if kelly_toggle == "Full Kelly" else 0.5
stake_a = kelly_stake(win_prob_a, odds_a, bankroll, fraction=fraction)
stake_b = kelly_stake(win_prob_b, odds_b, bankroll, fraction=fraction)

st.markdown("### 💰 Suggested Bets")
if edge_a > 0:
    st.success(f"✅ BACK {player_a} for £{stake_a:.2f} (Positive EV)")
if edge_b > 0:
    st.success(f"✅ BACK {player_b} for £{stake_b:.2f} (Positive EV)")
if edge_a <= 0 and edge_b <= 0:
    st.warning("⚠️ No Positive EV — No Bet")

# --- Final Notes ---
st.caption("Monte7 | Implied Probability Trading | Min £2 Stake | Pressure-Aware Simulation")
