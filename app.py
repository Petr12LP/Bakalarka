import streamlit as st
import copy
import random

st.set_page_config(page_title="Online Sudoku", layout="centered")

GRID_CONFIGS = {
    "Klasické 9×9 (bloky 3×3)": (3, 3),
    "Obdélníkové 6×6 (bloky 2×3)": (2, 3),
    "Shidoku 4×4 (bloky 2×2)": (2, 2),
}

DIFFICULTIES = {
    "Lehké": 0.45,
    "Střední": 0.60,
    "Těžké (maximální redukce)": 1.0,
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

    br = block_r * (r // block_r)
    bc = block_c * (c // block_c)
    for i in range(br, br + block_r):
        for j in range(bc, bc + block_c):
            if board[i][j] == num:
                return False
    return True


def solve_bruteforce(board, block_r, block_c, randomize=False):
    """
    Obecný brute-force řešič. Při randomize=True náhodně míchá zkoušená čísla 1..N,
    díky čemuž dokáže vygenerovat libovolnou platnou vyplněnou mřížku.
    """
    n = len(board)
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                nums = list(range(1, n + 1))
                if randomize:
                    random.shuffle(nums)
                for num in nums:
                    if is_valid_move(board, r, c, num, block_r, block_c):
                        board[r][c] = num
                        if solve_bruteforce(board, block_r, block_c, randomize):
                            return True
                        board[r][c] = 0
                return False
    return True


def generate_sudoku(block_r, block_c, remove_ratio=1.0):
    """
    Vygeneruje zadání metodou postupného odebírání čísel (digging holes):
    1. Vyplní prázdnou mřížku randomizovaným backtrackingem (vznikne vzorové řešení).
    2. V náhodném pořadí zkouší mazat buňky. Po každém smazání otestuje, zda neexistuje
       řešení s jiným číslem na dané pozici. Pokud ano, číslo vrátí, aby zůstala jednoznačnost.
    """
    n = block_r * block_c
    solution = [[0] * n for _ in range(n)]
    solve_bruteforce(solution, block_r, block_c, randomize=True)

    puzzle = copy.deepcopy(solution)
    cells = [(r, c) for r in range(n) for c in range(n)]
    random.shuffle(cells)

    target_removals = int(len(cells) * remove_ratio)
    removed = 0

    for r, c in cells:
        if removed >= target_removals:
            break

        backup = puzzle[r][c]
        puzzle[r][c] = 0

        # Ověření jednoznačnosti: zkusíme na pozici (r, c) dosadit všechna jiná přípustná čísla
        has_alternative = False
        for other_num in range(1, n + 1):
            if other_num == backup:
                continue
            if is_valid_move(puzzle, r, c, other_num, block_r, block_c):
                test_board = copy.deepcopy(puzzle)
                test_board[r][c] = other_num
                if solve_bruteforce(test_board, block_r, block_c, randomize=False):
                    has_alternative = True
                    break

        if has_alternative:
            puzzle[r][c] = backup
        else:
            removed += 1

    return puzzle, solution


def start_new_game(grid_label, diff_label):
    b_r, b_c = GRID_CONFIGS[grid_label]
    ratio = DIFFICULTIES[diff_label]
    puzzle, solution = generate_sudoku(b_r, b_c, ratio)

    st.session_state.grid_label = grid_label
    st.session_state.diff_label = diff_label
    st.session_state.block_r = b_r
    st.session_state.block_c = b_c
    st.session_state.initial_board = puzzle
    st.session_state.board = copy.deepcopy(puzzle)
    st.session_state.solution = solution
    st.session_state.selected_num = 1
    st.session_state.active_cell = None


# Inicializace při prvním spuštění aplikace
if "board" not in st.session_state:
    start_new_game("Klasické 9×9 (bloky 3×3)", "Střední")

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

# Ovládací lišta pro generování náhodného zadání
gen_col1, gen_col2, gen_col3 = st.columns([2, 2, 1.5], vertical_alignment="bottom")

with gen_col1:
    selected_grid = st.selectbox(
        "Rozměr mřížky:",
        options=list(GRID_CONFIGS.keys()),
        index=list(GRID_CONFIGS.keys()).index(st.session_state.grid_label),
    )

with gen_col2:
    selected_diff = st.selectbox(
        "Obtížnost generátoru:",
        options=list(DIFFICULTIES.keys()),
        index=list(DIFFICULTIES.keys()).index(st.session_state.diff_label),
    )

with gen_col3:
    generate_clicked = st.button("Nové zadání", type="primary", use_container_width=True)

if (
    generate_clicked
    or selected_grid != st.session_state.grid_label
    or selected_diff != st.session_state.diff_label
):
    start_new_game(selected_grid, selected_diff)
    st.rerun()

clues_count = sum(1 for r in range(N) for c in range(N) if INITIAL_BOARD[r][c] != 0)
st.caption(f"Počet nápověd v vygenerovaném zadání: **{clues_count} / {N * N}** (garantované jednoznačné řešení)")

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

# Vykreslení mřížky rozdělené do bloků BLOCK_R × BLOCK_C
num_block_rows = N // BLOCK_R
num_block_cols = N // BLOCK_C

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
