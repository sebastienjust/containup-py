import re

MAX_DURATION_NS = 168 * 3600 * 1_000_000_000  # one week, to avoid overflows


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
    pattern = re.compile(r"^(\d+)([a-zµ]+)$")
    match = pattern.match(value.strip())
    if not match:
        raise ValueError(f"Invalid duration format: '{value}'")

    number_as_unsafe_string, unit = match.groups()
    if unit not in units:
        raise ValueError(f"Unknown unit: '{unit}'")

    # Avoid overflows
    number = int(number_as_unsafe_string) * units[unit]
    if number > MAX_DURATION_NS:
        raise ValueError(
            f"Duration too large: {number_as_unsafe_string}{unit} ({number}ns). max is {MAX_DURATION_NS}ns"
        )

    return number


def duration_to_seconds(value: str) -> float:
    return (duration_to_nano(value) * 1.0) / 1_000_000_000
