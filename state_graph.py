

class Termination:

	UNCHANGED = "unchanged"
	EPSILON = "Epsilon termination"
	VALUE = "Value termination"
	EXOGENOUS = "Exogenous termination"
	AMBIGUOUS = "Ambiguous termination"

	def __init__(self, quantities=None, vals=None, term_type=None):
		if quantities is None:
			quantities = list()
		elif not isinstance(quantities, list):
			quantities = [quantities]
		if vals is None:
			vals = list()
		elif len(vals) > 0 and not isinstance(vals[0], list):
			vals = [vals]
		self.quantities = quantities
		self.vals = vals
		if not isinstance(term_type, list):
			self.initial_term_type = term_type
			term_type = [[term_type if v != Termination.UNCHANGED else None for v in self.vals[v_index]] for v_index in range(len(vals))]
		else:
			if len(term_type) > 0 and not isinstance(term_type[0], list):
				term_type = [[term_type[v_index] if v != Termination.UNCHANGED else None for v in self.vals[v_index]] for v_index in range(len(vals))]
			self.initial_term_type = None
		self.types = term_type

	def add_change(self, quantity, val, term_type=None):
		if term_type is None:
			term_type = self.initial_term_type
		if not isinstance(term_type, list):
			term_type = [term_type if v != Termination.UNCHANGED else None for v in val]
		
		if quantity not in self.quantities:
			self.quantities.append(quantity)
			self.vals.append(val)
			self.types.append(term_type)
		else:
			index = self.quantities.index(quantity)
			for v_index in range(len(val)):
				if self.vals[index][v_index] == Termination.UNCHANGED:
					self.vals[index][v_index] = val[v_index]
					self.types[index][v_index] = term_type[v_index]
				elif val[v_index] != Termination.UNCHANGED and val[v_index] != self.vals[index][v_index]:
					# Cannot be combined, two different values to which it should be changed
					print("Warning: two value changed cannot be combined. Index " + str(index) + ", previously \"" + str(self.vals[index][v_index]) + "\", new value \"" + str(val[v_index]) + "\"")
					return False
		return True

	def combine_terminations(self, other_term):
		for q, v, t in zip(other_term.quantities, other_term.vals, other_term.types):
			return self.add_change(q,v,t)

	def print(self):
		print("="*40)
		print("Termination output")
		print("-"*40)
		print(self.to_string())
		print("="*40)

	def to_string(self):
		s = ""
		for q, q_vals, v_types in zip(self.quantities, self.vals, self.types):
			for v, t_type, m_name, prev_val in zip(q_vals, v_types, ["magnitude", "derivative", "2nd oder derivative "], [q.magnitude, q.derivative, q.derivative_2nd]):
				if v != Termination.UNCHANGED:
					s += (((str(t_type) + ": ") if t_type is not None else "") + "Quantity \"" + str(q.name) + "\": changing " + m_name + " from \"" + str(prev_val) + "\" to \"" + str(v) + "\"") + "\n"
		return s
		

	def copy(self):
		term = Termination(self.quantities[:], [v[:] for v in self.vals], [t[:] for t in self.types])
		return term


class Entity:

	def __init__(self, name):
		self.name = name 
		self.quantities = list()

	def add_quantity(self,q):
		self.quantities.append(q)



