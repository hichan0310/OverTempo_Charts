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
