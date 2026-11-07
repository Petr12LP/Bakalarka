import streamlit as st
import copy

st.set_page_config(page_title="Sudoku – Bakalářská práce", layout="centered")

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
if "hint_msg" not in st.session_state:
    st.session_state.hint_msg = ""


def get_used_colors(board, r, c):
    """Vrátí množinu čísel (barev) použitých v sousedství vrcholu (r, c)."""
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


def get_candidates(board, r, c):
    """Vrátí přípustné barvy {1..9} pro neobarvený vrchol (r, c)."""
    return set(range(1, 10)) - get_used_colors(board, r, c)


def is_board_valid(board):
    """Zkontroluje, zda aktuální obarvení grafu neobsahuje kolizi."""
    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val != 0 and val in get_used_colors(board, r, c):
                return False, (r, c)
    return True, None


def find_dsatur_vertex(board):
    """Najde neobarvený vrchol s nejvyšším stupněm saturace (DSATUR)."""
    best_cell = None
    max_saturation = -1
    best_candidates = set()

    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                used = get_used_colors(board, r, c)
                saturation = len(used)
                if saturation > max_saturation:
                    max_saturation = saturation
                    best_cell = (r, c)
                    best_candidates = set(range(1, 10)) - used
    return best_cell, max_saturation, sorted(list(best_candidates))


def solve_dsatur(board):
    """Vyřeší Sudoku pomocí grafové heuristiky DSATUR a backtrackingu."""
    cell, _, candidates = find_dsatur_vertex(board)
    if cell is None:
        return True
    r, c = cell
    for val in candidates:
        board[r][c] = val
        if solve_dsatur(board):
            return True
        board[r][c] = 0
    return False


st.title("Online Sudoku (Model barvení grafu)")
st.caption("Implementace s kontrolou pravidel a nápovědou přes stupeň saturace (DSATUR)")

# Vykreslení mřížky 9x9
for r in range(9):
    if r % 3 == 0 and r != 0:
        st.divider()
    cols = st.columns(9)
    for c in range(9):
        is_fixed = INITIAL_BOARD[r][c] != 0
        current_val = st.session_state.board[r][c]
        with cols[c]:
            val_str = st.text_input(
                label=f"r{r}c{c}",
                value="" if current_val == 0 else str(current_val),
                max_chars=1,
                disabled=is_fixed,
                label_visibility="collapsed",
                key=f"cell_{r}_{c}"
            )
            if not is_fixed:
                if val_str.isdigit() and 1 <= int(val_str) <= 9:
                    st.session_state.board[r][c] = int(val_str)
                else:
                    st.session_state.board[r][c] = 0

st.write("")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Ověřit stav", use_container_width=True):
        valid, conflict = is_board_valid(st.session_state.board)
        if not valid:
            st.error(f"Kolize pravidel na souřadnici: řádek {conflict[0]+1}, sloupec {conflict[1]+1}.")
        elif any(0 in row for row in st.session_state.board):
            st.success("Zatím bez kolizí. Můžete pokračovat.")
        else:
            st.balloons()
            st.success("Sudoku je kompletně a správně vyřešené!")

with col2:
    if st.button("Nápověda (DSATUR)", use_container_width=True):
        cell, sat, cands = find_dsatur_vertex(st.session_state.board)
        if cell is None:
            st.session_state.hint_msg = "Mřížka je již plně vyplněná."
        else:
            st.session_state.hint_msg = (
                f"Nejvyšší stupeň saturace ({sat} různých barev v sousedství) má "
                f"**řádek {cell[0]+1}, sloupec {cell[1]+1}**. "
                f"Zbývající přípustní kandidáti: **{cands}**"
            )

with col3:
    if st.button("Vyřešit (Solver)", use_container_width=True):
        board_copy = copy.deepcopy(st.session_state.board)
        valid, _ = is_board_valid(board_copy)
        if valid and solve_dsatur(board_copy):
            st.session_state.board = board_copy
            for r in range(9):
                for c in range(9):
                    st.session_state[f"cell_{r}_{c}"] = str(board_copy[r][c])
            st.rerun()
        else:
            st.error("Aktuální stav mřížky nemá řešení (obsahuje chybu).")

with col4:
    if st.button("Resetovat", use_container_width=True):
        st.session_state.board = copy.deepcopy(INITIAL_BOARD)
        st.session_state.hint_msg = ""
        for r in range(9):
            for c in range(9):
                val = INITIAL_BOARD[r][c]
                st.session_state[f"cell_{r}_{c}"] = "" if val == 0 else str(val)
        st.rerun()

if st.session_state.hint_msg:
    st.info(st.session_state.hint_msg)