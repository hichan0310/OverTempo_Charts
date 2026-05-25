# OverTempo Chart Editor v3

`OverTempo_Charts/Tools/chart-editor`에 넣고 실행하는 로컬 채보 에디터입니다.

## 실행

```bash
cd OverTempo_Charts/Tools/chart-editor
python3 server.py
```

Windows PowerShell:

```powershell
cd OverTempo_Charts\Tools\chart-editor
python server.py
```

또는 Windows에서 `start_editor.bat` 더블클릭.

브라우저가 자동으로 열립니다.

```text
http://127.0.0.1:5173/
```

## 주요 기능

- `Songs/` 아래 곡 폴더 자동 탐색
- 곡 선택 / 채보 선택 / 오디오 선택
- 채보 JSON의 `meta.audioFileName`을 우선해서 오디오 자동 로드
- `meta.audioFileName`이 없으면 선택된 오디오 또는 첫 번째 오디오 자동 로드
- `New Song`으로 새 곡 폴더 + 오디오 업로드 + 첫 빈 채보 생성
- `New Chart`로 선택된 곡에 새 빈 채보 생성
- `Save Chart`로 원본 JSON 저장
- 저장 시 기존 파일은 `.bak` 백업 생성
- Auto Coef / Difficulty Curve 생성 및 optimized JSON export

## 권장 작업 흐름

1. `OverTempo_Charts` 레포 clone/pull
2. `Tools/chart-editor/server.py` 실행
3. `New Song` 또는 기존 Song/Chart Load
4. 편집 후 `Save Chart`
5. 게임/런처로 테스트
6. `git add Songs/... && git commit && git push`

## 주의

`index.html`을 `file://`로 직접 열면 브라우저 보안 때문에 `Songs/` 폴더 자동 연동과 저장이 안 됩니다. 반드시 `server.py`로 띄우세요.

서버는 `127.0.0.1:5173`에만 열립니다. 외부 공개용이 아니라 로컬 작업 도구입니다.


## v4 오디오 수정

BGM 재생을 HTMLAudioElement에서 WebAudio `AudioBufferSourceNode` 기반으로 변경했습니다.
키음과 BGM이 같은 AudioContext에서 재생되므로 Chrome 탭 포커스/`audio.play()` 타이밍 문제를 줄였습니다.


## v5 Auto Coef 저장 방식

- `Save Chart`는 더 이상 단순 0/1 JSON만 저장하지 않습니다.
- 저장 시 Gaussian density curve를 생성하고, `baseSpeedupCoef × autoSpeedupCoefMultiplier`를 계산해 최종 `speedupCoef`를 저장합니다.
- 각 note에는 `baseSpeedupCoef`가 같이 저장되므로 다시 Load하면 에디터에서는 coef 0/1 편집 상태로 복원됩니다.
- 기본 Density Min/Max는 `0.2` / `1.0`입니다.
- `Generate + Save Chart`는 curve를 다시 생성한 뒤 같은 방식으로 저장합니다.

## v6 변경

- 난이도 커브 표시 영역을 캔버스 오른쪽의 약 1.5레인 폭으로 확대했습니다.
- `Show Curve`가 켜져 있으면 레인 영역이 자동으로 줄어들고, 오른쪽에 큰 auto-coef rail이 표시됩니다.


## v7 Auto Coef 변경

- `Save Chart` 저장 시 `speedupCoef`를 float 값으로 저장합니다.
- 편집 상태 복원을 위해 각 노트에 `baseSpeedupCoef`도 같이 저장합니다.
- 밀도 기반 곡선은 기본적으로 `Density Min=0.2`, `Density Max=1.0` 범위에서 자동 스케일됩니다.
- 곡 전체 후반부로 갈수록 조금씩 증가하는 `Ramp Start`, `Ramp End`, `Ramp Power`를 추가했습니다.
- 오른쪽 curve rail에서 다음 세 곡선을 동시에 볼 수 있습니다.
  - cyan: density multiplier
  - yellow: global ramp multiplier
  - purple: final multiplier
