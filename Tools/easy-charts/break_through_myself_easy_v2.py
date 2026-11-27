import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rhythm
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Songs", 'Break Through Myself/Break_Through_Myself_osu_base.4k-speedcoef.json')
R = rhythm.easy(SRC, pair_every=2, chord_every=2)
O = {}
