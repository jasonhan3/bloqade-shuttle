from typing import cast

from kirin import ir
from kirin.analysis import const, forward
from kirin.interp import MethodTable, impl

from bloqade.shuttle.codegen import TraceInterpreter, reverse_path
from bloqade.shuttle.dialects import schedule
from bloqade.shuttle.dialects.path import dialect, stmts, types


@dialect.register(key="constprop")
class ConstProp(MethodTable):

    @impl(stmts.Gen)
    def gen(
        self,
        interp: const.Propagate,
        frame: forward.ForwardFrame[const.Result],
        stmt: stmts.Gen,
    ):
        if stmt.arch_spec is None:
            return (const.Result.top(),)

        device_task_prop = frame.get(stmt.device_task)
        if not isinstance(device_task_prop, const.Value):
            return (const.Result.top(),)

        if isinstance(device_task := device_task_prop.data, schedule.DeviceFunction):
            reverse = False
        elif isinstance(device_task, schedule.ReverseDeviceFunction):
            device_task = device_task.device_task
            reverse = True
        else:
            return (const.Result.top(),)

        inputs_results = list(frame.get_values(stmt.inputs))

        if not all(isinstance(input_, const.Value) for input_ in inputs_results):
            return (const.Result.top(),)

        trait = device_task.move_fn.code.get_trait(ir.CallableStmtInterface)
        if trait is None:
            return (const.Result.top(),)
        if stmt.kwargs:
            kw_count = len(stmt.kwargs)
            kw_values = inputs_results[-kw_count:]
            inputs_results = inputs_results[:-kw_count]
            kwargs = dict(zip(stmt.kwargs, kw_values))
        else:
            kwargs = {}
        args = trait.align_input_args(
            device_task.move_fn.code, *inputs_results, **kwargs
        )

        path = TraceInterpreter(stmt.arch_spec).run_trace(
            device_task.move_fn,
            tuple(
                cast(const.Value, arg).data if isinstance(arg, const.Value) else arg
                for arg in args
            ),
            {},
        )

        if reverse:
            path = reverse_path(path)

        return (
            const.Value(
                types.Path(
                    x_tones=device_task.x_tones,
                    y_tones=device_task.y_tones,
                    path=path,
                )
            ),
        )
