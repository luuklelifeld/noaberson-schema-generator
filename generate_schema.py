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
    ("Team 8", "adult"),
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
    ("Team 19", "adult"),
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
    ("Team 37", "non-adult"),
    ("Team 38", "adult"),
    ("Team 39", "adult"),
    ("Team 40", "non-adult"),
]
TEAMS_PER_GAME = 4
SEED = 42

ADULT = "adult"
NON_ADULT = "non-adult"

games_seen_history = {game: {team: False for team, _ in TEAMS} for game in GAMES}
rng = random.Random(SEED)

def build_schedule():
    num_games = len(GAMES)

    slots_per_round = num_games * TEAMS_PER_GAME
    num_rounds = max(1, len(TEAMS) * num_games // slots_per_round)

    rounds = []
    for round in range(num_rounds):
        round_row = []
        for game in GAMES:
            team_one = pick_team(game);
            team_two = pick_team(game);
            team_three = pick_team(game);
            team_four = pick_team(game);

            round_row.append([team_one, team_two, team_three, team_four])
        rounds.append(round_row)

    return rounds

def pick_team(game_name):
    random_team = rng.choice(TEAMS);
    if (games_seen_history[game_name][random_team[0]] == False):
        random_team = rng.choice(TEAMS);

    games_seen_history[game_name][random_team[0]] = True
    return random_team;

def format_team(team):
    print(team)
    name, _ = team
    return name.replace("Team ", "T")


def cell_kind(teams):
    kinds = {kind for _, kind in teams}
    print(kinds)
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

    col_labels = [""] + GAMES
    row_data = []
    cell_colors = []
    for i, round_row in enumerate(rounds, 1):
        print(round_row)
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
    path = render_schedule(build_schedule())
    print(f"Wrote {path}")