class Quantity:

	ZERO = '0'
	NEGATIVE = '-'
	POSITIVE = '+'
	MAX_VAL = 'max'
	MIN_VAL = 'min'

	IS_LANDMARK = {
		ZERO: True,
		NEGATIVE: False,
		POSITIVE: False,
		MAX_VAL: True,
		MIN_VAL: True
	}

	def __init__(self, name, magn_space=None, deriv_space=None, deriv_2nd_space=None, model_2nd_derivative=True):
		self.name = name
		if magn_space is None:
			magn_space = [Quantity.ZERO, Quantity.POSITIVE, Quantity.MAX_VAL]
		if deriv_space is None:
			deriv_space = [Quantity.NEGATIVE, Quantity.ZERO, Quantity.POSITIVE]
		if deriv_2nd_space is None:
			deriv_2nd_space = [Quantity.NEGATIVE, Quantity.ZERO, Quantity.POSITIVE]
		self.magn_space = magn_space
		self.deriv_space = deriv_space
		self.deriv_2nd_space = deriv_2nd_space
		self.magnitude = Quantity.ZERO
		self.derivative = Quantity.ZERO
		self.derivative_2nd = Quantity.ZERO
		self.magnitude_fixed = False
		self.derivative_fixed = False
		self.derivative_2nd_fixed = False
		self.model_2nd_derivative = model_2nd_derivative
		self.relations = list()

	def set_value(self, magnitude=None, derivative=None, derivative_2nd=None):
		if magnitude is not None:
			self.magnitude = magnitude
		if derivative is not None:
			self.derivative = derivative
		if derivative_2nd is not None:
			self.derivative_2nd = derivative_2nd

	def remove_fixing(self):
		self.magnitude_fixed = False
		self.derivative_fixed = False
		self.derivative_2nd_fixed = False

	def add_relation(self, rel):
		self.relations.append(rel)
		print("Adding relation " + rel.to_string() + " to " + self.name)

	def is_quantity_valid(self, quantities):
		return (self.check_causal_relations(quantities) and self.check_quantity_space_boundaries())
		
	def check_quantity_space_boundaries(self):
		# For simplicity, we do not check the same for derivative and 2nd order derivative
		if (self.derivative == Quantity.POSITIVE or (self.derivative == Quantity.ZERO and self.derivative_2nd == Quantity.POSITIVE)) and self.magn_space.index(self.magnitude) == (len(self.magn_space) - 1) and Quantity.is_landmark(self.magnitude):
			return False
		if (self.derivative == Quantity.NEGATIVE or (self.derivative == Quantity.ZERO and self.derivative_2nd == Quantity.NEGATIVE)) and self.magn_space.index(self.magnitude) == 0 and Quantity.is_landmark(self.magnitude):
			return False
		return True

	def get_influences_on_quantity(self, quantities):
		magn_constraints = []
		deriv_influences = []
		deriv_2nd_influences = []
		for rel in self.relations:
			if rel.q1.name == self.name:
				continue
			q1 = None
			for q in quantities:
				if rel.q1.name == q.name:
					q1 = q 
					break
			if rel.rel_opt in [Relationship.PROPORTIONAL, Relationship.INFLUENCE]:
				if rel.rel_opt == Relationship.PROPORTIONAL:
					deriv_influences.append(q1.derivative)
					deriv_2nd_influences.append(q1.derivative_2nd)
				elif rel.rel_opt == Relationship.INFLUENCE:
					deriv_influences.append(Quantity.POSITIVE if q1.magnitude in [Quantity.POSITIVE, Quantity.MAX_VAL] else Quantity.ZERO)
					deriv_2nd_influences.append(q1.derivative)
				if not rel.positive:
					deriv_influences[-1] = Quantity.inver_derivative(deriv_influences[-1])
					deriv_2nd_influences[-1] = Quantity.inver_derivative(deriv_2nd_influences[-1])
			elif rel.rel_opt == Relationship.VALUE_EQ and q1.magnitude == rel.get_val(q1):
				if q1.magnitude == rel.get_val(q1):
					magn_constraints.append(rel.get_val(self))
		return magn_constraints, deriv_influences, deriv_2nd_influences

	def check_causal_relations(self, quantities):
		magn_constraints, deriv_influences, deriv_2nd_influences = self.get_influences_on_quantity(quantities)

		if len(magn_constraints) != 0:
			for mc in magn_constraints:
				if self.magnitude != mc:
					return False
		
		if len(deriv_influences) != 0:
			pos_infs = sum([i == Quantity.POSITIVE for i in deriv_influences])
			neg_infs = sum([i == Quantity.NEGATIVE for i in deriv_influences])
			if pos_infs > 0 and neg_infs == 0 and self.derivative != Quantity.POSITIVE:
				return False
			if neg_infs > 0 and pos_infs == 0 and self.derivative != Quantity.NEGATIVE:
				return False
			if pos_infs == 0 and neg_infs == 0 and self.derivative != Quantity.ZERO:
				return False
		
		if len(deriv_2nd_influences) != 0:
			pos_infs = sum([i == Quantity.POSITIVE for i in deriv_2nd_influences])
			neg_infs = sum([i == Quantity.NEGATIVE for i in deriv_2nd_influences])
			if pos_infs > 0 and neg_infs == 0 and self.derivative_2nd != Quantity.POSITIVE:
				return False
			if neg_infs > 0 and pos_infs == 0 and self.derivative_2nd != Quantity.NEGATIVE:
				return False
			if pos_infs == 0 and neg_infs == 0 and self.derivative_2nd != Quantity.ZERO:
				return False
		
		return True

	def make_quantity_valid(self, quantities):
		if not self.check_quantity_space_boundaries() and not self.resolve_quantity_space_issues():
			return False
		if not self.check_causal_relations(quantities) and not self.resolve_causal_relation_issues(quantities):
			return False
		return True

	def resolve_quantity_space_issues(self):
		if self.magn_space.index(self.magnitude) == (len(self.magn_space) - 1) and Quantity.is_landmark(self.magnitude):
			if self.derivative == Quantity.POSITIVE:
				if self.derivative_fixed:
					return False
				else:
					self.derivative = Quantity.ZERO
					self.derivative_fixed = True
			if self.derivative_2nd == Quantity.POSITIVE and self.derivative != Quantity.NEGATIVE:
				if self.derivative_2nd_fixed:
					return False
				else:
					self.derivative_2nd = Quantity.ZERO
					self.derivative_2nd_fixed = True

		if self.magn_space.index(self.magnitude) == 0 and Quantity.is_landmark(self.magnitude):
			if self.derivative == Quantity.NEGATIVE:
				if self.derivative_fixed:
					return False
				else:
					self.derivative = Quantity.ZERO
					self.derivative_fixed = True
			if self.derivative_2nd == Quantity.NEGATIVE and self.derivative != Quantity.POSITIVE:
				if self.derivative_2nd_fixed:
					return False
				else:
					self.derivative_2nd = Quantity.ZERO
					self.derivative_2nd_fixed = True
		return True

	def resolve_causal_relation_issues(self, quantities):
		magn_constraints, deriv_influences, deriv_2nd_influences = self.get_influences_on_quantity(quantities)

		if len(magn_constraints) != 0:
			for mc in magn_constraints:
				if self.magnitude != mc:
					if self.magnitude_fixed:
						return False
					else:
						if (self.magn_space.index(mc) == self.magn_space.index(self.magnitude) + 1 and self.derivative == Quantity.POSITIVE) or \
						   (self.magn_space.index(mc) == self.magn_space.index(self.magnitude) - 1 and self.derivative == Quantity.NEGATIVE):
						   self.magnitude = mc
						   self.magnitude_fixed = True
						else:
						  	return False
		
		if len(deriv_influences) != 0:
			pos_infs = sum([i == Quantity.POSITIVE for i in deriv_influences])
			neg_infs = sum([i == Quantity.NEGATIVE for i in deriv_influences])
			if pos_infs > 0 and neg_infs == 0 and self.derivative != Quantity.POSITIVE:
				if self.derivative_fixed or self.derivative == Quantity.NEGATIVE:
					return False
				else:
					self.derivative = Quantity.POSITIVE
					self.derivative_fixed = True
			if neg_infs > 0 and pos_infs == 0 and self.derivative != Quantity.NEGATIVE:
				if self.derivative_fixed or self.derivative == Quantity.POSITIVE:
					return False
				else:
					self.derivative = Quantity.NEGATIVE
					self.derivative_fixed = True
			if pos_infs == 0 and neg_infs == 0 and self.derivative != Quantity.ZERO:
				if self.derivative_fixed:
					return False
				else:
					self.derivative = Quantity.ZERO
					self.derivative_fixed = True
		
		if len(deriv_2nd_influences) != 0:
			pos_infs = sum([i == Quantity.POSITIVE for i in deriv_2nd_influences])
			neg_infs = sum([i == Quantity.NEGATIVE for i in deriv_2nd_influences])
			if pos_infs > 0 and neg_infs == 0 and self.derivative_2nd != Quantity.POSITIVE:
				if self.derivative_2nd_fixed or self.derivative_2nd == Quantity.NEGATIVE:
					return False
				else:
					self.derivative_2nd = Quantity.POSITIVE
					self.derivative_2nd_fixed = True
			if neg_infs > 0 and pos_infs == 0 and self.derivative_2nd != Quantity.NEGATIVE:
				if self.derivative_2nd_fixed or self.derivative_2nd == Quantity.POSITIVE:
					return False
				else:
					self.derivative_2nd = Quantity.NEGATIVE
					self.derivative_2nd_fixed = True
			if pos_infs == 0 and neg_infs == 0 and self.derivative_2nd != Quantity.ZERO:
				if self.derivative_2nd_fixed:
					return False
				else:
					self.derivative_2nd = Quantity.ZERO
					self.derivative_2nd_fixed = True

		return True

	def print(self):
		print("Quantity \"" + str(self.name) + "\": Magnitude = " + str(self.magnitude) + (" (fixed)" if self.magnitude_fixed else "") + \
			  ", derivative " + str(self.derivative) + (" (fixed)" if self.derivative_fixed else "") + \
			  ", 2nd oder derivative " + str(self.derivative_2nd) + (" (fixed)" if self.derivative_2nd_fixed else ""))

	@staticmethod
	def inver_derivative(d):
		if d == Quantity.ZERO:
			return Quantity.ZERO
		elif d == Quantity.POSITIVE:
			return Quantity.NEGATIVE
		elif d == Quantity.NEGATIVE:
			return Quantity.POSITIVE
		else:
			print("Warning: unknown derivative \"" + str(d) + "\" could not be inverted")
			return d

	@staticmethod
	def is_landmark(val):
		if val not in Quantity.IS_LANDMARK:
			print("Warning: Asking for space value \"" + str(val) + "\" being a landmark, but no information was saved")
			return False
		else:
			return Quantity.IS_LANDMARK[val]

	@staticmethod
	def add_landmark_information(val_name, is_landmark):
		Quantity.IS_LANDMARK[val_name] = is_landmark;

	# def propagate_change(self, magn_change=None, deriv_change=None):
	# 	# print("propagating change of state " + self.name)
	# 	# Check if something changes, then...
	# 	prop_deriv = False
	# 	prop_magn = False
	# 	if self.fixed_magnitude:
	# 		magn_change = self.fixed_magnitude
	# 	if magn_change:
	# 		print("Magnitude change: " + str(magn_change))
	# 		prop_magn = (magn_change not in self.change_magnitude)
	# 		self.change_magnitude.append(magn_change)
	# 		if magn_change == Quantity.MAX_VAL or magn_change == Quantity.MIN_VAL:
	# 			deriv_change = Quantity.ZERO
	# 			# TODO: Check what can go wrong here (overwriting previous derivative change. Needed for propagating the zero)
	# 	if self.fixed_derivative is not None:
	# 		deriv_change = self.fixed_derivative
	# 		print(self.name + " -> Fixed change " + str(deriv_change))
	# 	if deriv_change:
	# 		print("Derivative change " + deriv_change + " for quantity " + self.name)
	# 		prop_deriv = (deriv_change not in self.change_derivative)
	# 		# print("Derivative change: " + str(deriv_change) + ". Propagated: " + str(prop_deriv))
	# 		self.change_derivative.append(deriv_change)
	# 	if not self.has_ambiguous_change()[0]:
	# 		for r in self.relations:
	# 			if prop_deriv and r.rel_opt == Relationship.PROPORTIONAL:
	# 				# print("Propagate proportional relationship to state " + r.counter_part(self).name)
	# 				d_c = deriv_change if r.positive else Quantity.invert_derivative(deriv_change)
	# 				r.counter_part(self).propagate_change(magn_change=None, deriv_change=d_c)
	# 			if prop_magn and r.rel_opt == Relationship.VALUE_EQ:
	# 				if r.get_val(self) == magn_change:
	# 					r.counter_part(self).propagate_change(magn_change=r.get_val(r.counter_part(self)), deriv_change=None)
	# 			if prop_magn and r.rel_opt == Relationship.INFLUENCE and r.q1 == self:
	# 				if magn_change == Quantity.ZERO:
	# 					d_c = Quantity.ZERO
	# 				else:
	# 					d_c = Quantity.POSITIVE if r.positive else Quantity.NEGATIVE
	# 				r.q2.propagate_change(magn_change=None, deriv_change=d_c)

		

	# def has_ambiguous_change(self):
	# 	unique_changes = list(set([c for c in self.change_derivative if c != Quantity.ZERO]))
	# 	if len(unique_changes) > 1:
	# 		return (True, unique_changes + [Quantity.ZERO], 1)
	# 	unique_changes = list(set([c for c in self.change_magnitude if c != Quantity.POSITIVE]))
	# 	if len(unique_changes) > 1:
	# 		return (True, unique_changes + [Quantity.POSITIVE], 2)
	# 	return (False, None, -1)

	# def apply_change(self):
	# 	if len(self.change_derivative) > 0:
	# 		unique_changes = list(set([c for c in self.change_derivative if c != Quantity.ZERO]))
	# 		if len(unique_changes) == 0:
	# 			self.derivative = Quantity.ZERO
	# 		else:
	# 			self.derivative = unique_changes[0]
	# 		self.change_derivative = list()
	# 	if len(self.change_magnitude) > 0:
	# 		unique_changes = list(set([c for c in self.change_magnitude if c != Quantity.POSITIVE]))
	# 		if len(unique_changes) == 0:
	# 			self.magnitude = Quantity.POSITIVE
	# 		else:
	# 			self.magnitude = unique_changes[0]
	# 		self.change_magnitude = list()
	# 	self.fixed_derivative = None
	# 	self.fixed_magnitude = None

	# def apply_pure_derivative_change(self):
	# 	if (self.derivative == Quantity.NEGATIVE and self.magnitude == Quantity.MAX_VAL) or \
	# 	   (self.derivative == Quantity.POSITIVE and self.magnitude == Quantity.ZERO):
	# 		# self.magnitude = Quantity.POSITIVE
	# 		self.propagate_change(magn_change=Quantity.POSITIVE, deriv_change=None)

	# def check_unchanged_states(self):
	# 	if len(self.change_derivative) == 0:
	# 		self.propagate_change(deriv_change=self.derivative)
	# 	if len(self.change_magnitude) == 0:
	# 		self.propagate_change(magn_change=self.magnitude)

	# def get_possible_change(self):
	# 	if self.derivative == Quantity.ZERO:
	# 		return None
	# 	elif self.derivate == Quantity.POSITIVE and self.magn_space.index(self.magnitude) < (len(self.magn_space) - 1):
	# 		return self.magn_space[self.magn_space.index(self.magnitude)+1]
	# 	elif self.derivate == Quantity.NEGATIVE and self.magn_space.index(self.magnitude) > 0:
	# 		return self.magn_space[self.magn_space.index(self.magnitude)-1]
	# 	else:
	# 		return None


