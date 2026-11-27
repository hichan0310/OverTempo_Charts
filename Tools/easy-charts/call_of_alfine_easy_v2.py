import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rhythm
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Songs", "Call of Alfine/Call_of_Alfine_7k_folded_base.4k-speedcoef.json")
R = rhythm.easy(SRC)
O = {}
