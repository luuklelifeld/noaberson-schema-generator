import copy
import math
import random

GAMES = [f"Game {i}" for i in range(1, 9)]
TEAMS = [
    ("Team 1", "adult"),
    ("Team 2", "non-adult"),
    ("Team 3", "adult"),
    ("Team 4", "non-adult"),
    ("Team 5", "adult"),
    ("Team 6", "adult"),
    ("Team 7", "non-adult"),
    ("Team 8", "non-adult"),
    ("Team 9", "non-adult"),
    ("Team 10", "adult"),
    ("Team 11", "non-adult"),
    ("Team 12", "adult"),
    ("Team 13", "adult"),
    ("Team 14", "non-adult"),
    ("Team 15", "adult"),
    ("Team 16", "adult"),
    ("Team 17", "non-adult"),
    ("Team 18", "adult"),
    ("Team 19", "non-adult"),
    ("Team 20", "non-adult"),
    ("Team 21", "adult"),
    ("Team 22", "adult"),
    ("Team 23", "non-adult"),
    ("Team 24", "adult"),
    ("Team 25", "adult"),
    ("Team 26", "non-adult"),
    ("Team 27", "adult"),
    ("Team 28", "adult"),
    ("Team 29", "non-adult"),
    ("Team 30", "adult"),
    ("Team 31", "non-adult"),
    ("Team 32", "adult"),
    ("Team 33", "adult"),
    ("Team 34", "non-adult"),
    ("Team 35", "adult"),
    ("Team 36", "adult"),
    #("Team 37", "non-adult"),
    #("Team 38", "adult"),
    #("Team 39", "adult"),
    #("Team 40", "non-adult"),
]
TEAMS_PER_GAME = 4

ADULT = "adult"
NON_ADULT = "non-adult"


PER_ROUND_TRIES = 30
MAX_ATTEMPTS = 30
SA_ITERATIONS = 500_000
SA_T_START = 3.0
SA_T_END = 0.005
MATCH_RETRIES = 200


