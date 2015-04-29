'''

1. Find scriptNotify handlers (for both WebView and WebBrowser)
2. Find methods called by handlers
TODO:
- check all of the above
3. Filter methods by sensitive API
	- define sensitive API
4. Determine data dependencies between handler args and sensitive API function args

'''

import clr
clr.AddReference("Mono.Cecil")
from Mono.Cecil import *
import sys
sys.path.append("C:\Program Files (x86)\IronPython 2.7\Lib")
import os
import string
import random
import subprocess
import StackElement

apps_dir = "C:\\Users\\b\\Downloads\\apps"
unzipped_apps_dir = "C:\\Users\\b\\Downloads\\apps\\unzipped"
UNZIP = "C:\\Users\\b\\Downloads\\7za920\\7za.exe"

def main():
	of = open('blah.txt', 'w')
	of.write('')
	of.close()

	
	for f in os.listdir(apps_dir):
		if '.appx' in f:
			app_folder = unzipped_apps_dir + "\\" + str(f)
			if not os.path.isdir(app_folder):
				cmd = UNZIP + ' x -o' + app_folder + ' -y ' + str(os.path.join(apps_dir, f))
				rc = subprocess.call(cmd, shell=True)
				if rc:
					print "unzipping failed"

	for d in os.listdir(unzipped_apps_dir):
		if os.path.isdir(os.path.join(unzipped_apps_dir, d)):
			for f in os.listdir(os.path.join(unzipped_apps_dir, d)):
				f_dir = os.path.join(unzipped_apps_dir, d)
				if f.endswith('exe'):
					of = open('blah.txt', 'a')
					of.write("FILE: " + str(f_dir) + " " + str(f) + "\n")
					of.close()
					
					try:
						asm = AssemblyDefinition.ReadAssembly(os.path.join(f_dir, f))
					except SystemError:
						print "FAILED: " + str(os.path.join(f_dir, f))
						continue

					handlers = searchScriptNotifyHandler(asm)
					
					for handler in handlers:
						of = open("blah.txt", "a")
						of.write("HANDLER: " + str(handler.Name) + "\n")
						of.write("METHODS CALLED: \n")
						of.close()
						getMethodsCalled(handler)

'''
	Searches for NotifyEventHandler (aka ScriptNotify) handlers

	i.e. myWebView.scriptNotify += someHandler
	
	Returns list of MethodDefinitions/MethodReferences (i.e. handlers)
'''
def searchScriptNotifyHandler(asm):
	handlers = []
	for module in asm.Modules:
		for t in module.Types:
			for method in t.Methods:
				if method.Body:
					for i in method.Body.Instructions:
						if i.OpCode.Name == "newobj":
							if i.Operand:
								if i.Operand.DeclaringType.FullName == "Windows.UI.Xaml.Controls.NotifyEventHandler":
									handlers.append(i.Previous.Operand.GetElementMethod())
								
	return handlers

'''
	Checks to see that application uses WebView
	
	Returns True | False
'''
def checkForWebView(asm):
	for module in asm.Modules:
		for t in module.Types:
			for method in t.Methods:
				if method.Body:
					for i in method.Body.Instructions:
						if i.OpCode.Name == "newobj":
							if i.Operand:
								if i.Operand.DeclaringType.FullName == "Windows.UI.Xaml.Controls.WebView":
									return True
	return False
	
def getMethodsCalled(method):
	if method.GetType().Name == "MethodDefinition":
		if method.Body:
			for i in method.Body.Instructions:
				if "call" in i.OpCode.Name:
					of = open("blah.txt", "a")
					of.write("\t" + str(i.Operand.Name) + "\n")
					of.close()
					getMethodsCalled(i.Operand.GetElementMethod())

'''
	Returns number of parameters for a given method
'''
def getMethodParamCount(method):
	return method.Parameters.Count

