import streamlit as st
import copy

st.set_page_config(page_title="Online Sudoku", layout="centered")

# Ukázková zadání pro různé rozměry bloků (p x q)
PRESETS = {
    "Klasické 9×9 (bloky 3×3)": {
        "block_r": 3,
        "block_c": 3,
        "board": [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ],
    },
    "Obdélníkové 6×6 (bloky 2×3)": {
        "block_r": 2,
        "block_c": 3,
        "board": [
            [0, 0, 3, 0, 1, 0],
            [5, 6, 0, 3, 2, 0],
            [0, 5, 4, 2, 0, 3],
            [2, 0, 6, 4, 5, 0],
            [0, 1, 2, 0, 4, 5],
            [0, 4, 0, 1, 0, 0],
        ],
    },
    "Shidoku 4×4 (bloky 2×2)": {
        "block_r": 2,
        "block_c": 2,
        "board": [
            [1, 0, 0, 4],
            [0, 0, 1, 0],
            [0, 3, 0, 0],
            [2, 0, 0, 3],
        ],
    },
}


def is_valid_move(board, r, c, num, block_r, block_c):
    """
    Obecná kontrola tahu pro mřížku N×N s bloky rozměru block_r × block_c.
    Složitost: O(N).
    """
    n = len(board)
    for i in range(n):
        if board[r][i] == num or board[i][c] == num:
            return False

    # Levý horní roh příslušného bloku (block_r × block_c)
    br = block_r * (r // block_r)
    bc = block_c * (c // block_c)
    for i in range(br, br + block_r):
        for j in range(bc, bc + block_c):
            if board[i][j] == num:
                return False
    return True


def solve_bruteforce(board, block_r, block_c):
    """
    Obecný brute-force řešič pro libovolné rozměry bloků (N = block_r * block_c).
    """
    n = len(board)
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                for num in range(1, n + 1):
                    if is_valid_move(board, r, c, num, block_r, block_c):
                        board[r][c] = num
                        if solve_bruteforce(board, block_r, block_c):
                            return True
                        board[r][c] = 0
                return False
    return True


def load_preset(preset_name):
    """Načte vybranou variantu mřížky a předpočítá její řešení."""
    preset = PRESETS[preset_name]
    b_r = preset["block_r"]
    b_c = preset["block_c"]
    initial = copy.deepcopy(preset["board"])

    solved = copy.deepcopy(initial)
    solve_bruteforce(solved, b_r, b_c)

    st.session_state.current_preset = preset_name
    st.session_state.block_r = b_r
    st.session_state.block_c = b_c
    st.session_state.initial_board = initial
    st.session_state.board = copy.deepcopy(initial)
    st.session_state.solution = solved
    st.session_state.selected_num = 1
    st.session_state.active_cell = None


# Inicializace při prvním spuštění
if "current_preset" not in st.session_state:
    load_preset("Klasické 9×9 (bloky 3×3)")

BLOCK_R = st.session_state.block_r
BLOCK_C = st.session_state.block_c
N = BLOCK_R * BLOCK_C
INITIAL_BOARD = st.session_state.initial_board


def select_tool(num):
    st.session_state.selected_num = num


def cell_clicked(r, c):
    st.session_state.active_cell = (r, c)
    tool = st.session_state.selected_num

    if tool == -1 or INITIAL_BOARD[r][c] != 0:
        return

    if tool == 0 or st.session_state.board[r][c] == tool:
        st.session_state.board[r][c] = 0
    else:
        st.session_state.board[r][c] = tool


def find_mistakes(board, solution):
    mistakes = set()
    for r in range(N):
        for c in range(N):
            val = board[r][c]
            if val != 0 and val != solution[r][c]:
                mistakes.add((r, c))
    return mistakes


def build_dynamic_grid_css(mistakes):
    rules = ["""
    div.stButton > button {
        width: 100%;
        height: 50px;
        padding: 0px !important;
        border-radius: 8px !important;
        transition: all 0.1s ease-in-out !important;
    }
    div.stButton > button p,
    div.stButton > button span {
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        margin: 0 !important;
        font-family: system-ui, -apple-system, sans-serif !important;
    }
    """]

    active_r, active_c = st.session_state.active_cell if st.session_state.active_cell else (-1, -1)
    sel_num = st.session_state.selected_num

    for r in range(N):
        for c in range(N):
            val = st.session_state.board[r][c]
            is_fixed = INITIAL_BOARD[r][c] != 0
            is_player = (val != 0 and not is_fixed)
            in_crosshair = (r == active_r or c == active_c)
            is_active_cell = (r == active_r and c == active_c)
            is_num_match = (val != 0 and sel_num in range(1, N + 1) and val == sel_num)
            is_mistake = (r, c) in mistakes

            if is_fixed:
                bg, fg, border = "#e2e8f0", "#0f172a", "#94a3b8"
            elif is_player:
                bg, fg, border = "#dbeafe", "#1e3a8a", "#60a5fa"
            else:
                bg, fg, border = "#ffffff", "#0f172a", "#cbd5e1"

            if in_crosshair:
                if is_fixed:
                    bg, fg, border = "#fde68a", "#0f172a", "#d97706"
                elif is_player:
                    bg, fg, border = "#38bdf8", "#082f49", "#0284c7"
                else:
                    bg, fg, border = "#fef9c3", "#0f172a", "#eab308"

            if is_num_match:
                if is_fixed:
                    bg, fg, border = "#334155", "#ffffff", "#0f172a"
                else:
                    bg, fg, border = "#4f46e5", "#ffffff", "#312e81"

            box_shadow = "none"
            if is_mistake:
                bg, fg, border = "#ef4444", "#ffffff", "#991b1b"
                box_shadow = "0 0 0 2px #dc2626"

            outline = "3px solid #0f172a" if is_active_cell else "none"

            rules.append(f"""
            .st-key-cell_{r}_{c} button {{
                background-color: {bg} !important;
                color: {fg} !important;
                border: 2px solid {border} !important;
                box-shadow: {box_shadow} !important;
                outline: {outline} !important;
            }}
            .st-key-cell_{r}_{c} button p {{
                color: {fg} !important;
            }}
            """)

    return "<style>" + "\n".join(rules) + "</style>"


current_mistakes = find_mistakes(st.session_state.board, st.session_state.solution)
st.markdown(build_dynamic_grid_css(current_mistakes), unsafe_allow_html=True)

st.title("Online Sudoku")

# Výběr rozměru mřížky a bloků
selected_preset = st.selectbox(
    "Rozměr mřížky a bloků:",
    options=list(PRESETS.keys()),
    index=list(PRESETS.keys()).index(st.session_state.current_preset),
)
if selected_preset != st.session_state.current_preset:
    load_preset(selected_preset)
    st.rerun()

st.write("**Vyber číslo (nebo 🔍 pro pouhé zvýraznění řádku a sloupce) a klikni do tabulky:**")
palette_cols = st.columns(N + 2, gap="small")

for num in range(1, N + 1):
    with palette_cols[num - 1]:
        st.button(
            label=str(num),
            key=f"pick_{num}",
            type="primary" if st.session_state.selected_num == num else "secondary",
            on_click=select_tool,
            args=(num,),
            use_container_width=True,
        )

with palette_cols[N]:
    st.button(
        label="✕",
        key="pick_0",
        type="primary" if st.session_state.selected_num == 0 else "secondary",
        on_click=select_tool,
        args=(0,),
        help="Smazat políčko",
        use_container_width=True,
    )

with palette_cols[N + 1]:
    st.button(
        label="🔍",
        key="pick_inspect",
        type="primary" if st.session_state.selected_num == -1 else "secondary",
        on_click=select_tool,
        args=(-1,),
        help="Jen označit řádek a sloupec bez vkládání čísla",
        use_container_width=True,
    )

st.caption(
    "⬜ Šedé = zadání | 🟦 Modré = vyplněné hráčem | "
    "🟪 Fialové = vybrané číslo hráče | ⬛ Tmavé = vybrané číslo zadání | "
    "🟥 Červené = chyba oproti řešení"
)

if current_mistakes:
    st.error(f"Pozor: V mřížce máš chybu ({len(current_mistakes)} políček neodpovídá řešení).")

# Vykreslení obecné mřížky rozdělené do bloků rozměru BLOCK_R × BLOCK_C
num_block_rows = N // BLOCK_R  # odpovídá BLOCK_C
num_block_cols = N // BLOCK_C  # odpovídá BLOCK_R

for b_r in range(num_block_rows):
    block_cols = st.columns(num_block_cols, gap="small")
    for b_c in range(num_block_cols):
        with block_cols[b_c]:
            with st.container(border=True):
                for inner_r in range(BLOCK_R):
                    r = b_r * BLOCK_R + inner_r
                    cell_cols = st.columns(BLOCK_C, gap="small")
                    for inner_c in range(BLOCK_C):
                        c = b_c * BLOCK_C + inner_c
                        val = st.session_state.board[r][c]
                        label = str(val) if val != 0 else "\u00A0"
                        with cell_cols[inner_c]:
                            st.button(
                                label=label,
                                key=f"cell_{r}_{c}",
                                on_click=cell_clicked,
                                args=(r, c),
                                use_container_width=True,
                            )

st.write("")

ctrl1, ctrl2, ctrl3 = st.columns(3)

with ctrl1:
    if st.button("Ověřit stav", use_container_width=True):
        if current_mistakes:
            st.error("Některá políčka jsou vyplněná špatně (jsou zvýrazněná červeně).")
        elif any(0 in row for row in st.session_state.board):
            st.success("Všechna dosud vyplněná čísla jsou správně!")
        else:
            st.balloons()
            st.success("Gratulace! Sudoku je kompletně vyřešené.")

with ctrl2:
    if st.button("Vyřešit", use_container_width=True):
        st.session_state.board = copy.deepcopy(st.session_state.solution)
        st.rerun()

with ctrl3:
    if st.button("Resetovat", use_container_width=True):
        st.session_state.board = copy.deepcopy(INITIAL_BOARD)
        st.session_state.active_cell = None
        st.rerun()
