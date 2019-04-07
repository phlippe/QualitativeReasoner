from state_graph import Entity, Quantity, Relationship, State, create_default_graph
from visualization import visualize_state_graph
from copy import copy
import sys 

class ContainerReasoner:

	def __init__(self):
		entities, quantities, relations = create_default_graph()
		self.state_list = list()
		self.state_connections = dict()
		self.quantities = quantities
		self.quantities[1].derivative = Quantity.POSITIVE

	def start(self):
		self.add_to_state_list(self.quantities, None)
		print("Found " + str(len(self.state_list)) + " states")
		visualize_state_graph("test_states.dot", self.state_list, self.state_connections)


	def find_next_states(self, quantities, orig_state):
		epsilon_transitions = self.create_epsilon_transitions(quantities)
		value_terminations = self.create_value_terminations(quantities)
		exogenous_terminations = self.create_exogenous_terminations(quantities[0])
		poss_transitions = self.create_cross_product(epsilon_transitions, value_terminations, exogenous_terminations)
		for t in poss_transitions:
			next_state_quant = self.create_next_state(quantities, t)
			if next_state_quant is not None:
				self.add_to_state_list(next_state_quant, orig_state)


	def add_to_state_list(self, quantities, orig_state):
		s = State(quantities)
		res = self.is_in_state_list(s)
		if res < 0:
			s_index = len(self.state_list)
			self.state_list.append(s)
			self.state_connections[s_index] = list()
			if orig_state is not None:
				self.state_connections[s_index] = [self.state_list.index(orig_state)]
			if len(self.state_list) <= 2:
				self.find_next_states(quantities, s)
		elif orig_state is not None:
			if res not in self.state_connections[self.state_list.index(orig_state)]:
				self.state_connections[self.state_list.index(orig_state)].append(res)


	def is_in_state_list(self, s):
		for i, st in enumerate(self.state_list):
			if st == s:
				return i
		return -1 

	def copy_quantities(quantities):
		return [copy(q) for q in quantities]

	def create_epsilon_transitions(self, quantities):
		# If quantity has derivative at landmark, add transition/termination here
		return list()

	def create_value_terminations(self, quantities):
		# For all quantities, check if a value termination is possible (magnitude based on derivative, derivative based on second order derivative)
		# But only if magnitude is an interval. The landmarks are considered in epsilon transitions
		return list()

	def create_exogenous_terminations(self, quantity):
		# Check for single quantity, to what we can change the derivative. Note that staying the same is *not* a transition!
		# For positive derivative => zero derivative
		# For negative derivative => zero derivative
		# For zero derivative => positive derivative (if magnitude != max, not possible for inflow), negative derivative (if magnitude != 0)
		return list()

	def create_cross_product(self, epsilon_transitions, value_terminations, exogenous_terminations):
		# Combining epsilon, value and exogenous terminations together.
		# All epsilon transitions always have to happen, but all possible combinations of value terminations and exogenous terminations must be generated
		# Create set of larger transitions that summarize all possible transitions
		# Already remove transitions that are not able (if for example one sets derivative to +, the other to -; unsure if that is even possible)
		return list()


# Class for testing basic functionalities of reasoner above
class ReasonerTest:

	def __init__(self):
		self.reasoner = ContainerReasoner()

	def run_tests(self):
		tests = [self.test_epsilon_transitions,
				 self.test_value_terminations,
				 self.test_exogenous_terminations,
				 self.test_cross_product]

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
		pass

	def test_value_terminations(self):
		pass

	def test_exogenous_terminations(self):
		pass

	def test_cross_product(self):
		pass


if __name__ == '__main__':
	tester = ReasonerTest()
	tester.run_tests()
	# r = ContainerReasoner()
	# r.start()