// End Time — the final unlock.
// The library freezes, glitches, and splinters apart on the break's
// heaviest hit. In the dark a clock unwinds and stops at twelve; "NOW" and the last
// sentence condense out of dust while the song rises, then everything turns white.
// Only the song itself is heard: no extra sound effects.
// Timing is on End Time's own grid: 180 BPM, chart offset -31 ms.
//
// Layers: 0 black · 1 clock · 2 glass · 3 dust/letters · 5 frozen screen · 6 words
//         7 glitch strips · 8 flash · 9 white-out  (particles: 1000)

const BEAT = 60 / 180, BAR = BEAT * 4;
const BREAK = 2 * BAR;                           // glass collapses here
const NOW = 4 * BAR, LINE = 6 * BAR, WHITE = 8.75 * BAR, COVER = 11 * BAR;

async function reveal(api) {
  const at = (t) => api.waitUntil(t);

  // ---- sound: only the song, entering at NOW --------------------------------
  // The song itself enters silently at NOW and reaches full volume on the cover card.
  api.music.leadIn({ coverAt: COVER, lead: COVER - NOW, whiteAt: WHITE });

  // ---- freeze, crack, glitch --------------------------------------------------
  api.rect({ color: '#000', layer: 0 });
  const still = api.image('screen', { layer: 5 });
  await at(BREAK - 2.1);                         // glass breaks up 2.1 s after it starts
  api.shatter({ layer: 2 }).remove();            // keep the shards, drop the radial crack lines
  still.remove();                                // identical pixels: the hand-over is invisible

  await at(BAR);

  const strips = [];
  for (let i = 0; i < 10; i++) strips.push(api.image('screen', { layer: 7, alpha: 0 }));
  const glitch = api.onFrame((dt, t) => {
    const k = Math.min(1, Math.max(0, (t - (BAR + BEAT)) / (BREAK - BAR - BEAT)));
    for (const s of strips) {
      if (api.random() > 0.15 + 0.6 * k) { s.set({ alpha: 0 }); continue; }
      const v = api.random(), h = api.random(0.008, 0.04 + 0.08 * k);
      s.set({ alpha: 1, width: 1920, height: h * 1080, y: (v + h / 2 - 0.5) * 1080,
              x: api.random(-1, 1) * (12 + 160 * k), uv: [0, v, 1, h] });
    }
  });

  // ---- collapse -----------------------------------------------------------------
  await at(BREAK);
  glitch.stop();
  strips.forEach((s) => s.remove());
  api.flash('#ffffff', 0.35, { layer: 8 });
  api.shake(26, 0.6);
  api.particles.burst({ count: 900, speed: [300, 1500], angle: 90, spread: 360, life: [0.6, 1.6],
                        size: [3, 9], sizeEnd: 0.3, gravity: 1400, drag: 0.6, spin: 400,
                        color: ['#ffffff', '#cfefff', '#8fd8ff'] });
  const dust = api.particles.emitter({ rate: 60, x: 0, y: -600, width: 1920, angle: 90, spread: 25,
                                       speed: [30, 90], life: [3, 6], size: [2, 4], color: ['#9fc8ff', '#ffffff'] });

  // ---- the clock unwinds and stops at twelve -------------------------------
  const face = api.image('clock_face.png', { layer: 1, alpha: 0, scale: 0.55 });
  const hand = api.image('clock_hand.png', { layer: 1, alpha: 0, scale: 0.55, rotation: 0 });
  face.tween({ alpha: 0.28, scale: 0.6 }, BAR, 'easeOutCubic');
  hand.tween({ alpha: 0.5, scale: 0.6 }, BAR, 'easeOutCubic');
  await hand.tween({ rotation: 1080 }, NOW - BEAT - BREAK, 'easeOutCubic');   // three turns back
  api.shake(4, 0.15);                                                           // the last tick lands

  // ---- NOW ----------------------------------------------------------------------
  await at(NOW);
  api.assemble('NOW', { size: 84, y: 55, duration: 1.6, dust: true, particleLayer: 3, layer: 6 });
  face.tween({ alpha: 0.08, scale: 0.64 }, 1.2, 'easeInOutQuad');
  hand.tween({ alpha: 0, scale: 0.64 }, 1.2, 'easeInOutQuad');         // keep the words clean

  await at(LINE);
  await api.assemble('THE END OF THIS JOURNEY IS HERE',
                     { size: 40, y: -48, duration: 1.6, particleLayer: 3, layer: 6 }).done;
  face.tween({ rotation: -6 }, WHITE - api.time(), 'linear');                  // the dial drifts while you read

  // ---- white-out into the unlock card -------------------------------------------
  await at(WHITE);
  dust.stop();
  await api.fade('#ffffff', COVER - WHITE, { ease: 'smoothstep', layer: 9 });
}
