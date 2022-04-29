"""The ARC tasks are drawn from a broad domain, which includes many concepts
such 2D transformations, symmetry, relational logic, kinematics, and others.
If we break down the body of tasks by labelling them with certain 'traits',
we can divide and conquer the problem.
"""

from arc.task import Task


class TaskTraits:
    methods: list[str] = ["color_ct", "const_size", "size", "tiled", "from_paper"]

    @classmethod
    def color_ct(cls, task: Task) -> None:
        colors = [0] * 10
        for scene in task.cases:
            for color, _ in scene.input.rep.c_rank:
                colors[color] = 1
            for color, _ in scene.output.rep.c_rank:
                colors[color] = 1
        label = sum(colors)
        if label > 5:
            label = "many"
        task.traits.add(f"{label}-color")

    @classmethod
    def const_size(cls, task: Task) -> None:
        if all(
            [scene.input.rep.shape == scene.output.rep.shape for scene in task.cases]
        ):
            task.traits.add("constant_size")

    @classmethod
    def size(cls, task: Task) -> None:
        small, large = 36, 225  # e.g. 6x6 and 15x15
        if all([scene.input.rep.size <= small for scene in task.cases]) and all(
            [scene.output.rep.size <= small for scene in task.cases]
        ):
            task.traits.add("small")
        elif all([scene.input.rep.size >= large for scene in task.cases]) or all(
            [scene.output.rep.size >= large for scene in task.cases]
        ):
            task.traits.add("large")

    @classmethod
    def tiled(cls, task: Task) -> None:
        threshold = 0.95
        # Test if either all inputs or outputs have high ordering
        ordered = False
        for scene in task.cases:
            rows, row_order = scene.input.rep.order_trans_row
            cols, col_order = scene.input.rep.order_trans_col
            if rows == 1 and cols == 1:
                continue
            elif row_order < threshold and col_order < threshold:
                ordered = False
                break
            else:
                ordered = True
        if ordered:
            task.traits.add("tiled")
            return

        for scene in task.cases:
            rows, row_order = scene.output.rep.order_trans_row
            cols, col_order = scene.output.rep.order_trans_col
            if rows == 1 and cols == 1:
                continue
            elif row_order < threshold and col_order < threshold:
                ordered = False
                break
            else:
                ordered = True

        if ordered:
            task.traits.add("tiled")
        return

    @classmethod
    def from_paper(cls, task: Task) -> None:
        # Tasks solved in Sebastien Ferre's paper using MDL
        ferre_idxs = {
            10,
            28,
            31,
            36,
            47,
            53,
            100,
            111,
            128,
            129,
            153,
            156,
            171,
            174,
            192,
            222,
            245,
            253,
            254,
            261,
            263,
            267,
            276,
            290,
            293,
            294,
            298,
            299,
            300,
            354,
            362,
            373,
            374,
        }

        # Tasks mentioned the Alford thesis that mostly involve simple transforms
        alford_idxs = {
            83,
            87,
            106,
            116,
            140,
            142,
            150,
            152,
            154,
            172,
            179,
            210,
            211,
            241,
            249,
            311,
            380,
        }

        if task.idx in ferre_idxs:
            task.traits.add("mdl")

        if task.idx in alford_idxs:
            task.traits.add("dreamcoder")
