# ARG 해금 연출 스크립트

암호화 채보마다 해금 연출을 JavaScript로 짤 수 있다. 스크립트와 그림·소리는
채보와 같은 키로 암호화된 `<ARG ID>.otpack`에 들어가고, 개발자 키로 서명된
패키지만 게임에서 실행된다. 해금 전에는 스크립트도 그림도 클라이언트에 없다.

우선순위: 서명된 `.otpack` → 채보 `meta.argReveal`(유리 깨짐 프리셋) → 기본 카드 연출.
스크립트가 끝나면(또는 오류로 멈추면) 기본 카드(커버·제목·레벨)가 이어진다.

## 폴더 구조

```
Songs/<곡>/reveal/
  reveal.js          // function reveal(api) { ... }  (async 가능)
  assets/            // png, jpg, wav, ogg, mp3 — 이름은 소문자/숫자/._- (최대 64개)
```

예제: `Tools/arg-reveal-example/` (API 전체 사용), `Songs/End Time/reveal/` (End Time 원본 연출).

## 작업 흐름

1. Unity 메뉴 **OverTempo/ARG/Reveal Script Preview**에서 폴더를 고른다.
   파일을 저장하면 자동으로 다시 불러온다. 슬라이더로 원하는 시점으로 이동한다.
   (미리보기는 화면만 나온다. 소리는 실제 게임에서 확인한다.)
2. 배포용 암호화 때 마지막 인자로 폴더를 넘긴다:

   ```bash
   node Tools/encrypt_release_chart.mjs \
     'Songs/End Time/End_Time.4k-speedcoef.json' \
     'Songs/End Time/25225c1fd02259bf95c4d9f1d4262a11.otchart' \
     25225c1fd02259bf95c4d9f1d4262a11 audio.wav 'Songs/End Time/reveal'
   ```

   같은 키로 `.otchart`와 `.otpack`이 함께 만들어진다. 폴더를 빼고 실행하면 이전 `.otpack`은 지워진다.
3. `build_manifest.py`가 `.otpack`을 배포 ZIP에 넣는다. `reveal/` 원본 폴더는 들어가지 않는다.

서명 키: `~/.config/overtempo/arg-reveal-signing.pem` (`Tools/arg_reveal_keygen.mjs`로 생성).
**반드시 백업한다.** 잃어버리면 새 키를 만들고 클라이언트의 `ArgRevealTrust.cs`를 바꿔 업데이트해야 한다.
`OVERTEMPO_REVEAL_SIGNING_KEY` 환경변수로 다른 위치를 지정할 수 있다.

## 좌표와 시간

- 화면은 1920×1080, 원점은 가운데, y는 위쪽이 +.
- 시간은 초. `api.time()`은 연출 시작부터의 시간이며 오디오 DSP 시계를 따른다.
- `layer`가 클수록 위에 그려진다. 같은 layer는 만든 순서대로. 파티클은 layer 1000.

## API

| 함수 | 설명 |
|---|---|
| `api.wait(s)` / `api.waitUntil(t)` | Promise. `await`로 기다린다 |
| `api.waitForKey()` | Enter/Space/Esc/클릭까지 대기 |
| `api.time()`, `api.random(min,max)`, `api.log(...)` | 시간, 난수, 에디터 로그 |
| `api.rect(o)` | 단색 사각형 (기본 전체 화면, 검정) |
| `api.image(name, o)` | `assets/`의 그림. `'screen'`이면 해금 직전 정지 화면 |
| `api.text(str, o)` | 글자 (`size`, `color`, `x`, `y` …) |
| `api.assemble(str, o)` | 먼지가 모여 글자가 됨. `delay`, `duration`, `dust`, `particleLayer`. `.done` Promise |
| `api.shatter(o)` | 정지 화면이 금 가고 깨져 떨어짐 (End Time 효과) |
| `api.shake(strength, s)` | 화면 흔들림 |
| `api.fade(color, s, o)` / `api.flash(color, s, o)` | 전체 화면 페이드 / 플래시 (layer 900) |
| `api.particles.burst(o)` | 한 번에 터뜨림 (최대 5000개) |
| `api.particles.emitter(o)` | 계속 뿜기 (`rate`/초, `duration`) → `.stop()` |
| `api.music.play(o)` | 곡의 `from`~`to`초 구간 재생. `at`(연출 시각), `fadeIn`, `fadeOut`, `volume` → `.stop(fade)` |
| `api.sound.play(name, o)` | `assets/`의 소리. 옵션은 music.play와 같음 |
| `api.music.leadIn({coverAt, lead, whiteAt})` | 기본 카드의 미리듣기를 이 시점들에 맞춰 시작 |

