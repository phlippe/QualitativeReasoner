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
	dot_file_string = "digraph graphname {\n\trankdir=LR;\n"
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
		label += key + " (" + ",".join(val) + ")\n"
	return label

def save_transitions(filename, state_list, state_connections, state_transitions):
	s = "Transition recording\n"
	s += "#"*50+"\n"
	for goal_state, connections in state_transitions.items():
		for source_state, transition in connections.items():
			sub_s = "** Transition from " + str(source_state) + " to " + str(goal_state) + " **"
			s += "*"*len(sub_s) + "\n" + sub_s + "\n" + "*"*len(sub_s) + "\n"
			s += transition.to_string()
			s += "-"*len(sub_s) + "\n" + "\n"

	with open(filename, "w") as f:
		f.write(s)


def save_inter_state_trace(filename, state_list, state_connections, state_transitions):
	s = "Inter state trace\n"
	s += "#" * 50 + "\n"
	pass


def save_intra_state_trace(filename, relations, state_list):
	s = "Intra state trace\n"
	s += "#" * 50 + "\n"
	for s_index, state in enumerate(state_list):
		s += "="*50+"\nState " + str(s_index) + "\n" + "-"*50 + "\n"
		for q_name, vals in state.value_dict.items():
			s += "The " + q_name + " " + magnitude_to_text(vals[0]) + " and " + derivative_to_text(vals[1]) + "."
			if len(vals) > 2:
				s += " In addition, the derivative of " + q_name + " " + derivative_to_text(vals[2]) + "."
			s += "\n"
		for rel in relations:
			if rel.rel_opt == Relationship.INFLUENCE:
				s += rel.q1.name + " has " + influence_to_text(state.value_dict[rel.q1.name][0]) + " on " + rel.q2.name + " which " + derivative_to_text(state.value_dict[rel.q1.name][1]) + ".\n"
		s += "="*50+"\n\n"

	with open(filename, "w") as f:
		f.write(s)


def magnitude_to_text(magn_val):
	if magn_val == Quantity.ZERO:
		return "is zero"
	elif magn_val == Quantity.POSITIVE:
		return "has a positive value"
	elif magn_val == Quantity.NEGATIVE:
		return "has a negative value"
	elif magn_val == Quantity.MAX_VAL:
		return "reached its maximum value"
	elif magn_val == Quantity.MIN_VAL:
		return "reached its minimum value"

def derivative_to_text(deriv_val):
	if deriv_val == Quantity.ZERO:
		return "stays steady"
	elif deriv_val == Quantity.POSITIVE:
		return "increases"
	elif deriv_val == Quantity.NEGATIVE:
		return "decreases"
	else:
		return "changes"

def influence_to_text(infl_val):
	if infl_val == Quantity.ZERO:
		return "no influence"
	if infl_val == Quantity.POSITIVE or infl_val == Quantity.MAX_VAL:
		return "a positive influence"
	if infl_val == Quantity.NEGATIVE or infl_val == Quantity.MIN_VAL:
		return "a negative influence"
	else:
		return "an influence"


if __name__ == "__main__":
	entities, _, relations = create_default_graph()
	visualize_system('test.dot', entities, relations)