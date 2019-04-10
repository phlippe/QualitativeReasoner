####################################
## Main file for reasoning engine ##
####################################

from state_graph import Entity, Quantity, Relationship, State, Termination, create_default_graph, debugging_active
from visualization import visualize_state_graph, save_transitions, save_intra_state_trace, save_inter_state_trace
from copy import copy
import sys 


################
## Qualitative Reasoning engine
################
class QualitativeReasoner:

	def __init__(self, graph=None):
		if graph is None:
			entities, quantities, relations = create_default_graph()
		else:
			entities, quantities, relations = graph
		self.state_list = list()
		self.state_connections = dict()
		self.state_transitions = dict()
		self.quantities = quantities
		self.relations = relations

	# Main function. Start reasoning process
	def simulate(self, generate_all_states=False, 
				 filename_state_graph="test_states.dot", 
				 filename_state_transitions="test_states_transitions.txt",
				 filename_intra_state="intra_state_trace.txt",
				 filename_inter_state="inter_state_trace.txt"):
		self.add_to_state_list(self.quantities, None)
		if generate_all_states:
			self.try_all_states()
		print("Found " + str(len(self.state_list)) + " states")
		print("Found " + str(sum([len(val) for key, val in self.state_connections.items()])) + " transitions")
		visualize_state_graph(filename_state_graph, self.state_list, self.state_connections)
		save_transitions(filename_state_transitions, self.state_list, self.state_connections, self.state_transitions)
		save_intra_state_trace(filename_intra_state, self.relations, self.state_list)
		save_inter_state_trace(filename_inter_state, self.state_list, self.state_connections, self.state_transitions)

	# Extension for generating all possible states. First creates all possible states, filters those that are not possible, and continues by reasoning from those
	def try_all_states(self):
		poss_vals = []
		for q in self.quantities:
			poss_vals.append(len(q.magn_space))
			poss_vals.append(len(q.deriv_space))
			if q.model_2nd_derivative:
				poss_vals.append(len(q.deriv_2nd_space))
		combs = QualitativeReasoner.generate_all_combinations(len(poss_vals), poss_vals)
		if debugging_active():
			print("Creating all possible states\n" + "="*30)
			print("Number of possible combinations: " + str(len(combs)))
			print("Possible values: " + str(poss_vals))

		for c_index, c in enumerate(combs):
			if c_index % 1000 == 0:
				print("Checked %4.2f%% of all states" % (100*c_index/len(combs)), end="\r")
			index = 0
			quants = QualitativeReasoner.copy_quantities(self.quantities)
			for q in quants:
				q.set_value(magnitude=q.magn_space[c[index]])
				index += 1
				q.set_value(derivative=q.deriv_space[c[index]])
				index += 1
				if q.model_2nd_derivative:
					q.set_value(derivative_2nd=q.deriv_2nd_space[c[index]])
					index += 1
			if all([q.is_quantity_valid(quants) for q in quants]):
				self.add_to_state_list(quants, None)

	# Finds the next state of a given state by the three steps described in the report
	def find_next_states(self, quantities, orig_state):
		# Step 1: Create terminations
		epsilon_terminations = self.create_epsilon_terminations(quantities)
		value_terminations = self.create_value_terminations(quantities)
		exogenous_terminations = self.create_exogenous_terminations(quantities)
		ambiguous_terminations = self.create_ambiguous_terminations(quantities)
		# Step 2: Combine terminations to transitions
		poss_transitions = self.create_cross_product(epsilon_terminations, value_terminations + exogenous_terminations + ambiguous_terminations)
		# Step 3: Check transitions to valid states
		for t in poss_transitions:
			next_state_quant = self.create_next_state(QualitativeReasoner.copy_quantities(quantities), t)
			if next_state_quant is not None:
				if debugging_active():
					print("Creating new state by the following transition: ")
					t.print()
				# Note: will be recursive call of this function is state is new
				self.add_to_state_list(next_state_quant, orig_state, t)
			else:
				if debugging_active():
					print("Invalid transition:")
					t.print()

	# Adds a state to the state list if it is not in there, and starts reasoning process again
	# If state already in state list, just adds new transition (if also not already there)
	def add_to_state_list(self, quantities, orig_state, transition=None):
		s = State(quantities)
		res = self.is_in_state_list(s)
		if res < 0:
			s_index = len(self.state_list)
			if debugging_active():
				print("Adding new state " + str(s_index))
				s.print()
			self.state_list.append(s)
			self.state_connections[s_index] = list()
			self.state_transitions[s_index] = dict()
			if orig_state is not None:
				self.state_connections[s_index] = [self.state_list.index(orig_state)]
				self.state_transitions[s_index] = {self.state_list.index(orig_state): transition}
			self.find_next_states(QualitativeReasoner.copy_quantities(quantities), s)
		elif orig_state is not None:
			if self.state_list.index(orig_state) not in self.state_connections[res] and res != self.state_list.index(orig_state):
				self.state_connections[res].append(self.state_list.index(orig_state))
				self.state_transitions[res][self.state_list.index(orig_state)] = transition

	# Checks whether certain state is already state list. If yes, returns its position
	def is_in_state_list(self, s):
		for i, st in enumerate(self.state_list):
			if st == s:
				return i
		return -1 

	# Deep copy of quantity list
	@staticmethod
	def copy_quantities(quantities):
		return [copy(q) for q in quantities]

	# Searches for epsilon terminations in current state
	def create_epsilon_terminations(self, quantities):
		# If quantity has derivative at landmark, add transition/termination here
		eps_term = Termination(term_type=Termination.EPSILON)
		for q in quantities:
			# 1st order derivative changing magnitude
			if q.derivative != Quantity.ZERO and Quantity.is_landmark(q.magnitude):
				prev_index = q.magn_space.index(q.magnitude)
				if q.derivative == Quantity.POSITIVE:
					new_index = prev_index + 1
				else:
					new_index = prev_index - 1
				if new_index < 0:
					print("Warning: magnitude index out of bounds. Lowest magnitude landmark with negative derivative at quantity " + str(q.name))
				elif new_index > len(q.magn_space):
					print("Warning: magnitude index out of bounds. Highest magnitude landmark with positive derivative at quantity " + str(q.name))
				val_change = [q.magn_space[new_index], Termination.UNCHANGED, Termination.UNCHANGED]
				eps_term.add_change(q, val_change)

			# 2nd order derivative changing 1st order derivative
			if q.derivative_2nd != Quantity.ZERO and Quantity.is_landmark(q.derivative):
				prev_index = q.deriv_space.index(q.derivative)
				if q.derivative_2nd == Quantity.POSITIVE:
					new_index = prev_index + 1
				else:
					new_index = prev_index - 1
				if new_index < 0:
					print("Warning: derivative index out of bounds. Lowest derivative landmark with negative 2nd order derivative at quantity " + str(q.name))
				elif new_index > len(q.deriv_space):
					print("Warning: derivative index out of bounds. Highest derivative landmark with positive 2nd oder derivative at quantity " + str(q.name))
				val_change = [Termination.UNCHANGED, q.deriv_space[new_index], Termination.UNCHANGED]
				eps_term.add_change(q, val_change)

		return eps_term

	# Searches for value terminations in current state
	def create_value_terminations(self, quantities):
		# For all quantities, check if a value termination is possible (magnitude based on derivative, derivative based on second order derivative)
		# But only if magnitude is an interval. The landmarks are considered in epsilon transitions
		val_terms = list()
		for q in quantities:
			# 1st order derivative changing magnitude
			if q.derivative != Quantity.ZERO and not Quantity.is_landmark(q.magnitude):
				prev_index = q.magn_space.index(q.magnitude)
				if q.derivative == Quantity.POSITIVE:
					new_index = prev_index + 1
				else:
					new_index = prev_index - 1
				if new_index < 0 or new_index >= len(q.magn_space):
					# If out of bounds, then there is no possible value transition
					# Still, not a warning/error because inflow can be (+,+) without any value terminations
					continue
				val_change = [q.magn_space[new_index], Termination.UNCHANGED, Termination.UNCHANGED]
				val_terms.append(Termination(q, val_change, term_type=Termination.VALUE))

			# 2nd order derivative changing 1st order derivative
			if q.derivative_2nd != Quantity.ZERO and not Quantity.is_landmark(q.derivative):
				prev_index = q.deriv_space.index(q.derivative)
				if q.derivative_2nd == Quantity.POSITIVE:
					new_index = prev_index + 1
				else:
					new_index = prev_index - 1
				if new_index < 0 or new_index >= len(q.deriv_space):
					# If out of bounds, then there is no possible value transition
					# Still, not a warning/error because inflow can be (+,+) without any value terminations
					continue
				val_change = [Termination.UNCHANGED, q.deriv_space[new_index], Termination.UNCHANGED]
				val_terms.append(Termination(q, val_change, term_type=Termination.VALUE))

		return val_terms

	# Searches for exogenous terminations in current state
	def create_exogenous_terminations(self, quantities):
		# Check for single quantity, to what we can change the derivative. Note that staying the same is *not* a transition!
		# For positive derivative => zero derivative
		# For negative derivative => zero derivative
		# For zero derivative => positive derivative (if magnitude != max, not possible for inflow), negative derivative (if magnitude != 0)
		exog_terms = list()
		for quantity in quantities:
			if not quantity.exogenous:
				continue
			if quantity.derivative == Quantity.POSITIVE or quantity.derivative == Quantity.NEGATIVE:
				exog_terms.append(Termination(quantity, [Termination.UNCHANGED, Quantity.ZERO, Termination.UNCHANGED], term_type=Termination.EXOGENOUS))
			if quantity.derivative == Quantity.ZERO:
				if not (quantity.magnitude == quantity.magn_space[-1] and Quantity.is_landmark(quantity.magnitude)):
					exog_terms.append(Termination(quantity, [Termination.UNCHANGED, Quantity.POSITIVE, Termination.UNCHANGED], term_type=Termination.EXOGENOUS))
				if not (quantity.magnitude == quantity.magn_space[0] and Quantity.is_landmark(quantity.magnitude)):
					exog_terms.append(Termination(quantity, [Termination.UNCHANGED, Quantity.NEGATIVE, Termination.UNCHANGED], term_type=Termination.EXOGENOUS))
		return exog_terms

	# Searches for ambiguous terminations in current state
	def create_ambiguous_terminations(self, quantities):
		# Check for all influence relations, if we have an ambiguity. If yes, it is possible to change (given 2nd order derivative)
		amb_terms = list()
		for q in quantities:
			magn_constraints, deriv_influences, deriv_2nd_influences = q.get_influences_on_quantity(quantities)
			pos_infs = sum([i == Quantity.POSITIVE for i in deriv_2nd_influences])
			neg_infs = sum([i == Quantity.NEGATIVE for i in deriv_2nd_influences])
			if pos_infs > 0 and neg_infs > 0:
				if q.derivative_2nd == Quantity.POSITIVE or q.derivative_2nd == Quantity.NEGATIVE:
					amb_terms.append(Termination(q, [Termination.UNCHANGED, Termination.UNCHANGED, Quantity.ZERO], term_type=Termination.AMBIGUOUS))
				if q.derivative_2nd == Quantity.ZERO:
					amb_terms.append(Termination(q, [Termination.UNCHANGED, Termination.UNCHANGED, Quantity.POSITIVE], term_type=Termination.AMBIGUOUS))
					amb_terms.append(Termination(q, [Termination.UNCHANGED, Termination.UNCHANGED, Quantity.NEGATIVE], term_type=Termination.AMBIGUOUS))

		return amb_terms

	# Combines terminations to transitions
	def create_cross_product(self, epsilon_terminations, extra_terminations):
		# Combining epsilon, value, ambiguity and exogenous terminations together.
		# All epsilon transitions always have to happen, but all possible combinations of value terminations and exogenous terminations must be generated
		# Create set of larger transitions that summarize all possible transitions
		# Already remove transitions that are not able (if for example one sets derivative to +, the other to -; unsure if that is even possible
		poss_combs = QualitativeReasoner.generate_all_combinations(len(extra_terminations))
		poss_terminations = list()
		for comb in poss_combs:
			term = epsilon_terminations.copy()
			valid_transition = True
			for c, extra_term in zip(comb, extra_terminations):
				if c == 1:
					valid_transition = valid_transition and term.combine_terminations(extra_term)
					if not valid_transition:
						break
			if not valid_transition:
				continue
			poss_terminations.append(term)
		return poss_terminations

	# Given a state (quantity values) and a transition/termination, try to come to a valid state
	def create_next_state(self, quantities, termination):
		# Apply transition and check if it leads to a valid state or not
		# Unsure if we might need to handle ambiguity here or if it is done in the transitions
		for q, v in zip(termination.quantities, termination.vals):
			for quant in quantities:
				if q.name == quant.name:
					if v[0] != Termination.UNCHANGED:
						quant.magnitude = v[0]
						quant.magnitude_fixed = True
					if v[1] != Termination.UNCHANGED:
						quant.derivative = v[1]
						quant.derivative_fixed = True
					if v[2] != Termination.UNCHANGED:
						quant.derivative_2nd = v[2]
						quant.derivative_2nd_fixed = True
					break

		valid_state = all([q.is_quantity_valid(quantities) for q in quantities])
		invalid_state = False
		while not valid_state and not invalid_state:
			for q in quantities:
				if not q.make_quantity_valid(quantities):
					invalid_state = True
					break
			valid_state = all([q.is_quantity_valid(quantities) for q in quantities])
		
		if invalid_state:
			return None

		for quant in quantities:
			quant.remove_fixing()
		return quantities

	# Getter for quantity by name
	def get_quantity(self, q_name):
		for q in self.quantities:
			if q.name == q_name:
				return q 
		return None

	# Function for generating all possible combinations of terminations and states
	@staticmethod
	def generate_all_combinations(num, poss=2):
		all_combs = [list()]
		for i in range(num):
			new_combs = list()
			for c in all_combs:
				if not isinstance(poss, list):
					for r in [1,0]:
						new_combs.append(c + [r])
				else:
					for r in range(poss[i]):
						new_combs.append(c + [r])
			all_combs = new_combs
		return all_combs


if __name__ == '__main__':
	r = QualitativeReasoner()
	r.start()

