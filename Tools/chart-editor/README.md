# OverTempo Chart Editor

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
- `New Song`으로 새 곡 폴더 + 오디오 업로드 + 첫 빈 채보 + 배포용 `song.patch.json` 생성
- 새 곡 생성 시 manifest에 사용할 고유 Song ID를 입력하며 잘못된 ID는 생성 전에 거부
- 대용량 오디오는 메모리에 통째로 복사하지 않고 스트리밍하며 상단 상태에 업로드 진행률 표시
- 업로드가 끊기거나 검증에 실패하면 임시 폴더를 제거해 불완전한 곡 폴더가 남지 않음
- `New Chart`로 선택된 곡에 새 빈 채보 생성
- `Save Chart`로 원본 JSON 저장
- 저장 시 기존 파일은 `.bak` 백업 생성
- 타임라인 중간 BPM 변경점 추가/삭제 및 변경 BPM 기준 격자·스냅
- 암호화 사용 여부와 ARG ID를 편집 설정으로 저장
- 비밀 코드를 브라우저 세션에서만 사용해 게임 호환 `.otchart` 생성
- Auto Coef / Difficulty Curve 생성 및 optimized JSON export

## 권장 작업 흐름

1. `OverTempo_Charts` 레포 clone/pull
2. `Tools/chart-editor/server.py` 실행
3. `New Song` 또는 기존 Song/Chart Load
4. 편집 후 `Save Chart`
5. 암호화 곡이면 `Encrypt release chart`를 켜고 ARG ID와 비밀 코드를 입력한 뒤 `Build Encrypted Release`
6. 게임/런처로 테스트
7. 자동 생성된 `song.patch.json`을 포함해 `git add Songs/... && git commit && git push`

## BPM 변경

- 상단 BPM은 0ms부터 적용되는 기본 BPM입니다.
- `Timeline Events > New BPM`에 값을 넣고 `Add BPM @ Playhead`를 누르면 현재 스냅 시각부터 새 BPM이 적용됩니다.
- 각 BPM 변경 시각은 새 템포 구간의 첫 박자입니다. 이후 캔버스 격자, 노트 배치 스냅, Prev/Next Beat·Bar·Snap이 해당 BPM을 사용합니다.
- JSON에는 `timing.bpmChanges: [{ "timeMs": 12000, "bpm": 210 }]` 형태로 저장됩니다.

## ARG 암호화

- `Save Chart`는 계속 편집용 평문 JSON을 저장합니다.
- `Build Encrypted Release`는 같은 이름의 `.otchart`를 곡 폴더에 생성합니다.
- 비밀 코드는 대소문자를 구분합니다. 앞뒤 공백을 제거하고 연속 공백은 하나로 정규화합니다.
- 비밀 코드는 JSON, undo/redo 기록, 서버 요청 로그에 저장되지 않으며 성공 직후 입력창에서도 지워집니다.
- 암호화는 런타임과 같은 PBKDF2-HMAC-SHA256 600,000회 + AES-256-CBC + HMAC-SHA256 포맷을 사용합니다.
- 배포 manifest에서 곡을 `encrypted: true`로 설정할 때는 기존 정책대로 배포 대상 곡 폴더에 평문 차트나 백업을 남기면 빌드가 거부됩니다. 편집 원본은 배포 전에 별도 보관하세요.

## 주의

`index.html`을 `file://`로 직접 열면 브라우저 보안 때문에 `Songs/` 폴더 자동 연동과 저장이 안 됩니다. 반드시 `server.py`로 띄우세요.

서버는 `127.0.0.1:5173`에만 열립니다. 외부 공개용이 아니라 로컬 작업 도구입니다.
