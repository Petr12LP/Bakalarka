import streamlit as st
import copy

st.set_page_config(page_title="Online Sudoku", layout="centered")

INITIAL_BOARD = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9]
]

if "board" not in st.session_state:
    st.session_state.board = copy.deepcopy(INITIAL_BOARD)
if "selected_num" not in st.session_state:
    st.session_state.selected_num = 1  # 1-9 = číslo, 0 = guma, -1 = jen označit řádek/sloupec
if "active_cell" not in st.session_state:
    st.session_state.active_cell = None  # (r, c) právě zakliknutého pole


def select_tool(num):
    """Nastaví aktivní číslo (1-9), gumu (0) nebo režim označování (-1)."""
    st.session_state.selected_num = num


def cell_clicked(r, c):
    """Zvýrazní řádek a sloupec zakliknutého pole a případně upraví hodnotu."""
    st.session_state.active_cell = (r, c)
    tool = st.session_state.selected_num

    # Režim "🔍" nebo kliknutí na pevné číslo ze zadání pouze zvýrazní řádek a sloupec
    if tool == -1 or INITIAL_BOARD[r][c] != 0:
        return

    # Vymazání pole gumou nebo opětovným kliknutím se stejným číslem
    if tool == 0 or st.session_state.board[r][c] == tool:
        st.session_state.board[r][c] = 0
    else:
        st.session_state.board[r][c] = tool


def get_used_colors(board, r, c):
    used = set()
    for i in range(9):
        if i != c and board[r][i] != 0:
            used.add(board[r][i])
        if i != r and board[i][c] != 0:
            used.add(board[i][c])
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if (i != r or j != c) and board[i][j] != 0:
                used.add(board[i][j])
    return used


def is_board_valid(board):
    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val != 0 and val in get_used_colors(board, r, c):
                return False, (r, c)
    return True, None


def solve_board(board):
    best_cell = None
    max_sat = -1
    best_cands = []
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                used = get_used_colors(board, r, c)
                if len(used) > max_sat:
                    max_sat = len(used)
                    best_cell = (r, c)
                    best_cands = [x for x in range(1, 10) if x not in used]
    if best_cell is None:
        return True
    r, c = best_cell
    for val in best_cands:
        board[r][c] = val
        if solve_board(board):
            return True
        board[r][c] = 0
    return False


def build_dynamic_Grid_css():
    """Vygeneruje CSS styly pro každé z 81 políček podle jeho stavu."""
    rules = ["""
    div.stButton > button {
        width: 100%;
        height: 42px;
        padding: 0px !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        transition: all 0.12s ease-in-out !important;
    }
    """]

    active_r, active_c = st.session_state.active_cell if st.session_state.active_cell else (-1, -1)
    sel_num = st.session_state.selected_num

    for r in range(9):
        for c in range(9):
            val = st.session_state.board[r][c]
            is_fixed = INITIAL_BOARD[r][c] != 0
            is_player = (val != 0 and not is_fixed)
            in_crosshair = (r == active_r or c == active_c)
            is_active_cell = (r == active_r and c == active_c)
            is_num_match = (val != 0 and sel_num in range(1, 10) and val == sel_num)

            # 1. Výchozí barvy (prázdné vs. zadání vs. vyplněné hráčem)
            if is_fixed:
                bg, fg, border = "#e2e8f0", "#0f172a", "#cbd5e1"
            elif is_player:
                bg, fg, border = "#dbeafe", "#1e3a8a", "#93c5fd"
            else:
                bg, fg, border = "#ffffff", "#0f172a", "#e2e8f0"

            # 2. Zvýraznění zakliknutého řádku a sloupce
            if in_crosshair:
                if is_fixed:
                    bg, fg, border = "#fde68a", "#0f172a", "#f59e0b"
                elif is_player:
                    # Hráčem vyplněné pole ve zvýrazněném řádku/sloupci (výrazný tyrkysový odstín)
                    bg, fg, border = "#38bdf8", "#082f49", "#0284c7"
                else:
                    # Prázdné pole ve zvýrazněném řádku/sloupci (jemně žluté)
                    bg, fg, border = "#fef9c3", "#0f172a", "#facc15"

            # 3. Zvýraznění polí se stejným číslem jako je navolené v paletě
            if is_num_match:
                if is_fixed:
                    # Pevné číslo ze zadání se stejným číslem (červené)
                    bg, fg, border = "#dc2626", "#ffffff", "#991b1b"
                else:
                    # Hráčem vyplněné zvýrazněné pole (výrazný fialovo-modrý odstín)
                    bg, fg, border = "#4f46e5", "#ffffff", "#312e81"

            # 4. Ohraničení právě zakliknutého pole (průsečík řádku a sloupce)
            outline = "3px solid #0f172a" if is_active_cell else "none"

            rules.append(f"""
            .st-key-cell_{r}_{c} button {{
                background-color: {bg} !important;
                color: {fg} !important;
                border: 2px solid {border} !important;
                outline: {outline} !important;
            }}
            """)

    return "<style>" + "\n".join(rules) + "</style
