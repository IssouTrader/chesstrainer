import streamlit as st
import chess
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

# --- Symboles unicode des pièces ---
PIECE_UNICODE = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}

# --- Initialisation de l'état ---
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "selected_square" not in st.session_state:
    st.session_state.selected_square = None

board = st.session_state.board

st.title("♞ Chess Trainer")

if STOCKFISH_PATH is None:
    st.error(
        "Stockfish n'a pas été trouvé sur le serveur. "
        "Vérifie que le fichier packages.txt contient bien 'stockfish'."
    )
    st.stop()

# --- Statut de la partie ---
if board.is_checkmate():
    st.success("Échec et mat !")
elif board.is_stalemate():
    st.info("Pat (match nul).")
elif board.is_check():
    st.warning("Échec !")

st.caption("Clique sur une pièce, puis sur la case où tu veux la déplacer.")


def square_label(square):
    """Retourne le texte affiché sur le bouton d'une case."""
    piece = board.piece_at(square)
    piece_str = PIECE_UNICODE.get(piece.symbol(), " ") if piece else " "

    is_selected = st.session_state.selected_square == square
    is_legal_target = False
    if st.session_state.selected_square is not None:
        move = chess.Move(st.session_state.selected_square, square)
        if move in board.legal_moves or _with_queen_promotion(move) in board.legal_moves:
            is_legal_target = True

    if is_selected:
        return f"🔵{piece_str}"
    if is_legal_target:
        return f"·{piece_str}·" if piece else "•"
    return piece_str


def _with_queen_promotion(move):
    return chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)


def handle_click(square):
    selected = st.session_state.selected_square
    clicked_piece = board.piece_at(square)

    if selected is None:
        if clicked_piece and clicked_piece.color == board.turn:
            st.session_state.selected_square = square
        return

    if square == selected:
        st.session_state.selected_square = None
        return

    move = chess.Move(selected, square)
    promo_move = _with_queen_promotion(move)

    if move in board.legal_moves:
        board.push(move)
        st.session_state.selected_square = None
        play_stockfish_reply()
        return
    elif promo_move in board.legal_moves:
        board.push(promo_move)
        st.session_state.selected_square = None
        play_stockfish_reply()
        return

    if clicked_piece and clicked_piece.color == board.turn:
        st.session_state.selected_square = square
    else:
        st.session_state.selected_square = None


def play_stockfish_reply():
    if board.is_game_over():
        return
    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        result = engine.play(board, chess.engine.Limit(time=2.0))
        board.push(result.move)


# --- Affichage de l'échiquier (rangée 8 en haut, rangée 1 en bas) ---
for rank in range(7, -1, -1):
    cols = st.columns(8)
    for file in range(8):
        square = chess.square(file, rank)
        with cols[file]:
            if st.button(square_label(square), key=f"sq_{square}", use_container_width=True):
                handle_click(square)
                st.rerun()

# --- Nouvelle partie ---
if st.button("Nouvelle partie"):
    st.session_state.board = chess.Board()
    st.session_state.selected_square = None
    st.rerun()
