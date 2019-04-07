from state_graph import Entity, Quantity, Relationship, State, create_default_graph

def visualize_system(filename, entities, relations=None):

	if relations is None:
		relations = list()
		for e in entities:
			for q in e.quantities:
				relations += q.relations
		relations = list(set(relations))

	s = "digraph graphname {\n"
	state_dict = dict()
	state_index = 0
	for e in entities:
		s += "\ts" + str(state_index) + " [label=\"" + str(e.name) + "\", style=filled, color=\"grey\"];\n"
		state_dict[e] = state_index
		state_index += 1
		for q in e.quantities:
			s += "\ts" + str(state_index) + " [label=\"" + str(q.name) + " (" + q.magnitude + "," + q.derivative + ")\", style=filled, color=\"#AAAADD\"];\n"
			s += "\ts" + str(state_dict[e]) + " -> s" + str(state_index) + " [color=\"#5555FF\"];\n"
			state_dict[q] = state_index
			state_index += 1

	for r in relations:
		s += "\ts" + str(state_index) + " [shape=box, label=\""+r.to_string()+"\"];\n"
		s += "\ts" + str(state_index) + " -> s" + str(state_dict[r.q1]) + " [arrowhead=none];\n"
		s += "\ts" + str(state_index) + " -> s" + str(state_dict[r.q2]) + ";\n"
		state_index += 1

	s += "}"
	with open(filename, "w") as f:
		f.write(s)


def visualize_state_graph(filename, state_list, state_connections):
	dot_file_string = "digraph graphname {\n"
	for i, s in enumerate(state_list):
		dot_file_string += "\ts" + (str(i)) + " [shape=box, label=\"" + state_to_label(s, i) + "\"];\n"

	for s_c, s_list in state_connections.items():
		for source in s_list:
			dot_file_string += "\ts" + str(source) + " -> s" + str(s_c) + ";\n"

	dot_file_string += "}"
	with open(filename, "w") as f:
		f.write(dot_file_string)

def state_to_label(s, i):
	label = "State " + str(i) + "\n"
	for key, val in s.value_dict.items():
		label += key + " (" + str(val[0]) + "," + str(val[1]) + ")\n"
	return label

if __name__ == "__main__":
	entities, _, relations = create_default_graph()
	visualize_system('test.dot', entities, relations)