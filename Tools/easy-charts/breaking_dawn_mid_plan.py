import sys; sys.path.insert(0, __import__('os').path.dirname(__file__))
from mid_auto import auto
SRC = __import__('os').path.join(__import__('os').path.dirname(__file__), '../../Songs/') + "Breaking Dawn/Breaking_Dawn_base.4k-speedcoef.json"
HOLD_MAX_BEATS = 4.0
R = auto(SRC)
def put(ms, s):
    for m in (ms if isinstance(ms, (list, range)) else [ms]): R[m] = s.replace(' ', '')
def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
O = {}
# hand fixes: no 8th jacks into holds, 16th streams as two-hand 8th stairs instead of a one-hand trill
O.update({
    49:  cells(s0='h3', s4='1', s6='h4', s10='1', s12='23', s14='h4'),
    50:  cells(s2='2', s4='14', s6='h3', s10='2', s12='14', s14='2'),
    53:  cells(s0='h2', s4='14', s8='24', s10='3', s12='24', s14='h1'),
    62:  cells(s2='4', s4='2', s6='h3', s10='2', s12='14'),
    83:  cells(s0='24', s2='3', s4='2', s6='3', s8='1', s10='2', s12='3', s14='4'),
    84:  cells(s0='1', s2='3', s4='2', s6='4', s8='1', s10='4', s12='2', s14='3'),
    85:  cells(s0='1', s2='4', s4='2', s6='3', s8='1', s10='4', s12='23'),
    115: cells(s0='13', s2='2', s4='4', s8='1', s10='3', s12='2'),
    116: cells(s0='4', s2='1', s4='3', s8='2', s10='4', s12='1'),
    117: cells(s0='3', s2='2', s4='4', s8='1', s10='3', s12='2', s14='h14'),
    118: cells(s2='2', s4='3', s6='14', s8='h3', s10='h2', s12='4'),
})
