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
PUSH_INS = ["ldarg", "ldc", "ldelem", "ldfld", "ldftn", "ldind", "ldlen", "ldloc", "ldnull", "ldobj", "ldsfld", "ldstr", "ldtoken", "ldvirtfn"]
POP_INS = ["pop", "stloc", "stobj", "stfld", "stelem", "starg", "stind", "stsfld", "cpblk", "cpobj", "endfilter", "initblk", "initobj", "throw"]
BRANCH_INS = ["beq", "bge", "bgt", "ble", "blt", "bne", "brfalse", "brtrue"]
SWITCH_INS = ["switch"]
BREAK_INS = ["break"]

def push(method, ins, ins_index, fstack, memory):
	if ins.OpCode in [ Mono.Cecil.Cil.OpCodes.Ldarg_0, Mono.Cecil.Cil.OpCodes.Ldarg_1, Mono.Cecil.Cil.OpCodes.Ldarg_2, Mono.Cecil.Cil.OpCodes.Ldarg_3, Mono.Cecil.Cil.OpCodes.Ldarg_S, Mono.Cecil.Cil.OpCodes.Ldarga_S ]:
		argslot = ins.OpCode.ToString().split('.')[1]
		se = StackElement("arg"+argslot, True)
		
		# push onto stack
		fstack.append(se)
		
	elif ins.OpCode in [ Mono.Cecil.Cil.Opcodes.Ldc_I4_M1, Mono.Cecil.Cil.Opcodes.Ldc_I4_0, Mono.Cecil.Cil.Opcodes.Ldc_I4_1, Mono.Cecil.Cil.Opcodes.Ldc_I4_2, Mono.Cecil.Cil.Opcodes.Ldc_I4_3, Mono.Cecil.Cil.Opcodes.Ldc_I4_4, Mono.Cecil.Cil.Opcodes.Ldc_I4_5, Mono.Cecil.Cil.Opcodes.Ldc_I4_6, Mono.Cecil.Cil.Opcodes.Ldc_I4_7, Mono.Cecil.Cil.Opcodes.Ldc_I4_8, Mono.Cecil.Cil.Opcodes.Ldc_I4_S, Mono.Cecil.Cil.Opcodes.Ldc_I4, Mono.Cecil.Cil.Opcodes.Ldc_R4, Mono.Cecil.Cil.Opcodes.Ldc_R8 ]:
		if ins.Operand:
			value = ins.Operand.ToString()
		else:
			value = ins.OpCode.ToString().split('.')[2]

		# create stack element
		se = StackElement(value, False)

		# push onto stack
		fstack.append(se)

	elif ins.OpCode in [ Mono.Cecil.Cil.Opcodes.Ldelema, Mono.Cecil.Cil.Opcodes.Ldelem_I1, Mono.Cecil.Cil.Opcodes.Ldelem_U1, Mono.Cecil.Cil.Opcodes.Ldelem_I2, Mono.Cecil.Cil.Opcodes.Ldelem_U2, Mono.Cecil.Cil.Opcodes.Ldelem_I4, Mono.Cecil.Cil.Opcodes.Ldelem_U4, Mono.Cecil.Cil.Opcodes.Ldelem_I8, Mono.Cecil.Cil.Opcodes.Ldelem_I, Mono.Cecil.Cil.Opcodes.Ldelem_R4, Mono.Cecil.Cil.Opcodes.Ldelem_R8, Mono.Cecil.Cil.Opcodes.Ldelem_Ref ]:
		# pop
		index = fstack.pop()
		array_ref = fstack.pop()

		#TODO: does this really matter? we just care if it's tainted...
		value = ""
		se = StackElement(value, array_ref.isTainted())
		
		# push onto stack
		fstack.append(se)

	elif ins.Opcode in [ Mono.Cecil.Cil.Opcodes.Ldfld, Mono.Cecil.Cil.Opcodes.Ldflda ]:
	 	# pop
		obj_ref = fstack.pop()

		se = StackElement("", obj_ref.isTainted())		

		# push onto stack
		fstack.append(se)

	elif ins.OpCode in [ Mono.Cecil.Cil.Opcodes.Ldind_I1, Mono.Cecil.Cil.Opcodes.Ldind_U1, Mono.Cecil.Cil.Opcodes.Ldind_I2, Mono.Cecil.Cil.Opcodes.Ldind_U2, Mono.Cecil.Cil.Opcodes.Ldind_I4, Mono.Cecil.Cil.Opcodes.Ldind_U4, Mono.Cecil.Cil.Opcodes.Ldind_I8, Mono.Cecil.Cil.Opcodes.Ldind_I, Mono.Cecil.Cil.Opcodes.Ldind_R4, Mono.Cecil.Cil.Opcodes.Ldind_R8, Mono.Cecil.Cil.Opcodes.Ldind_Ref ]:
	 	# pop
		addr = fstack.pop()

		se = StackElement("", memory[addr['data']].isTainted())
	
		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Ldlen:
		# pop
		array_ref = fstack.pop()

		se = StackElement("", False)	 	

		# push onto stack
		fstack.append(se)

	elif ins.Opcode in [ Mono.Cecil.Cil.Opcodes.Ldloc, Mono.Cecil.Cil.Opcodes.Ldloca, Mono.Cecil.Cil.Opcodes.Ldloc_S, Mono.Cecil.Cil.Opcodes.Ldloca_S ]:
		if ins.Operand:
			loc = ins.Operand.ToString()
		else:
			loc = ins.OpCode.ToString().split('.')[1]

		se = memory[loc] 
	 	
		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Ldnull:
		se = StackElement("null", False)
	 	
		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Ldobj:
		# pop
		addr = fstack.pop()

		se = memory[addr['data']]
	 	
		# push onto stack
		fstack.append(se)

	elif ins.Opcode in [ Mono.Cecil.Cil.Opcodes.Ldsfld, Mono.Cecil.Cil.Opcodes.Ldsflda ]:
	 	# TODO
		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Ldstr:
		se = StackElement("", False)
	 	
		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Ldtoken:
		se = StackElement("", False)
	 	
		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Ldvirtftn:
		# pop
		fstack.pop()

		se = StackElement("", False)

		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Sizeof:
		se = StackElement("", False)

		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Volatile:

		# push onto stack
		fstack.append(se)

	elif ins.Opcode == Mono.Cecil.Cil.Opcodes.Unaligned:

		# push onto stack
		fstack.append(se)

	else:
		print "Not handling ins " + ins.ToString()
			

