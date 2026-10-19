"""Static HTML report: fleet summary, per-node table, downtime by cause and figures.

The report is a folder with ``index.html``, two PNG figures and the per-node table as CSV,
so it can be opened from disk, archived by a CI server or served by any web server.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import __version__
from .metrics import attach_causes, failures_by_cause, find_outages, overall, summarize
from .plot import plot_causes, plot_timeline

STYLE = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:32px auto;
max-width:980px;padding:0 16px;color:#1d2b36;background:#fbfbf9}
h1{font-size:26px;margin-bottom:4px}h2{font-size:19px;margin-top:32px}
.meta{color:#5b6670;font-size:14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}
.kpi{background:#fff;border:1px solid #dde2e6;border-radius:10px;padding:12px 14px}
.kpi b{display:block;font-size:22px}.kpi span{font-size:13px;color:#5b6670}
table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}
th,td{border:1px solid #dde2e6;padding:6px 8px;text-align:right}th{background:#eef2f5}
td:first-child,th:first-child{text-align:left}img{max-width:100%;border:1px solid #dde2e6}
"""


def _minutes(interval) -> str:
    return f"{pd.Timedelta(interval) / pd.Timedelta(minutes=1):g}"


def _kpis(fleet: pd.Series) -> str:
    items = [
        (f"{fleet['availability']:.2%}", "availability"),
        (f"{fleet['completeness']:.2%}", "data completeness"),
        ("n/a" if pd.isna(fleet["pdr"]) else f"{fleet['pdr']:.2%}", "packet delivery ratio"),
        (f"{fleet['mtbf_h']:.1f} h", "MTBF"),
        ("n/a" if pd.isna(fleet["mttr_h"]) else f"{fleet['mttr_h']:.2f} h", "MTTR"),
        (str(fleet["outages"]), "outages"),
    ]
    cells = "".join(f'<div class="kpi"><b>{v}</b><span>{k}</span></div>' for v, k in items)
    return f'<div class="kpis">{cells}</div>'


def build_report(
    readings: pd.DataFrame,
    interval,
    out_dir: str | Path,
    events: pd.DataFrame | None = None,
    min_missed: int = 3,
    title: str = "AgroTrust reliability report",
) -> Path:
    """Write the report folder and return the path of ``index.html``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    table = summarize(readings, interval, min_missed=min_missed)
    fleet = overall(table)
    outages = find_outages(readings, interval, min_missed)
    causes_html = ""
    if events is not None:
        outages = attach_causes(outages, events)
        causes = failures_by_cause(outages)
        plot_causes(causes, out / "causes.png")
        causes_html = (
            "<h2>Downtime by cause</h2>"
            + causes.round(3).to_html(border=0)
            + '<p><img src="causes.png" alt="Downtime by failure cause"></p>'
        )
    plot_timeline(readings, interval, outages, out / "timeline.png")
    table.to_csv(out / "summary.csv")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>{STYLE}</style></head>
<body><h1>{html.escape(title)}</h1>
<p class="meta">Generated {stamp} by agrotrust-metrics {__version__}.
{len(table)} nodes, sampling interval {_minutes(interval)} min.</p>
{_kpis(fleet)}
<h2>Outage timeline</h2><p><img src="timeline.png" alt="Outage timeline per node"></p>
{causes_html}
<h2>Per-node metrics</h2>{table.round(4).to_html(border=0)}
<p class="meta">Per-node table as CSV: <a href="summary.csv">summary.csv</a></p>
</body></html>"""
    index = out / "index.html"
    index.write_text(page, encoding="utf-8")
    return index
