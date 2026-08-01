import streamlit as st
import chess
import chess.svg
import chess.engine
import shutil
import os

st.set_page_config(page_title="Chess Trainer", page_icon="♞", layout="centered")

# --- Recherche du moteur Stockfish installé sur le serveur ---
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

# --- Initialisation de l'état du jeu ---
if "board" not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

st.title("♞ Chess Trainer")

if STOCKFISH_PATH is None:
    st.error(
        "Stockfish n'a pas été trouvé sur le serveur. "
        "Vérifie que le fichier packages.txt contient bien 'stockfish' "
        "et que le déploiement a bien réinstallé les paquets système."
    )
    st.stop()

# --- Affichage de l'échiquier ---
board_svg = chess.svg.board(board=board, size=400)
st.markdown(f'<div style="display:flex; justify-content:center;">{board_svg}</div>', unsafe_allow_html=True)

# --- Statut de la partie ---
if board.is_checkmate():
    st.success("Échec et mat !")
elif board.is_stalemate():
    st.info("Pat (match nul).")
elif board.is_check():
    st.warning("Échec !")

# --- Choix et jeu du coup ---
if not board.is_game_over():
    legal_moves = list(board.legal_moves)
    move_labels = [board.san(m) for m in legal_moves]
    move_map = dict(zip(move_labels, legal_moves))

    chosen_label = st.selectbox("Choisis ton coup :", sorted(move_labels))

    if st.button("Jouer ce coup"):
        move = move_map[chosen_label]
        board.push(move)
        st.session_state.board = board

        # Réponse de Stockfish si la partie n'est pas terminée
        if not board.is_game_over():
            with st.spinner("Stockfish réfléchit..."):
                with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                    result = engine.play(board, chess.engine.Limit(time=1.0))
                    board.push(result.move)
                    st.session_state.board = board

        st.rerun()

# --- Nouvelle partie ---
if st.button("Nouvelle partie"):
    st.session_state.board = chess.Board()
    st.rerun()
