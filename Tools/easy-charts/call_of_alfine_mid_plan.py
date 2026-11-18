import sys; sys.path.insert(0, __import__('os').path.dirname(__file__))
from mid_auto import auto
SRC = __import__('os').path.join(__import__('os').path.dirname(__file__), '../../Songs/') + "Call of Alfine/Call_of_Alfine_7k_folded_base.4k-speedcoef.json"
HOLD_MAX_BEATS = 4.0
R = auto(SRC, thin=False)
def put(ms, s):
    for m in (ms if isinstance(ms, (list, range)) else [ms]): R[m] = s.replace(' ', '')
def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
O = {}
# hand fixes: 8th jacks into holds moved, the 16th stream at 69 as a stair
O.update({
    31:  cells(s0='h1', s8='34', s10='1', s12='h2'),
    42:  cells(s0='h2', s8='13', s10='2', s12='14', s14='3'),
    58:  cells(s0='h2', s12='12', s14='4'),
    69:  cells(s0='13', s2='4', s4='2', s6='3', s8='1', s10='4', s12='2', s14='3'),
    73:  cells(s0='24', s2='h3', s6='h2', s8='4', s10='1'),
    74:  cells(s0='13', s2='2', s4='14', s6='3', s8='24', s10='h1', s14='2'),
    79:  cells(s0='1', s2='3', s4='h4', s6='3', s8='1', s10='h2', s14='4'),
    82:  cells(s4='12', s6='3', s8='24', s10='h1', s14='4'),
    83:  cells(s0='3', s2='2', s4='h3', s8='14', s10='h2'),
    86:  cells(s4='13', s6='2', s8='4', s10='h1', s12='3', s14='2'),
    88:  cells(s0='23', s2='4', s4='13', s6='4', s8='h2', s10='1', s12='34', s14='2'),
    90:  cells(s4='2', s6='1', s8='3', s10='h4'),
    105: cells(s0='3', s2='4', s4='12', s6='3', s8='14', s10='3', s12='2', s14='3'),
    106: cells(s0='h14', s4='23'),
})
