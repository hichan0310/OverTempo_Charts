# OverTempo_Charts chart-editor minimal timeline-event patch

이 ZIP은 `Tools/chart-editor/index.html` 전체를 새로 만든 파일로 덮어쓰지 않습니다.
현재 GitHub의 chart editor 원본을 기준으로, 아래 기능만 최소 삽입하는 패처입니다.

- `speedLimitLines` UI
- `stageDeltaLines` UI
- 두 라인의 캔버스 표시
- JSON import/export 및 프로젝트 저장 payload 포함
- 새 차트 생성 시 빈 배열 추가(`server.py`)

건드리지 않는 부분:

- `drawNote()`
- 롱노트 렌더링/리사이즈/선택 로직
- `addNote()`
- 노트 충돌 판정
- `autoCoefGenerateCurve()`
- 노트 밀도 Gaussian smoothing 계산
- `projectBuildPayload()`의 auto-coef 계수 계산 부분

## 적용 방법

먼저 망가진 에디터 파일을 GitHub 현재 원본으로 되돌리세요.

```bash
git checkout HEAD -- Tools/chart-editor/index.html Tools/chart-editor/server.py
```

그 다음 ZIP 안의 `chart-editor/apply_minimal_timeline_events.py`를 아래 위치로 복사합니다.

```text
OverTempo_Charts/Tools/chart-editor/apply_minimal_timeline_events.py
```

그리고 실행합니다.

```bash
cd OverTempo_Charts/Tools/chart-editor
python3 apply_minimal_timeline_events.py
```

성공하면 아래 백업이 생깁니다.

```text
index.html.bak-before-timeline-events
server.py.bak-before-timeline-events
```

## 저장 JSON 예시

```json
{
  "speedLimitLines": [
    { "timeMs": 30000, "maxSpeed": 1.25 }
  ],
  "stageDeltaLines": [
    { "timeMs": 45000, "stageDelta": -5.0 }
  ]
}
```

## 실패 시

패처가 현재 GitHub 원본의 롱노트 렌더링 마커를 확인합니다. 이전에 잘못 생성된 에디터 파일이면 적용을 중단합니다.
그 경우 다시 아래 명령으로 원복 후 재실행하세요.

```bash
git checkout HEAD -- Tools/chart-editor/index.html Tools/chart-editor/server.py
python3 Tools/chart-editor/apply_minimal_timeline_events.py
```
