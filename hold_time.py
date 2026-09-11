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
            "end": s.get("end"), "duration_h": round(dur, 2),
            "limit_h": limit,
            "status": step_status(dur, limit),
            "cumulative_h": round(cum, 2),
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
        "cumulative_total_h": round(total, 2),
        "cumulative_status": cum_status,
        "remaining_h": round(max(0.0, global_limit_h - total), 2),
        "over_by_h": round(max(0.0, total - global_limit_h), 2),
        "projected_total_h": round(projected, 2) if projected is not None else None,
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
    print("Step                       Dura(h)   Limit(h)  Status  Cumulative(h)")
    for r in res["steps"]:
        print("%-24s %9.2f %10s %-8s %13.2f"
              % (r["name"], r["duration_h"], r["limit_h"], r["status"],
                 r["cumulative_h"]))
    print()
    print("Cumulative hold: %s h of %s h -> %s"
          % (res["cumulative_total_h"], res["global_limit_h"],
             res["cumulative_status"]))
    if res["over_by_h"] > 0:
        print("EXCURSION: over by %s h" % res["over_by_h"])
    elif res["projected_total_h"] is not None:
        print("Projected total at planned end: %s h" % res["projected_total_h"])
    else:
        print("Remaining before limit: %s h" % res["remaining_h"])
    return 0


if __name__ == "__main__":
    sys.exit(main())