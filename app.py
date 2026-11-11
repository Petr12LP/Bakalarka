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


def find_all_conflicts(board):
    """Vrátí množinu souřadnic (r, c) všech políček, která porušují pravidla."""
    conflicts = set()
    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val != 0 and val in get_used_colors(board, r, c):
                conflicts.add((r, c))
    return conflicts


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


def build_dynamic_grid_css(conflicts):
    """Vygeneruje CSS styly pro čitelné velké číslice, podbarvení a kolize."""
    rules = ["""
    /* Zvětšení tlačítek a vycentrování obsahu */
    div.stButton > button {
        width: 100%;
        height: 50px;
        padding: 0px !important;
        border-radius: 8px !important;
        transition: all 0.1s ease-in-out !important;
    }

    /* Výrazné zvětšení a ztučnění samotných číslic uvnitř tlačítek */
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

    for r in range(9):
        for c in range(9):
            val = st.session_state.board[r][c]
            is_fixed = INITIAL_BOARD[r][c] != 0
            is_player = (val != 0 and not is_fixed)
            in_crosshair = (r == active_r or c == active_c)
            is_active_cell = (r == active_r and c == active_c)
            is_num_match = (val != 0 and sel_num in range(1, 10) and val == sel_num)
            is_conflict = (r, c) in conflicts

            # 1. Výchozí barvy (prázdné vs. zadání vs. vyplněné hráčem)
            if is_fixed:
                bg, fg, border = "#e2e8f0", "#0f172a", "#94a3b8"
            elif is_player:
                bg, fg, border = "#dbeafe", "#1e3a8a", "#60a5fa"
            else:
                bg, fg, border = "#ffffff", "#0f172a", "#cbd5e1"

            # 2. Zvýraznění zakliknutého řádku a sloupce
            if in_crosshair:
                if is_fixed:
                    bg, fg, border = "#fde68a", "#0f172a", "#d97706"
                elif is_player:
                    bg, fg, border = "#38bdf8", "#082f49", "#0284c7"
                else:
                    bg, fg, border = "#fef9c3", "#0f172a", "#eab308"

            # 3. Zvýraznění polí se stejným číslem jako je navolené v paletě
            if is_num_match:
                if is_fixed:
                    bg, fg, border = "#334155", "#ffffff", "#0f172a"
                else:
                    bg, fg, border = "#4f46e5", "#ffffff", "#312e81"

            # 4. Okamžité červené zvýraznění kolizí (má nejvyšší vizuální prioritu)
            box_shadow = "none"
            if is_conflict:
                if is_fixed:
                    bg, fg, border = "#fecaca", "#7f1d1d", "#dc2626"
                else:
                    bg, fg, border = "#ef4444", "#ffffff", "#991b1b"
                box_shadow = "0 0 0 2px #dc2626"

            # 5. Ohraničení právě zakliknutého pole (průsečík řádku a sloupce)
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


# Výpočet aktuálních kolizí před vykreslením mřížky
current_conflicts = find_all_conflicts(st.session_state.board)
st.markdown(build_dynamic_grid_css(current_conflicts), unsafe_allow_html=True)

st.title("Online Sudoku")

# 1. Paleta nástrojů (1-9, guma a režim označení řádku/sloupce)
st.write("**Vyber číslo (nebo 🔍 pro pouhé zvýraznění řádku a sloupce) a klikni do tabulky:**")
palette_cols = st.columns(11, gap="small")

for num in range(1, 10):
    with palette_cols[num - 1]:
        st.button(
            label=str(num),
            key=f"pick_{num}",
            type="primary" if st.session_state.selected_num == num else "secondary",
            on_click=select_tool,
            args=(num,),
            use_container_width=True
        )

with palette_cols[9]:
    st.button(
        label="✕",
        key="pick_0",
        type="primary" if st.session_state.selected_num == 0 else "secondary",
        on_click=select_tool,
        args=(0,),
        help="Smazat políčko",
        use_container_width=True
    )

with palette_cols[10]:
    st.button(
        label="🔍",
        key="pick_inspect",
        type="primary" if st.session_state.selected_num == -1 else "secondary",
        on_click=select_tool,
        args=(-1,),
        help="Jen označit řádek a sloupec bez vkládání čísla",
        use_container_width=True
    )

st.caption(
    "⬜ Šedé = zadání | 🟦 Modré = vyplněné hráčem | "
    "🟪 Fialové = vybrané číslo hráče | ⬛ Tmavé = vybrané číslo zadání | "
    "🟥 Červené = kolize pravidel"
)

if current_conflicts:
    st.error(f"Pozor: V mřížce je kolize pravidel ({len(current_conflicts)} kolidujících políček je zvýrazněno červeně).")

# 2. Hrací mřížka rozdělená na 3 sloupce a 3 řady bloků (3x3)
for block_r in range(3):
    block_cols = st.columns(3, gap="small")
    for block_c in range(3):
        with block_cols[block_c]:
            with st.container(border=True):
                for inner_r in range(3):
                    r = block_r * 3 + inner_r
                    cell_cols = st.columns(3, gap="small")
                    for inner_c in range(3):
                        c = block_c * 3 + inner_c
                        val = st.session_state.board[r][c]
                        label = str(val) if val != 0 else "\u00A0"
                        with cell_cols[inner_c]:
                            st.button(
                                label=label,
                                key=f"cell_{r}_{c}",
                                on_click=cell_clicked,
                                args=(r, c),
                                use_container_width=True
                            )

st.write("")

# 3. Ovládací tlačítka pod mřížkou
ctrl1, ctrl2, ctrl3 = st.columns(3)

with ctrl1:
    if st.button("Ověřit stav", use_container_width=True):
        if current_conflicts:
            st.error("V mřížce jsou červeně vyznačené kolize. Oprav je před pokračováním.")
        elif any(0 in row for row in st.session_state.board):
            st.success("Zatím bez chyb, můžeš pokračovat.")
        else:
            st.balloons()
            st.success("Gratulace! Sudoku je kompletně vyřešené.")

with ctrl2:
    if st.button("Vyřešit", use_container_width=True):
        board_copy = copy.deepcopy(st.session_state.board)
        if not current_conflicts and solve_board(board_copy):
            st.session_state.board = board_copy
            st.rerun()
        else:
            st.error("Z aktuálního stavu neexistuje platné řešení (nejprve odstraň kolize).")

with ctrl3:
    if st.button("Resetovat", use_container_width=True):
        st.session_state.board = copy.deepcopy(INITIAL_BOARD)
        st.session_state.active_cell = None
        st.rerun()
