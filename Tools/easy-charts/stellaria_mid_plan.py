import sys; sys.path.insert(0, __import__('os').path.dirname(__file__))
from mid_auto import auto
SRC = __import__('os').path.join(__import__('os').path.dirname(__file__), '../../Songs/') + "Stellaria/Stellaria_Draft.4k-speedcoef.json"
HOLD_MAX_BEATS = 4.0
R = auto(SRC, thin=False)
def put(ms, s):
    for m in (ms if isinstance(ms, (list, range)) else [ms]): R[m] = s.replace(' ', '')
def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
O = {}
# hand fixes: one-hand trills split across hands, 8th jacks into holds moved
O.update({
    9:   cells(s0='3', s2='h1', s6='3', s8='h2', s12='34', s14='1'),
    41:  cells(s0='1', s2='2', s4='4', s6='2', s8='3', s10='1', s12='2', s14='3'),
    47:  cells(s0='4', s2='3', s4='2', s6='4', s8='3', s10='2', s12='34', s14='h1'),
    53:  cells(s0='4', s2='2', s4='3', s6='2', s8='4', s10='3', s12='1', s14='3'),
    73:  cells(s0='12', s4='34', s6='h2'),
    77:  cells(s0='h2', s6='3', s8='h4', s12='13'),
    124: cells(s0='3', s2='14', s4='h2'),
})
