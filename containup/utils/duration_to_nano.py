import re


def duration_to_nano(value: str) -> int:
    units = {
        "ns": 1,
        "us": 1_000,
        "µs": 1_000,  # alias Go
        "ms": 1_000_000,
        "s": 1_000_000_000,
        "m": 60 * 1_000_000_000,
        "h": 3600 * 1_000_000_000,
    }
    pattern = re.compile(r"^(\d+(?:\.\d+)?)([a-zµ]+)$", re.IGNORECASE)
    match = pattern.match(value.strip())
    if not match:
        raise ValueError(f"Invalid duration format: '{value}'")

    number, unit = match.groups()
    if unit not in units:
        raise ValueError(f"Unknown unit: '{unit}'")

    return int(float(number) * units[unit])
