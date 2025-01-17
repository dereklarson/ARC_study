import numpy as np
from arc.actions import Actions, chebyshev_vector
from arc.object import Object


def test_translations():
    """Test each action that translates an Object."""
    pt1 = Object(1, 1, 1)
    pt2 = Actions.Horizontal().act(pt1, 1)
    assert pt2 == Object(1, 2, 1)
    assert pt2 != pt1

    # 'Konami' test :) (up down left right is idempotent)
    pt3 = Actions.Horizontal.act(
        Actions.Horizontal.act(
            Actions.Vertical.act(Actions.Vertical.act(pt1, -1), 1), -1
        ),
        1,
    )
    assert pt3 == pt1

    # Zeroing should be equivalent to justifying each axis
    assert Actions.Zero.act(pt1) == Actions.Justify.act(Actions.Justify.act(pt1, 0), 1)

    # Tiling ops translate based on the object size
    group = Object(children=[Object(0, 0, 1), pt1])
    assert Actions.VTile.act(group, 1).loc == (2, 0)
    assert Actions.HTile.act(group, 1).loc == (0, 2)
    assert Actions.Tile.act(group, 1, 1) == Actions.VTile.act(Actions.HTile.act(group))


def test_deformations():
    """Test scaling, skewing, etc of Objects."""
    # If there's no generator, just return a copy of the original object
    pt1 = Object(1, 1, 1)
    assert Actions.Scale.act(pt1, 2, 0) == pt1

    square = Object(1, 1, 1, codes={"H": 4, "V": 4})

    flat = Actions.VScale.act(square, 3)
    assert flat.loc == (1, 1)
    assert flat.shape == (3, 5)

    thin = Actions.HScale.act(square, 3)
    assert thin.loc == (1, 1)
    assert thin.shape == (5, 3)

    assert Actions.Scale.act(Actions.Scale.act(square, 2, 0), 5, 0) == square


def test_orthogonal():
    input_grid = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    obj = Object.from_grid(input_grid)
    r90 = Object.from_grid(np.rot90(obj.grid))  # type: ignore
    r180 = Object.from_grid(np.rot90(r90.grid))  # type: ignore
    r270 = Object.from_grid(np.rot90(r180.grid))  # type: ignore
    vflip = Object.from_grid(np.flip(obj.grid, 0))  # type: ignore
    hflip = Object.from_grid(np.flip(obj.grid, 1))  # type: ignore
    diag1 = Object.from_grid(np.flip(r90.grid, 0))  # type: ignore
    diag2 = Object.from_grid(np.flip(r90.grid, 1))  # type: ignore

    assert r90 == Actions.Orthogonal.act(obj, 0, 1)
    assert r180 == Actions.Orthogonal.act(obj, 0, 2)
    assert r270 == Actions.Orthogonal.act(obj, 0, 3)
    assert vflip == Actions.Orthogonal.act(obj, 1, 0)
    assert hflip == Actions.Orthogonal.act(obj, 2, 0)
    assert diag1 == Actions.Orthogonal.act(obj, 1, 3)
    assert diag2 == Actions.Orthogonal.act(obj, 1, 1)

    assert r90 == Actions.Orthogonal.act(obj, *Actions.Orthogonal.inv(obj, r90))  # type: ignore
    assert r180 == Actions.Orthogonal.act(obj, *Actions.Orthogonal.inv(obj, r180))  # type: ignore
    assert r270 == Actions.Orthogonal.act(obj, *Actions.Orthogonal.inv(obj, r270))  # type: ignore
    assert vflip == Actions.Orthogonal.act(obj, *Actions.Orthogonal.inv(obj, vflip))  # type: ignore
    assert hflip == Actions.Orthogonal.act(obj, *Actions.Orthogonal.inv(obj, hflip))  # type: ignore
    assert diag1 == Actions.Orthogonal.act(obj, *Actions.Orthogonal.inv(obj, diag1))  # type: ignore
    assert diag2 == Actions.Orthogonal.act(obj, *Actions.Orthogonal.inv(obj, diag2))  # type: ignore


