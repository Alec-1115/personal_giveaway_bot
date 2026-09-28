import random


def select_winners(
    entries: set[int],
    winner_count: int
) -> list[int]:
    """
    Randomly select winners from the giveaway entries.

    Each user can only win once.
    If there are fewer entries than winners,
    everyone who entered wins.
    """

    entry_ids = list(entries)

    if not entry_ids:
        return []

    winner_count = min(
        winner_count,
        len(entry_ids)
    )

    return random.sample(
        entry_ids,
        winner_count
    )