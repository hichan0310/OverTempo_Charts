# Call of Alfine easy (Lv4). One string per measure, 16 slots (16th notes).
#  x = single (melody lane from the original), c = 2-note chord, h = hold (max 2 beats), . = nothing.
R = {}
def put(ms, s):
    for m in (ms if isinstance(ms, (list, range)) else [ms]): R[m] = s.replace(' ', '')
# intro: one held note per bar, the off-beat answers kept
put([2, 4, 5, 6, 10], 'h... .... x... c...')
put([3, 7, 8, 11, 13, 15], 'h... .... h... ....')
put(9,  'x... c... h... ....')
put(12, 'h... .... x... x...')
put(14, 'h... .... .... ....')
# 18-23 dense 8ths with chords: quarter pulse, chord every other beat, one 8th pair
put(18, 'c... x... x... x.x.')
put(19, 'x... x... c... x...')
put(20, 'x... c... x... x.x.')
put(21, 'c... x... x... x.x.')
put(22, 'x... x... c... x...')
put(23, 'x... c... x... x...')
# 24-26 hold melody
put(24, 'h... ..x. x... h...')
put(25, '..h. x... h... ..x.')
put(26, 'x... h... ..x. x...')
put(27, 'c... x... c... x...')
put(28, 'x... x... c... c...')
put(29, 'h... .... .... ....')
put(30, 'x... x... x... x.x.')
put(31, 'h... .... c... h...')
put(32, 'h... x... x... c...')
put(33, 'h... x... x... c...')
put(34, 'h... .... x... c...')
put(35, 'c... x... c... x.x.')
put(36, 'h... .... x.x. x...')
put(37, 'c... x... h... h...')
put(38, 'h... .... .... ....')
put(39, 'h... x... c... x...')
put(40, 'h... x... h... ....')
put(41, 'x... c... x... c...')
put(42, 'h... .... c... x...')
put(43, 'h... .... x... c...')
put(44, 'c... x... c... x...')
put(45, 'c... x... c... x.x.')
# 46-60 hold-heavy part
put(48, 'c... x... c... x...')
put(49, 'h... ..x. h... ....')
put(50, '.... c... x... c...')
put(51, 'h... x... c... x...')
put(52, 'c... x... x... c...')
put(53, 'h... ..x. h... ..x.')
put(54, 'h... .... c... x...')
put(55, 'h... .... x... c...')
put(56, 'h... x... x... x...')
put(57, 'h... x... x.c. ....')
put(58, 'h... .... .... c.x.')
put(59, 'h... .... ..x. x.x.')
# 61-68 chord section (special note at 65)
put(61, '.... ..x. c... x...')
put(62, '..x. c... x... ..x.')
put(63, 'c... x... ..x. c...')
put(64, 'c... ..x. x... c...')
put(65, '..x. c... .... ..x.')
put(66, 'c... x... ..x. c...')
put(67, 'c... ..x. x... c...')
put(68, '..x. x... c... x.x.')
put(70, 'x.x. x... c... ..h.')
put(71, '..h. ..x. ..h. ..x.')
put(72, 'h... x... c... ..x.')
put(73, 'c... ..h. x... ....')
put(74, 'c... x... x.h. ..x.')
put(75, 'c.h. ..x. x.h. ..x.')
put(76, 'c... x... c... x...')
put(77, 'c... h... x... x.x.')
put(78, 'x... h... x.h. ..x.')
put(79, 'x... h... x.h. ..x.')
put(80, 'h... h... x... x...')
put(81, '..h. ..x. x.h. ....')
put(82, '.... x... c.h. ..x.')
put(83, 'x.x. h... x.h. ....')
put(84, '.... c... c... x...')
put(85, 'x.x. h... x.h. ....')
put(86, '.... c... x.h. ..x.')
put(87, 'h... x... x... c...')
put(88, 'c... x... h... c...')
put(89, 'x.h. ..x. x.h. ....')
put(90, '.... x.x. x.h. ....')
put(91, 'c... x... c... x...')
put(92, 'c... x... c... x.x.')
put(93, 'c... h... .... x.x.')
put(94, 'x.x. c... x.x. x...')
# final chorus
put(95, 'c... x... c... x.x.')
put(96, 'c... x... x... x...')
put(97, 'x... c... x... x.x.')
put(98, 'c... x... x... c...')
put(99, 'c... x... c... x...')
put(100,'x.x. h... x.h. ..x.')
put(101,'h... h... h... h...')
put(102,'..x. c... h... ....')
put(103,'.... x... x.x. x...')
put(104,'x... x.x. h... ....')
put(105,'x.x. c... x... c...')

def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
O = {
    46:  cells(s0='h23'),
    47:  cells(s0='h2', s4='4', s8='3', s12='4'),
    60:  cells(s0='h3', s4='2', s8='h1'),
    # 16th stream -> two-hand stairs
    69:  cells(s0='23', s4='1', s6='2', s8='3', s10='4', s12='2', s14='3'),
    105: cells(s0='3', s2='4', s4='12', s8='3', s12='14'),
    106: cells(s0='h14', s4='23'),
}
