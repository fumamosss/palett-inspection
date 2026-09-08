"""Экран инспекции: камеры + дистанция, статус, анализ."""

from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer

from service_panel import CamerasBlock, DistanceBlock, ResultBlock, StatusBlock
from screens import workers


class InspectionScreen(Screen):
    BINDINGS = [("escape", "back", "Назад")]

    DEFAULT_CSS = """
    InspectionScreen {
        layout: vertical;
    }

    #top-row {
        height: 1fr;
    }

    InspectionScreen CamerasBlock {
        width: 1fr;
        height: 100%;
    }

    InspectionScreen DistanceBlock {
        width: 30;
        height: 100%;
        content-align: center middle;
    }

    InspectionScreen StatusBlock {
        height: 1;
    }

    InspectionScreen ResultBlock {
        height: 1fr;
    }
    """

    def compose(self):
        with Horizontal(id="top-row"):
            yield CamerasBlock(auto_capture=False)
            yield DistanceBlock(auto_loop=False)
        yield StatusBlock()
        yield ResultBlock()
        yield Footer()

    def on_mount(self):
        self.stopped = False
        cameras = self.query_one(CamerasBlock)
        distance = self.query_one(DistanceBlock)
        status = self.query_one(StatusBlock)
        result = self.query_one(ResultBlock)

        def on_status(state, started_at):
            try:
                self.app.call_from_thread(status.set_state, state, started_at)
            except Exception:
                pass

        def on_distance(dist):
            try:
                self.app.call_from_thread(distance.set_distance, dist)
            except Exception:
                pass

        def on_camera(cam_idx, cam_state, detail):
            try:
                self.app.call_from_thread(cameras._apply_status, cam_idx, cam_state, detail)
            except Exception:
                pass

        def on_result(value, error):
            try:
                if value is None and error is None:
                    self.app.call_from_thread(result.set_analyzing, True)
                elif error is not None:
                    self.app.call_from_thread(result.set_error, error)
                else:
                    self.app.call_from_thread(result.set_result, value)
            except Exception:
                pass

        self.run_worker(
            lambda: workers.inspection_loop(on_status, on_distance, on_camera, on_result,
                                            lambda: self.stopped),
            thread=True,
        )

    def on_unmount(self):
        self.stopped = True

    def action_back(self):
        self.app.pop_screen()