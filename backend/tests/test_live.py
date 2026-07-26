import threading

from backend.services.live import LiveAnalysisManager


def test_live_manager_prevents_overlapping_workers(monkeypatch):
    manager = LiveAnalysisManager()
    entered = threading.Event()
    release = threading.Event()

    def fake_worker():
        entered.set()
        release.wait(2)

    monkeypatch.setattr(manager, "_run", fake_worker)
    assert manager.start() is True
    assert entered.wait(1)
    assert manager.start() is False
    release.set()
    assert manager.stop() is True
