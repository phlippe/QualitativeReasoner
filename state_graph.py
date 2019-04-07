

class Termination:

	UNCHANGED = "unchanged"

	def __init__(self, idx, vals):
		self.indices = idx
		self.vals = vals

	def add_change(self, idx, val):
		self.indicies.append(idx)
		self.vals.append(val)


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

	def __init__(self, name, magn_space=None, deriv_space=None, deriv_2nd_space=None):
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
		self.change_derivative = list()
		self.change_magnitude = list()
		self.fixed_derivative = None
		self.fixed_magnitude = None
		self.relations = list()

	def set_value(self, magnitude, derivative):
		self.magnitude = magnitude
		self.derivative = 0

	def add_relation(self, rel):
		self.relations.append(rel)
		print("Adding relation " + rel.to_string() + " to " + self.name)

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

	def is_directed(self):
		return self.rel_opt in [Relationship.INFLUENCE]

	def counter_part(self, q):
		if q == self.q1:
			return self.q2
		elif q == self.q2:
			return self.q1
		else:
			print("Warning: counter part could not be found in relationship")
			return None

	def get_val(self, q):
		if q == self.q1:
			return self.add_params[0]
		elif q == self.q2:
			return self.add_params[1]
		else:
			print("Warning: value could not been found in relationship")
			return None

class State:

	def __init__(self, quantities):
		self.value_dict = dict()
		for q in quantities:
			self.value_dict[q.name] = (q.magnitude, q.derivative, q.derivative_2nd)

	def __eq__(self, other):
		return self.value_dict == other.value_dict

def create_default_graph():
	# D = Entity(name="Drain")
	T = Entity(name="Tab")
	C = Entity(name="Container")

	QD = Quantity(name="Outflow", magn_space=[Quantity.ZERO, Quantity.POSITIVE, Quantity.MAX_VAL])
	C.add_quantity(QD)
	QT = Quantity(name="Inflow", magn_space=[Quantity.ZERO, Quantity.POSITIVE])
	T.add_quantity(QT)
	QC = Quantity(name="Volume", magn_space=[Quantity.ZERO, Quantity.POSITIVE, Quantity.MAX_VAL])
	C.add_quantity(QC)
	QO = Quantity(name="Overflow", magn_space=[Quantity.ZERO, Quantity.POSITIVE])
	C.add_quantity(QO)

	rels = [Relationship(rel_opt=Relationship.INFLUENCE, q1=QT, q2=QC, positive=True),
			Relationship(rel_opt=Relationship.INFLUENCE, q1=QD, q2=QC, positive=False),
			Relationship(rel_opt=Relationship.PROPORTIONAL, q1=QC, q2=QD, positive=True),
			Relationship(rel_opt=Relationship.VALUE_EQ, q1=QD, q2=QC, add_params=(Quantity.MAX_VAL, Quantity.MAX_VAL)),
			Relationship(rel_opt=Relationship.VALUE_EQ, q1=QD, q2=QC, add_params=(Quantity.ZERO, Quantity.ZERO)),
			Relationship(rel_opt=Relationship.VALUE_EQ, q1=QC, q2=QO, add_params=(Quantity.ZERO, Quantity.ZERO)),
			Relationship(rel_opt=Relationship.VALUE_EQ, q1=QC, q2=QO, add_params=(Quantity.POSITIVE, Quantity.ZERO)),
			Relationship(rel_opt=Relationship.INFLUENCE, q1=QO, q2=QC, positive=False)]

	return [T, C], [QD, QT, QC, QO], rels




