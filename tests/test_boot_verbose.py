import logging
import sys
from contextlib import contextmanager

import envycontrol


def test_verbose_switch_reports_selected_boot_backend_and_evidence(monkeypatch, caplog):
    class FakePlan:
        backend = "dracut"
        diagnostics = (
            "active dracut pacman hook detected",
            "mkinitcpio is installed but is weaker evidence",
        )

    class FakeCachedConfig:
        def __init__(self, args):
            self.args = args

        @contextmanager
        def adapter(self):
            yield

    monkeypatch.setattr(
        sys,
        "argv",
        ["envycontrol", "--switch", "hybrid", "--verbose"],
    )
    monkeypatch.setattr(envycontrol, "assert_root", lambda: None)
    monkeypatch.setattr(envycontrol, "CachedConfig", FakeCachedConfig)
    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", lambda: FakePlan())
    monkeypatch.setattr(envycontrol, "graphics_mode_switcher", lambda *args, **kwargs: None)

    with caplog.at_level(logging.DEBUG):
        envycontrol.main()

    assert "Selected boot rebuild backend: dracut" in caplog.text
    assert "active dracut pacman hook detected" in caplog.text
    assert "mkinitcpio is installed but is weaker evidence" in caplog.text
