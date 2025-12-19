import asyncio
import multiprocessing

from statemachine import State
from statemachine import StateMachine


class AsyncTrafficLight(StateMachine):
    green = State(initial=True)
    yellow = State()
    red = State()

    cycle = green.to(yellow) | yellow.to(red) | red.to(green)

    def __init__(self):
        self.calls = []
        super().__init__()

    async def on_enter_state(self, state):
        await asyncio.sleep(0.01)
        self.calls.append(f"enter_{state.id}")


def run_async_sm(sm, result_queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def work():
        # If the machine was not activated in the parent, we activate it here.
        await sm.activate_initial_state()
        await sm.cycle()
        await sm.cycle()
        return sm.current_state.id, sm.calls

    try:
        result = loop.run_until_complete(work())
        result_queue.put(result)
    except Exception as e:
        result_queue.put(e)


def test_multiprocessing_execution():
    # Use spawn to ensure we test pickling across processes properly
    ctx = multiprocessing.get_context("spawn")

    sm = AsyncTrafficLight()
    # Do not activate in parent

    queue = ctx.Queue()
    p = ctx.Process(target=run_async_sm, args=(sm, queue))
    p.start()
    p.join()

    assert p.exitcode == 0

    result = queue.get()
    if isinstance(result, Exception):
        raise result

    final_state_id, calls = result
    assert final_state_id == "red"
    assert calls == ["enter_green", "enter_yellow", "enter_red"]
