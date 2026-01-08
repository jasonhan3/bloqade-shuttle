from kirin import ir, rewrite
from kirin.dialects import func

from bloqade.shuttle.rewrite.schedule2path import Canonicalize

from .utils import assert_block_equal, sch


def test_canonicalize_do_nothing():

    callee_1 = ir.TestValue()
    callee_2 = ir.TestValue()
    input_1 = ir.TestValue()
    input_2 = ir.TestValue()

    test_block = ir.Block(
        [
            sch.auto(
                sch.parallel(
                    func.Call(callee_1, (input_1,), kwargs=(), keys=()),
                    sch.auto(func.Call(callee_1, (input_1,), kwargs=(), keys=())),
                ),
                sch.parallel(func.Call(callee_2, (input_2,), kwargs=(), keys=())),
            )
        ]
    )

    expected_block = ir.Block(
        [
            sch.auto(
                sch.parallel(
                    func.Call(callee_1, (input_1,), kwargs=(), keys=()),
                    sch.auto(func.Call(callee_1, (input_1,), kwargs=(), keys=())),
                ),
                sch.parallel(func.Call(callee_2, (input_2,), kwargs=(), keys=())),
            )
        ]
    )

    rewrite.Walk(Canonicalize()).rewrite(test_block)

    assert_block_equal(test_block, expected_block)


def test_canonicalize_flatten_auto():

    callee_1 = ir.TestValue()
    callee_2 = ir.TestValue()
    input_1 = ir.TestValue()
    input_2 = ir.TestValue()

    test_block = ir.Block(
        [
            sch.auto(
                sch.parallel(
                    func.Call(callee_1, (input_1,), kwargs=(), keys=()),
                    sch.parallel(func.Call(callee_1, (input_1,), kwargs=(), keys=())),
                ),
                sch.auto(
                    func.Call(callee_2, (input_2,), kwargs=(), keys=()),
                    func.Call(callee_1, (input_1,), kwargs=(), keys=()),
                ),
            )
        ]
    )

    expected_block = ir.Block(
        [
            sch.auto(
                sch.parallel(
                    func.Call(callee_1, (input_1,), kwargs=(), keys=()),
                    func.Call(callee_1, (input_1,), kwargs=(), keys=()),
                ),
                func.Call(callee_2, (input_2,), kwargs=(), keys=()),
                func.Call(callee_1, (input_1,), kwargs=(), keys=()),
            )
        ]
    )

    rewrite.Walk(Canonicalize()).rewrite(test_block)

    assert_block_equal(test_block, expected_block)
