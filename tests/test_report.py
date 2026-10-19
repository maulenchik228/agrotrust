import pandas as pd

from agrotrust_metrics.cli import main
from agrotrust_metrics.io import clean_events, clean_readings
from agrotrust_metrics.report import build_report
from agrotrust_metrics.simulate import simulate_fleet

IV = pd.Timedelta(minutes=10)


def test_build_report_writes_all_files(tmp_path):
    readings, events = simulate_fleet(3, 5, seed=2)
    index = build_report(clean_readings(readings), IV, tmp_path / "site", clean_events(events))
    text = index.read_text(encoding="utf-8")
    assert "availability" in text and "Downtime by cause" in text
    assert "sampling interval 10 min" in text
    for name in ("timeline.png", "causes.png", "summary.csv"):
        assert (tmp_path / "site" / name).stat().st_size > 0


def test_report_without_events_has_no_cause_section(tmp_path):
    readings, _ = simulate_fleet(2, 3, seed=4)
    index = build_report(clean_readings(readings), IV, tmp_path / "site")
    assert "Downtime by cause" not in index.read_text(encoding="utf-8")
    assert not (tmp_path / "site" / "causes.png").exists()


def test_report_command(tmp_path, capsys):
    data = tmp_path / "data"
    main(["simulate", "--nodes", "2", "--days", "3", "--out", str(data)])
    site = tmp_path / "site"
    args = ["report", str(data / "readings.csv"), "--events", str(data / "events.csv")]
    assert main([*args, "--out", str(site)]) == 0
    assert "index.html" in capsys.readouterr().out
    assert (site / "index.html").exists()