def build_schedule(rng):
    num_games = len(GAMES)
    slots_per_round = num_games * TEAMS_PER_GAME
    num_rounds = max(1, len(TEAMS) * num_games // slots_per_round)

    best_rounds = None
    best_mixed = num_rounds * num_games + 1

    for _ in range(MAX_ATTEMPTS):
        rounds = _build_initial(rng, num_rounds, num_games)
        if rounds is None:
            continue
        _rectangle_swaps(rounds, num_games, rng)
        _simulated_annealing(rounds, num_games, rng)
        _rectangle_swaps(rounds, num_games, rng)
        mixed = _count_mixed_total(rounds)
        if mixed < best_mixed:
            best_mixed = mixed
            best_rounds = copy.deepcopy(rounds)
            if best_mixed <= 8:
                break

    if best_rounds is not None:
        _validate_schedule(best_rounds)
    return best_rounds


def _validate_schedule(rounds):
    num_games = len(GAMES)
    teams_set = set(TEAMS)

    for r_idx, rnd in enumerate(rounds):
        assert len(rnd) == num_games, f"round {r_idx} has {len(rnd)} games, expected {num_games}"
        seen_in_round = set()
        for g_idx, cell in enumerate(rnd):
            assert len(cell) == TEAMS_PER_GAME, f"round {r_idx} game {g_idx} has {len(cell)} teams"
            for t in cell:
                assert t not in seen_in_round, f"round {r_idx} contains duplicate team {t}"
                seen_in_round.add(t)

    for g_idx, game_name in enumerate(GAMES):
        teams_in_column = [t for rnd in rounds for t in rnd[g_idx]]
        assert len(teams_in_column) == len(teams_set), \
            f"{game_name} has {len(teams_in_column)} entries, expected {len(teams_set)}"
        assert set(teams_in_column) == teams_set, \
            f"{game_name} missing teams {teams_set - set(teams_in_column)} or duplicates {[t for t in teams_in_column if teams_in_column.count(t) > 1]}"


def _build_initial(rng, num_rounds, num_games):
    for _ in range(MATCH_RETRIES):
        sit_outs = _make_sitout_plan(rng, num_rounds)
        history = {game: {team: False for team in TEAMS} for game in GAMES}
        rounds = []
        ok = True
        for r in range(num_rounds):
            playing = [t for t in TEAMS if t not in sit_outs[r]]
            best = None
            best_mixed_r = num_games + 1
            for _ in range(PER_ROUND_TRIES):
                m = _match_round(history, playing, num_games, rng)
                if m is None:
                    continue
                mr = _count_mixed_in_match(m)
                if mr < best_mixed_r:
                    best = m
                    best_mixed_r = mr
                    if mr == 0:
                        break
            if best is None:
                ok = False
                break
            rounds.append([list(best[gi]) for gi in range(num_games)])
            for gi, teams in best.items():
                for t in teams:
                    history[GAMES[gi]][t] = True
        if ok:
            return rounds
    return None


def _make_sitout_plan(rng, num_rounds):
    """Sit-out plan that admits theoretical-minimum mixed-cell count.

    With 21 adults, 15 non-adults, 4 sit-outs/round across 9 rounds:
    3 rounds with j=0 (4 non-adult sit-outs each), 5 with j=4 (4 adult), 1 with j=1.
    Totals: 21 adult sit-outs, 15 non-adult sit-outs. Per-round mixed minimums: 1,1,1,1,1,1,1,1,0 = 8.
    """
    adults = [t for t in TEAMS if t[1] == ADULT]
    non_adults = [t for t in TEAMS if t[1] == NON_ADULT]
    rng.shuffle(adults)
    rng.shuffle(non_adults)

    j_per_round = [0] * 3 + [4] * 5 + [1] * 1
    if len(j_per_round) != num_rounds or sum(j_per_round) != len(adults):
        # Fallback to random partition if counts changed
        teams_pool = list(TEAMS)
        rng.shuffle(teams_pool)
        return [set(teams_pool[i * 4:(i + 1) * 4]) for i in range(num_rounds)]
    rng.shuffle(j_per_round)

    sit_outs = []
    a_idx = 0
    n_idx = 0
    for j in j_per_round:
        n_count = 4 - j
        so = set(adults[a_idx:a_idx + j]) | set(non_adults[n_idx:n_idx + n_count])
        a_idx += j
        n_idx += n_count
        sit_outs.append(so)
    return sit_outs


def _count_mixed_in_match(game_teams):
    return sum(1 for ts in game_teams.values() if len({t[1] for t in ts}) > 1)


def _count_mixed_total(rounds):
    return sum(1 for rnd in rounds for cell in rnd if len({t[1] for t in cell}) > 1)


def _match_round(history, playing_teams, num_games, rng):
    game_teams = {gi: [] for gi in range(num_games)}
    team_game = {}
    eligible = {t: [gi for gi in range(num_games) if not history[GAMES[gi]][t]] for t in playing_teams}

    def priority_key(team, gi):
        contents = game_teams[gi]
        if not contents:
            return 1
        kinds = {t[1] for t in contents}
        if len(kinds) == 1:
            return 0 if team[1] in kinds else 3
        return 2

    def augment(team, visited, depth=0):
        if depth > 30:
            return False
        cands = sorted(eligible[team], key=lambda gi: (priority_key(team, gi), rng.random()))
        for gi in cands:
            if gi in visited:
                continue
            visited.add(gi)
            if len(game_teams[gi]) < TEAMS_PER_GAME:
                game_teams[gi].append(team)
                team_game[team] = gi
                return True
            others = list(game_teams[gi])
            rng.shuffle(others)
            for other in others:
                game_teams[gi].remove(other)
                del team_game[other]
                if augment(other, visited, depth + 1):
                    game_teams[gi].append(team)
                    team_game[team] = gi
                    return True
                game_teams[gi].append(other)
                team_game[other] = gi
        return False

    adults = [t for t in playing_teams if t[1] == ADULT]
    non_adults = [t for t in playing_teams if t[1] == NON_ADULT]
    rng.shuffle(adults)
    rng.shuffle(non_adults)
    for t in adults + non_adults:
        if not augment(t, set()):
            return None
    if any(len(game_teams[gi]) != TEAMS_PER_GAME for gi in range(num_games)):
        return None
    return game_teams


def _build_state(rounds, num_games):
    """Returns (team_cell, cell_adult). team_cell[team][g] = round_idx; cell_adult[(r,g)] = adult count."""
    team_cell = {}
    cell_adult = {}
    for r, rnd in enumerate(rounds):
        for g, cell in enumerate(rnd):
            count = 0
            for t in cell:
                team_cell.setdefault(t, {})[g] = r
                if t[1] == ADULT:
                    count += 1
            cell_adult[(r, g)] = count
    return team_cell, cell_adult


def _is_mixed(adult_count):
    return 0 < adult_count < TEAMS_PER_GAME


def _swap_delta(cell_adult, r1, r2, g1, g2, a_is_adult, b_is_adult):
    """Mixed-count delta if we apply rectangle swap A<->B at the 4 cells."""
    if a_is_adult == b_is_adult:
        return 0
    # If A adult (1) and B non-adult (0): cells losing A and gaining B change by -1.
    # Else inverse.
    d_a_to_b = (1 if b_is_adult else 0) - (1 if a_is_adult else 0)  # cells where A leaves, B enters
    d_b_to_a = -d_a_to_b  # cells where B leaves, A enters
    changes = [
        ((r1, g1), d_a_to_b),
        ((r1, g2), d_b_to_a),
        ((r2, g1), d_b_to_a),
        ((r2, g2), d_a_to_b),
    ]
    delta = 0
    for cell, d in changes:
        old = cell_adult[cell]
        new = old + d
        delta += (1 if _is_mixed(new) else 0) - (1 if _is_mixed(old) else 0)
    return delta


def _apply_swap(rounds, team_cell, cell_adult, A, B, r1, r2, g1, g2):
    a_is_adult = A[1] == ADULT
    b_is_adult = B[1] == ADULT
    d_a_to_b = (1 if b_is_adult else 0) - (1 if a_is_adult else 0)
    d_b_to_a = -d_a_to_b

    # Replace A with B at (r1,g1) and (r2,g2); replace B with A at (r1,g2) and (r2,g1)
    _replace(rounds[r1][g1], A, B)
    _replace(rounds[r2][g2], A, B)
    _replace(rounds[r1][g2], B, A)
    _replace(rounds[r2][g1], B, A)

    cell_adult[(r1, g1)] += d_a_to_b
    cell_adult[(r2, g2)] += d_a_to_b
    cell_adult[(r1, g2)] += d_b_to_a
    cell_adult[(r2, g1)] += d_b_to_a

    team_cell[A][g1], team_cell[A][g2] = r2, r1
    team_cell[B][g1], team_cell[B][g2] = r1, r2


def _replace(cell, old_team, new_team):
    idx = cell.index(old_team)
    cell[idx] = new_team


def _find_rectangle_partner(rounds, team_cell, A, g1, g2):
    """Return B such that A is in (r1,g1)&(r2,g2), B is in (r1,g2)&(r2,g1)."""
    r1 = team_cell[A][g1]
    r2 = team_cell[A][g2]
    if r1 == r2:
        return None
    for cand in rounds[r1][g2]:
        if cand is A:
            continue
        if team_cell[cand][g1] == r2:
            return cand
    return None


def _rectangle_swaps(rounds, num_games, rng):
    """Iterate rectangle swaps to fixpoint."""
    team_cell, cell_adult = _build_state(rounds, num_games)
    candidates_template = [(A, g1, g2) for A in TEAMS for g1 in range(num_games) for g2 in range(g1 + 1, num_games)]

    while True:
        improved = False
        rng.shuffle(candidates_template)
        for A, g1, g2 in candidates_template:
            B = _find_rectangle_partner(rounds, team_cell, A, g1, g2)
            if B is None or A[1] == B[1]:
                continue
            r1 = team_cell[A][g1]
            r2 = team_cell[A][g2]
            delta = _swap_delta(cell_adult, r1, r2, g1, g2, A[1] == ADULT, B[1] == ADULT)
            if delta < 0:
                _apply_swap(rounds, team_cell, cell_adult, A, B, r1, r2, g1, g2)
                improved = True
                break
        if not improved:
            return


def _simulated_annealing(rounds, num_games, rng):
    team_cell, cell_adult = _build_state(rounds, num_games)
    current_mixed = _count_mixed_total(rounds)
    best_mixed = current_mixed
    best_snapshot = copy.deepcopy(rounds)

    teams_list = list(TEAMS)
    log_ratio = math.log(SA_T_END / SA_T_START)

    for i in range(SA_ITERATIONS):
        t = SA_T_START * math.exp(log_ratio * i / SA_ITERATIONS)

        A = teams_list[rng.randrange(len(teams_list))]
        g1 = rng.randrange(num_games)
        g2 = rng.randrange(num_games)
        if g1 == g2:
            continue
        if g1 > g2:
            g1, g2 = g2, g1

        r1 = team_cell[A][g1]
        r2 = team_cell[A][g2]
        if r1 == r2:
            continue

        cell = rounds[r1][g2]
        B = None
        for cand in cell:
            if cand is A:
                continue
            if team_cell[cand][g1] == r2:
                B = cand
                break
        if B is None:
            continue

        delta = _swap_delta(cell_adult, r1, r2, g1, g2, A[1] == ADULT, B[1] == ADULT)
        if delta < 0 or rng.random() < math.exp(-delta / t):
            _apply_swap(rounds, team_cell, cell_adult, A, B, r1, r2, g1, g2)
            current_mixed += delta
            if current_mixed < best_mixed:
                best_mixed = current_mixed
                best_snapshot = copy.deepcopy(rounds)

    # Restore best snapshot
    for r in range(len(rounds)):
        for g in range(num_games):
            rounds[r][g] = list(best_snapshot[r][g])


def format_team(team):
    name, _ = team
    return name.replace("Team ", "T")


def cell_kind(teams):
    kinds = {kind for _, kind in teams}
    if len(kinds) == 1:
        return next(iter(kinds))
    return "mixed"


KIND_COLORS = {
    ADULT: "#cfe6ff",
    NON_ADULT: "#ffe0b3",
    "mixed": "#ff0000",
}


def render_schedule(rounds, output_path="schema.png"):
    import matplotlib.pyplot as plt

    num_games = len(GAMES)
    num_rounds = len(rounds)

    for round in rounds:
        for game in round:
            if len(game) != 4:
                return "skipped"

    col_labels = [""] + GAMES
    row_data = []
    cell_colors = []
    for i, round_row in enumerate(rounds, 1):
        row = [f"Round {i}"] + [", ".join(format_team(t) for t in teams) for teams in round_row]
        colors = ["#f0f0f0"] + [KIND_COLORS[cell_kind(teams)] for teams in round_row]
        row_data.append(row)
        cell_colors.append(colors)

    fig_w = 2 + num_games * 2.2
    fig_h = 1.2 + num_rounds * 0.6
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")

    table = ax.table(
        cellText=row_data,
        colLabels=col_labels,
        cellColours=cell_colors,
        colColours=["#d9d9d9"] * (num_games + 1),
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.8)

    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#888")
        if r == 0 or c == 0:
            cell.set_text_props(weight="bold")

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    for i in range(9999999):
        rng = random.Random(i)
        schedule = build_schedule(rng)
        if schedule is None:
            continue
        path = render_schedule(schedule, f"schema-{i}.png")
        if path != "skipped":
            print(f"Wrote {path}")
