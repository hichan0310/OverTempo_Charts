# chart-editor corrected timeline-events build

이 빌드는 기존 `Tools/chart-editor/index.html`의 핵심 기능을 보존한 상태로 timeline event 2종만 추가합니다.

보존된 기존 기능:

- `speedupCoef` / `baseSpeedupCoef` 기반 채보 계수 편집
- `Auto Coef / Difficulty Curve`
- 노트 밀도 Gaussian smoothing 기반 `densityMultiplier`
- global ramp multiplier
- manual anchor multiplier
- 저장 시 `speedupCoef = baseSpeedupCoef * autoSpeedupCoefMultiplier`
- 난이도 표시/편집: `difficulty.name`, `difficulty.level`, `difficulty.scroll`, `difficulty.baseSpeed`, `difficulty.notes`

추가된 기능:

- `speedLimitLines`: 지정 시간에서 현재 배속이 `maxSpeed`를 넘으면 stage를 역산해서 제한
- `stageDeltaLines`: 지정 시간에서 `GameManager.stage`에 `stageDelta`를 더함

같은 시간에는 stage delta가 먼저 적용되고, speed limit가 나중에 적용됩니다.

## v3 특수 노트

속도 이벤트는 이제 4레인 전체를 채우는 청록색 특수 노트입니다. 기본 입력은 Space이며 게임 설정의 SPECIAL에서 변경할 수 있습니다. 입력 여부와 관계없이 속도 효과는 적용되고, 성공/실패는 Perfect 비율에만 직접 반영됩니다.

`Special Duration (ms)`가 0이면 탭, 양수이면 홀드입니다. 패널에서 생성한 노트의 시작 시간·길이·배속 변화량·목표 limit을 수정할 수 있습니다. limit 홀드는 실제 진입 배속을 기준으로 합니다. 특수 노트와 일반 탭·홀드는 겹쳐 배치할 수 있으며, 불러오기·저장·특수 노트 이동/길이 수정 때도 일반 노트를 유지합니다. 배치 도구는 특수 노트 위에도 일반 노트를 놓고, 선택 도구는 겹친 일반 노트를 우선 선택합니다. 홀드는 배속 0.01 단위로 변화하며 마지막에는 정확한 목표값에 도달합니다.

저장 시 `version: 4`와 `specialNotes`를 내보냅니다. 각 항목은 `timeMs`, `durationMs`, `effect: "delta" | "limit"` 및 `speedDelta` 또는 `maxSpeed`를 가집니다. `speedDelta: -0.20`은 배속을 총 0.20 낮춘다는 뜻입니다. 기존 stage 값은 0.065를 곱해 배속 단위로 변환합니다.

limit 탭은 즉시 상한을 적용합니다. limit 홀드는 실제 진입 배속과 목표 배속의 차이를 전체 길이에 균등 분배하여 0.01씩 낮춥니다. 10초 길이의 1.3 limit 홀드라면 1.8 진입은 0.2초마다, 1.55 진입은 0.4초마다 0.01씩 낮춥니다. `startMaxSpeed`는 더 이상 계산에 사용하지 않으며 에디터에서도 지정하지 않습니다. 판정 성공 여부와 관계없이 효과는 작동합니다.
