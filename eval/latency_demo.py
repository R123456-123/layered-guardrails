import asyncio, time
from app.guards.injection import InjectionGuard
from app.guards.pii import PIIGuard
from app.guards.topic import TopicGuard
from app.pipeline import run_input_guards

guards = [InjectionGuard(delay_ms=50), PIIGuard(delay_ms=50), TopicGuard(["x"], delay_ms=50)]

async def main():
    for parallel in (False, True):
        t = time.perf_counter()
        await run_input_guards("hello there", guards, parallel=parallel)
        print(f"parallel={parallel}: {(time.perf_counter()-t)*1000:.0f} ms")

asyncio.run(main())