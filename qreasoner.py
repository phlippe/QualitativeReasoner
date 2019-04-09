from state_graph import Entity, Quantity, Relationship, State, Termination, create_default_graph
from visualization import visualize_state_graph, save_transitions, save_intra_state_trace
from copy import copy
import sys 

class ContainerReasoner:

	def __init__(self):
		entities, quantities, relations = create_default_graph()
		self.state_list = list()
		self.state_connections = dict()
		self.state_transitions = dict()
		self.quantities = quantities
		self.relations = relations

	def start(self):
		self.add_to_state_list(self.quantities, None)
		print("Found " + str(len(self.state_list)) + " states")
		visualize_state_graph("test_states.dot", self.state_list, self.state_connections)
		save_transitions("test_states_transitions.txt", self.state_list, self.state_connections, self.state_transitions)
		save_intra_state_trace("intra_state_trace.txt", self.relations, self.state_list)


	def find_next_states(self, quantities, orig_state):
		epsilon_transitions = self.create_epsilon_transitions(quantities)
		value_terminations = self.create_value_terminations(quantities)
		exogenous_terminations = self.create_exogenous_terminations(quantities[0])
		ambiguous_terminations = self.create_ambiguous_terminations(quantities)
		poss_transitions = self.create_cross_product(epsilon_transitions, value_terminations + exogenous_terminations + ambiguous_terminations)
		
		for t in poss_transitions:
			next_state_quant = self.create_next_state(ContainerReasoner.copy_quantities(quantities), t)
			if next_state_quant is not None:
				print("Creating new state by the following transition: ")
				t.print()
				self.add_to_state_list(next_state_quant, orig_state, t)
			else:
				print("Invalid transition:")
				t.print()


	def add_to_state_list(self, quantities, orig_state, transition=None):
		s = State(quantities)
		res = self.is_in_state_list(s)
		if res < 0:
			s_index = len(self.state_list)
			print("Adding new state " + str(s_index))
			s.print()
			self.state_list.append(s)
			self.state_connections[s_index] = list()
			if orig_state is not None:
				self.state_connections[s_index] = [self.state_list.index(orig_state)]
				self.state_transitions[s_index] = {self.state_list.index(orig_state): transition}
			self.find_next_states(ContainerReasoner.copy_quantities(quantities), s)
		elif orig_state is not None:
			if self.state_list.index(orig_state) not in self.state_connections[res] and res != self.state_list.index(orig_state):
				self.state_connections[res].append(self.state_list.index(orig_state))
				self.state_transitions[self.state_list.index(orig_state)][res] = transition


	def is_in_state_list(self, s):
		for i, st in enumerate(self.state_list):
			if st == s:
				return i
		return -1 

	@staticmethod
	def copy_quantities(quantities):
		return [copy(q) for q in quantities]

	def create_epsilon_transitions(self, quantities):
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

	def create_exogenous_terminations(self, quantity):
		# Check for single quantity, to what we can change the derivative. Note that staying the same is *not* a transition!
		# For positive derivative => zero derivative
		# For negative derivative => zero derivative
		# For zero derivative => positive derivative (if magnitude != max, not possible for inflow), negative derivative (if magnitude != 0)
		exog_terms = list()
		if quantity.derivative == Quantity.POSITIVE or quantity.derivative == Quantity.NEGATIVE:
			exog_terms.append(Termination(quantity, [Termination.UNCHANGED, Quantity.ZERO, Termination.UNCHANGED], term_type=Termination.EXOGENOUS))
		if quantity.derivative == Quantity.ZERO:
			if not (quantity.magnitude == quantity.magn_space[-1] and Quantity.is_landmark(quantity.magnitude)):
				exog_terms.append(Termination(quantity, [Termination.UNCHANGED, Quantity.POSITIVE, Termination.UNCHANGED], term_type=Termination.EXOGENOUS))
			if not (quantity.magnitude == quantity.magn_space[0] and Quantity.is_landmark(quantity.magnitude)):
				exog_terms.append(Termination(quantity, [Termination.UNCHANGED, Quantity.NEGATIVE, Termination.UNCHANGED], term_type=Termination.EXOGENOUS))
		return exog_terms

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
		print("Number of found ambiguous terminations: " + str(len(amb_terms)))
		return amb_terms

	def create_cross_product(self, epsilon_transitions, extra_terminations):
		# Combining epsilon, value and exogenous terminations together.
		# All epsilon transitions always have to happen, but all possible combinations of value terminations and exogenous terminations must be generated
		# Create set of larger transitions that summarize all possible transitions
		# Already remove transitions that are not able (if for example one sets derivative to +, the other to -; unsure if that is even possible
		poss_combs = ContainerReasoner.generate_all_combinations(len(extra_terminations))
		poss_terminations = list()
		for comb in poss_combs:
			print("Creating transition for combination " + str(comb))
			term = epsilon_transitions.copy()
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

	def get_quantity(self, q_name):
		for q in self.quantities:
			if q.name == q_name:
				return q 
		return None

	@staticmethod
	def generate_all_combinations(num):
		all_combs = [list()]
		for _ in range(num):
			new_combs = list()
			for c in all_combs:
				new_combs.append(c + [1])
				new_combs.append(c + [0])
			all_combs = new_combs
		return all_combs


