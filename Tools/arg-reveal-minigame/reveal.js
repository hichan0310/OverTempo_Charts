// Mini-game example: an 8-bar, 4-lane rhythm challenge played with the player's own
// lane keys. Timing is judged against the song segment's playback position, so it
// stays in sync with what is heard. Clearing it reveals the song.
const BPM = 200, BEAT = 60 / BPM, FROM = 63.022;      // song cut starts on a downbeat
const JUDGE_Y = -380, SPEED = 900, WINDOW = 0.09, LANE_W = 160;
const laneX = (lane) => (lane - 1.5) * LANE_W;

async function reveal(api) {
  api.rect({ color: '#05080f', layer: 0 });
  for (let lane = 0; lane < 4; lane++) {
    api.rect({ color: '#16233a', width: LANE_W - 8, height: 1080, x: laneX(lane), layer: 1 });
  }
  api.rect({ color: '#7fe8ff', width: LANE_W * 4, height: 6, y: JUDGE_Y, layer: 2 });
  const scoreText = api.text('0 / 0', { size: 44, y: 440, layer: 5 });
  const title = api.text('HIT THE NOTES', { size: 60, y: 120, alpha: 0, layer: 5 });
  await title.tween({ alpha: 1 }, 0.4, 'easeOutQuad');
  await api.wait(0.8);
  title.tween({ alpha: 0 }, 0.3);

  // Chart: one note per beat for 8 bars after a one-bar count-in, lanes from a fixed pattern.
  const pattern = [0, 1, 2, 3, 2, 1, 0, 3, 1, 2, 0, 3, 3, 2, 1, 0];
  const notes = [];
  for (let beat = 4; beat < 36; beat++) {
    const lane = pattern[beat % pattern.length];
    notes.push({ time: beat * BEAT, lane, node: api.rect({ color: '#ffffff', width: LANE_W - 20, height: 24,
      x: laneX(lane), y: 1200, layer: 3 }), done: false });
  }
  const track = api.music.play({ from: FROM, to: FROM + 37 * BEAT, fadeOut: 0.2 });
  let hit = 0, judged = 0;

  await new Promise((finish) => {
    const loop = api.onFrame(() => {
      const now = track.position() - FROM;            // seconds into the cut
      for (let lane = 0; lane < 4; lane++) {
        if (!api.input.pressed('lane' + lane)) continue;
        const target = notes.find((n) => !n.done && n.lane === lane && Math.abs(n.time - now) <= WINDOW);
        if (!target) continue;
        target.done = true; hit++; judged++;
        target.node.remove();
        api.particles.burst({ x: laneX(lane), y: JUDGE_Y, count: 40, speed: [200, 500], life: [0.2, 0.5],
          angle: 90, spread: 120, color: ['#9ff', '#fff'] });
      }
      for (const note of notes) {
        if (note.done) continue;
        if (now - note.time > WINDOW) { note.done = true; judged++; note.node.set({ color: '#ff4d6a', alpha: 0.4 }); continue; }
        note.node.set({ y: JUDGE_Y + (note.time - now) * SPEED });
      }
      scoreText.set({ text: `${hit} / ${judged}` });
      if (judged === notes.length) { loop.stop(); finish(); }
    });
  });

  const cleared = hit >= notes.length * 0.7;
  const result = api.text(cleared ? 'UNLOCKED' : `${hit} / ${notes.length} — TRY AGAIN NEXT TIME`, { size: 72, y: 60, alpha: 0, layer: 6 });
  await result.tween({ alpha: 1, scale: 1.1 }, 0.5, 'easeOutBack');
  if (cleared) api.particles.burst({ count: 1200, speed: [200, 900], life: [0.8, 1.8], color: ['#9ff', '#fff', '#ffd27f'] });
  await api.wait(1.5);
  await api.fade('#fff', 1.2);
}
