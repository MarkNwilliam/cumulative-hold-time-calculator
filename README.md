<div align="center">

# Cumulative Hold Time Calculator

**Tracks in process dwell time from wet granulation to compression, enforces a limit per step and a global cumulative limit, and flags an excursion before the batch clock runs out.**

[![Tests](https://img.shields.io/badge/tests-13%20passing-green)](#)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](#)
[![Deps](https://img.shields.io/badge/deps-none-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Live demo](https://img.shields.io/badge/live%20demo-online-0e7490)](https://marknwilliam.github.io/cumulative-hold-time-calculator/)

</div>

---

![Dashboard preview](docs/preview.png)

## About

A granulation batch that sits too long picks up moisture, grows fines, segregates and can drift off spec before anyone notices. Hold time is usually controlled step by step, but the cumulative sitting time is what really matters at compression. This tool takes your step list with start, planned end and a limit per step, adds any still running step evaluated against the current time, and rolls everything into a cumulative total against a global limit. Step status and cumulative status are marked On time, Near at 80%, or Over. If any step or the running total crosses its line, the batch raises an excursion flag for the deviation review.

## Inputs

Each step has a name, an ISO start, an optional end, and a limit in hours. The final step may be left running, in which case it is evaluated at the current time and a projected total is forecast to its limit. The global limit is the total allowed sitting time across the whole run.

## Quick start

```bash
cat > steps.json <<'EOF'
[
  {"name": "Wet granulation", "start": "2026-09-01 06:00", "end": "2026-09-01 09:30", "limit_h": 4},
  {"name": "Drying", "start": "2026-09-01 09:30", "end": "2026-09-01 13:00", "limit_h": 6},
  {"name": "Lubricated blend", "start": "2026-09-01 13:00", "limit_h": 6}
]
EOF
python3 hold_time.py --json steps.json --global-limit 24
```

```bash
python3 -m unittest test_hold_time.py
```

## Repository layout

```
cumulative-hold-time-calculator/
├── index.html        # interactive dashboard (open this)
├── hold_time.py      # hold time library + CLI
├── test_hold_time.py # 13 unit tests
├── docs/             # README preview screenshot
└── README.md
```

## License

MIT.