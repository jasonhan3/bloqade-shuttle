from bloqade.geometry.dialects import grid

from bloqade.shuttle import spec
from bloqade.shuttle.passes import inject_spec
from bloqade.shuttle.prelude import move


def get_spec(slm_grid: grid.Grid) -> spec.ArchSpec:
    return spec.ArchSpec(
        layout=spec.Layout(
            {"slm": slm_grid},
            fillable=set(["slm"]),
            has_cz=set(["slm"]),
            has_local=set(["slm"]),
        )
    )


def test_inject_spec():
    slm_grid = grid.Grid.from_positions([1, 2, 3], [4, 5, 6])
    test_spec = get_spec(slm_grid)

    @move(arch_spec=test_spec)
    def test():
        return spec.get_static_trap(zone_id="slm")

    assert (
        test() == slm_grid
    ), "The injected static trap should match the expected grid."


def test_inject_spac_callgraph():
    slm_grid = grid.Grid.from_positions([1, 2, 3], [4, 5, 6])
    test_spec = get_spec(slm_grid)

    @move
    def leaf():
        return spec.get_static_trap(zone_id="slm")

    @move
    def subroutine(depth: int):
        result = leaf()
        if depth >= 1:
            result = leaf()
        return result

    @move
    def test():
        return subroutine(0)

    inject_spec.InjectSpecsPass(move, arch_spec=test_spec, fold=False)(test)

    test.verify_type()

    assert (
        test() == slm_grid
    ), "The injected static trap should match the expected grid."


def test_inject_constants():
    test_spec = spec.ArchSpec(
        int_constants={"my_int": 42},
        float_constants={"my_float": 3.14},
    )

    @move(arch_spec=test_spec)
    def test():
        return spec.get_int_constant(constant_id="my_int"), spec.get_float_constant(
            constant_id="my_float"
        )

    assert test() == (
        42,
        3.14,
    ), "The injected constants should match the expected values."
