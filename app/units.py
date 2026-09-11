COPPER_PER_GOLD = 10_000


def copper_to_gold(copper: int) -> int:
    return copper // COPPER_PER_GOLD
