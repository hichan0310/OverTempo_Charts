import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rhythm
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Songs", 'Change the Game/Change_the_Game_Draft.4k-speedcoef.json')
# every 8th the music plays is kept (no gaps where the line continues); holds only on real sustains
R = rhythm.mid(SRC, phrase='F', hold_min=1.5, chord_slots=(0, 8))
JACK_BEATS = 0.5; HAND_RUN = 3; SPIRAL_COST = 1.0; ONEHAND_CHORD_COST = 1.0; HOLD_MIN_BEATS = 1.5; HOLD_MAX_BEATS = 4.0
def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
O = {m: cells(s0='12', s2='34', s4='12', s6='34') for m in (33, 49, 67, 83)}   # 16th chord swaps -> 8th swaps
