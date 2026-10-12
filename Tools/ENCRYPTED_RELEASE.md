# 암호화 채보 배포

`Songs/End Time`에는 편집용 JSON과 백업을 남겨 둔다. `song.patch.json`의
`encrypted: true`와 `encryptedAssets`가 배포용 ZIP에 들어갈 파일을 정한다.
`Tools/build_manifest.py`는 편집용 JSON, 백업, 원본 파일명과 원본 곡 메타데이터를
ZIP에서 제외한다. 배포된 매니페스트에는 불투명한 ID와 `?`만 나타난다.

채보를 수정한 뒤에는 `meta.previewStartMs` 및 `preview.startMs` 같은 미리보기
값을 확인하고 암호화 파일을 다시 생성한다. 다음 명령은 키를 표준 입력에서 읽으며
명령행 인수와 소스 파일에 기록하지 않는다.

```bash
node Tools/encrypt_release_chart.mjs \
  'Songs/End Time/End_Time.4k-speedcoef.json' \
  'Songs/End Time/25225c1fd02259bf95c4d9f1d4262a11.otchart' \
  25225c1fd02259bf95c4d9f1d4262a11 audio.wav
```

암호화 파일을 다시 만들면 salt·IV가 바뀌고 저장된 해금 지문도 바뀐다. 이미 해금한
계정이 다시 코드를 입력해야 하므로, 단순 재배포 때는 암호화 파일을 재생성하지 않는다.

이 보호 범위는 런처가 배포하는 ZIP과 게임의 잠금 화면이다. 공개 GitHub
`OverTempo_Charts` 저장소에는 과거 커밋과 현재 편집용 평문 채보가 남아 있다.
소스 자체를 비공개로 만들려면 별도로 저장소 접근 권한과 기존 기록을 정리해야 한다.