#
# for any store instructions, store even if the value is not tained (in case we need it later)
#
# what to store?
#	a StackElement (data, tainted bool)
#		where data (i.e. X) is:
#			- usually empty or something bogus
#			- if it is a memory reference (array ref or obj ref etc) then it's the address
# 		and tainted describes if data from the argument could have flown into the data (directly or indirectly)
def pop(method, ins, ins_index, fstack, memory):
	if ins.OpCode == Mono.Cecil.Cil.OpCodes.Starg or ins.OpCode == Mono.Cecil.Cil.OpCodes.Starg_S:
		value = fstack.pop()
		
		argslot = ins.OpCode.ToString().split('.')[1]
	
		memory["arg"+str(argslot)] = value

	elif ins.OpCode in [ Mono.Cecil.Cil.Opcodes.Stelem_I, Mono.Cecil.Cil.Opcodes.Stelem_I1, Mono.Cecil.Cil.Opcodes.Stelem_I2, Mono.Cecil.Cil.Opcodes.Stelem_I4, Mono.Cecil.Cil.Opcodes.Stelem_I8, Mono.Cecil.Cil.Opcodes.Stelem_R4, Mono.Cecil.Cil.Opcodes.Stelem_R8, Mono.Cecil.Cil.Opcodes.Stelem_Ref, Mono.Cecil.Cil.Opcodes.Stelem_Any ]:
		value = fstack.pop()
		index = fstack.pop()
		addr = fstack.pop()
	
		if value.isTainted():
			try:
				memory[addr['data']].markTainted()	
			except KeyError:
				memory[addr['data']] = value	

	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Stfld:
		value = fstack.pop()
		# TODO: get actual obj_ref from stack element 
		addr = fstack.pop()

		if value.isTainted():	
			try:
				memory[addr['data']].markTainted()	
			except KeyError:
				memory[addr['data']] = value	
		
	elif ins.OpCode in [ Mono.Cecil.Cil.Opcodes.Stind_Ref, Mono.Cecil.Cil.Opcodes.Stind_I1, Mono.Cecil.Cil.Opcodes.Stind_I2, Mono.Cecil.Cil.Opcodes.Stind_I4, Mono.Cecil.Cil.Opcodes.Stind_I8, Mono.Cecil.Cil.Opcodes.Stind_R4, Mono.Cecil.Cil.Opcodes.Stind_R8, Mono.Cecil.Cil.Opcodes.Stind_I ]:
		# pop
		value = fstack.pop()
		# pop address
		address = fstack.pop()
		
		memory[addr['data']] = value
		
	elif ins.OpCode in [ Mono.Cecil.Cil.Opcodes.Stloc, Mono.Cecil.Cil.Opcodes.Stloc_0, Mono.Cecil.Cil.Opcodes.Stloc_1, Mono.Cecil.Cil.Opcodes.Stloc_2, Mono.Cecil.Cil.Opcodes.Stloc_3, Mono.Cecil.Cil.Opcodes.Stloc_S ]:
		# pop stack
		se = fstack.pop()
	
		# index comes after . (e.g. stloc.0)
		index = value["data"].split('.')[1]
		
		memory["loc"+str(index)] = value
				
	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Stobj:
		# pop object ref
		obj_ref = fstack.pop()
		# pop address
		addr = fstack.pop()
		
		memory[addr['data']] = obj_ref
		
	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Stsfld:
		value = fstack.pop()
		
		field = ins.ToString.split(' ')[2]
		memory[field] = value
	
	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Initblk:
		num_bytes = fstack.pop()
		init_val = fstack.pop()
		address = fstack.pop()

		memory[address['data']] = init_val
	
	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Initobj:
		address = fstack.pop()
		
		memory[address['data']] = StackElement("", False)

	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Endfilter:
		value = fstack.pop()

	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Throw:
		obj_ref = fstack.pop()

	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Pop:
		fstack.pop()

	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Cpblk:
		num_bytes = fstack.pop()
		src_addr = fstack.pop()
		dst_addr = fstack.pop()
		
		memory[dst_addr['data']] = memory[src_addr['data']]

	elif ins.OpCode == Mono.Cecil.Cil.Opcodes.Cpobj:
		src_obj = fstack.pop()
		dst_obj = fstack.pop()
		
		# check if src addr is tainted
		memory[dst_obj['data']] = memory[src_obj['data']]

	else:
		print "Not handling ins " + ins.ToString()
		
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
		se = StackElement("", tainted)
		memory[data] = se
		
		# push reference (StackElement) onto stack
		se = StackElement(data, tainted)
		fstack.append(se)

	elif "newarr" in ins.OpCode.ToString():
		num_elements = fstack.pop()
		
		# store in simulated memory
		data = generateRandomAddress()
		se = StackElement("", False)
		memory[data] = se

		# push reference onto stack
		se = StackElement(data, False)
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
	
	while True
		opcode = cur_ins.OpCode.ToString()
		if opcode in PUSH_INS:
			tainted = False
			if "ldarg" in opcode.ToString():
				tainted = True
			fstack.append({'data': ins.ToString(), 'tainted': tainted})
		elif opcode in POP_INS:
			pop(method, cur_ins, ins_index, fstack, memory)
		elif opcode in SPECIAL_INS:
		
		elif opcode in BRANCH_INS:
			branch(method, ins, ins_index, fstack, memory):
		else:
			print "Don't recognize ins: " + cur_ins.ToString()
	
		cur_ins = cur_ins.Next
		if not cur_ins:
			break

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
	