### 미니게임용

| 함수 | 설명 |
|---|---|
| `api.onFrame((dt, t) => {...})` | 매 프레임 호출 → `.stop()` |
| `api.input.down(key)` / `pressed(key)` / `released(key)` | 누르고 있음 / 이번 프레임에 눌림 / 떼짐 |
| `api.input.onKey((name, down) => {...})` | 모든 키 눌림·뗌 이벤트 → `.stop()` |
| `await api.input.waitFor(key)` | 특정 키(생략하면 아무 키)를 기다림, 눌린 키 이름을 돌려줌 |
| `api.input.mouse()` | `{x, y, down, pressed, released}` (무대 좌표) |
| `node.get()` | `{x, y, scaleX, scaleY, rotation, alpha, width, height, layer}` |
| `node.contains(x, y)`, `a.overlaps(b)` | 점·사각형 충돌 (회전은 무시한 박스) |
| `track.position()` | `music.play`/`sound.play` 구간의 현재 재생 위치(원본 기준 초). 리듬 판정에 사용 |
| `api.end()` | 스크립트가 직접 연출을 끝냄 |

키 이름: Input System 이름(`a`, `space`, `enter`, `leftArrow`, `digit1` …), `left/right/up/down`,
그리고 **플레이어가 설정한 키** `lane0`~`lane3`, `special`.
텍스트 노드는 `align`('left'|'center'|'right'), `wrap`, `size`, 이미지 노드는 `uv: [x, y, w, h]`(스프라이트 시트 프레임)도 바꿀 수 있다.

예제: `Tools/arg-reveal-minigame/` — 레인 키로 하는 8마디 리듬 미니게임. 미리보기 창을 클릭해서
포커스를 주면 키보드·마우스로 직접 플레이할 수 있다.

노드(rect/image/text/assemble/shatter가 돌려주는 것):
`node.set(props)`, `await node.tween(props, seconds, ease)`, `node.remove()`.
props: `x`, `y`, `scale`, `scaleX`, `scaleY`, `rotation`(도), `alpha`, `width`, `height`, `color`('#rrggbb' 또는 '#rrggbbaa'), `layer`, `text`.

ease: `linear`, `smoothstep`, `easeIn/Out/InOutQuad`, `easeIn/Out/InOutCubic`, `easeInExpo`, `easeOutExpo`, `easeOutBack`, `easeOutElastic`, `step`.

파티클 옵션: `x`, `y`, `width`, `height`(생성 영역), `count`, `angle`(도, 90=위), `spread`(도),
`speed`, `life`, `size`(숫자 또는 `[min,max]`), `sizeEnd`(배율), `color`/`colorEnd`(문자열 또는 배열),
`gravity`, `drag`, `spin`.

음악 구간은 FMOD 오디오 시계로 샘플 단위 예약된다. 프레임이 밀려도 끊는 지점이 박자에서 어긋나지 않는다.

## 제한 (넘으면 연출이 멈추고 기본 카드로 넘어간다)

- 한 번 실행에 1초(무거운 글자 파티클 준비는 제외), 500만 문장, 재귀 256단계, 배열 10만 칸. `eval`/`new Function` 금지.
- 노드 512개, 트윈 2048개, 대기 4096개, 이미터 32개, 소리 채널 32개, 파티클 16000개, 프레임 콜백 64개, 키 콜백 32개, 전체 300초.
- 스크립트 256KB, 에셋 64개·각 16MB·합계 96MB.
- 스크립트는 `api`만 쓸 수 있다. 파일·네트워크·게임 내부 객체에 접근할 수 없다.
