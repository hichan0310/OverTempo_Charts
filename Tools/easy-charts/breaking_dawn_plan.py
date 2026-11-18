# Breaking Dawn easy (Lv4). One string per measure, 16 slots (16th notes).
#  x = single note (melody lane from the original), c = 2-note chord (outer lanes of the original chord),
#  h = hold (original hold, at most 2 beats), . = nothing.  Measures not listed are empty.
R = {}
def put(ms, s):
    for m in (ms if isinstance(ms, (list, range)) else [ms]): R[m] = s.replace(' ', '')
# intro: the song's own syncopation, sparse
put(1,  'c... x... x... x...')
put(2,  'x... ..x. ..x. ..x.')
# build-up: quarters, then the 16th roll becomes two 8th pairs
put(3,  '.... x... x... x.h.')
put(4,  '..x. x... x... c...')
put(5,  'c... x... c... ..x.')
# first chorus (dense 8ths + chords in the original): quarter pulse, chord every other bar, 8th pair at phrase ends
put(6,  'c... x... x... x.x.')
put(7,  'x... x... x... x.x.')
put(8,  'h... x... x... x...')
put(9,  'c... x... x... x...')
put(10, 'c... h... x... x...')
put(11, 'x... c... x... x.x.')
put(12, 'c... x... x... c...')
put(13, 'x... x..x x... h...')
put(14, 'c... x.x. x... c...')
put(15, 'x... x... x... x.x.')
put(16, 'x... x.x. ..x. x...')
put(17, 'x... x... x... x.x.')
put(18, 'x... x.x. x... x...')
put(19, 'x... x..x ..x. x...')
put(20, 'c... x... ..h. x.x.')
put(21, 'x... x.x. x... x.x.')
put(22, 'x... .... .... x.x.')
# arpeggio section: quarters on the beat, the 8th arpeggio kept as one pair per bar
put(range(23, 30), 'x... x.x. x... x...')
put(30, 'x... x... h... ....')
# second verse (8ths with chords): quarters, chords on bar starts
put(31, 'c... x... x... x...')
put(32, 'x... x... x... x...')
put(33, 'c... x... x... x...')
put(34, 'x... c... x... c...')
put(35, 'c... x... x... x.x.')
put(36, 'c... x... x... x...')
put(37, 'c... x... c... x...')
put(38, 'x... x... c... x...')
put(range(39, 46), 'c... x... x... x.x.')
# hold section: keep the holds, quarters around them
put(46, '.... h... h... h...')
put(47, 'c... h... x... x.x.')
put(48, '..x. x... x... x...')
put(49, 'h... x.h. ..x. x...')
put(50, '..x. x.h. ..x. x...')
put(51, 'c... x... x... x.h.')
put(52, '..x. x... x... x...')
put(53, 'h... x... x... x.h.')
put(54, '..x. x... x... x...')
put(55, 'c... x... x... x...')
put(56, 'h... x... x... x...')
put(57, 'h... x... h... x...')
put(58, 'x... x.h. ..x. x...')
put(59, 'c... x... x... x...')
put(60, 'c... x... x... x...')
put(61, '..x. x... x... x.h.')
put(62, '..x. x.h. ..x. x...')
# 63-66: speed-limit special note over silence (kept as is)
put(67, '.... h... x... x.h.')
put(68, '..h. ..h. ..x. x.h.')
put(69, '..x. ..h. ..x. x...')
put(70, 'x... x... x... x...')
put(71, 'x... x... x... x...')
put(range(72, 79), '..x. x... x... x...')
put(79, 'c... x... x... x...')
put(80, 'x... x... x... x...')
put(81, 'c... x... x... x...')
put(82, 'x... x... x... x...')
# 16th stream (83-85) becomes an 8th trill that ends on a chord
put(83, 'x... x.x. x.x. x.x.')
put(84, 'x.x. x.x. x.x. x.x.')
put(85, 'x.x. x.x. x... ....')
# final chorus
put(87, 'c... x... x... x...')
put(88, 'c... x... x... x...')
put(89, 'x... x... x... x.x.')
put(90, 'x... c... x... x...')
put(91, 'c... x... x... x...')
put(92, 'x... c... x... x.x.')
put(93, 'x... c... x... x...')
put(94, '..x. x... h... x...')
put(95, 'x.x. c... x... x...')
put(96, 'x... c... x... c...')
put(97, 'c... c... x... x...')
put(98, 'x... x... x... c...')
put(99, '.... x... x... x...')
put(100,'..h. ..h. ..h. ..h.')
put(101,'..x. x... h.h. x...')
put(102,'..x. x... x.x. x...')
put(range(103, 110), 'c... x... x... x...')
put(110,'..x. x... h... x...')
put(range(111, 115), 'c... x... x... x.x.')
put(115,'x... x.x. x.x. x.x.')
put(116,'x.x. x.x. x.x. x.x.')
put(117,'x.x. x.x. x... ..h.')
put(118,'..x. x... h.h. h.h.')

# Hand-written measures (slot: lanes; 'h' = hold with the original length, max 2 beats).
def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
O = {
    2:   cells(s0='3', s6='2', s10='1', s14='2'),
    12:  cells(s0='14', s4='3', s8='2', s12='34'),
    32:  cells(s0='4', s4='3', s8='2', s12='1'),
    34:  cells(s0='1', s4='3', s8='4', s12='14'),
    37:  cells(s0='14', s4='2', s8='14', s12='3'),
    42:  cells(s0='23', s4='4', s8='2', s12='1', s14='2'),
    70:  cells(s0='2', s4='3', s8='1', s12='2'),
    # 16th streams -> two-hand stairs instead of a one-hand trill
    83:  cells(s0='24', s4='1', s6='2', s8='3', s10='4', s12='3', s14='2'),
    84:  cells(s0='1', s2='2', s4='3', s6='4', s8='1', s10='2', s12='3', s14='4'),
    85:  cells(s0='3', s2='2', s4='1', s6='2', s8='14'),
    90:  cells(s0='2', s4='13', s8='2', s12='4'),
    93:  cells(s0='3', s4='12', s8='3', s12='1'),
    95:  cells(s0='2', s2='3', s4='14', s8='2', s12='3'),
    96:  cells(s0='3', s4='12', s8='4', s12='34'),
    97:  cells(s0='12', s4='34', s8='3', s12='2'),
    112: cells(s0='14', s4='2', s8='3', s12='2', s14='1'),
    114: cells(s0='14', s4='3', s8='2', s12='1', s14='2'),
    115: cells(s0='13', s4='2', s6='3', s8='4', s10='3', s12='2', s14='1'),
    116: cells(s0='2', s2='3', s4='4', s6='3', s8='2', s10='1', s12='2', s14='3'),
    117: cells(s0='4', s2='3', s4='2', s6='1', s8='14', s14='h14'),
    118: cells(s2='23', s6='14', s8='h4', s10='h2', s12='4'),
}
