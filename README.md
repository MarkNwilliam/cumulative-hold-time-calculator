<div align="center">

# Cumulative Hold Time Calculator

**Tracks in process dwell time from wet granulation to compression, enforces a limit per step and a global cumulative limit, and flags an excursion before the batch clock runs out.**

[![Tests](https://img.shields.io/badge/tests-19%20passing-green)](#)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](#)
[![Deps](https://img.shields.io/badge/deps-none-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Live demo](https://img.shields.io/badge/live%20demo-online-0e7490)](https://marknwilliam.github.io/cumulative-hold-time-calculator/)

</div>

---

![Dashboard preview](docs/preview.png)

## About

A granulation batch that sits too long picks up moisture, grows fines, segregates and can drift off spec before anyone notices. Hold time is usually controlled step by step, but the cumulative sitting time is what really matters at compression. This tool takes your step list with start, planned end and a limit per step, adds any still running step evaluated against the current time, and rolls everything into a cumulative total against a global limit. Step status and cumulative status are marked On time, Near at 80%, or Over. If any step or the running total crosses its line, the batch raises an excursion flag for the deviation review.

Every time value is dated, so the clock lives on the 24 hour system at hh:mm and nothing depends on memory of which shift something landed. Durations, the cumulative total, the remaining allowance and how far over you are all come back in hh:mm, with running hours carrying on past 24:00 if a step crosses midnight.

## Using the dashboard

The page is a field calculator, so you type your own numbers. Dates are day.month.year and times are hh:mm on the 24 hour clock, no AM or PM.

- **Elapsed time:** enter the taken date and time, then the processed date and time, and the tool gives the difference as hh:mm with a breakdown in days, hours and minutes. The Use now button fills the end with the live clock.
- **Running total:** any number of hh:mm durations can be typed or added onto the list, and the total rolls up live against the 72:00 hold limit, showing the amount still left or how far over you are. An elapsed gap from the first panel can be pushed straight into the running total.
- **Valid up to:** give a from date and time plus a validity written as days and hh:mm, and the tool returns the valid up to date and the valid up to time on the 24 hour clock. From now fills the start with the live clock.

## Inputs

Each step has a name, an ISO start on the 24 hour clock, an optional end, and a limit in hours. The final step may be left running, in which case it is evaluated at the current time and a projected total is forecast to its limit. The global limit is the total allowed sitting time across the whole run.

## Quick start

```bash
cat > steps.json <<'EOF'
[
  {"name": "Wet granulation", "start": "2026-09-01 06:00", "end": "2026-09-01 09:30", "limit_h": 4},
  {"name": "Drying", "start": "2026-09-01 09:30", "end": "2026-09-01 13:00", "limit_h": 6},
  {"name": "Lubricated blend", "start": "2026-09-01 13:00", "limit_h": 6}
]
EOF
python3 hold_time.py --json steps.json --global-limit 24 --now "2026-09-01 16:00"
```

```bash
python3 -m unittest test_hold_time.py
```

## Repository layout

```
cumulative-hold-time-calculator/
├── index.html        # interactive dashboard (open this)
├── hold_time.py      # hold time library + CLI
├── test_hold_time.py # 19 unit tests
├── docs/             # README preview screenshot
└── README.md
```

## License

MIT.