"""Deterministic lane compression helpers for rhythm-game chart importers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FoldStats:
    source_notes: int
    output_notes: int
    duplicate_taps: int
    merged_holds: int
    taps_inside_holds: int

    @property
    def collapsed_notes(self) -> int:
        return self.source_notes - self.output_notes

    def summary(self, source_keys: int, target_keys: int = 4) -> str:
        return (
            f"folded {source_keys}K->{target_keys}K "
            f"({self.source_notes}->{self.output_notes} notes; "
            f"{self.duplicate_taps} duplicate taps, "
            f"{self.merged_holds} overlapping holds, "
            f"{self.taps_inside_holds} taps inside holds collapsed)"
        )


def target_lane(source_lane: int, source_keys: int, target_keys: int = 4) -> int:
    """Map lane centres proportionally, preserving left-to-right geometry."""
    if source_keys <= target_keys:
        raise ValueError("lane folding requires more source keys than target keys")
    if not 0 <= source_lane < source_keys:
        raise ValueError(f"source lane {source_lane} is outside 0..{source_keys - 1}")
    return min(
        target_keys - 1,
        int((source_lane + 0.5) * target_keys / source_keys),
    )


def fold_notes(
    notes: list[dict],
    source_keys: int,
    target_keys: int = 4,
) -> tuple[list[dict], FoldStats]:
    """Fold lanes, treating colliding lane contents as a playable union."""
    mapped: list[dict] = []
    for source in notes:
        note = dict(source)
        note["lane"] = target_lane(
            int(source["lane"]),
            source_keys,
            target_keys,
        )
        mapped.append(note)

    output: list[dict] = []
    duplicate_taps = 0
    merged_holds = 0
    taps_inside_holds = 0

    for lane in range(target_keys):
        lane_notes = [note for note in mapped if note["lane"] == lane]
        holds = sorted(
            (dict(note) for note in lane_notes if int(note.get("durationMs", 0)) > 0),
            key=lambda note: (int(note["timeMs"]), int(note["durationMs"])),
        )
        merged: list[dict] = []
        for hold in holds:
            start = int(hold["timeMs"])
            end = start + int(hold["durationMs"])
            if merged:
                previous = merged[-1]
                previous_end = int(previous["timeMs"]) + int(previous["durationMs"])
                if start <= previous_end:
                    previous["durationMs"] = max(previous_end, end) - int(
                        previous["timeMs"]
                    )
                    merged_holds += 1
                    continue
            merged.append(hold)

        seen_taps: set[int] = set()
        taps: list[dict] = []
        for tap in sorted(
            (dict(note) for note in lane_notes if int(note.get("durationMs", 0)) <= 0),
            key=lambda note: int(note["timeMs"]),
        ):
            time_ms = int(tap["timeMs"])
            if time_ms in seen_taps:
                duplicate_taps += 1
                continue
            seen_taps.add(time_ms)
            if any(
                int(hold["timeMs"])
                <= time_ms
                <= int(hold["timeMs"]) + int(hold["durationMs"])
                for hold in merged
            ):
                taps_inside_holds += 1
                continue
            taps.append(tap)

        output.extend(merged)
        output.extend(taps)

    output.sort(
        key=lambda note: (
            int(note["timeMs"]),
            int(note["lane"]),
            int(note.get("durationMs", 0)),
        )
    )
    return output, FoldStats(
        source_notes=len(notes),
        output_notes=len(output),
        duplicate_taps=duplicate_taps,
        merged_holds=merged_holds,
        taps_inside_holds=taps_inside_holds,
    )
