"""Verify that 8-number polygons from a model are rectangles (DOTA rotated boxes).

Usage: python check_rectangle.py '[[x1,y1,x2,y2,x3,y3,x4,y4], ...]'
Prints one line per polygon: index, ok/skewed. Requires `annotools` (pip install annotools).
"""

import json
import sys

from annotools.geometry import is_rectangle


def main(argv: list[str]) -> int:
    polygons = json.loads(argv[1])
    bad = 0
    for index, points in enumerate(polygons):
        ok = is_rectangle(points, angle_tol_deg=2.0, length_tol=0.02)
        bad += not ok
        print(f"{index}\t{'ok' if ok else 'skewed'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
