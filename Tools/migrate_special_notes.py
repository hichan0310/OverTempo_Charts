#!/usr/bin/env python3
"""Migrate speed events to playable full-width notes. Dry-run unless --write."""
import argparse
import copy
import json
import math
from pathlib import Path


def remove_speed_chords(chart, tolerance_ms=60):
    """Remove historical zero-coefficient four-lane tap markers near a special head.

    Opt-in cleanup: ordinary overlapping notes remain valid in new charts.
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for index, note in enumerate(chart.get('notes', [])):
        groups[note['timeMs']].append((index, note))
    removed = set()
    heads = [note['timeMs'] for note in chart.get('specialNotes', [])
             if note.get('effect') in ('delta', 'limit')]
    for time, group in groups.items():
        if len(group) != 4 or {note['lane'] for _, note in group} != {0, 1, 2, 3}:
            continue
        if not any(abs(time - head) <= tolerance_ms for head in heads):
            continue
        if any(note.get('durationMs', 0) > 0 or note.get('speedupCoef', 1) != 0
               or note.get('baseSpeedupCoef', 0) != 0 or note.get('keySound')
               for _, note in group):
            continue
        removed.update(index for index, _ in group)
    chart['notes'] = [note for index, note in enumerate(chart.get('notes', [])) if index not in removed]
    return len(removed)


def remove_special_overlaps(chart):
    """Special intervals own all lanes, including both endpoints of normal holds."""
    special = [n for n in chart.get('specialNotes', []) if n.get('effect') in ('delta', 'limit')]
    def overlaps(note):
        start = max(0, note['timeMs'])
        end = start + max(0, note.get('durationMs', 0))
        return any(start <= max(0, s['timeMs']) + max(0, s.get('durationMs', 0))
                   and end >= max(0, s['timeMs']) for s in special)
    original = chart.get('notes', [])
    chart['notes'] = [n for n in original if not overlaps(n)]
    return len(original) - len(chart['notes'])


def convert_chart(chart, gap_ms=200, minimum_events=3, remove_speed_markers=False, remove_overlaps=False):
    result = copy.deepcopy(chart)
    special = list(result.get('specialNotes', []))
    for field, effect, value_key in [('stageDeltaLines', 'delta', 'stageDelta'),
                                      ('speedLimitLines', 'limit', 'maxSpeed')]:
        lines = sorted((line for line in result.pop(field, []) if line is not None), key=lambda line: line['timeMs'])
        groups = []
        for line in lines:
            previous = groups[-1][-1] if groups else None
            same_direction = previous is not None and (
                (line[value_key] * previous[value_key] > 0) if effect == 'delta'
                else line[value_key] <= previous[value_key])
            if previous is not None and 0 < line['timeMs'] - previous['timeMs'] <= gap_ms and same_direction and not line.get('durationMs') and not previous.get('durationMs'):
                groups[-1].append(line)
            else:
                groups.append([line])
        for group in groups:
            if len(group) >= minimum_events and group[-1]['timeMs'] - group[0]['timeMs'] >= 100:
                note = {'timeMs': group[0]['timeMs'], 'durationMs': group[-1]['timeMs'] - group[0]['timeMs'], 'effect': effect}
                if effect == 'delta':
                    note['stageDelta'] = round(math.fsum(line[value_key] for line in group), 10)
                else:
                    note['startMaxSpeed'] = group[0][value_key]
                    note['maxSpeed'] = group[-1][value_key]
                labels = list(dict.fromkeys(line['label'] for line in group if line.get('label')))
                if labels:
                    note['label'] = ' / '.join(labels)
                special.append(note)
            else:
                special.extend(dict(line, effect=effect, durationMs=max(0, line.get('durationMs', 0))) for line in group)
    for note in special:
        if note.get('effect') == 'delta':
            note['speedDelta'] = round(note.get('speedDelta', note.get('stageDelta', 0) * .065), 10)
            note.pop('stageDelta', None)
        note.pop('startMaxSpeed', None)
    result['specialNotes'] = sorted(special, key=lambda note: note['timeMs'])
    result['version'] = max(4, result.get('version', 0))
    if remove_speed_markers:
        remove_speed_chords(result)
    if remove_overlaps:
        remove_special_overlaps(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', type=Path, default=[Path(__file__).resolve().parents[1] / 'Songs', Path(__file__).resolve().parents[1] / 'ReferenceAssets'])
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--gap-ms', type=int, default=200)
    parser.add_argument('--remove-overlaps', action='store_true', help='Remove every normal note intersecting a special interval')
    parser.add_argument('--remove-speed-chords', action='store_true', help='Remove historical zero-coefficient four-lane tap markers within 60 ms of special heads')
    args = parser.parse_args()
    paths = sorted({file for path in args.paths for file in (path.rglob('*.4k-speedcoef.json') if path.is_dir() else [path])})
    for path in paths:
        chart = json.loads(path.read_text(encoding='utf-8-sig'))
        converted = convert_chart(chart, args.gap_ms, remove_speed_markers=args.remove_speed_chords, remove_overlaps=args.remove_overlaps)
        if converted == chart:
            continue
        old_count = len(chart.get('stageDeltaLines', [])) + len(chart.get('speedLimitLines', []))
        notes = converted['specialNotes']
        removed = len(chart.get('notes', [])) - len(converted.get('notes', []))
        print(f'{path}: removed {removed} lane notes; {old_count} legacy events -> {sum(n["durationMs"] == 0 for n in notes)} taps, {sum(n["durationMs"] > 0 for n in notes)} holds')
        if args.write:
            path.write_text(json.dumps(converted, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
