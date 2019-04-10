###############################
## Main file to run reasoner ##
###############################
from qreasoner import QualitativeReasoner
from state_graph import create_default_graph, create_extended_graph, set_debugging
import argparse
import os 

parser = argparse.ArgumentParser()
parser.add_argument("-d","--debug", help="Increases output to all generated transitions and states", action="store_true")
parser.add_argument("--graph", help="Options for which graph to use. 1: default in the report, 2: bidrectional value constraints, 3: extended graph with height and pressure. Default: 1", type=int, default=1)
parser.add_argument("--all_states", help="Generates all states and not only from initial zero state.", action="store_true")
parser.add_argument("--state_graph", help="Filename for state graph dot file. Default: \"state_graph.dot\"", type=str, default="state_graph.dot")
parser.add_argument("--intra_state", help="Filename for intra state description file. Default: \"intra_state_description.txt\"", type=str, default="intra_state_description.txt")
parser.add_argument("--inter_state", help="Filename for inter state description file. Default: \"inter_state_description.txt\"", type=str, default="inter_state_description.txt")
parser.add_argument("--state_trans", help="Filename for state transition description file. Default: \"transition_description.txt\"", type=str, default="transition_description.txt")

args = parser.parse_args()

graph = None
if args.graph == 1:
	graph = create_default_graph(bidirectional_vc=False)
elif args.graph == 2:
	graph = create_default_graph(bidirectional_vc=True)
elif args.graph == 3:
	graph = create_extended_graph()

set_debugging(args.debug)

reasoner = QualitativeReasoner(graph)
reasoner.simulate(generate_all_states=args.all_states, 
				  filename_state_graph=args.state_graph, 
				  filename_state_transitions=args.state_trans,
				  filename_intra_state=args.intra_state,
				  filename_inter_state=args.inter_state)
os.system("dot -Tpdf " + args.state_graph + " -o " + args.state_graph.rsplit(".",1)[0] + ".pdf")