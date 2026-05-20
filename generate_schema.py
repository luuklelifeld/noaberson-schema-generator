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


def build_schedule():
    import random

    rng = random.Random(SEED)

    num_games = len(GAMES)
    adults = [name for name, kind in TEAMS if kind == ADULT]
    non_adults = [name for name, kind in TEAMS if kind == NON_ADULT]

    slots_per_round = num_games * TEAMS_PER_GAME
    num_rounds = max(1, len(TEAMS) * num_games // slots_per_round)

    if adults and non_adults:
        adult_games = round(len(adults) / len(TEAMS) * num_games)
        adult_games = max(1, min(num_games - 1, adult_games))
    elif adults:
        adult_games = num_games
    else:
        adult_games = 0
    non_adult_games = num_games - adult_games

    adult_slots_per_round = adult_games * TEAMS_PER_GAME
    non_adult_slots_per_round = non_adult_games * TEAMS_PER_GAME

    adult_play_count = {t: 0 for t in adults}
    non_adult_play_count = {t: 0 for t in non_adults}

    rounds = []
    for r in range(num_rounds):
        adult_lineup = pick_lineup(
            adults, non_adults, adult_play_count, non_adult_play_count,
            adult_slots_per_round, ADULT, rng,
        )
        non_adult_lineup = pick_lineup(
            non_adults, adults, non_adult_play_count, adult_play_count,
            non_adult_slots_per_round, NON_ADULT, rng,
        )

        round_row = []
        for g in range(adult_games):
            start = g * TEAMS_PER_GAME
            round_row.append(adult_lineup[start : start + TEAMS_PER_GAME])
        for g in range(non_adult_games):
            start = g * TEAMS_PER_GAME
            round_row.append(non_adult_lineup[start : start + TEAMS_PER_GAME])
        rounds.append(round_row)
    return rounds


def pick_lineup(primary, fallback, primary_counts, fallback_counts, slots, primary_kind, rng):
    fallback_kind = NON_ADULT if primary_kind == ADULT else ADULT
    lineup = []

    if not primary:
        chosen = sorted(fallback, key=lambda t: (fallback_counts[t], rng.random()))[:slots]
        rng.shuffle(chosen)
        for t in chosen:
            lineup.append((t, fallback_kind))
            fallback_counts[t] += 1
        return lineup

    take_primary = min(slots, len(primary))
    primary_chosen = sorted(primary, key=lambda t: (primary_counts[t], rng.random()))[:take_primary]
    for t in primary_chosen:
        primary_counts[t] += 1

    surplus = slots - take_primary
    fallback_chosen = []
    if surplus:
        fallback_chosen = sorted(fallback, key=lambda t: (fallback_counts[t], rng.random()))[:surplus]
        for t in fallback_chosen:
            fallback_counts[t] += 1

    tagged = [(t, primary_kind) for t in primary_chosen] + [(t, fallback_kind) for t in fallback_chosen]
    rng.shuffle(tagged)
    return tagged


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
    "mixed": "#e6ccff",
}


def render_schedule(rounds, output_path="schema.png"):
    import matplotlib.pyplot as plt

    num_games = len(GAMES)
    num_rounds = len(rounds)

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
    path = render_schedule(build_schedule())
    print(f"Wrote {path}")
