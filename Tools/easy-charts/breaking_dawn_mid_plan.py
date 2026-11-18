import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rhythm
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Songs", "Breaking Dawn/Breaking_Dawn_base.4k-speedcoef.json")
# 4-bar phrases varied bar by bar: a 5-note run, plain quarters with a pickup, a run into the next downbeat
R = rhythm.mid(SRC, phrase='ADBA', chord_slots=(0, 8))
JACK_BEATS = 0.5; HAND_RUN = 3; SPIRAL_COST = 1.0; ONEHAND_CHORD_COST = 1.0; HOLD_MIN_BEATS = 1.0; HOLD_MAX_BEATS = 4.0
def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
# 16th streams: two-hand 8th stairs
O = {
    83:  cells(s0='24', s2='3', s4='2', s6='3', s8='1', s10='2', s12='3', s14='4'),
    84:  cells(s0='1', s2='3', s4='2', s6='4', s8='1', s10='4', s12='2', s14='3'),
    85:  cells(s0='1', s2='4', s4='2', s6='3', s8='1', s10='4', s12='23'),
    115: cells(s0='13', s2='2', s4='4', s8='1', s10='3', s12='2'),
    116: cells(s0='4', s2='1', s4='3', s8='2', s10='4', s12='1'),
    117: cells(s0='3', s2='2', s4='4', s8='1', s10='3', s12='2', s14='h14'),
    118: cells(s2='2', s4='3', s6='14', s8='h3', s10='h2', s12='4'),
}
