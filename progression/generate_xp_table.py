import json
import math
from pathlib import Path


X = 100
Y = 1.8
LEVEL_MAX = 100


def java_round(value: float) -> int:
    return int(math.floor(value + 0.5))


def required_xp(current_level: int) -> int:
    return X * java_round(math.pow(current_level, Y))


def build_xp_table() -> list[dict[str, int]]:
    return [
        {"level": level, "required_xp": required_xp(level)}
        for level in range(1, LEVEL_MAX + 1)
    ]


def main() -> None:
    output_path = Path(__file__).resolve().parent /  "xp_table.json"
    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(build_xp_table(), file_handle, indent=2)
        file_handle.write("\n")


if __name__ == "__main__":
    main()