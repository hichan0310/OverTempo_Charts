import sys; sys.path.insert(0, __import__('os').path.dirname(__file__))
from mid_auto import auto
SRC = __import__('os').path.join(__import__('os').path.dirname(__file__), '../../Songs/') + "Change the Game/Change_the_Game_Draft.4k-speedcoef.json"
HOLD_MAX_BEATS = 4.0
R = auto(SRC)
def put(ms, s):
    for m in (ms if isinstance(ms, (list, range)) else [ms]): R[m] = s.replace(' ', '')
def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
O = {}
# hand fixes: 16th chord swaps as one bar of 8th swaps, 8th jacks into holds moved
O.update({m: cells(s0='12', s2='34', s4='12', s6='34') for m in (33, 49, 67, 83)})
O.update({
    19:  cells(s0='3', s2='2', s4='34', s6='h1', s8='4', s12='3'),
    59:  cells(s0='h3', s2='2', s4='h1', s8='34', s12='h4'),
    85:  cells(s0='34', s2='1', s4='24', s6='h1', s8='4', s10='2', s12='3'),
    95:  cells(s0='3', s2='1', s4='24', s6='h3', s8='2', s10='4', s12='h1'),
})
