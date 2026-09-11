#!/usr/bin/env python3
"""cumulative-hold-time-calculator

Tracks in process dwell time across an OSD granulation sequence (wet
granulation, drying, milling, pre lubrication blend, lubricated blend,
compression) with a limit per step and a global cumulative limit for the
whole run. It reports each step as On time, Near limit or Over, rolls the
elapsed hold hours into a cumulative figure, forecasts the running step into
its planned end and flags an excursion before the batch clock runs out.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

NEAR_FRACTION = 0.80


class HoldTimeError(ValueError):
    pass


def parse_ts(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def format_datetime(dt):
    """Render a datetime on the 24 hour clock as YYYY-MM-DD HH:MM."""
    return dt.strftime("%Y-%m-%d %H:%M")


def format_hours(hours):
    """Render decimal hours as hh:mm on the 24 hour clock, hours can pass 24."""
    if hours is None:
        return None
    sign = "-" if hours < 0 else ""
    total = abs(hours)
    h = int(total)
    m = int(round((total - h) * 60))
    if m == 60:
        h += 1
        m = 0
    return "%s%02d:%02d" % (sign, h, m)


def duration_hours(start, end):
    if end < start:
        raise HoldTimeError("End cannot be before start (step %s)" % start)
    return (end - start).total_seconds() / 3600.0


def step_status(dur_h, limit_h):
    if limit_h is None:
        return "Track"
    frac = dur_h / limit_h
    if frac >= 1.0:
        return "Over"
    if frac >= NEAR_FRACTION:
        return "Near"
    return "On time"


def evaluate(steps, global_limit_h, now=None):
    """steps: list of dicts with name, start, end (optional), limit_h."""
    if not steps:
        raise HoldTimeError("Provide at least one hold step")
    if global_limit_h <= 0:
        raise HoldTimeError("Global cumulative limit must be positive")
    now = parse_ts(now) if now else datetime.now()

    rows = []
    cum = 0.0
    for s in steps:
        start = parse_ts(s["start"])
        planned_end = parse_ts(s["end"]) if s.get("end") else None
        end = planned_end if planned_end is not None else now
        dur = duration_hours(start, end)
        limit = s.get("limit_h")
        cum += dur
        rows.append({
            "name": s.get("name"), "start": s["start"],
            "end": s.get("end"),
            "start_time": format_datetime(start),
            "end_time": format_datetime(end),
            "duration_h": round(dur, 2),
            "duration_hhmm": format_hours(dur),
            "limit_h": limit,
            "status": step_status(dur, limit),
            "cumulative_h": round(cum, 2),
            "cumulative_hhmm": format_hours(cum),
        })

    total = cum
    frac = total / global_limit_h
    if frac >= 1.0:
        cum_status = "Over"
    elif frac >= NEAR_FRACTION:
        cum_status = "Near"
    else:
        cum_status = "On time"

    projected = None
    last = steps[-1]
    if not last.get("end"):
        limit = last.get("limit_h")
        if limit is not None:
            projected = cum + max(0.0, limit - dur)

    return {
        "steps": rows,
        "global_limit_h": global_limit_h,
        "global_limit_hhmm": format_hours(global_limit_h),
        "cumulative_total_h": round(total, 2),
        "cumulative_total_hhmm": format_hours(total),
        "cumulative_status": cum_status,
        "remaining_h": round(max(0.0, global_limit_h - total), 2),
        "remaining_hhmm": format_hours(max(0.0, global_limit_h - total)),
        "over_by_h": round(max(0.0, total - global_limit_h), 2),
        "over_by_hhmm": format_hours(max(0.0, total - global_limit_h)),
        "projected_total_h": round(projected, 2) if projected is not None else None,
        "projected_total_hhmm": format_hours(projected),
        "excursion": cum_status == "Over"
                     or any(r["status"] == "Over" for r in rows),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(prog="hold-time", description=__doc__)
    ap.add_argument("--json", required=True, help="JSON file with steps list")
    ap.add_argument("--global-limit", type=float, default=24.0,
                    help="global cumulative limit, hours")
    ap.add_argument("--now", help="ISO timestamp to evaluate against")
    args = ap.parse_args(argv)

    with open(args.json) as f:
        steps = json.load(f)
    res = evaluate(steps, args.global_limit, args.now)
    print("Step                        Start (24h)        End (24h)          Dura   Limit  Status  Cumm (HH:MM)")
    for r in res["steps"]:
        print("%-26s %-18s %-18s %-6s %-6s %-7s %s"
              % (r["name"], r["start_time"], r["end_time"],
                 r["duration_hhmm"], format_hours(r["limit_h"]),
                 r["status"], r["cumulative_hhmm"]))
    print()
    print("Cumulative hold: %s of %s -> %s"
          % (res["cumulative_total_hhmm"], res["global_limit_hhmm"],
             res["cumulative_status"]))
    if res["over_by_h"] > 0:
        print("EXCURSION: over by %s" % res["over_by_hhmm"])
    elif res["projected_total_hhmm"] is not None:
        print("Projected total at planned end: %s" % res["projected_total_hhmm"])
    else:
        print("Remaining before limit: %s" % res["remaining_hhmm"])
    return 0


if __name__ == "__main__":
    sys.exit(main())