class Relationship:

	PROPORTIONAL = 1
	INFLUENCE = 2
	VALUE_EQ = 3

	def __init__(self, rel_opt, q1, q2, positive=True, add_params=None):
		self.rel_opt = rel_opt
		if self.rel_opt not in [Relationship.PROPORTIONAL, Relationship.INFLUENCE, Relationship.VALUE_EQ]:
			print("Warning: unknown relation option: " + str(self.rel_opt))
		self.positive = positive
		self.q1 = q1
		self.q2 = q2
		self.add_params = add_params

		self.q1.add_relation(self)
		self.q2.add_relation(self)

	def to_string(self):
		s = ""
		if self.rel_opt == Relationship.PROPORTIONAL:
			s = "P" + ("+" if self.positive else "-")
		elif self.rel_opt == Relationship.INFLUENCE:
			s = "I" + ("+" if self.positive else "-")
		elif self.rel_opt == Relationship.VALUE_EQ:
			s = "VC(" + str(self.add_params[0]) + ", " + str(self.add_params[1]) + ")"
		else:
			print("Warning: unknown relation option: " + str(self.rel_opt))
		return s

	def counter_part(self, q):
		if q.name == self.q1.name:
			return self.q2
		elif q.name == self.q2.name:
			return self.q1
		else:
			print("Warning: counter part could not be found in relationship")
			return None

	def get_val(self, q):
		if q.name == self.q1.name:
			return self.add_params[0]
		elif q.name == self.q2.name:
			return self.add_params[1]
		else:
			print("Warning: value could not been found in relationship")
			return None

