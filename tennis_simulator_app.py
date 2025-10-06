import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO

# App config
st.set_page_config(layout="wide", page_title="Monte Carlo Tennis EV Simulator")

# Load dataset from GitHub (to bypass Streamlit file limits)
DATA_URL = "https://raw.githubusercontent.com/antonysamios-source/Monte7/main/player_surface_stats_master.csv"
@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL)

stats_df = load_data()

# Style tweaks
st.markdown("<style>div.block-container{padding-top:1rem}</style>", unsafe_allow_html=True)
st.markdown("### 🎾 Monte Carlo Tennis Trading Simulator")

# Scoreboard-style inputs
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        match_format = st.radio("Match Format", [3, 5], horizontal=True)
        surface = st.radio("Surface", ["Hard", "Clay", "Grass"], horizontal=True)
        tour = st.radio("Tour", ["ATP", "WTA"], horizontal=True)
    with col2:
        player_a = st.selectbox("Player A", sorted(stats_df['player'].unique()), key="a")
        sets_a = st.number_input("Sets Won", min_value=0, max_value=match_format, value=0, key="sets_a")
        games_a = st.number_input("Games in Current Set", min_value=0, max_value=7, value=0, key="games_a")
        points_a = st.number_input("Points", min_value=0, max_value=4, value=0, key="points_a")
    with col3:
        player_b = st.selectbox("Player B", sorted(stats_df['player'].unique()), key="b")
        sets_b = st.number_input("Sets Won", min_value=0, max_value=match_format, value=0, key="sets_b")
        games_b = st.number_input("Games in Current Set", min_value=0, max_value=7, value=0, key="games_b")
        points_b = st.number_input("Points", min_value=0, max_value=4, value=0, key="points_b")
    with col4:
        server = st.radio("Who is Serving?", [player_a, player_b])
        bankroll = st.number_input("Bankroll (£)", value=1000.00, step=10.0)
        odds_a = st.number_input(f"Betfair Odds {player_a}", value=2.0, step=0.01, key="odds_a")
        odds_b = st.number_input(f"Betfair Odds {player_b}", value=2.0, step=0.01, key="odds_b")
        commission = st.slider("Betfair Commission (%)", 0.0, 10.0, 5.0, step=0.1)
        toggle_kelly = st.radio("Staking Strategy", ["Kelly", "Half Kelly"])
        toggle_pressure = st.checkbox("Enable Pressure Logic", value=True)

# Get player serve/return stats based on surface
def get_player_stats(player_name):
    row = stats_df[(stats_df["player"] == player_name) & (stats_df["surface"] == surface)]
    if row.empty:
        st.error(f"No data found for {player_name} on {surface}")
        return 0.6, 0.4  # defaults
    return float(row['serve_win'].values[0]), float(row['return_win'].values[0])

sa_serve, sa_return = get_player_stats(player_a)
sb_serve, sb_return = get_player_stats(player_b)

# Adjust for pressure points
def is_pressure_point(points_a, points_b):
    return (points_a >= 3 or points_b >= 3) and abs(points_a - points_b) <= 1

pressure = is_pressure_point(points_a, points_b)
pressure_multiplier = 1.15 if pressure and toggle_pressure else 1.0

# Monte Carlo Simulation
def monte_carlo_sim(serve_a, serve_b, pressure_mult=1.0, n=100000):
    wins_a = 0
    for _ in range(n):
        pa = serve_a * pressure_mult
        pb = serve_b
        if np.random.rand() < pa / (pa + pb):
            wins_a += 1
    return wins_a / n

sim_prob_a = monte_carlo_sim(sa_serve, sb_serve, pressure_multiplier)
implied_prob_a = 1 / odds_a if odds_a > 0 else 0
edge_a = sim_prob_a - implied_prob_a

# Betting logic
min_stake = 2.0
kelly_fraction = 1.0 if toggle_kelly == "Kelly" else 0.5

def kelly_bet(prob, odds, bankroll):
    b = odds - 1
    q = 1 - prob
    f = (b * prob - q) / b
    stake = max(f * bankroll * kelly_fraction, 0)
    return stake if stake >= min_stake else 0.0

stake_a = kelly_bet(sim_prob_a, odds_a, bankroll)

# Show results
colx, coly = st.columns(2)
with colx:
    st.metric(label=f"📊 Simulated Win % for {player_a}", value=f"{sim_prob_a:.2%}")
    st.metric(label="Implied Probability (Market)", value=f"{implied_prob_a:.2%}")
    st.metric(label="Edge", value=f"{edge_a:.2%}")
with coly:
    if stake_a > 0:
        st.success(f"✅ Back {player_a} — Stake: £{stake_a:.2f}")
    else:
        st.warning("No value bet found based on Kelly/£2 min stake.")

# Visual
fig, ax = plt.subplots(figsize=(4, 1))
sns.barplot(x=[player_a, "Market"], y=[sim_prob_a, implied_prob_a], ax=ax)
ax.set_ylim(0, 1)
st.pyplot(fig)