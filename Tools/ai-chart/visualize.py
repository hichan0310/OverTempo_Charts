#!/usr/bin/env python3
"""Make a read-only event-strength plot and a 4-key piano-roll draft preview."""
import argparse
import json
from pathlib import Path


def render(analysis: dict, chart: dict | None, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    events = analysis["events"]
    if not events:
        raise ValueError("analysis has no candidate events")
    tracks = {"": events}
    if "sourceParts" in events[0]:
        tracks = {}
        for event in events:
            for part in event["sourceParts"]:
                tracks.setdefault(part["sourceKey"], []).append(part["originalEvent"])
    panel_count = len(tracks) + bool(chart)
    fig, axes = plt.subplots(panel_count, 1, sharex=True, figsize=(15, 3 * panel_count))
    if panel_count == 1:
        axes = [axes]
    for ax, (source, track_events) in zip(axes, tracks.items()):
        seconds = [e["audioMs"] / 1000 for e in track_events]
        ax.plot(seconds, [e["onset"] for e in track_events], "-o", label="onset", markersize=3)
        ax.plot(seconds, [e["low"] for e in track_events], label="low band", alpha=.65)
        ax.plot(seconds, [e["mid"] for e in track_events], label="mid band", alpha=.65)
        ax.plot(seconds, [e["high"] for e in track_events], label="high band", alpha=.65)
        ax.set_ylabel(f"{source}\nnormalized" if source else "normalized")
        ax.set_ylim(0, 1.05)
        ax.grid(alpha=.15)
        ax.legend(loc="upper right", ncol=4)
    if chart:
        ax2 = axes[-1]
        offset = float(chart["timing"].get("offsetMs", 0))
        for note in chart["notes"]:
            if note.get("durationMs", 0) > 0:
                ax2.plot([(note["timeMs"] - offset) / 1000,
                          (note["timeMs"] + note["durationMs"] - offset) / 1000],
                         [note["lane"] + 1] * 2, linewidth=7, alpha=.3)
            ax2.scatter((note["timeMs"] - offset) / 1000, note["lane"] + 1,
                        s=50 if note["baseSpeedupCoef"] else 24,
                        marker="s", alpha=.8)
        ax2.set_yticks([1, 2, 3, 4])
        ax2.set_ylabel("lane")
        ax2.set_ylim(.5, 4.5)
        ax2.grid(alpha=.2)
    axes[-1].set_xlabel("audio timeline (seconds)")
    seconds = [e["audioMs"] / 1000 for e in events]
    axes[-1].set_xlim(min(seconds) - .2, max(seconds) + .2)
    fig.suptitle(f"{analysis.get('song', '')} - event evidence / 4-key chart")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=135)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", required=True, type=Path)
    parser.add_argument("--chart", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    chart = json.loads(args.chart.read_text(encoding="utf-8")) if args.chart else None
    if args.output.exists():
        parser.error("refusing to overwrite existing plot")
    render(analysis, chart, args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