'''
	Traces data from current method's parameters to the parameters of a method called within
	
	e.g. foo(int x, int y) { bar(x) }  # traces foo's param x to argument of bar() func
	
	TODO:
	- what if data gets stored into memory and then loaded?
		st instructions, then ld
		also cpblk 
		
	- what if new object/array gets created and argument is attribute/element of array
		newarr
		newobj
	
'''
#TODO: PUSH_INS, SWITCH
PUSH_INS = ["ldarg", "ldc", ]
POP_INS = ["pop", "stloc", "stobj", "stfld", "stelem", "starg", "stind", "stsfld", "cpblk", "cpobj", "endfilter", "initblk", "initobj", "throw"]
BRANCH_INS = ["beq", "bge", "bgt", "ble", "blt", "bne", "brfalse", "brtrue"]
SWITCH_INS = ["switch"]


#TODO:
#
# for any store instructions, store even if the value is not tained (in case we need it later)
# if it is an 'object' store under memory['object']
# if it is an 'array' store under memory['array']
# etc
#
# what to store?
# 	a tuple {data: X, tainted: T/F}
#		where data (i.e. X) is:
#			- random identifier, do we even need this?
# 		and tainted describes if data from the argument could have flown into the data (directly or indirectly)
def pop(method, ins, ins_index, fstack, memory):
	if "starg" in ins.OpCode.ToString():
		value = fstack.pop()
		
		argslot = ins.OpCode.ToString().split('.')[1]
	
		memory["arg"+str(argslot)] = value

	elif "stelem" in ins.OpCode.ToString():
		value = fstack.pop()
		index = fstack.pop()
		addr = fstack.pop()
	
		if value.isTainted():
			try:
				memory[addr['data']].markTainted()	
			except KeyError:
				memory[addr['data']] = value	

	elif "stfld" in ins.OpCode.ToString():
		value = fstack.pop()
		# TODO: get actual obj_ref from stack element 
		addr = fstack.pop()

		if value.isTainted():	
			try:
				memory[addr['data']].markTainted()	
			except KeyError:
				memory[addr['data']] = value	
		
	elif "stind" in ins.OpCode.ToString():
		# pop
		value = fstack.pop()
		# pop address
		address = fstack.pop()
		
		memory[addr['data']] = value
		
	elif "stloc" in ins.OpCode.ToString():
		# pop stack
		se = fstack.pop()
	
		# index comes after . (e.g. stloc.0)
		index = value["data"].split('.')[1]
		
		memory["loc"+str(index)] = value
				
	elif "stobj" in ins.OpCode.ToString():
		# pop object ref
		obj_ref = fstack.pop()
		# pop address
		addr = fstack.pop()
		
		memory[addr['data']] = obj_ref
		
	elif "stsfld" in ins.OpCode.ToString():
		value = fstack.pop()
		
		field = ins.ToString.split(' ')[2]
		memory[field] = value
	
	elif "initblk" in ins.OpCode.ToString():
		num_bytes = fstack.pop()
		init_val = fstack.pop()
		address = fstack.pop()
	
	elif "initobj" in ins.OpCode.ToString():
		value = fstack.pop()

	elif "endfilter" in ins.OpCode.ToString():
		value = fstack.pop()

	elif "throw" in ins.OpCode.ToString():
		obj_ref = fstack.pop()

	elif "pop" in ins.OpCode.ToString():
		fstack.pop()

	elif "cpblk" in ins.OpCode.ToString():
		num_bytes = fstack.pop()
		src_addr = fstack.pop()
		dst_addr = fstack.pop()
		
		memory[dst_addr['data']] = memory[src_addr['data']]

	elif "cpobj" in ins.OpCode.ToString():
		src_obj = fstack.pop()
		dst_obj = fstack.pop()
		
		# check if src addr is tainted
		memory[dst_obj['data']] = memory[src_obj['data']]

	else:
		print "Not handling ins " + ins.ToString()
		
def load(method, ins, ins_index, fstack, memory):
	print "stuff goes here.."

