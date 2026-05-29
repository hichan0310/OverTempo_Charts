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
