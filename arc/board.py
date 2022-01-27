import collections

import numpy as np

from arc.comparisons import get_color_diff, get_order_diff, get_translation
from arc.util import logger
from arc.object import Object, ObjectDelta
from arc.processes import Process, MakeBase, ConnectObjects, SeparateColor
from arc.types import BoardData

log = logger.fancy_logger("Board", level=20)


class Board:
    """One 2D set of colored squares--the base unit of the ARC dataset.

    We use the recursive Object class to build a hierarchical representation
    of the Board that minimizes total properties used.

    Attributes:
        rep: The current representation of the Board via Objects.
        name: An auto-generated, descriptive name for the board.
        proc_q: A priority queue for holding decomposition candidates.
        bank: Any decompositions with no further possible operations.

    """

    def __init__(
        self, data: BoardData, name: str = "", processes: list[Process] = None
    ):
        self.name = name
        self.rep = Object.from_grid(grid=np.array(data))
        self.processes = processes or [MakeBase(), ConnectObjects(), SeparateColor()]

        # Used during decomposition process
        self.proc_q = collections.deque([self.rep])
        self.bank: list[Object] = []

    def select_representation(self) -> None:
        """Find the most compact representation from decomposition."""
        best_props = self.rep.props
        for obj in self.bank + list(self.proc_q):
            if obj.props < best_props:
                best_props = obj.props
                self.rep = obj.flatten()
                log.debug(f"Selected flattened object: {self.rep}")

    def decompose(self, batch: int = 10, max_iter: int = 10) -> None:
        """Determine the optimal representation of the Board.

        Args:
            batch: Number of candidates to keep each round. E.g. if batch=1, only the best
              candidate is retained.
            max_iter: Maximum number of iterations of decomposition.
        """
        for ct in range(max_iter):
            log.info(f"== Begin decomposition round {ct+1}")
            log.debug("  Processing queue:")
            for obj in self.proc_q:
                log.debug(f"  {obj}")
            self.batch_decomposition(batch=batch)
            log.info(f"== Decomposition at {self.rep.props}p after {ct+1} rounds")
            if not self.proc_q:
                log.info("==! Ending decomposition due to empty processing queue")
                break
        self.select_representation()
        self.rep.info("info")

    def batch_decomposition(self, batch: int = 10) -> None:
        """Decompose the top 'batch' candidates."""
        ct = 0
        while self.proc_q and ct < batch:
            ct += 1
            obj = self.proc_q.popleft()
            log.debug(f" = Batch item {ct}/{batch}")
            obj.info(level="debug")
            new_objs = self._decomposition(obj)
            if not new_objs:
                self.bank.append(obj.flatten())
            self.proc_q.extend(new_objs)
            log.debug(
                f" - Item {ct}, proc_q: {len(self.proc_q)}, bank: {len(self.bank)}"
            )
            self.select_representation()

    def _decomposition(self, obj: Object) -> list[Object]:
        """Attempts to find a more canonical or condensed way to represent the object"""
        # No children means nothing to simplify
        if len(obj.children) == 0:
            return []
        # Search for the first object that's not decomposed and apply decomposition
        # TODO Need to redo occlusion
        elif obj.traits.get("finished"):
            # NOTE: We run in reverse order to handle occlusion
            decompositions = []
            for rev_idx, child in enumerate(obj.children[::-1]):
                child_candidates = self._decomposition(child)
                if child_candidates:
                    # Each new decomposition needs a new top-level object
                    for new_child in child_candidates:
                        new_obj = obj.spawn()
                        new_obj.children[-(1 + rev_idx)] = new_child
                        decompositions.append(new_obj)
                    break
            return decompositions

        # TODO
        # Begin decomposition process:  check for existing context representations
        if check := find_closest(obj, [], threshold=0.75):
            # banked = check.right.spawn()
            pass

        candidates = self.generate_candidates(obj)
        for candidate in candidates:
            log.debug(f"  {candidate}")
        return candidates

    def generate_candidates(self, obj: Object) -> list[Object]:
        candidates: list[Object] = []
        for process in self.processes:
            if process.test(obj):
                candidate = process.run(obj)
                if candidate:
                    candidates.append(candidate)

        return candidates


default_comparisons = [get_order_diff, get_color_diff, get_translation]


def find_closest(
    obj: Object, inventory: list[Object], threshold: float = None
) -> ObjectDelta | None:
    if not inventory:
        return None
    match = ObjectDelta(obj, inventory[0], comparisons=default_comparisons)
    for source in inventory[1:]:
        delta = ObjectDelta(obj, source, comparisons=default_comparisons)
        if delta.dist < match.dist:
            match = delta
    if threshold is not None and match.dist > threshold:
        log.debug(f"{obj} No matches meeting threshold (best {match.dist})")
        return None
    log.info(f"{obj} Match! Distance: {match.dist}")
    return match