# Class for testing basic functionalities of reasoner above
class ReasonerTest:

	def __init__(self):
		self.reasoner = ContainerReasoner()

	def run_tests(self):
		tests = [self.test_epsilon_transitions,
				 self.test_value_terminations,
				 self.test_exogenous_terminations,
				 self.test_cross_product,
				 self.test_quantity_valid_checking]

		print("="*30)
		print("Starting " + str(len(tests)) + " tests...")
		print("-"*30)
		passed = 0
		for test_fun in tests:
			success = test_fun()
			print("Test " + str(test_fun) + ": " + ("Passed" if success else "FAILED!"))
			if success:
				passed += 1

		print("-"*30)
		print(str(passed) + " tests passed, " + str(len(tests) - passed) + " failed")
		print("="*30)

	def test_epsilon_transitions(self):
		quantities = ContainerReasoner.copy_quantities(self.reasoner.quantities)
		q_inflow = ReasonerTest.get_quantity(quantities, "Inflow")
		q_outflow = ReasonerTest.get_quantity(quantities, "Outflow")
		q_volume = ReasonerTest.get_quantity(quantities, "Volume")

		q_inflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		q_outflow.set_value(magnitude=Quantity.ZERO, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.POSITIVE)
		q_volume.set_value(magnitude=Quantity.ZERO, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.POSITIVE)

		eps_term = self.reasoner.create_epsilon_transitions(quantities)
		eps_term.print()

		term_quants = eps_term.quantities
		# TODO: Add real test condition here
		return True

	def test_value_terminations(self):
		quantities = ContainerReasoner.copy_quantities(self.reasoner.quantities)
		q_inflow = ReasonerTest.get_quantity(quantities, "Inflow")
		q_outflow = ReasonerTest.get_quantity(quantities, "Outflow")
		q_volume = ReasonerTest.get_quantity(quantities, "Volume")

		q_inflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		q_outflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.NEGATIVE, derivative_2nd=Quantity.POSITIVE)
		q_volume.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.NEGATIVE, derivative_2nd=Quantity.ZERO)

		val_terms = self.reasoner.create_value_terminations(quantities)
		print("#"*50)
		print("Found value terminations:")
		for term in val_terms:
			term.print()

		# TODO: Add real test condition here
		return True

	def test_exogenous_terminations(self):
		quantities = ContainerReasoner.copy_quantities(self.reasoner.quantities)
		q_inflow = ReasonerTest.get_quantity(quantities, "Inflow")
		q_outflow = ReasonerTest.get_quantity(quantities, "Outflow")
		q_volume = ReasonerTest.get_quantity(quantities, "Volume")

		q_inflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		exog_terms_1 = self.reasoner.create_exogenous_terminations(q_inflow)
		print("#"*50)
		print("Found exogenous terminations for case 1:")
		for term in exog_terms_1:
			term.print()

		q_inflow.set_value(magnitude=Quantity.ZERO, derivative=Quantity.ZERO, derivative_2nd=Quantity.ZERO)
		exog_terms_2 = self.reasoner.create_exogenous_terminations(q_inflow)
		print("#"*50)
		print("Found exogenous terminations for case 2:")
		for term in exog_terms_2:
			term.print()

		q_inflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.ZERO, derivative_2nd=Quantity.ZERO)
		exog_terms_3 = self.reasoner.create_exogenous_terminations(q_inflow)
		print("#"*50)
		print("Found exogenous terminations for case 3:")
		for term in exog_terms_3:
			term.print()

		# TODO: Add real test condition here
		return True

	def test_cross_product(self):
		quantities = ContainerReasoner.copy_quantities(self.reasoner.quantities)
		q_inflow = ReasonerTest.get_quantity(quantities, "Inflow")
		q_outflow = ReasonerTest.get_quantity(quantities, "Outflow")
		q_volume = ReasonerTest.get_quantity(quantities, "Volume")

		q_inflow.set_value(magnitude=Quantity.ZERO, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		q_outflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		q_volume.set_value(magnitude=Quantity.MAX_VAL, derivative=Quantity.NEGATIVE, derivative_2nd=Quantity.POSITIVE)

		eps_term = self.reasoner.create_epsilon_transitions(quantities)
		val_terms = self.reasoner.create_value_terminations(quantities)
		exog_terms = self.reasoner.create_exogenous_terminations(q_inflow)
		eps_term.print()

		poss_terms = self.reasoner.create_cross_product(eps_term, val_terms + exog_terms)
		print("#"*50)
		print("Found " + str(len(poss_terms)) + " possible terminations:")
		for term in poss_terms:
			term.print()

		# TODO: Add real test condition here
		return True

	def test_quantity_valid_checking(self):
		quantities = ContainerReasoner.copy_quantities(self.reasoner.quantities)
		q_inflow = ReasonerTest.get_quantity(quantities, "Inflow")
		q_outflow = ReasonerTest.get_quantity(quantities, "Outflow")
		q_volume = ReasonerTest.get_quantity(quantities, "Volume")

		q_inflow.set_value(magnitude=Quantity.ZERO, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		q_outflow.set_value(magnitude=Quantity.ZERO, derivative=Quantity.ZERO, derivative_2nd=Quantity.ZERO)
		q_volume.set_value(magnitude=Quantity.ZERO, derivative=Quantity.ZERO, derivative_2nd=Quantity.ZERO)

		q_inflow.remove_fixing()
		q_outflow.remove_fixing()
		q_volume.remove_fixing()
		q_volume.magnitude_fixed = True
		print("Quantity inflow valid: " + str(q_inflow.is_quantity_valid(quantities)))
		print("Quantity outflow valid: " + str(q_outflow.is_quantity_valid(quantities)))
		print("Quantity volume valid: " + str(q_volume.is_quantity_valid(quantities)))
		outflow_possible = q_outflow.make_quantity_valid(quantities)
		volume_possible = q_volume.make_quantity_valid(quantities)
		print("Quantity outflow valid: " + str(q_outflow.is_quantity_valid(quantities)))
		print("Quantity volume valid: " + str(q_volume.is_quantity_valid(quantities)))
		q_outflow.print()
		q_volume.print()

		return True

	@staticmethod
	def get_quantity(quantities, q_name):
		for q in quantities:
			if q.name == q_name:
				return q 
		return None


if __name__ == '__main__':
	tester = ReasonerTest()
	tester.run_tests()
	print(ContainerReasoner.generate_all_combinations(5))

	r = ContainerReasoner()
	r.start()

