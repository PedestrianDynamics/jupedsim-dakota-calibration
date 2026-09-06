"""Read named parameters from Dakota's best-point report."""
import pathlib
import re
import sys


def best_parameters(path):
    text = pathlib.Path(path).read_text()
    match = re.search(
        r"Best parameters\s*=\s*\n((?:\s*\S+\s+\S+\n)+)",
        text,
    )
    if match is None:
        raise ValueError(f"no best parameters found in {path}")
    return {
        line.split()[1]: float(line.split()[0])
        for line in match.group(1).strip().splitlines()
    }


if __name__ == "__main__":
    parameters = best_parameters(sys.argv[1])
    print(" ".join(str(parameters[name]) for name in sys.argv[2:]))
