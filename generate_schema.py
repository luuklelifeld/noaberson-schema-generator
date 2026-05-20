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


PER_ROUND_TRIES = 50
MAX_OUTER_ATTEMPTS = 50


def build_schedule(rng):
    num_games = len(GAMES)
    slots_per_round = num_games * TEAMS_PER_GAME
    num_rounds = max(1, len(TEAMS) * num_games // slots_per_round)
    teams_pool = list(TEAMS)

    for _ in range(MAX_OUTER_ATTEMPTS):
        rng.shuffle(teams_pool)
        sit_outs = [set(teams_pool[i * 4:(i + 1) * 4]) for i in range(num_rounds)]

        history = {game: {team: False for team in TEAMS} for game in GAMES}
        rounds = []
        ok = True
        for r in range(num_rounds):
            playing = [t for t in TEAMS if t not in sit_outs[r]]
            best = None
            best_mixed = num_games + 1
            for _ in range(PER_ROUND_TRIES):
                m = _match_round(history, playing, num_games, rng)
                if m is None:
                    continue
                mixed = _count_mixed(m)
                if mixed < best_mixed:
                    best = m
                    best_mixed = mixed
                    if mixed == 0:
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


def _count_mixed(game_teams):
    return sum(1 for ts in game_teams.values() if len({t[1] for t in ts}) > 1)


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
