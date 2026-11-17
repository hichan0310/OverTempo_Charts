// Example reveal exercising the whole API. Copy this folder next to an ARG chart as
// `reveal/` and pass it to encrypt_release_chart.mjs as REVEAL_DIR.
async function reveal(api) {
  // Freeze-frame of the library, then darken it.
  const screen = api.image('screen', { layer: 0 });
  const dim = api.rect({ color: '#000', alpha: 0, layer: 1 });
  await dim.tween({ alpha: 0.85 }, 0.8, 'easeOutQuad');
  screen.remove();

  // A sigil grows out of a particle burst while the song plays a one-bar cut.
  api.music.play({ from: 77.0, to: 78.2, fadeOut: 0.05 });
  api.particles.burst({ count: 600, speed: [150, 700], life: [0.6, 1.6], size: [3, 9],
                        color: ['#9ff', '#fff', '#8cf'], drag: 1.5 });
  api.shake(14, 0.35);
  const sigil = api.image('sigil.png', { scale: 0.2, alpha: 0, layer: 2 });
  sigil.tween({ scale: 1, alpha: 1 }, 0.9, 'easeOutBack');
  await sigil.tween({ rotation: 180 }, 2.4, 'easeInOutCubic');

  // Dust rises continuously while text types itself out of particles.
  const dust = api.particles.emitter({ rate: 220, x: 0, y: -560, width: 1920, angle: 90, spread: 20,
                                       speed: [80, 200], life: [2, 4], size: [2, 5], color: '#bdf' });
  const title = api.assemble('A NEW SONG AWAKENS', { size: 56, y: -300, duration: 1.4, layer: 3 });
  await title.done;
  await api.wait(0.8);

  // Second cut of the song (three 200 BPM bars after the first), then flash to white.
  api.music.play({ from: 80.6, to: 81.8, fadeIn: 0.02, fadeOut: 0.3 });
  api.flash('#fff', 0.5);
  dust.stop();
  await api.wait(1.2);
  await api.fade('#fff', 1.5);
}
