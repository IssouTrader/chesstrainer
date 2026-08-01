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
GOOD_MOVE_MARGIN_CP = 30  # tolerance : 0.30 point d'evaluation consideree comme negligeable


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
if "current_suggestion" not in st.session_state:
    st.session_state.current_suggestion = None
if "suggestion_move_count" not in st.session_state:
    st.session_state.suggestion_move_count = None

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
        info_list = engine.analyse(board, chess.engine.Limit(time=ANALYSIS_TIME), multipv=3)
        if isinstance(info_list, dict):
            info_list = [info_list]

        best_entry = info_list[0]
        best_move = best_entry["pv"][0]
        best_san = board.san(best_move)
        eval_score = best_entry["score"].white()
        best_reason = explain_move(board, best_move)

        played_san = board.san(move)
        was_best = (move == best_move)

        quality = "best" if was_best else "suboptimal"
        if not was_best:
            for entry in info_list:
                entry_move = entry.get("pv", [None])[0]
                if entry_move == move:
                    entry_score = entry["score"].white()
                    if not eval_score.is_mate() and not entry_score.is_mate():
                        diff_cp = abs((eval_score.score() or 0) - (entry_score.score() or 0))
                        if diff_cp <= GOOD_MOVE_MARGIN_CP:
                            quality = "good"
                    break

        board.push(move)

        st.session_state.analysis_log.insert(0, {
            "num": move_number,
            "side": side_played,
            "played": played_san,
            "best": best_san,
            "best_reason": best_reason,
            "was_best": was_best,
            "quality": quality,
            "eval": format_eval(eval_score),
        })

        if not board.is_game_over():
            result = engine.play(board, chess.engine.Limit(time=REPLY_TIME))
            board.push(result.move)

    st.session_state.current_suggestion = None
    st.session_state.suggestion_move_count = None


def get_current_suggestion():
    """Interroge Stockfish sur la position ACTUELLE, sans jouer de coup."""
    engine = get_engine()
    lock = get_engine_lock()
    with lock:
        info = engine.analyse(board, chess.engine.Limit(time=ANALYSIS_TIME))
        suggested_move = info["pv"][0]
        suggested_san = board.san(suggested_move)
        reason = explain_move(board, suggested_move)
        eval_score = info["score"].white()
    return {
        "san": suggested_san,
        "reason": reason,
        "eval": format_eval(eval_score),
    }


def undo_last_round():
    if len(board.move_stack) >= 2:
        board.pop()
        board.pop()
    elif len(board.move_stack) == 1:
        board.pop()
    if st.session_state.analysis_log:
        st.session_state.analysis_log.pop(0)
    st.session_state.selected_square = None
    st.session_state.current_suggestion = None
    st.session_state.suggestion_move_count = None


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


def get_opening_status():
    played = [m.uci() for m in board.move_stack]
    reached = [
        op for op in OPENINGS
        if len(op["moves"]) <= len(played) and op["moves"] == played[:len(op["moves"])]
    ]
    current = max(reached, key=lambda o: len(o["moves"])) if reached else None

    in_progress = [
        op for op in OPENINGS
        if len(op["moves"]) > len(played) and op["moves"][:len(played)] == played
    ]
    in_progress.sort(key=lambda o: len(o["moves"]))

    # Regroupe les coups suivants possibles par notation SAN, avec les noms d'ouvertures associees
    suggestions = {}
    for op in in_progress:
        next_uci = op["moves"][len(played)]
        try:
            next_move = chess.Move.from_uci(next_uci)
        except ValueError:
            continue
        if next_move not in board.legal_moves:
            continue
        san = board.san(next_move)
        suggestions.setdefault(san, []).append(op["name"])

    return current, in_progress, suggestions


left_col, board_col, opening_col = st.columns([1, 2, 1], gap="large")

with left_col:
    st.markdown("## 🎓 Trainer")
    st.markdown('<p class="subtitle">Le meilleur coup, a chaque tour</p>', unsafe_allow_html=True)

    if st.session_state.analysis_log:
        last = st.session_state.analysis_log[0]
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        if last["quality"] == "best":
            st.success(f"✅ Meilleur coup joué : **{last['played']}**")
            st.caption(last["best_reason"])
        elif last["quality"] == "good":
            st.info(f"👍 Bon coup : **{last['played']}** (quasi aussi fort que {last['best']})")
            st.caption(last["best_reason"])
        else:
            st.warning(f"Toi : **{last['played']}**  \nMeilleur coup : **{last['best']}**")
            st.caption(f"Pourquoi : {last['best_reason']}")
        st.caption(f"Evaluation : {last['eval']}")
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("📜 Historique des coups"):
            for entry in st.session_state.analysis_log:
                icon = {"best": "✅", "good": "👍"}.get(entry["quality"], "🔸")
                st.write(
                    f"{icon} {entry['num']}. ({entry['side']}) "
                    f"joue: {entry['played']} — meilleur: {entry['best']} "
                    f"({entry['eval']})"
                )
                st.caption(entry["best_reason"])
    else:
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.caption("Joue un coup pour voir l'analyse apparaitre ici.")
        st.markdown('</div>', unsafe_allow_html=True)

with board_col:
    st.markdown("# ♞ Chess Trainer")
    st.markdown('<p class="subtitle">Clique sur une piece, puis sur sa case de destination</p>', unsafe_allow_html=True)

    if board.is_checkmate():
        st.success("Echec et mat !")
    elif board.is_stalemate():
        st.info("Pat (match nul).")
    elif board.is_check():
        st.warning("Echec !")

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
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("↩️ Annuler le dernier coup", use_container_width=True):
            undo_last_round()
            st.rerun()
    with btn_col2:
        if st.button("💡 Suggestion", use_container_width=True):
            if not board.is_game_over():
                st.session_state.current_suggestion = get_current_suggestion()
                st.session_state.suggestion_move_count = len(board.move_stack)
            st.rerun()
    with btn_col3:
        if st.button("🔄 Nouvelle partie", use_container_width=True):
            st.session_state.board = chess.Board()
            st.session_state.selected_square = None
            st.session_state.analysis_log = []
            st.session_state.last_click_time = None
            st.session_state.current_suggestion = None
            st.session_state.suggestion_move_count = None
            st.rerun()

    if (st.session_state.current_suggestion is not None
            and st.session_state.suggestion_move_count == len(board.move_stack)):
        sug = st.session_state.current_suggestion
        st.info(f"💡 Coup suggéré pour la position actuelle : **{sug['san']}**")
        st.caption(f"{sug['reason']} — Évaluation : {sug['eval']}")

with opening_col:
    st.markdown("## 📖 Ouverture")
    current, in_progress, suggestions = get_opening_status()

    if current:
        st.markdown(
            f'<div class="opening-current">🎯 <strong>{current["name"]}</strong></div>',
            unsafe_allow_html=True,
        )
    elif len(board.move_stack) == 0:
        st.caption("La partie n'a pas encore commence.")
    else:
        st.caption("Position en dehors des ouvertures repertoriees.")

    if suggestions:
        st.markdown("**➡️ Pour continuer :**")
        for san, names in suggestions.items():
            noms_affiches = ", ".join(names[:2])
            if len(names) > 2:
                noms_affiches += f" (+{len(names) - 2} autres)"
            st.markdown(f"**{san}** — {noms_affiches}")

    if in_progress:
        with st.expander("Toutes les ouvertures encore possibles"):
            for op in in_progress[:15]:
                st.write(f"• {op['name']}")
