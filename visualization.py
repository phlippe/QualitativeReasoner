###########################################
# Functions for visualization and tracing #
###########################################

from state_graph import Termination,Entity, Quantity, Relationship, State, create_default_graph
import random

# Visualizing causal model
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

# Visualizing a state graph as shown in the report
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
# Helper function to convert state to text (label for dot node)
def state_to_label(s, i):
	label = "State " + str(i) + "\n"
	for key, val in s.value_dict.items():
		label += key + " (" + ",".join(val) + ")\n"
	return label

# Exports transitions for debugging
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


#############
## Tracing ##
#############

# Inter-state trace relies on transitions/terminations that were used. 
def save_inter_state_trace(filename, state_list, state_connections, state_transitions):
	s = "Inter state trace\n"
	s += "#" * 50 + "\n"
	for goal_state, connections in state_transitions.items():
		for source_state, transition in connections.items():
			sub_s = "** Transition from " + str(source_state) + " to " + str(goal_state) + " **"
			s += "*"*len(sub_s) + "\n" + sub_s + "\n" + "*"*len(sub_s) + "\n"
			for q, vs, typ in zip(transition.quantities, transition.vals, transition.types):
				if vs[0] != Termination.UNCHANGED:
					s += "The magnitude of " + q.name + " changes from " + state_list[source_state].value_dict[q.name][0] + " to " + vs[0] + " because" + termination_type_to_text(typ[0], vs[0], state_list[source_state].value_dict[q.name][0], state_list[source_state].value_dict[q.name][1]) + "\n"
				if vs[1] != Termination.UNCHANGED:
					s += "The derivative of " + q.name + " changes from " + state_list[source_state].value_dict[q.name][1] + " to " + vs[1] + " because" + termination_type_to_text(typ[1], vs[1], state_list[source_state].value_dict[q.name][1], state_list[source_state].value_dict[q.name][2] if len(state_list[source_state].value_dict[q.name])>2 else None) + "\n"
				if q.model_2nd_derivative and len(vs) > 2 and vs[2] != Termination.UNCHANGED:
					s += "The second order derivative of " + q.name + " changes from " + state_list[source_state].value_dict[q.name][2] + " to " + vs[2] + " because" + termination_type_to_text(typ[2], vs[2], state_list[source_state].value_dict[q.name][2], None) + "\n"
	
	with open(filename, "w") as f:
		f.write(s)		

# Intra-state trace is generated by taking a state and describing the values as well as the active influences on quantities
def save_intra_state_trace(filename, relations, state_list):
	s = "Intra state trace\n"
	s += "#" * 50 + "\n"
	for s_index, state in enumerate(state_list):
		s += "="*50+"\nState " + str(s_index) + "\n" + "-"*50 + "\n"
		for q_name, vals in state.value_dict.items():
			s += "The " + q_name + " " + magnitude_to_text(vals[0]) + " and " + derivative_to_text(vals[1]) + "."
			if len(vals) > 2:
				s += " " + get_random_phrase() + " the derivative of " + q_name + " " + derivative_to_text(vals[2]) + "."
			s += "\n"
		for rel in relations:
			if rel.rel_opt == Relationship.INFLUENCE:
				s += rel.q1.name + " has " + influence_to_text(state.value_dict[rel.q1.name][0], rel.positive) + " on " + rel.q2.name + " which " + derivative_to_text(state.value_dict[rel.q1.name][1]) + ".\n"
		for q_name, vals in state.value_dict.items():
			if q_name == "Volume":
				s += "Combined, this leads to a " + ("positive" if vals[1] == Quantity.POSITIVE else ("negative" if vals[1] == Quantity.NEGATIVE else "empty")) + " influence which " + derivative_to_text(vals[2]) + ".\n"
		s += "="*50+"\n\n"

	with open(filename, "w") as f:
		f.write(s)


###########
## Helper function to convert values to text
###########

PHRASES = ["In addition,", "Additionally,", "Furthermore,","Consecutively,","Moreover,","As well,"]
def get_random_phrase():
	return PHRASES[random.randint(0,len(PHRASES)-1)]

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

def influence_to_text(infl_val, positive):
	if infl_val == Quantity.ZERO:
		return "no influence"
	elif positive and (infl_val == Quantity.POSITIVE or infl_val == Quantity.MAX_VAL) or \
		 not positive and (infl_val == Quantity.NEGATIVE or infl_val == Quantity.MIN_VAL):
		return "a positive influence"
	elif not positive and (infl_val == Quantity.POSITIVE or infl_val == Quantity.MAX_VAL) or \
		 positive and (infl_val == Quantity.NEGATIVE or infl_val == Quantity.MIN_VAL):
		return "a negative influence"
	else:
		return "an influence"

def termination_type_to_text(term_type, new_val, prev_val, deriv):
	if term_type == Termination.EPSILON:
		return " of an epsilon termination. The previous value " + prev_val + " is a landmark which we leave immediately (delta t -> 0) because of an " + ("positive" if deriv == Quantity.POSITIVE else "negative") + " derivative."
	elif term_type == Termination.VALUE:
		return " of a value termination. As its value " + derivative_to_text(deriv) + ", we are able to change in terms of the quantity space to the new value " + new_val + " at some point."
	elif term_type == Termination.EXOGENOUS:
		return " of a exogenous control."
	elif term_type == Termination.AMBIGUOUS:
		return " the influences on the quantity's value are ambiguous."
	return "everything"

