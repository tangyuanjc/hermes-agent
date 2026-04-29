import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "x_signal_sync.py"


def load_x_signal_sync_module():
    spec = importlib.util.spec_from_file_location("x_signal_sync", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_owner_channels_fetch_each_layer_at_depth_50(monkeypatch):
    module = load_x_signal_sync_module()
    calls = {}

    def fake_bookmarks(_cj, _ids, limit):
        calls["bookmarks"] = limit
        return [], None

    def fake_timeline(_cj, _ids, typ, limit):
        calls[typ] = limit
        return [], None

    def fake_likes(_cj, _ids, username=None, user_id=None, limit=0):
        calls["likes"] = limit
        return [], None

    monkeypatch.setattr(module, "fetch_bookmarks", fake_bookmarks)
    monkeypatch.setattr(module, "fetch_timeline", fake_timeline)
    monkeypatch.setattr(module, "fetch_likes", fake_likes)

    module.fetch_owner_channels(object(), {}, "tangyuanjc", "u=1")

    assert calls == {
        "bookmarks": 50,
        "for-you": 50,
        "following": 50,
        "likes": 50,
    }


def test_kol_timeline_fetch_uses_same_depth_50(monkeypatch):
    module = load_x_signal_sync_module()
    calls = {}

    def fake_user_tweets(_cj, _ids, username, limit):
        calls[username] = limit
        return [], None

    monkeypatch.setattr(module, "fetch_user_tweets", fake_user_tweets)

    module.fetch_kol_channels(object(), {}, "sama")

    assert calls == {"sama": 50}
