
    import streamlit as st
    import pandas as pd
    import numpy as np
    import random

    st.set_page_config(layout="wide")

    # Load player stats
    @st.cache_data
    def load_data():
        return pd.read_csv("player_surface_stats_master.csv")

    df = load_data()

    # --- Layout styling ---
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .css-1y0tads {
            gap: 0.25rem !important;
        }
        .stNumberInput input {
            height: 1.2em;
            font-size: 12px;
            padding: 0.2em;
        }
        .stSelectbox > div {
            font-size: 12px !important;
        }
        .stSlider {
            padding: 0px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🎾 Monte Carlo Tennis Match Simulator (Monte7)")

    # Match configuration
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        match_format = st.radio("Match Format", [3, 5], horizontal=True)
    with col2:
        surface = st.selectbox("Surface", ["Hard", "Clay", "Grass"])
    with col3:
        tour = st.radio("Tour", ["ATP", "WTA"], horizontal=True)
    with col4:
        pressure_on = st.checkbox("Pressure Logic ON", value=True)

    players = df[(df["tour"] == tour) & (df["surface"] == surface)]["player"].unique()
    col5, col6 = st.columns(2)
    with col5:
        player_a = st.selectbox("Select Player A", sorted(players), key="a")
    with col6:
        player_b = st.selectbox("Select Player B", sorted(players), key="b")

    def get_stats(player):
        stats = df[(df["player"] == player) & (df["surface"] == surface)]
        return float(stats["serve_win"]), float(stats["return_win"])

    sa_serve, sa_return = get_stats(player_a)
    sb_serve, sb_return = get_stats(player_b)

    # Scoreboard
    st.markdown("### 🟩 Live Scoreboard")
    score_cols = st.columns([1, 1, 1, 1, 1, 1])
    sets_a = score_cols[0].number_input("Sets A", min_value=0, step=1, key="sa")
    games_a = score_cols[1].number_input("Games A", min_value=0, step=1, key="ga")
    points_a = score_cols[2].number_input("Points A", min_value=0, max_value=4, step=1, key="pa")
    sets_b = score_cols[3].number_input("Sets B", min_value=0, step=1, key="sb")
    games_b = score_cols[4].number_input("Games B", min_value=0, step=1, key="gb")
    points_b = score_cols[5].number_input("Points B", min_value=0, max_value=4, step=1, key="pb")

    def simulate_match(sa_s, sa_r, sb_s, sb_r, pressure, sets_a, sets_b, games_a, games_b, points_a, points_b):
        wins_a, wins_b = 0, 0
        for _ in range(100_000):
            p1_sets, p2_sets = sets_a, sets_b
            p1_games, p2_games = games_a, games_b
            p1_points, p2_points = points_a, points_b

            while p1_sets < (match_format // 2 + 1) and p2_sets < (match_format // 2 + 1):
                p1_games, p2_games = 0, 0
                while p1_games < 6 and p2_games < 6:
                    p1_points, p2_points = 0, 0
                    while True:
                        p_server = sa_s if random.random() < 0.5 else sb_s
                        if random.random() < p_server:
                            p1_points += 1
                        else:
                            p2_points += 1
                        if p1_points >= 4 and p1_points - p2_points >= 2:
                            p1_games += 1
                            break
                        if p2_points >= 4 and p2_points - p1_points >= 2:
                            p2_games += 1
                            break
                if p1_games > p2_games:
                    p1_sets += 1
                else:
                    p2_sets += 1

            if p1_sets > p2_sets:
                wins_a += 1
            else:
                wins_b += 1

        return wins_a / 100_000, wins_b / 100_000

    wp_a, wp_b = simulate_match(sa_serve, sa_return, sb_serve, sb_return, pressure_on,
                                sets_a, sets_b, games_a, games_b, points_a, points_b)

    st.markdown("### 💰 Odds & Betting Setup")
    col7, col8 = st.columns(2)
    with col7:
        odds_back_a = st.number_input(f"Back Odds for {player_a}", value=2.0, step=0.01, key="oba")
        odds_lay_a = st.number_input(f"Lay Odds for {player_a}", value=2.2, step=0.01, key="ola")
    with col8:
        odds_back_b = st.number_input(f"Back Odds for {player_b}", value=2.0, step=0.01, key="obb")
        odds_lay_b = st.number_input(f"Lay Odds for {player_b}", value=2.2, step=0.01, key="olb")

    def implied_prob(odds): return 1 / odds if odds > 0 else 0
    imp_a, imp_b = implied_prob(odds_back_a), implied_prob(odds_back_b)

    edge_a = wp_a - imp_a
    edge_b = wp_b - imp_b

    st.markdown(f"#### ✅ Win Probabilities
- {player_a}: {wp_a:.2%} | EV vs Back: {edge_a:.2%}
- {player_b}: {wp_b:.2%} | EV vs Back: {edge_b:.2%}")

