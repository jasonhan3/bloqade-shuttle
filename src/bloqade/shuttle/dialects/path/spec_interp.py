from kirin import ir
from kirin.interp import (
    Frame,
    InterpreterError,
    MethodTable,
    impl,
)

from bloqade.shuttle.arch import ArchSpecInterpreter
from bloqade.shuttle.codegen import TraceInterpreter, reverse_path
from bloqade.shuttle.dialects import schedule
from bloqade.shuttle.dialects.path import dialect, stmts, types


@dialect.register(key="spec.interp")
class SpecPathInterpreter(MethodTable):

    @impl(stmts.Gen)
    def gen(self, interp: ArchSpecInterpreter, frame: Frame, stmt: stmts.Gen):

        device_task = frame.get(stmt.device_task)
        if isinstance(device_task, schedule.DeviceFunction):
            reverse = False
        elif isinstance(device_task, schedule.ReverseDeviceFunction):
            device_task = device_task.device_task
            reverse = True
        else:
            raise InterpreterError("Invalid device task type")

        inputs = list(frame.get_values(stmt.inputs))
        trait = device_task.move_fn.code.get_trait(ir.CallableStmtInterface)
        if trait is None:
            raise InterpreterError("Device function is not callable")
        if stmt.kwargs:
            kw_count = len(stmt.kwargs)
            kw_values = inputs[-kw_count:]
            inputs = inputs[:-kw_count]
            kwargs = dict(zip(stmt.kwargs, kw_values))
        else:
            kwargs = {}
        args = trait.align_input_args(device_task.move_fn.code, *inputs, **kwargs)
        path = TraceInterpreter(interp.arch_spec).run_trace(
            device_task.move_fn, args, {}
        )

        if reverse:
            path = reverse_path(path)

        return (
            types.Path(
                x_tones=device_task.x_tones,
                y_tones=device_task.y_tones,
                path=path,
            ),
        )
