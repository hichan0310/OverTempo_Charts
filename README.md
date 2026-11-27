# OverTempo 채보

`Songs/<곡>/`에 곡마다 `song.patch.json`, 채보(`*.4k-speedcoef.json`), 음원, 커버가 있습니다.
배포는 `Tools/build_manifest.py`가 곡 ZIP과 매니페스트를 만들고,
`OverTempo_Launcher/deploy charts-dev` 또는 채보 에디터의 배포 버튼이 Netlify 개발 채널에 올립니다.

- ARG 곡 공개/암호화: 루트의 `release.json` 한 곳에서 바꿉니다. 지금은 `"argEncryption": false`라
  ARG 곡도 일반 채보로 공개됩니다. 자세한 내용은 [Tools/ENCRYPTED_RELEASE.md](Tools/ENCRYPTED_RELEASE.md)에 있습니다.
- 도구 목록: [Tools/README.md](Tools/README.md)
- `ReferenceAssets/`: 배포하지 않는 참고 자료. `ReferenceAssets/Covers/`는 커버 원본(로컬 보관, git 제외)
