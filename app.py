import streamlit as st
import chess
import chess.svg
import chess.engine
import cairosvg
import shutil
import os
import io
import threading
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Chess Trainer", page_icon="♞", layout="wide")

ANALYSIS_TIME = 0.6
REPLY_TIME = 1.2
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


@st.cache_resource
def get_engine():
    return chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)


@st.cache_resource
def get_engine_lock():
    return threading.Lock()


OPENINGS = [
    {"name": "Ruy Lopez (Espagnole)", "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"]},
    {"name": "Ruy Lopez : Defense Berlinoise", "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6"]},
    {"name": "Partie Italienne", "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]},
    {"name": "Giuoco Piano", "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"]},
    {"name": "Partie Ecossaise", "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "d2d4"]},
    {"name": "Defense Petrov", "moves": ["e2e4", "e7e5", "g1f3", "g8f6"]},
    {"name": "Defense Philidor", "moves": ["e2e4", "e7e5", "g1f3", "d7d6"]},
    {"name": "Partie des Quatre Cavaliers", "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "b1c3", "g8f6"]},
    {"name": "Partie du Centre", "moves": ["e2e4", "e7e5", "d2d4"]},
    {"name": "Partie Viennoise", "moves": ["e2e4", "e7e5", "b1c3"]},
    {"name": "Gambit Roi", "moves": ["e2e4", "e7e5", "f2f4"]},
    {"name": "Gambit Roi accepte", "moves": ["e2e4", "e7e5", "f2f4", "e5f4"]},
    {"name": "Defense Sicilienne", "moves": ["e2e4", "c7c5"]},
    {"name": "Sicilienne Najdorf", "moves": ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"]},
    {"name": "Sicilienne Dragon", "moves": ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "g7g6"]},
    {"name": "Sicilienne Sveshnikov", "moves": ["e2e4", "c7c5", "g1f3", "b8c6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "e7e5"]},
    {"name": "Defense Francaise", "moves": ["e2e4", "e7e6"]},
    {"name": "Defense Caro-Kann", "moves": ["e2e4", "c7c6"]},
    {"name": "Defense Pirc", "moves": ["e2e4", "d7d6"]},
    {"name": "Defense Scandinave", "moves": ["e2e4", "d7d5"]},
    {"name": "Defense Alekhine", "moves": ["e2e4", "g8f6"]},
    {"name": "Gambit Dame", "moves": ["d2d4", "d7d5", "c2c4"]},
    {"name": "Gambit Dame refuse", "moves": ["d2d4", "d7d5", "c2c4", "e7e6"]},
    {"name": "Gambit Dame accepte", "moves": ["d2d4", "d7d5", "c2c4", "d5c4"]},
    {"name": "Defense Slave", "moves": ["d2d4", "d7d5", "c2c4", "c7c6"]},
    {"name": "Defense Est-Indienne", "moves": ["d2d4", "g8f6", "c2c4", "g7g6"]},
    {"name": "Defense Grunfeld", "moves": ["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d5"]},
    {"name": "Defense Nimzo-Indienne", "moves": ["d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4"]},
    {"name": "Defense Ouest-Indienne", "moves": ["d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "b7b6"]},
    {"name": "Defense Bogo-Indienne", "moves": ["d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "f8b4"]},
    {"name": "Ouverture Catalane", "moves": ["d2d4", "g8f6", "c2c4", "e7e6", "g2g3"]},
    {"name": "Defense Benoni", "moves": ["d2d4", "g8f6", "c2c4", "c7c5"]},
    {"name": "Defense Hollandaise", "moves": ["d2d4", "f7f5"]},
    {"name": "Systeme Londres", "moves": ["d2d4", "d7d5", "g1f3", "g8f6", "c1f4"]},
    {"name": "Systeme Colle", "moves": ["d2d4", "d7d5", "g1f3", "g8f6", "e2e3"]},
    {"name": "Attaque Trompowsky", "moves": ["d2d4", "g8f6", "c1g5"]},
    {"name": "Ouverture Anglaise", "moves": ["c2c4"]},
    {"name": "Ouverture Reti", "moves": ["g1f3", "d7d5", "c2c4"]},
    {"name": "Ouverture Bird", "moves": ["f2f4"]},
]


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
    .opening-current {
        background-color: #1c1f26;
        border: 1px solid #d4a017;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

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
        "Stockfish n'a pas ete trouve sur le serveur. "
        "Verifie que le fichier packages.txt contient bien 'stockfish'."
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


PIECE_NAMES_FR = {
    chess.PAWN: "un pion",
    chess.KNIGHT: "un cavalier",
    chess.BISHOP: "un fou",
    chess.ROOK: "une tour",
    chess.QUEEN: "une dame",
    chess.KING: "le roi",
}

CENTER_SQUARES = {chess.D4, chess.E4, chess.D5, chess.E5}


def explain_move(pre_move_board, move):
    reasons = []

    if pre_move_board.is_castling(move):
        reasons.append("met le roi a l'abri en roquant")

    if pre_move_board.is_capture(move):
        captured = pre_move_board.piece_at(move.to_square)
        if captured:
            reasons.append(f"capture {PIECE_NAMES_FR.get(captured.piece_type, 'une piece')} adverse")
        else:
            reasons.append("capture un pion en passant")

    test_board = pre_move_board.copy()
    test_board.push(move)
    if test_board.is_check():
        reasons.append("met le roi adverse en echec")

    piece = pre_move_board.piece_at(move.from_square)
    back_rank = 0 if pre_move_board.turn == chess.WHITE else 7
    if (piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP)
            and chess.square_rank(move.from_square) == back_rank):
        reasons.append("developpe une piece")

    if move.to_square in CENTER_SQUARES:
        reasons.append("prend le controle du centre")

    if pre_move_board.is_attacked_by(not pre_move_board.turn, move.from_square):
        reasons.append("echappe a une piece qui l'attaquait")

    if not reasons:
        reasons.append("ameliore la position selon l'evaluation du moteur")

    return ", ".join(reasons).capitalize()


def process_human_move(move):
    move_number = board.fullmove_number
    side_played = "Blancs" if board.turn == chess.WHITE else "Noirs"

    engine = get_engine()
    lock = get_engine_lock()

    with lock:
        info = engine.analyse(board, chess.engine.Limit(time=ANALYSIS_TIME))
        best_move = info["pv"][0]
        best_san = board.san(best_move)
        eval_score = info["score"].white()
