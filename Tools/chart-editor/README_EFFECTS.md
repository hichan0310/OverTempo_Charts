# 연출 트리거 (노트 그룹 / 효과 / 사진)

차트 에디터의 **Effects / 연출 트리거** 카드에서 작업합니다.
상단 미리보기는 실제 게임 화면 에셋(`game-preview/`)으로 플레이헤드 시점의 화면을 그립니다.
**Large Preview** 버튼을 누르면 확대됩니다.

## 트리거 공통

- 플레이헤드 위치에 **Add @ Playhead**로 트리거를 추가합니다.
- **Duration 0**이면 그 순간 바로 적용됩니다(단발).
- **Duration > 0**이면 그 시간 동안 나누어 변합니다(롱노트형). 변화 곡선은 Ease로 고릅니다.
- 같은 대상에 다음 트리거가 오면 직전 값에서 이어서 변합니다.
- 변화가 진행되는 도중에 다음 트리거가 오면, 그 시점의 값에서 끊고 이어 갑니다.
- 판정 시각은 절대 바뀌지 않습니다.

## 1. 노트 그룹 — `alpha`, `speed`

**그룹 지정**
1. 노트를 선택합니다.
2. Group 칸에 이름을 입력합니다.
3. **Set Group on Selected Notes**를 누릅니다.

그룹은 노트 JSON에 `"group"` 필드로 저장됩니다.
그룹이 없는 노트는 Group 칸을 비운 트리거로 조작할 수 있습니다.

**`alpha`** — 투명도(0~1)
- step 이징을 쓰거나 짧은 단발 트리거를 연속으로 찍으면 깜빡이는 글리치가 됩니다.

**`speed`** — 낙하 속도 배수
- 1은 기본 속도, 0은 정지, 음수는 역행입니다.
- 노트 위치는 남은 시간 동안의 속도를 적분해서 계산합니다. 그래서 속도 곡선이 어떻든 노트는 정확한 시각에 판정선에 도착합니다.

## 2. End Time 효과 — `glitch`, `shatter`, `restore`

**`glitch`**
- End Time 해금 연출에 쓰인 화면 띠 글리치입니다.
- Intensity에서 End까지 세기가 변합니다.

**`shatter`**
- End Time의 유리 깨짐 효과입니다.
- Duration 동안 금이 번지고, Break 동안 파편이 흩어집니다.
- Freeze를 체크하면 금이 가는 동안 화면이 멈춥니다.
- Shake와 Flash로 흔들림과 섬광 세기를 조절합니다.
- **Behind the shards**에서 사진을 고르면 파편 뒤로 그 사진이 나타나고, `restore` 트리거가 올 때까지 유지됩니다.

**`restore`** — 사진에서 원래 게임 화면으로 돌아오는 방식
- `cut`: 즉시 전환
- `fade`: 서서히 사라짐
- `wipe`: 한쪽 방향(up/down/left/right)으로 걷힘
- `glitch`: 띠 단위로 끊기며 사라짐
- `shatter`: 사진이 깨져 나감
- `reassemble`: 깨졌던 게임 화면 조각이 다시 모여 붙음

## 3. 사진 — `images`

- **Add @ Playhead**로 PNG/JPG/WebP 파일(6MB 이하)을 넣습니다.
- 사진은 차트 JSON 안에 data URL로 저장되므로 암호화 릴리스에도 포함됩니다.
- 사진 중앙이 Time에 판정선에 닿도록 노트처럼 흘러옵니다.

| 항목 | 의미 |
|---|---|
| X | 가로 위치. −1~1이 플레이필드 왼쪽 끝~오른쪽 끝 |
| Width | 플레이필드 폭에 대한 비율 |
| Layer | 노트 뒤 또는 노트 앞 |
| End | 이 시각 이후 숨김 |

- 사진도 Group(비워 두면 ID)으로 `alpha`/`speed` 트리거를 그대로 받습니다.
- 예: 시작할 때 alpha 0으로 숨겨 두고 원하는 때 fade in, 또는 speed 0으로 멈춤.

## 미리보기 에셋 갱신

게임 화면이 바뀌면 Unity에서 미리보기 에셋을 다시 내보냅니다.

```
Unity -batchmode -projectPath OverTempo -executeMethod OverTempoUI.Editor.OverTempoThemePreview.ExportChartEditorPreview -quit
```

출력 위치는 `OT_CHART_EDITOR_DIR` 환경 변수로 바꿀 수 있습니다.

## 오토 모드 미리보기

Effects 카드의 **Auto mode**를 켜 두면(기본값) 미리보기와 에디터 재생이 게임의 오토 플레이(가속 켬)와 똑같이 움직입니다.

- 모든 노트 머리와 롱노트 끝을 PERFECT로 처리합니다.
- PERFECT 하나마다 stage가 `perfectThreshold × speedupCoef`만큼 오르고, 속도는 `1 + speedMultiplier × stage`입니다. 두 값은 게임 씬에서 내보낸 값을 씁니다.
- 특수 노트의 delta/limit도 게임과 같은 방식으로 적용됩니다.
- 노트 간격, 음악 재생 속도, 화면의 CURRENT SPEED·중앙 속도 숫자·CLEAR TIME이 모두 그 속도를 따릅니다.

Auto mode를 끄면 기존 Rate 슬라이더 속도로 재생합니다.
