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


def build_schedule(rng):
    history = {game: {team: False for team in TEAMS} for game in GAMES}
    num_games = len(GAMES)

    slots_per_round = num_games * TEAMS_PER_GAME
    num_rounds = max(1, len(TEAMS) * num_games // slots_per_round)

    rounds = []
    for _ in range(num_rounds):
        teams_picked_this_round = []
        round_row = []
        for game in GAMES:
            picked_teams = pick_teams(game, history, teams_picked_this_round, rng)
            if picked_teams:
                teams_picked_this_round.extend(picked_teams);
                round_row.append(picked_teams)
            else:
                round_row.append([('fake', 'adult'), ('fake', 'adult'), ('fake', 'adult'), ('fake', 'adult')])
        rounds.append(round_row)

    return rounds

def pick_teams(game_name, history, teams_picked_this_round, rng):
    available_teams = [team for team in history[game_name].keys() if history[game_name][team] == False]
    available_teams = [team for team in available_teams if team not in teams_picked_this_round]

    try:
        first_team = rng.choice(available_teams);
    except:
        return
    available_teams.remove(first_team)
    history[game_name][first_team] = True

    team_age = first_team[1]
    available_teams_same_age = [team for team in available_teams if team[1] == team_age]

    # Pick from the same age group if enough same-age-group teams are available to fill the game
    if (len(available_teams_same_age) >= 3):
        available_teams = available_teams_same_age

    picked_teams = [first_team]

    for _ in range(3):
        try:
            picked_team = rng.choice(available_teams)
            available_teams.remove(picked_team)
            history[game_name][picked_team] = True
            picked_teams.append(picked_team)
        except:
            pass

    return picked_teams


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
        path = render_schedule(build_schedule(rng), f"schema-{i}.png")
        if path != "skipped":
            print(f"Wrote {path}")
