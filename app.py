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
        reasons.append("met le roi à l'abri en roquant")

    if pre_move_board.is_capture(move):
        captured = pre_move_board.piece_at(move.to_square)
        if captured:
            reasons.append(f"capture {PIECE_NAMES_FR.get(captured.piece_type, 'une pièce')} adverse")
        else:
            reasons.append("capture un pion en passant")

    test_board = pre_move_board.copy()
    test_board.push(move)
    if test_board.is_check():
        reasons.append("met le roi adverse en échec")

    piece = pre_move_board.piece_at(move.from_square)
    back_rank = 0 if pre_move_board.turn == chess.WHITE else 7
    if (piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP)
            and chess.square_rank(move.from_square) == back_rank):
        reasons.append("développe une pièce")

    if move.to_square in CENTER_SQUARES:
        reasons.append("prend le contrôle du centre")

    if pre_move_board.is_attacked_by(not pre_move_board.turn, move.from_square):
        reasons.append("échappe à une pièce qui l'attaquait")

    if not reasons:
        reasons.append("améliore la position selon l'évaluation du moteur")

    return ", ".join(reasons).capitalize()


def process_human_move(move):
    move_number = board.fullmove_number
    side_played = "Blancs" if board.turn == chess.WHITE else "Noirs"

    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        info = engine.analyse(board, chess.engine.Limit(time=ANALYSIS_TIME))
        best_move = info["pv"][0]
        best_san = board.san(best_move)
        eval_score = info["score"].white()
        best_reason = explain_move(board, best_move)

        played_san = board.san(move)
        was_best = (move == best_move)

        board.push(move)

        st.session_state.analysis_log.insert(0, {
            "num": move_number,
            "side": side_played,
            "played": played_san,
            "best": best_san,
            "best_reason": best_reason,
            "was_best": was_best,
            "eval": format_eval(eval_score),
        })

        if not board.is_game_over():
            result = engine.play(board, chess.engine.Limit(time=REPLY_TIME))
            board.push(result.move)


def pixel_to_square(x, y):
    file = int(x // SQUARE_SIZE)
    rank = 7 - int(y // SQUARE_SIZE)
    file = max(0, min(7, file))
    rank = max(0, min(7, rank))
    return chess.square(file, rank)


def handle_square_click(square):
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
        st.session_state.selected_square = None
        process_human_move(move)
        return
    elif promo_move in board.legal_moves:
        st.session_state.selected_square = None
        process_human_move(promo_move)
        return

    if clicked_piece and clicked_piece.color == board.turn:
        st.session_state.selected_square = square
    else:
        st.session_state.selected_square = None


def add_coordinate_labels(img):
    draw = ImageDraw.Draw(img)
    files = "abcdefgh"
    sq = int(SQUARE_SIZE)

    for i, letter in enumerate(files):
        x = i * sq + 3
        y = BOARD_SIZE - 14
        draw.text((x, y), letter, fill=LABEL_COLOR)

    for rank_index in range(8):
        number = str(8 - rank_index)
        x = 3
        y = rank_index * sq + 2
        draw.text((x, y), number, fill=LABEL_COLOR)

    return img


def render_board_image():
    fill = {}
    selected = st.session_state.selected_square
    if selected is not None:
        fill[selected] = "#d4a01780"
        for move in board.legal_moves:
            if move.from_square == selected:
                fill[move.to_square] = "#4ade8080"

    svg_code = chess.svg.board(
        board=board,
        size=BOARD_SIZE,
        coordinates=False,
        fill=fill,
    )
    png_bytes = cairosvg.svg2png(bytestring=svg_code.encode("utf-8"))
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    return add_coordinate_labels(img)


left_col, right_col = st.columns([1, 2], gap="large")

with left_col:
    st.markdown("## 🎓 Trainer")
    st.markdown('<p class="subtitle">Le meilleur coup, à chaque tour</p>', unsafe_allow_html=True)

    if st.session_state.analysis_log:
        last = st.session_state.analysis_log[0]
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        if last["was_best"]:
            st.success(f"✅ Meilleur coup joué : **{last['played']}**")
            st.caption(last["best_reason"])
        else:
            st.warning(f"Toi : **{last['played']}**  \nMeilleur coup : **{last['best']}**")
            st.caption(f"Pourquoi : {last['best_reason']}")
        st.caption(f"Évaluation : {last['eval']}")
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("📜 Historique des coups"):
            for entry in st.session_state.analysis_log:
                icon = "✅" if entry["was_best"] else "🔸"
                st.write(
                    f"{icon} {entry['num']}. ({entry['side']}) "
                    f"joué: {entry['played']} — meilleur: {entry['best']} "
                    f"({entry['eval']})"
                )
                st.caption(entry["best_reason"])
    else:
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.caption("Joue un coup pour voir l'analyse apparaître ici.")
        st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown("# ♞ Chess Trainer")
    st.markdown('<p class="subtitle">Clique sur une pièce, puis sur sa case de destination</p>', unsafe_allow_html=True)

    if board.is_checkmate():
        st.success("Échec et mat !")
    elif board.is_stalemate():
        st.info("Pat (match nul).")
    elif board.is_check():
        st.warning("Échec !")

    board_image = render_board_image()
    click_value = streamlit_image_coordinates(board_image, key="board_click")

    if click_value is not None:
        click_time = click_value.get("unix_time")
        if click_time != st.session_state.last_click_time:
            st.session_state.last_click_time = click_time
            square = pixel_to_square(click_value["x"], click_value["y"])
            handle_square_click(square)
            st.rerun()

    st.write("")
    if st.button("🔄 Nouvelle partie"):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.analysis_log = []
        st.session_state.last_click_time = None
        st.rerun()