def branch(method, ins, ins_index, fstack, memory):
	# for branch ins, split execution one contiunuing with branch and another contiuning from the next target ins (end of branch)
	if ins.OpCode.ToString() in BRANCH_INS:
		value1 = fstack.pop()
		value2 = fstack.pop()

		target = ins.ToString().split(' ')[2]
		if "IL" not in target:
			print "messed up split"

		# split execution
		end_of_branch = findInsOfInterest(method, ins_index, "target")
		dataFlow(method, fstack, end_of_branch, memory)
		
def newIns(method, ins, ins_index, fstack, memory):
	if "newobj" in ins.OpCode.ToString():
		# find how many arguments
		num_args = ins.Operand.Parameters.Count 
		# pop X arguments
		tainted = False
		for arg in range(0, num_args):
			value = fstack.pop()
			if value['tainted']:
				tainted = True

		# store in simulated memory
		data = generateRandomAddress()
		se = StackElement(data, tainted)
		memory[data] = se
		
		# push reference (StackElement) onto stack
		fstack.append(se)

	elif "newarr" in ins.OpCode.ToString():
		num_elements = fstack.pop()
		
		# store in simulated memory
		data = generateRandomAddress()
		se = StackElement(data, False)
		memory[data] = se

		# push reference onto stack
		fstack.append(se}

	else:
		print "Not handling ins " + ins.ToString()

def generateRandomAddress():
	return ''.join(random.choice(string.ascii_uppercase[0:6] + string.digits) for _ in range(10))

# e.g. findInsOfInterest(method, cur_index, "ret") finds the next return ins from the current index
def findInsOfInterest(method, cur_index, target):
	ins = method.Body.Instructions[cur_index]
	while ins.Next:
		ins = ins.Next
		cur_index += 1
		if target in ins.ToString():
			return cur_index
	return 0
		
def dataFlow(method, fstack, ins_index, memory):
	cur_ins = method.Body.Instructions[ins_index]
	
	opcode = cur_ins.OpCode.ToString()
	if opcode in PUSH_INS:
		tainted = False
		if "ldarg" in opcode.ToString():
			tainted = True
		fstack.append({'data': ins.ToString(), 'tainted': tainted})
	elif opcode in POP_INS:
		pop(method, cur_ins, ins_index, fstack, memory)
	elif opcode in SPECIAL_INS:
		

def traceParamsToArgs(method):
	fstack = []
	memory = []
	# remember to ignore ctor methods
	if method.Body:
		tainted_return = False
		for ins in method.Body.Instructions:
			if ins.OpCode in PUSH_INS:
				# push onto stack
				data = '' 
				fstack.append({'data': ins.ToString(), 'tainted': tainted})
			if ins.OpCode in POP_INS:
				# pop off the stack
				# how many pop operations?
				data = fstack.pop()
				if data['tainted']:
					tainted_return = True
			if ins.OpCode in SPECIAL_INS:
				# push and pop (or vice versa)
				# e.g. call = pops data and push return value
				
				# how many pop operations?
				
				# is there a return value
				if returns:
					# push the return value
					#fstack.append({'data': data, 'tainted': tainted_return})
					#tainted_return = False	
			if ins.OpCode in JMP_INS:
				print "JMP ins, cannot handle"
				break
	
def test():
	# TEST USING WEBVIEW EXAMPLE
	
	of = open('blah.txt', 'w')
	of.write('')
	of.close()

	f = "Controls_WebView.WindowsPhone.exe"
	f_dir = "C:\\Users\\b\\Downloads\\XAML WebView control sample\\C#\\WindowsPhone\\bin\\Debug"
	of = open('blah.txt', 'a')
	of.write("FILE: " + str(f_dir) + " " + str(f) + "\n")
	of.close()
					
	try:
		asm = AssemblyDefinition.ReadAssembly(os.path.join(f_dir, f))
	except SystemError:
		print "FAILED: " + str(os.path.join(f_dir, f))

	searchScriptNotifyHandler(asm)
	for handler in handlers:
		of = open("blah.txt", "a")
		of.write("HANDLER: " + str(handler.Name) + "\n")
		of.write("METHODS CALLED: \n")
		of.close()
		getMethodsCalled(handler)
	