def test_rotation():
    """Test object rotation."""
    # Rotating a point should yield itself
    pt1 = Object(1, 1, 1)
    assert Actions.Rotate.act(pt1, 1) == pt1

    # A monocolor line is symmetric under 180 deg rotation
    blue_line = Object(children=[Object(0, 0, 1), Object(1, 0, 1), Object(2, 0, 1)])
    assert Actions.Rotate.act(blue_line, 1).shape == (1, 3)
    assert Actions.Rotate.act(blue_line, 2) == blue_line

    composite = Object(children=[blue_line, pt1])
    assert Actions.Rotate.act(composite, 1).shape == (2, 3)
    assert Actions.Rotate.act(composite, 2).shape == (3, 2)
    assert Actions.Rotate.act(composite, 2) != composite
    assert Actions.Rotate.act(composite, 4) == composite


def test_reflection():
    """Test reflecting the Object over an axis."""
    pt1 = Object(1, 1, 1)
    assert Actions.VFlip.act(pt1) == pt1
    assert Actions.HFlip.act(pt1) == pt1

    group = Object(children=[Object(0, 0, 2), pt1])

    h_true_points = {(0, 1): 2, (1, 0): 1}
    assert Actions.HFlip.act(group).points == h_true_points

    v_true_points = {(0, 1): 1, (1, 0): 2}
    assert Actions.VFlip.act(group).points == v_true_points


def test_color():
    pt1 = Object(1, 1, 1)
    assert Actions.Paint.act(pt1, 2).color == 2
    assert Actions.Paint.act(Actions.Paint.act(pt1, 0), 1) == pt1


def test_resize():
    obj1 = Object(codes={"V": 5, "H": 3})
    obj2 = Object(2, 1, codes={"V": 1, "H": 1})
    obj3 = Object(codes={"V": 1, "H": 1})
    assert Actions.Resize.act(obj1, obj2) == obj3

    obj4 = Object(1, 5, codes={"V": 5, "H": 1})
    obj5 = Object(codes={"V": 5, "H": 1})
    assert Actions.Resize.act(obj1, obj4) == obj5

    obj6 = Object(codes={"V": 3, "H": 3})
    obj7 = Object(codes={"V": 3, "H": 3})
    assert Actions.Resize.act(obj1, obj6) == obj7


def test_chebyshev():
    obj1 = Object(5, 5, codes={"V": 2, "H": 3})
    obj2 = Object(2, 1, codes={"V": 1, "H": 1})
    assert chebyshev_vector(obj2, obj1) == (1, 0)
    assert chebyshev_vector(obj1, obj2) == (-1, 0)

    obj3 = Object(2, 1, codes={"V": 5, "H": 1})
    assert chebyshev_vector(obj3, obj1) == (0, 2)
    assert chebyshev_vector(obj1, obj3) == (0, -2)

    obj4 = Object(4, 4, codes={"V": 1, "H": 2})
    assert chebyshev_vector(obj1, obj4) == (0, 0)
    assert chebyshev_vector(obj4, obj1) == (0, 0)

    obj5 = Object(10, 1)
    assert chebyshev_vector(obj5, obj1) == (-2, 0)
    assert chebyshev_vector(obj1, obj5) == (2, 0)

    obj6 = Object(10, 10)
    assert chebyshev_vector(obj6, obj1) == (0, -1)
    assert chebyshev_vector(obj1, obj6) == (0, 1)

    obj7 = Object(
        10,
        6,
        codes={
            "H": 6,
        },
    )
    assert chebyshev_vector(obj7, obj1) == (-2, 0)
    assert chebyshev_vector(obj1, obj7) == (2, 0)


def test_adjoin():
    obj1 = Object(5, 5, codes={"V": 2, "H": 3})
    obj2 = Object(2, 1, codes={"V": 1, "H": 1})
    assert Actions.Adjoin.act(obj2, obj1) == Actions.Vertical.act(obj2, 1)

    obj3 = Object(10, 10)
    assert Actions.Adjoin.act(obj3, obj1) == Actions.Horizontal.act(obj3, -1)


def test_align():
    obj1 = Object(5, 5, codes={"V": 2, "H": 3})
    obj2 = Object(2, 1, codes={"V": 1, "H": 1})
    assert Actions.Align.act(obj2, obj1) == Actions.Vertical.act(obj2, 3)

    obj3 = Object(2, 3)
    assert Actions.Align.act(obj3, obj1) == Actions.Horizontal.act(obj3, 2)
