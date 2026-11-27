# 채보 도구

| 도구 | 용도 |
| --- | --- |
| `chart-editor/` | 브라우저 채보 에디터(4키). `start_editor.sh`로 `http://127.0.0.1:5173`에서 연다. 커밋·push와 dev 배포 버튼 포함 |
| `build_manifest.py` | 배포용 곡 ZIP과 `manifest.json` 생성. `OverTempo_Launcher/deploy charts-dev`와 에디터 배포 버튼이 사용 |
| `ENCRYPTED_RELEASE.md` | ARG 곡 공개/암호화 스위치(`release.json`)와 암호화 절차 |
| `encrypt_release_chart.mjs`, `arg_reveal_keygen.mjs` | ARG 채보 암호화, 해금 연출 패키지 서명 |
| `ARG_REVEAL_SCRIPTING.md`, `arg-reveal-example/`, `arg-reveal-minigame/`, `render_reveal_movie.py` | 해금 연출 스크립트와 미리보기 영상 |
| `ai-chart/` | AI 보조 채보 초안 생성 |
| `easy-charts/` | 쉬운 난이도 채보 생성 스크립트 |
| `song-picker/` | 수록 후보 곡 고르기 로컬 서버(`python3 server.py`, `http://127.0.0.1:5310/`) |
| `audio-restoration/` | BMS 음원 복원 결과 |
| `audit_audio_alignment.py` | 음원·채보 타이밍 정렬 검사 |
| `migrate_special_notes.py`, `snap_chart_notes.py`, `limit_chart_coef_per_measure.py`, `generate_luminaria_normal.py` | 채보 일괄 변환 스크립트 |

검사: `python3 -m unittest discover -s Tools -p 'test_*.py'`
