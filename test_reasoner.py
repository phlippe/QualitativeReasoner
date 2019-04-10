from state_graph import Entity, Quantity, Relationship, State, Termination, DEBUG
from qreasoner import QualitativeReasoner
import sys

# Class for testing basic functionalities of reasoner
# Is purely based on checking outputs in terminal currently
class ReasonerTest:

	def __init__(self):
		self.reasoner = QualitativeReasoner()

	def run_tests(self):
		tests = [self.test_epsilon_terminations,
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

	def test_epsilon_terminations(self):
		quantities = QualitativeReasoner.copy_quantities(self.reasoner.quantities)
		q_inflow = ReasonerTest.get_quantity(quantities, "Inflow")
		q_outflow = ReasonerTest.get_quantity(quantities, "Outflow")
		q_volume = ReasonerTest.get_quantity(quantities, "Volume")

		q_inflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		q_outflow.set_value(magnitude=Quantity.ZERO, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.POSITIVE)
		q_volume.set_value(magnitude=Quantity.ZERO, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.POSITIVE)

		eps_term = self.reasoner.create_epsilon_terminations(quantities)
		eps_term.print()

		term_quants = eps_term.quantities
		# TODO: Add real test condition here
		return True

	def test_value_terminations(self):
		quantities = QualitativeReasoner.copy_quantities(self.reasoner.quantities)
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
		quantities = QualitativeReasoner.copy_quantities(self.reasoner.quantities)
		q_inflow = ReasonerTest.get_quantity(quantities, "Inflow")
		q_outflow = ReasonerTest.get_quantity(quantities, "Outflow")
		q_volume = ReasonerTest.get_quantity(quantities, "Volume")

		q_inflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		exog_terms_1 = self.reasoner.create_exogenous_terminations(quantities)
		print("#"*50)
		print("Found exogenous terminations for case 1:")
		for term in exog_terms_1:
			term.print()

		q_inflow.set_value(magnitude=Quantity.ZERO, derivative=Quantity.ZERO, derivative_2nd=Quantity.ZERO)
		exog_terms_2 = self.reasoner.create_exogenous_terminations(quantities)
		print("#"*50)
		print("Found exogenous terminations for case 2:")
		for term in exog_terms_2:
			term.print()

		q_inflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.ZERO, derivative_2nd=Quantity.ZERO)
		exog_terms_3 = self.reasoner.create_exogenous_terminations(quantities)
		print("#"*50)
		print("Found exogenous terminations for case 3:")
		for term in exog_terms_3:
			term.print()

		# TODO: Add real test condition here
		return True

	def test_cross_product(self):
		quantities = QualitativeReasoner.copy_quantities(self.reasoner.quantities)
		q_inflow = ReasonerTest.get_quantity(quantities, "Inflow")
		q_outflow = ReasonerTest.get_quantity(quantities, "Outflow")
		q_volume = ReasonerTest.get_quantity(quantities, "Volume")
		
		q_inflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		q_outflow.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		q_volume.set_value(magnitude=Quantity.POSITIVE, derivative=Quantity.POSITIVE, derivative_2nd=Quantity.ZERO)
		
		eps_term = self.reasoner.create_epsilon_terminations(quantities)
		val_terms = self.reasoner.create_value_terminations(quantities)
		exog_terms = self.reasoner.create_exogenous_terminations(quantities)
		ambig_terms = self.reasoner.create_ambiguous_terminations(quantities)
		
		poss_terms = self.reasoner.create_cross_product(eps_term, val_terms + exog_terms + ambig_terms) # val_terms + exog_terms + 
		print("#"*50)
		print("Found " + str(len(poss_terms)) + " possible terminations:")
		for term in poss_terms:
			term.print()

		poss_terms[-2].print()
		next_state_quant = self.reasoner.create_next_state(QualitativeReasoner.copy_quantities(quantities), poss_terms[-2])
		s = State(quantities)
		s.print()
		# sys.exit(1)
		# TODO: Add real test condition here
		return True

	def test_quantity_valid_checking(self):
		quantities = QualitativeReasoner.copy_quantities(self.reasoner.quantities)
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


if name == '__main__':
	if DEBUG:
		tester = ReasonerTest()
		tester.run_tests()


