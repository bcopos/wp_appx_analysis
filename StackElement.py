

class StackElement:	
	def __init__(self, data, tainted):
		self.data = data
		self.tainted = tainted

	def isTainted(self):
		return self.tainted

	def getData(self):
		return self.data

	def markTainted(self):
		self.tainted = True

	def markNotTainted(self):
		self.tainted = False
