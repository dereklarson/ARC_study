from typing import Any
import numpy as np

from arc.definitions import Constants as cst
from arc.util import logger
from arc.object import Object

log = logger.fancy_logger("Comparisons", level=30)


def get_order_diff(left: Object, right: Object) -> tuple[int, dict[str, Any]]:
    """Checks for differences in the arrangement of points"""
    log.debug("Comparing Order")
    dist: int = 0
    transform: dict[str, Any] = {}
    if len(left.c_rank) == 1 and len(right.c_rank) == 1:
        # A monochrome, matching silhouette means no internal positioning differences
        if left.sil(right):
            log.debug("  Sillhouettes match")
            return dist, transform

    # Without a matching silhouette, only an ordered transformation works here
    # NOTE Including flooding and similar ops will change this
    if left.order[2] != 1 or right.order[2] != 1:
        return cst.MAX_DIST, transform
    else:
        # There could exist one or more generators to create the other object
        for axis, code in [(0, "R"), (1, "C")]:
            if left.shape[axis] != right.shape[axis]:
                ct = left.shape[axis]
                # ct = max(left.shape[axis] // right.shape[axis],
                #          right.shape[axis] // left.shape[axis])
                scaler = "f" if code == "R" else "p"
                transform[scaler] = ct - 1
                dist += 2
        return dist, transform


def get_color_diff(left: Object, right: Object) -> tuple[int, dict[str, Any]]:
    log.debug("Comparing Color")
    dist: int = 0
    transform: dict[str, Any] = {}
    c1 = set([item[0] for item in left.c_rank])
    c2 = set([item[0] for item in right.c_rank])
    if c1 != c2:
        # Color remapping is a basic transform
        if len(c1) == 1 and len(c2) == 1:
            transform["c"] = list(c1)[0]
            dist += 2
        # However, partial or multiple remapping is not
        else:
            dist = cst.MAX_DIST
    return dist, transform


def get_translation(left: Object, right: Object) -> tuple[int, dict[str, Any]]:
    log.debug("Comparing Position")
    dist: int = 0
    transform: dict[str, Any] = {}
    r1, c1 = left.loc
    r2, c2 = right.loc
    # NOTE Consider using center vs corner for this measure
    if r1 == r2 and c1 == c2:
        return dist, transform
    # Check for zeroing, which is special
    if r1 == 0 and c1 == 0:
        dist += 1
        transform["z"] = 0
    elif r2 != r1:
        # Justifying a single dimension is also special
        if r1 == 0:
            dist += 1
            transform["j"] = 0
        else:
            dist += 2
            transform["w"] = r1 - r2
    elif c2 != c1:
        if c1 == 0:
            dist += 1
            transform["j"] = 1
        else:
            dist += 2
            transform["s"] = c1 - c2
    return dist, transform
