# キミとボクへの葬送歌 easy (Lv4). '=' keeps the original measure (already easy: intro holds, quarter verses).
R = {}
def put(ms, s):
    for m in (ms if isinstance(ms, (list, range)) else [ms]): R[m] = s.replace(' ', '')
put(list(range(2, 17, 2)), '=')         # double holds every other bar
put(range(18, 26), '=')                 # quarter-note verse
put(26, 'h... ..h. ..h. ..h.')
put(27, '..c. x... h... x...')
put(28, 'c... x... c... x...')
put(29, 'x... x... x... x.x.')
put(30, 'h... x.h. ..x. x...')
put(31, 'x... x... h... ..h.')
put(32, '..x. c... c... x...')
put(33, 'c... x... x... h...')
put(34, 'x... c... x... c...')
put(35, 'x.x. x... h... c...')
put(36, 'c... x... c... x.x.')
put(37, '.... .... .... c.x.')
put(38, 'c... x... h... x...')
put(39, 'c... x... x... c...')
put(40, 'x... c... x... c...')
put(41, 'x.x. x... x... x...')
put(42, 'h... x.h. .... ....')
put(43, 'x... c... c... x...')
put(44, 'h... ..h. .... ....')
put(45, 'x... x... x... c...')
put(46, 'h... ..h. .... ....')
put(47, 'x... x... c... x...')
put(48, 'h... x.h. .... ....')
put(49, 'x... x... c... x...')
put(50, 'h... x.h. x... h...')
put(52, 'h... ..h. .... h...')
put(53, '.... x.x. h... ....')
put(54, 'h... x.h. x... x...')
put(55, 'c... x... x... c...')
put(56, 'h... x.h. x... x...')
put(57, 'h... ..h. x... ....')
put(58, '=')
put(59, 'h... c... x... ..x.')
put(60, '=')
put(61, 'x... x... x... c...')
put(64, 'h... .... c... x...')
put(65, 'c... x... x... c...')
put(66, 'x... x... c..x ..x.')     # the song's 3-3-2 kept
put(67, '..c. .x.. x... x...')
put(68, 'x.x. x.x. x... x...')
put(69, 'x... c... x... c...')
put(70, '.... .... c... x...')
put(71, '=')                        # special note
put(range(74, 82), 'c... ..h. ..x. x...')
put(range(82, 87), '=')
put(87, 'x... x... x... c...')
put(88, 'x... c... x... c...')
put(89, 'x.x. c... x... c...')
put(90, '=')
put(range(91, 97), '=')             # special notes over silence
put(97, 'c... x... x... c...')
put(98, 'h... x... x... c...')
put(99, 'x... c... h... x...')
put(100,'x... x... c... ..h.')
put(101,'=')
put(102,'h... x.h. ..x. x...')
put(103,'c... x... c... x...')
put(104,'c... h... x... x...')
put(105,'x... x... c... x.x.')
put(106,'h... x.h. ..x. ..h.')
put(107,'..x. c... h... x...')
put(108,'x... x... c... ..h.')
put(109,'=')
put(110,'x... x... h... x...')
put(111,'x... c... c... x...')
put(112,'h... x... x... x.x.')
put(range(114, 123), '=')
put(123,'..x. x... x.x. h...')
put(124,'x... h... x... x...')
put(125,'=')
put(126,'x... x.h. ..x. x...')
put(127,'..x. x... x... c...')
put(130,'=')

def cells(**slots):
    row = ['.'] * 16
    for k, v in slots.items(): row[int(k[1:])] = v
    return row
O = {
    27:  cells(s2='34', s4='1', s8='h2', s12='3'),
    99:  cells(s0='1', s4='34', s8='h1', s12='3'),
    111: cells(s0='4', s4='23', s8='14', s12='2'),
    # 8th 4-1 trill -> quarter swings
    62:  cells(s0='h23', s4='4', s8='1', s12='4'),
    63:  cells(s0='1', s4='4', s8='1', s12='4'),
    72:  cells(s0='24', s4='3', s8='24', s12='3'),
    73:  cells(s0='1', s4='3', s8='14', s12='2'),
    113: cells(s0='14', s4='2', s8='3', s12='h4'),
    128: cells(s0='14', s4='14', s12='23'),
    129: cells(s0='23', s14='3'),
}
