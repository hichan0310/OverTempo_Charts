import sys; sys.path.insert(0, __import__('os').path.dirname(__file__))
from mid_auto import auto
SRC = __import__('os').path.join(__import__('os').path.dirname(__file__), '../../Songs/') + "キミとボクへの葬送歌/Kimi_to_Boku_7k_folded_base.4k-speedcoef.json"
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
    46:  cells(s0='h1', s4='3', s6='h4'),
    49:  cells(s0='2', s2='3', s4='1', s6='2', s8='34', s10='2', s12='1', s14='4'),
    63:  cells(s0='4', s2='1', s4='4', s6='1', s8='4', s10='1', s12='4'),
    74:  cells(s0='1', s2='3', s4='24', s6='h1', s10='3', s12='2', s14='4'),
    88:  cells(s0='2', s2='1', s4='24', s6='3', s8='2', s10='3', s12='4', s14='2'),
    97:  cells(s0='24', s2='3', s4='2', s6='3', s8='1', s10='4', s12='13', s14='2'),
    104: cells(s0='14', s2='3', s4='h2', s6='4', s8='3', s10='1', s12='3', s14='1'),
})
