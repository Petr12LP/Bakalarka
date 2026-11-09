import streamlit as st
import copy

st.set_page_config(page_title="Online Sudoku", layout="centered")

# Stylování mřížky a tlačítek pro kompaktní čtvercový vzhled
st.markdown("""
<style>
div.stButton > button {
    width: 100%;
    height: 42px;
    padding: 0px !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

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
    st.session_state.selected_num = 1


def select_number(num):
    """Nastaví aktivní číslo pro vkládání do mřížky."""
    st.session_state.selected_num = num


def cell_clicked(r, c):
    """Vloží právě navolené číslo do kliknuté buňky (nebo ji vymaže)."""
    if st.session_state.selected_num == 0 or st.session_state.board[r][c] == st.session_state.selected_num:
        st.session_state.board[r][c] = 0
    else:
        st.session_state.board[r][c] = st.session_state.selected_num


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


st.title("Online Sudoku")

# 1. Paleta pro navolení čísla (1-9 + guma)
st.write("**Vyber číslo a kliknutím ho vlož do tabulky:**")
palette_cols = st.columns(10)
for num in range(1, 10):
    with palette_cols[num - 1]:
        is_active = (st.session_state.selected_num == num)
        st.button(
            label=str(num),
            key=f"pick_{num}",
            type="primary" if is_active else "secondary",
            on_click=select_number,
            args=(num,),
            use_container_width=True
        )

with palette_cols[9]:
    is_eraser = (st.session_state.selected_num == 0)
    st.button(
        label="✕",
        key="pick_0",
        type="primary" if is_eraser else "secondary",
        on_click=select_number,
        args=(0,),
        help="Smazat políčko",
        use_container_width=True
    )

st.write("")

# 2. Hrací mřížka rozdělená na 3 sloupce a 3 řady bloků (3x3)
for block_r in range(3):
    block_cols = st.columns(3)
    for block_c in range(3):
        with block_cols[block_c]:
            with st.container(border=True):
                for inner_r in range(3):
                    r = block_r * 3 + inner_r
                    cell_cols = st.columns(3)
                    for inner_c in range(3):
                        c = block_c * 3 + inner_c
                        val = st.session_state.board[r][c]
                        is_fixed = INITIAL_BOARD[r][c] != 0
                        label = str(val) if val != 0 else "\u00A0"
                        with cell_cols[inner_c]:
                            st.button(
                                label=label,
                                key=f"cell_{r}_{c}",
                                disabled=is_fixed,
                                on_click=cell_clicked,
                                args=(r, c),
                                use_container_width=True
                            )

st.write("")

# 3. Ovládací tlačítka pod mřížkou
ctrl1, ctrl2, ctrl3 = st.columns(3)

with ctrl1:
    if st.button("Ověřit stav", use_container_width=True):
        valid, conflict = is_board_valid(st.session_state.board)
        if not valid:
            st.error(f"Kolize pravidel: řádek {conflict[0]+1}, sloupec {conflict[1]+1}.")
        elif any(0 in row for row in st.session_state.board):
            st.success("Zatím bez chyb, můžeš pokračovat.")
        else:
            st.balloons()
            st.success("Gratulace! Sudoku je kompletně vyřešené.")

with ctrl2:
    if st.button("Vyřešit", use_container_width=True):
        board_copy = copy.deepcopy(st.session_state.board)
        valid, _ = is_board_valid(board_copy)
        if valid and solve_board(board_copy):
            st.session_state.board = board_copy
            st.rerun()
        else:
            st.error("Z aktuálního stavu neexistuje platné řešení.")

with ctrl3:
    if st.button("Resetovat", use_container_width=True):
        st.session_state.board = copy.deepcopy(INITIAL_BOARD)
        st.rerun()
