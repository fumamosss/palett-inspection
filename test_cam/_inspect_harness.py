"""Headless harness to observe InspectionScreen/ResultBlock behavior.

Not a pytest file — run directly with venv python from repo root:
    $env:PYTHONPATH='C:\\Users\\fumam\\Documents\\work\\pallet'
    .venv\\Scripts\\python.exe test_cam\\_inspect_harness.py
"""

import asyncio
import threading
import time

from textual.app import App

# --- Mock the background worker before importing the screen ---
import screens.workers as workers_mod

_ANALYZE_RESULT = {"angle_front_deg": 12.5, "angle_side_deg": -3.1,
                   "confidence": 0.94, "reason": "test reason"}


def _thread_name():
    return threading.current_thread().name


def _fake_inspection_loop(on_status, on_distance, on_camera, on_result, stop):
    """Simulated sequence without hardware: drive every state."""
    def send_status(key, t):
        try:
            on_status(key, t)
        except Exception as e:
            print(f"  !! on_status({key}) raised: {e!r}")

    def send_distance(d):
        try:
            on_distance(d)
        except Exception as e:
            print(f"  !! on_distance({d}) raised: {e!r}")

    def send_camera(idx, status, detail):
        try:
            on_camera(idx, status, detail)
        except Exception as e:
            print(f"  !! on_camera raised: {e!r}")

    def send_result(value, error):
        try:
            on_result(value, error)
        except Exception as e:
            print(f"  !! on_result raised: {e!r}")

    send_status("WAIT", None)
    send_distance(120)
    time.sleep(0.05)

    send_status("FOUND", time.time())
    send_distance(25)
    time.sleep(0.05)

    send_status("FIX", None)
    send_camera(0, "TAKING", "")
    time.sleep(0.02)
    send_camera(0, "SAVED", "captures/cam0.jpg")
    send_camera(1, "TAKING", "")
    send_camera(1, "SAVED", "captures/cam1.jpg")

    send_status("ANALYZING", time.time())
    send_result(None, None)
    time.sleep(0.05)
    send_result(_ANALYZE_RESULT, None)
    send_status("DONE", None)

    send_distance(120)
    send_status("WAIT", None)

    print("  [fake_loop] completed (thread=%s)" % _thread_name())


workers_mod.inspection_loop = _fake_inspection_loop
workers_mod.distance_loop = lambda on_update, stop: (_ for _ in ()).throw(NotImplementedError())


from screens.inspection_screen import InspectionScreen
from service_panel import CamerasBlock, DistanceBlock, ResultBlock, StatusBlock


class Harness(App):
    def on_mount(self):
        self.push_screen(InspectionScreen())


async def _render_children(block, pilot):
    from rich.console import Console
    import io
    out = {}
    for sel in ("#analysis-loading", "#analysis-body"):
        try:
            w = block.query_one(sel)
            out[sel] = f"display={w.display} text={str(w)!r}"
        except Exception as e:
            out[sel] = f"<err {e!r}>"
    return out


async def screen_run():
    app = Harness()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        for _ in range(30):
            await pilot.pause(0.02)

        screen = pilot.app.screen
        status = screen.query_one(StatusBlock)
        result = screen.query_one(ResultBlock)
        cameras = screen.query_one(CamerasBlock)

        print("=== AFTER SEQUENCE (threaded inspection) ===")
        print("StatusBlock state:", status._state)
        print("StatusBlock text:", repr(str(status)))
        print("ResultBlock _front/_side/_conf/_reason:",
              result._front, result._side, result._conf, result._reason)
        print("ResultBlock children:", await _render_children(result, pilot))
        print("CamerasBlock statuses:", cameras._statuses)
        print("_last_times (should be populated):", cameras._last_times)


async def resultblock_run():
    async with App().run_test() as pilot:
        rb = ResultBlock()
        await pilot.app.mount(rb)
        await pilot.pause()

        print("=== RESULTBLOCK DIRECT ===")
        print("initial:", await _render_children(rb, pilot))

        rb.set_analyzing(True)
        await pilot.pause()
        print("analyzing:", await _render_children(rb, pilot))

        rb.set_result(_ANALYZE_RESULT)
        await pilot.pause()
        print("result:", await _render_children(rb, pilot))

        rb.set_error("Дальномер не найден")
        await pilot.pause()
        print("error:", await _render_children(rb, pilot))

        rb.set_analyzing(True)
        await pilot.pause()
        print("analyze-after-error (loading shows, error cleared):",
              await _render_children(rb, pilot), "rb._error=", rb._error)


if __name__ == "__main__":
    asyncio.run(screen_run())
    asyncio.run(resultblock_run())