class State:

	def __init__(self, quantities):
		self.value_dict = dict()
		for q in quantities:
			if q.model_2nd_derivative:
				self.value_dict[q.name] = (q.magnitude, q.derivative, q.derivative_2nd)
			else:
				self.value_dict[q.name] = (q.magnitude, q.derivative)

	def __eq__(self, other):
		return self.value_dict == other.value_dict

	def print(self):
		print("="*30)
		print("State")
		print("-"*30)
		for q_name, vals in self.value_dict.items():
			print(q_name + " (" + ",".join(vals) + ")")
		print("="*30)


def create_default_graph():
	# D = Entity(name="Drain")
	T = Entity(name="Tab")
	C = Entity(name="Container")

	QD = Quantity(name="Outflow", magn_space=[Quantity.ZERO, Quantity.POSITIVE, Quantity.MAX_VAL], model_2nd_derivative=False)
	C.add_quantity(QD)
	QT = Quantity(name="Inflow", magn_space=[Quantity.ZERO, Quantity.POSITIVE], model_2nd_derivative=False)
	T.add_quantity(QT)
	QC = Quantity(name="Volume", magn_space=[Quantity.ZERO, Quantity.POSITIVE, Quantity.MAX_VAL])
	C.add_quantity(QC)
	# QO = Quantity(name="Overflow", magn_space=[Quantity.ZERO, Quantity.POSITIVE])
	# C.add_quantity(QO)
	# QH = Quantity(name="Height", magn_space=[Quantity.ZERO, Quantity.POSITIVE, Quantity.MAX_VAL], model_2nd_derivative=False)
	# C.add_quantity(QH)
	# QP = Quantity(name="Pressure", magn_space=[Quantity.ZERO, Quantity.POSITIVE, Quantity.MAX_VAL], model_2nd_derivative=False)
	# C.add_quantity(QP)

	rels = [Relationship(rel_opt=Relationship.INFLUENCE, q1=QT, q2=QC, positive=True),
			Relationship(rel_opt=Relationship.INFLUENCE, q1=QD, q2=QC, positive=False),
			Relationship(rel_opt=Relationship.PROPORTIONAL, q1=QC, q2=QD, positive=True),
			Relationship(rel_opt=Relationship.VALUE_EQ, q1=QC, q2=QD, add_params=(Quantity.MAX_VAL, Quantity.MAX_VAL)),
			Relationship(rel_opt=Relationship.VALUE_EQ, q1=QC, q2=QD, add_params=(Quantity.ZERO, Quantity.ZERO)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QD, q2=QC, add_params=(Quantity.MAX_VAL, Quantity.MAX_VAL)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QD, q2=QC, add_params=(Quantity.ZERO, Quantity.ZERO)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QC, q2=QO, add_params=(Quantity.ZERO, Quantity.ZERO)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QC, q2=QO, add_params=(Quantity.POSITIVE, Quantity.ZERO)),
			# Relationship(rel_opt=Relationship.INFLUENCE, q1=QO, q2=QC, positive=False)
			
			# Relationship(rel_opt=Relationship.PROPORTIONAL, q1=QC, q2=QH, positive=True),
			# Relationship(rel_opt=Relationship.PROPORTIONAL, q1=QH, q2=QP, positive=True),
			# Relationship(rel_opt=Relationship.PROPORTIONAL, q1=QP, q2=QD, positive=True),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QC, q2=QH, add_params=(Quantity.ZERO, Quantity.ZERO)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QC, q2=QH, add_params=(Quantity.MAX_VAL, Quantity.MAX_VAL)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QH, q2=QC, add_params=(Quantity.ZERO, Quantity.ZERO)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QH, q2=QC, add_params=(Quantity.MAX_VAL, Quantity.MAX_VAL)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QP, q2=QH, add_params=(Quantity.ZERO, Quantity.ZERO)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QP, q2=QH, add_params=(Quantity.MAX_VAL, Quantity.MAX_VAL)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QH, q2=QP, add_params=(Quantity.ZERO, Quantity.ZERO)),
			# Relationship(rel_opt=Relationship.VALUE_EQ, q1=QH, q2=QP, add_params=(Quantity.MAX_VAL, Quantity.MAX_VAL)),
			
			]

	return [T, C], [QT, QD, QC], rels # ,QO, QH, QP




