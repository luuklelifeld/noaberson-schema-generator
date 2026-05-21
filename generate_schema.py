import csv
import random

from ortools.sat.python import cp_model

GAMES = [
    "Salty potato in the hole", 
    "Pony Polo", 
    "Straat van Hormuz", 
    "Red Claes Compaen", 
    "Nick's weekendspecial", 
    "Danoontje Powerrrrr", 
    "Kamelenrace", 
    "XXL Memory"
]
TEAMS = [
    ("Grolschgenoten", "non-adult"),
    ("De Barry's", "non-adult"),
    ("Zwartn Labradors", "non-adult"),
    ("Harde Kern", "non-adult"),
    ("The Flying Taco's", "non-adult"),
    ("Biercelona", "non-adult"),
    ("Aanhangers United", "adult"),
    ("Multifunctioneel", "adult"),
    ("Hennie Halfgas", "non-adult"),
    ("Team Jawel", "non-adult"),
    ("Bier Maatjes", "non-adult"),
    ("Online Kater", "adult"),
    ("Picobello.bv", "non-adult"),
    ("Waar is Lucas Broek?", "adult"),
    ("De Wasmachine's", "non-adult"),
    ("De Befbössels", "adult"),
    ("Plonsploeg Noabergirls en de Romeo's", "adult"),
    ("Bananenbende", "adult"),
    ("Bruh", "non-adult"),
    ("Spice Girls 2.0", "non-adult"),
    ("The Resurrection of the Return of the Revivial of Zeem and the Wankers", "adult"),
    ("Noaberson Legends", "adult"),
    ("Ties Mulder", "adult"),
    ("Liever Dood dan Tweede", "adult"),
    ("Meiden", "adult"),
    ("De Dinnies", "adult"),
    ("Daphne Mentink", "non-adult"),
    ("Bierbabes", "non-adult"),
    ("Adtje Kratje", "adult"),
    ("Poederpinda", "adult"),
    ("Geil", "adult"),
    ("Dankzij Jasper en Daan", "adult"),
    ("Flip Fluitketel", "adult"),
    ("Khz", "adult"),
    ("False Positivity", "adult"),
    ("Ernst, Bobbie en de groep is verpest", "adult"),
    ("Defietsenfamilie", "adult"),
    ("Team 38", "adult"),
    ("Team 39", "adult"),
    ("Team 40", "adult"),
]
TEAMS_PER_GAME = 4

ADULT = "adult"
NON_ADULT = "non-adult"

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
        missing = [team[0] for team in TEAMS if team not in seen_in_round]
        print(f"round {r_idx + 1} does not contain teams: {missing}")

    for g_idx, game_name in enumerate(GAMES):
        teams_in_column = [t for rnd in rounds for t in rnd[g_idx]]
        assert len(teams_in_column) == len(teams_set), \
            f"{game_name} has {len(teams_in_column)} entries, expected {len(teams_set)}"
        assert set(teams_in_column) == teams_set, \
            f"{game_name} missing teams {teams_set - set(teams_in_column)} or duplicates {[t for t in teams_in_column if teams_in_column.count(t) > 1]}"


def format_team(team):
    name, _ = team
    return name.replace("Team ", "T")


def _break_rows_for_round(round_row):
    playing = {team for game_teams in round_row for team in game_teams}
    idle = [team for team in TEAMS if team not in playing]
    return [idle[i:i + TEAMS_PER_GAME] for i in range(0, len(idle), TEAMS_PER_GAME)]


def render_schedule(rounds, output_path="schema.png"):
    import matplotlib.pyplot as plt

    num_cols = 1 + TEAMS_PER_GAME
    num_games = len(GAMES)
    num_rounds = len(rounds)

    blocks = []
    for round_row in rounds:
        break_rows = _break_rows_for_round(round_row)
        blocks.append((round_row, break_rows))

    rows_per_block = [1 + num_games + len(br) for _, br in blocks]
    height_ratios = rows_per_block

    fig_w = 20
    fig_h = sum(rows_per_block) * 0.45 + num_rounds * 0.3
    fig, axes = plt.subplots(
        num_rounds, 1,
        figsize=(fig_w, fig_h),
        gridspec_kw={"height_ratios": height_ratios},
    )
    if num_rounds == 1:
        axes = [axes]

    for ax, (round_idx, (round_row, break_rows)) in zip(axes, enumerate(blocks, 1)):
        ax.axis("off")

        cell_text = []
        cell_colors = []

        header_row = [f"Round {round_idx}"] + [""] * (num_cols - 1)
        cell_text.append(header_row)
        cell_colors.append([LABEL_COLOR] * num_cols)

        for game_name, teams in zip(GAMES, round_row):
            cell_text.append([game_name] + [format_team(t) for t in teams])
            cell_colors.append([ROW_HEADER_COLOR] + ["white"] * (num_cols - 1))

        for break_idx, chunk in enumerate(break_rows):
            label = "Pauze" if break_idx == 0 else ""
            padded = [format_team(t) for t in chunk] + [""] * (TEAMS_PER_GAME - len(chunk))
            cell_text.append([label] + padded)
            cell_colors.append([ROW_HEADER_COLOR] + ["white"] * (num_cols - 1))

        table = ax.table(
            cellText=cell_text,
            cellColours=cell_colors,
            cellLoc="center",
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 1.6)

        for (r, c), cell in table.get_celld().items():
            cell.set_edgecolor(GRID_EDGE_COLOR)
            if r == 0 or c == 0:
                cell.set_text_props(weight="bold")

    fig.subplots_adjust(hspace=0.4)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def write_csv(rounds, output_path="schema.csv"):
    num_cols = 1 + TEAMS_PER_GAME
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        for round_idx, round_row in enumerate(rounds, 1):
            writer.writerow([f"Round {round_idx}"] + [""] * (num_cols - 1))
            for game_name, teams in zip(GAMES, round_row):
                writer.writerow([game_name] + [format_team(t) for t in teams])
            for break_idx, chunk in enumerate(_break_rows_for_round(round_row)):
                label = "Break" if break_idx == 0 else ""
                padded = [format_team(t) for t in chunk] + [""] * (TEAMS_PER_GAME - len(chunk))
                writer.writerow([label] + padded)
            writer.writerow([""] * num_cols)
    return output_path


if __name__ == "__main__":
    for i in range(1):
        rng = random.Random(i)
        schedule = build_schedule(rng)
        if schedule is None:
            continue
        png_path = render_schedule(schedule, f"schema-{i}.png")
        csv_path = write_csv(schedule, f"schema-{i}.csv")
        print(f"Wrote {png_path} and {csv_path}")
