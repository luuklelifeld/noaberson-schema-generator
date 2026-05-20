import random

from ortools.sat.python import cp_model

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
]
TEAMS_PER_GAME = 4

ADULT = "adult"
NON_ADULT = "non-adult"
MIXED = "mixed"

KIND_COLORS = {
    ADULT: "#cfe6ff",
    NON_ADULT: "#ffe0b3",
    MIXED: "#ff0000",
}
LABEL_COLOR = "#d9d9d9"
ROW_HEADER_COLOR = "#f0f0f0"
GRID_EDGE_COLOR = "#888"

SOLVER_TIME_LIMIT_SECONDS = 30.0


class _StopAtObjective(cp_model.CpSolverSolutionCallback):
    def __init__(self, target):
        super().__init__()
        self._target = target

    def on_solution_callback(self):
        if self.objective_value <= self._target:
            self.stop_search()


def build_schedule(rng):
    num_games = len(GAMES)
    slots_per_round = num_games * TEAMS_PER_GAME
    num_rounds = max(1, len(TEAMS) * num_games // slots_per_round)
    num_teams = len(TEAMS)
    adult_indices = [t for t in range(num_teams) if TEAMS[t][1] == ADULT]

    model = cp_model.CpModel()

    x = [[[model.new_bool_var(f"x_{t}_{r}_{g}")
           for g in range(num_games)]
          for r in range(num_rounds)]
         for t in range(num_teams)]

    for t in range(num_teams):
        for g in range(num_games):
            model.add(sum(x[t][r][g] for r in range(num_rounds)) == 1)
        for r in range(num_rounds):
            model.add(sum(x[t][r][g] for g in range(num_games)) <= 1)

    for r in range(num_rounds):
        for g in range(num_games):
            model.add(sum(x[t][r][g] for t in range(num_teams)) == TEAMS_PER_GAME)

    mixed = [[model.new_bool_var(f"mixed_{r}_{g}")
              for g in range(num_games)]
             for r in range(num_rounds)]
    mixed_table = [(k, 1 if 0 < k < TEAMS_PER_GAME else 0) for k in range(TEAMS_PER_GAME + 1)]
    for r in range(num_rounds):
        for g in range(num_games):
            adult_count = model.new_int_var(0, TEAMS_PER_GAME, f"adult_count_{r}_{g}")
            model.add(adult_count == sum(x[t][r][g] for t in adult_indices))
            model.add_allowed_assignments([adult_count, mixed[r][g]], mixed_table)

    model.minimize(sum(mixed[r][g] for r in range(num_rounds) for g in range(num_games)))

    target = num_games if len(adult_indices) % TEAMS_PER_GAME != 0 else 0

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = rng.randrange(2**31)
    solver.parameters.max_time_in_seconds = SOLVER_TIME_LIMIT_SECONDS
    status = solver.solve(model, _StopAtObjective(target))
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    rounds = [
        [
            [TEAMS[t] for t in range(num_teams) if solver.value(x[t][r][g])]
            for g in range(num_games)
        ]
        for r in range(num_rounds)
    ]
    _validate_schedule(rounds)
    return rounds


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


def format_team(team):
    name, _ = team
    return name.replace("Team ", "T")


def cell_kind(teams):
    kinds = {kind for _, kind in teams}
    if len(kinds) == 1:
        return next(iter(kinds))
    return MIXED


def render_schedule(rounds, output_path="schema.png"):
    import matplotlib.pyplot as plt

    num_games = len(GAMES)
    num_rounds = len(rounds)

    col_labels = [""] + GAMES
    row_data = []
    cell_colors = []
    for i, round_row in enumerate(rounds, 1):
        row = [f"Round {i}"] + [", ".join(format_team(t) for t in teams) for teams in round_row]
        colors = [ROW_HEADER_COLOR] + [KIND_COLORS[cell_kind(teams)] for teams in round_row]
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
        colColours=[LABEL_COLOR] * (num_games + 1),
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.8)

    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(GRID_EDGE_COLOR)
        if r == 0 or c == 0:
            cell.set_text_props(weight="bold")

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    for i in range(10):
        rng = random.Random(i)
        schedule = build_schedule(rng)
        if schedule is None:
            continue
        path = render_schedule(schedule, f"schema-{i}.png")
        print(f"Wrote {path}")
