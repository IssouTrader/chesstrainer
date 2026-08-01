import streamlit as st
import chess
import chess.svg
import chess.engine
import cairosvg
import shutil
import os
import io
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Chess Trainer", page_icon="♞", layout="wide")

ANALYSIS_TIME = 1.0
REPLY_TIME = 2.0
BOARD_SIZE = 480
SQUARE_SIZE = BOARD_SIZE / 8
LABEL_COLOR = "#3b2a1a"


def find_stockfish():
    candidates = [
        shutil.which("stockfish"),
        "/usr/games/stockfish",
        "/usr/bin/stockfish",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


STOCKFISH_PATH = find_stockfish()

st.markdown("""
<style>
    h1 { font-weight: 700; letter-spacing: 1px; }
    .subtitle { color: #9a9a9a; font-size: 14px; margin-top: -8px; }
    .analysis-card {
        background-color: #1c1f26;
        border: 1px solid #2e323c;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialisation de l'état ---
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "selected_square" not in st.session_state:
    st.session_state.selected_square = None
if "analysis_log" not in st.session_state:
    st.session_state.analysis_log = []
if "last_click_time" not in st.session_state:
    st.session_state.last_click_time = None

board = st.session_state.board

if STOCKFISH_PATH is None:
    st.error(
        "Stockfish n'a pas été trouvé sur le serveur. "
        "Vérifie que le fichier packages.txt contient bien 'stockfish'."
    )
    st.stop()


def format_eval(score):
    if score.is_mate():
        mate_in = score.mate()
        return f"Mat en {abs(mate_in)}" if mate_in is not None else "Mat"
    cp = score.score()
    if cp is None:
        return "?"
    return f"{cp / 100:+.2f}"


def _with_queen_promotion(move):
    return chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)
