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
#sys.path.append("C:\\Users\b\\Downloads")
import os
import string
import random
import subprocess
from StackElement import StackElement

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
'''
PUSH_INS = [ Cil.OpCodes.Ldarg_0, Cil.OpCodes.Ldarg_1, Cil.OpCodes.Ldarg_2, Cil.OpCodes.Ldarg_3, Cil.OpCodes.Ldarg_S, Cil.OpCodes.Ldarga_S, Cil.OpCodes.Ldc_I4_M1, Cil.OpCodes.Ldc_I4_0, Cil.OpCodes.Ldc_I4_1, Cil.OpCodes.Ldc_I4_2, Cil.OpCodes.Ldc_I4_3, Cil.OpCodes.Ldc_I4_4, Cil.OpCodes.Ldc_I4_5, Cil.OpCodes.Ldc_I4_6, Cil.OpCodes.Ldc_I4_7, Cil.OpCodes.Ldc_I4_8, Cil.OpCodes.Ldc_I4_S, Cil.OpCodes.Ldc_I4, Cil.OpCodes.Ldc_R4, Cil.OpCodes.Ldc_R8, Cil.OpCodes.Ldelema, Cil.OpCodes.Ldelem_I1, Cil.OpCodes.Ldelem_U1, Cil.OpCodes.Ldelem_I2, Cil.OpCodes.Ldelem_U2, Cil.OpCodes.Ldelem_I4, Cil.OpCodes.Ldelem_U4, Cil.OpCodes.Ldelem_I8, Cil.OpCodes.Ldelem_I, Cil.OpCodes.Ldelem_R4, Cil.OpCodes.Ldelem_R8, Cil.OpCodes.Ldelem_Ref, Cil.OpCodes.Ldfld, Cil.OpCodes.Ldflda,  Cil.OpCodes.Ldind_I1, Cil.OpCodes.Ldind_U1, Cil.OpCodes.Ldind_I2, Cil.OpCodes.Ldind_U2, Cil.OpCodes.Ldind_I4, Cil.OpCodes.Ldind_U4, Cil.OpCodes.Ldind_I8, Cil.OpCodes.Ldind_I, Cil.OpCodes.Ldind_R4, Cil.OpCodes.Ldind_R8, Cil.OpCodes.Ldind_Ref, Cil.OpCodes.Ldlen, Cil.OpCodes.Ldloc, Cil.OpCodes.Ldloca, Cil.OpCodes.Ldloc_S, Cil.OpCodes.Ldloca_S, Cil.OpCodes.Ldnull, Cil.OpCodes.Ldobj, Cil.OpCodes.Unaligned, Cil.OpCodes.Volatile, Cil.OpCodes.Sizeof, Cil.OpCodes.Ldvirtftn, Cil.OpCodes.Ldtoken, Cil.OpCodes.Ldsfld, Cil.OpCodes.Ldsflda, Cil.OpCodes.Ldstr ]

POP_INS = [ Cil.OpCodes.Starg, Cil.OpCodes.Starg_S, Cil.OpCodes.Stelem_I, Cil.OpCodes.Stelem_I1, Cil.OpCodes.Stelem_I2, Cil.OpCodes.Stelem_I4, Cil.OpCodes.Stelem_I8, Cil.OpCodes.Stelem_R4, Cil.OpCodes.Stelem_R8, Cil.OpCodes.Stelem_Ref, Cil.OpCodes.Stelem_Any, Cil.OpCodes.Stfld, Cil.OpCodes.Stind_Ref, Cil.OpCodes.Stind_I1, Cil.OpCodes.Stind_I2, Cil.OpCodes.Stind_I4, Cil.OpCodes.Stind_I8, Cil.OpCodes.Stind_R4, Cil.OpCodes.Stind_R8, Cil.OpCodes.Stind_I, Cil.OpCodes.Stloc, Cil.OpCodes.Stloc_0, Cil.OpCodes.Stloc_1, Cil.OpCodes.Stloc_2, Cil.OpCodes.Stloc_3, Cil.OpCodes.Stloc_S, Cil.OpCodes.Stobj, Cil.OpCodes.Stsfld, Cil.OpCodes.Initblk, Cil.OpCodes.Initobj, Cil.OpCodes.Endfilter, Cil.OpCodes.Throw, Cil.OpCodes.Pop, Cil.OpCodes.Cpblk, Cil.OpCodes.Cpobj ]
BRANCH_INS = [ Cil.OpCodes.Beq, Cil.OpCodes.Beq_S, Cil.OpCodes.Bge, Cil.OpCodes.Bge_S, Cil.OpCodes.Bge_Un_S, Cil.OpCodes.Bge_Un, Cil.OpCodes.Bgt, Cil.OpCodes.Bgt_S, Cil.OpCodes.Bgt_Un, Cil.OpCodes.Bgt_Un_S, Cil.OpCodes.Ble, Cil.OpCodes.Ble_S, Cil.OpCodes.Ble_Un, Cil.OpCodes.Ble_Un_S, Cil.OpCodes.Blt, Cil.OpCodes.Blt_S, Cil.OpCodes.Blt_Un, Cil.OpCodes.Blt_Un_S, Cil.OpCodes.Bne_Un, Cil.OpCodes.Bne_Un_S ]
SWITCH_INS = [ Cil.OpCodes.Switch ]
BREAK_INS = [ Cil.OpCodes.Break ]
SPECIAL_INS = [ Cil.OpCodes.Call, Cil.OpCodes.Callvirt, Cil.OpCodes.Add, Cil.OpCodes.Box, Cil.OpCodes.Castclass, Cil.OpCodes.Ceq, Cil.OpCodes.Cgt, Cil.OpCodes.Cgt_Un, Cil.OpCodes.Ckfinite, Cil.OpCodes.Clt, Cil.OpCodes.Clt_Un, Cil.OpCodes.Conv_I, Cil.OpCodes.Conv_I1, Cil.OpCodes.Conv_I2, Cil.OpCodes.Conv_I4, Cil.OpCodes.Conv_I8, Cil.OpCodes.Conv_Ovf_I, Cil.OpCodes.Conv_Ovf_I_Un, Cil.OpCodes.Conv_Ovf_I1, Cil.OpCodes.Conv_Ovf_I1_Un, Cil.OpCodes.Conv_Ovf_I2, Cil.OpCodes.Conv_Ovf_I2_Un, Cil.OpCodes.Conv_Ovf_I4, Cil.OpCodes.Conv_Ovf_I4_Un, Cil.OpCodes.Conv_Ovf_I8, Cil.OpCodes.Conv_Ovf_I8_Un, Cil.OpCodes.Conv_Ovf_U, Cil.OpCodes.Conv_Ovf_U_Un, Cil.OpCodes.Conv_Ovf_U1, Cil.OpCodes.Conv_Ovf_U1_Un, Cil.OpCodes.Conv_Ovf_U2, Cil.OpCodes.Conv_Ovf_U2_Un, Cil.OpCodes.Conv_Ovf_U4, Cil.OpCodes.Conv_Ovf_U4_Un, Cil.OpCodes.Conv_Ovf_U8, Cil.OpCodes.Conv_Ovf_U8_Un, Cil.OpCodes.Conv_R_Un, Cil.OpCodes.Conv_R4, Cil.OpCodes.Conv_R8, Cil.OpCodes.Conv_U, Cil.OpCodes.Conv_U1, Cil.OpCodes.Conv_U2, Cil.OpCodes.Conv_U4, Cil.OpCodes.Conv_U8, Cil.OpCodes.Div, Cil.OpCodes.Div_Un, Cil.OpCodes.Dup, Cil.OpCodes.Isinst, Cil.OpCodes.Localloc, Cil.OpCodes.Mkrefany, Cil.OpCodes.Mul, Cil.OpCodes.Not, Cil.OpCodes.Or, Cil.OpCodes.Refanytype, Cil.OpCodes.Refanyval, Cil.OpCodes.Rem, Cil.OpCodes.Rem_Un, Cil.OpCodes.Ret, Cil.OpCodes.Shl, Cil.OpCodes.Shr, Cil.OpCodes.Shr_Un, Cil.OpCodes.Sub, Cil.OpCodes.Sub_Ovf, Cil.OpCodes.Sub_Ovf_Un, Cil.OpCodes.Unbox, Cil.OpCodes.Unbox_Any, Cil.OpCodes.Xor]

def pushIns(method, ins, ins_index, fstack, memory):
	if ins.OpCode in [ Cil.OpCodes.Ldarg_0, Cil.OpCodes.Ldarg_1, Cil.OpCodes.Ldarg_2, Cil.OpCodes.Ldarg_3, Cil.OpCodes.Ldarg_S, Cil.OpCodes.Ldarga_S ]:
		argslot = ins.OpCode.ToString().split('.')[1]
		se = StackElement("arg"+argslot, True)
		
		# push onto stack
		fstack.append(se)
		
	elif ins.OpCode in [ Cil.OpCodes.Ldc_I4_M1, Cil.OpCodes.Ldc_I4_0, Cil.OpCodes.Ldc_I4_1, Cil.OpCodes.Ldc_I4_2, Cil.OpCodes.Ldc_I4_3, Cil.OpCodes.Ldc_I4_4, Cil.OpCodes.Ldc_I4_5, Cil.OpCodes.Ldc_I4_6, Cil.OpCodes.Ldc_I4_7, Cil.OpCodes.Ldc_I4_8, Cil.OpCodes.Ldc_I4_S, Cil.OpCodes.Ldc_I4, Cil.OpCodes.Ldc_R4, Cil.OpCodes.Ldc_R8 ]:
		if ins.Operand:
			value = ins.Operand.ToString()
		else:
			value = ins.OpCode.ToString().split('.')[2]

		# create stack element
		se = StackElement(value, False)

		# push onto stack
		fstack.append(se)

	elif ins.OpCode in [ Cil.OpCodes.Ldelema, Cil.OpCodes.Ldelem_I1, Cil.OpCodes.Ldelem_U1, Cil.OpCodes.Ldelem_I2, Cil.OpCodes.Ldelem_U2, Cil.OpCodes.Ldelem_I4, Cil.OpCodes.Ldelem_U4, Cil.OpCodes.Ldelem_I8, Cil.OpCodes.Ldelem_I, Cil.OpCodes.Ldelem_R4, Cil.OpCodes.Ldelem_R8, Cil.OpCodes.Ldelem_Ref ]:
		# pop
		index = fstack.pop()
		array_ref = fstack.pop()

		#TODO: does this really matter? we just care if it's tainted...
		value = ""
		se = StackElement(value, memory[array_ref['data']].isTainted())
		
		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldfld:
	 	# pop
		obj_ref = fstack.pop()

		se = StackElement(memory[obj_ref['data']], memory[obj_ref['data']].isTainted())		

		# push onto stack
		fstack.append(se)
	
	elif ins.OpCode == Cil.OpCodes.Ldflda:
	 	# pop
		obj_ref = fstack.pop()
		
		addr = generateRandomAddress()
		memory[addr] = memory[obj_ref['data']]

		se = StackElement(addr, memory[obj_ref['data']].isTainted())		
		# push onto stack
		fstack.append(se)	

	elif ins.OpCode in [ Cil.OpCodes.Ldind_I1, Cil.OpCodes.Ldind_U1, Cil.OpCodes.Ldind_I2, Cil.OpCodes.Ldind_U2, Cil.OpCodes.Ldind_I4, Cil.OpCodes.Ldind_U4, Cil.OpCodes.Ldind_I8, Cil.OpCodes.Ldind_I, Cil.OpCodes.Ldind_R4, Cil.OpCodes.Ldind_R8, Cil.OpCodes.Ldind_Ref ]:
	 	# pop
		addr = fstack.pop()

		se = StackElement("", memory[addr['data']].isTainted())
	
		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldlen:
		# pop
		array_ref = fstack.pop()

		se = StackElement("", False)	 	

		# push onto stack
		fstack.append(se)

	elif ins.OpCode in [ Cil.OpCodes.Ldloc, Cil.OpCodes.Ldloca, Cil.OpCodes.Ldloc_S, Cil.OpCodes.Ldloca_S ]:
		if ins.Operand:
			loc = ins.Operand.ToString()
		else:
			loc = ins.OpCode.ToString().split('.')[1]

		se = memory[loc] 
	 	
		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldnull:
		se = StackElement("null", False)
	 	
		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldobj:
		# pop
		addr = fstack.pop()

		se = memory[addr['data']]
	 	
		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldsfld:
		field = ins.ToString().split(' ')[2]
		try:
			se = memory[field]['data']
		except KeyError:
			# this shouldn't happen, ldsflda implies previous stsfld
			print "This shouldn't happen"
			se = StackElement(field, False)
		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldsflda:
		field = ins.ToString().split(' ')[2]
		try:
			se = memory[field]['addr']
		except KeyError:
			# this shouldn't happen, ldsflda implies previous stsfld
			print "This shouldn't happen"
			se = StackElement(generateRandomAddress(), False)

		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldstr:
		se = StackElement("", False)
	 	
		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldtoken:
		se = StackElement("", False)
	 	
		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Ldvirtftn:
		# pop
		fstack.pop()

		se = StackElement("", False)

		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Sizeof:
		se = StackElement("", False)

		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Volatile:

		# push onto stack
		fstack.append(se)

	elif ins.OpCode == Cil.OpCodes.Unaligned:

		# push onto stack
		fstack.append(se)

	else:
		print "Not handling push ins " + ins.ToString()
			

#
# for any store instructions, store even if the value is not tained (in case we need it later)
#
# what to store?
#	a StackElement (data, tainted bool)
#		where data (i.e. X) is:
#			- usually empty or something bogus
#			- if it is a memory reference (array ref or obj ref etc) then it's the address
# 		and tainted describes if data from the argument could have flown into the data (directly or indirectly)
def popIns(method, ins, ins_index, fstack, memory):
	if ins.OpCode == Cil.OpCodes.Starg or ins.OpCode == Cil.OpCodes.Starg_S:
		value = fstack.pop()
		
		argslot = ins.OpCode.ToString().split('.')[1]
	
		memory["arg"+str(argslot)] = value

	elif ins.OpCode in [ Cil.OpCodes.Stelem_I, Cil.OpCodes.Stelem_I1, Cil.OpCodes.Stelem_I2, Cil.OpCodes.Stelem_I4, Cil.OpCodes.Stelem_I8, Cil.OpCodes.Stelem_R4, Cil.OpCodes.Stelem_R8, Cil.OpCodes.Stelem_Ref, Cil.OpCodes.Stelem_Any ]:
		value = fstack.pop()
		index = fstack.pop()
		addr = fstack.pop()
	
		if value.isTainted():
			try:
				memory[addr['data']].markTainted()	
			except KeyError:
				memory[addr['data']] = value	

	elif ins.OpCode == Cil.OpCodes.Stfld:
		value = fstack.pop()
		addr = fstack.pop()

		if value.isTainted():	
			try:
				memory[addr['data']].markTainted()	
			except KeyError:
				memory[addr['data']] = value	
		
	elif ins.OpCode in [ Cil.OpCodes.Stind_Ref, Cil.OpCodes.Stind_I1, Cil.OpCodes.Stind_I2, Cil.OpCodes.Stind_I4, Cil.OpCodes.Stind_I8, Cil.OpCodes.Stind_R4, Cil.OpCodes.Stind_R8, Cil.OpCodes.Stind_I ]:
		# pop
		value = fstack.pop()
		# pop address
		address = fstack.pop()
		
		memory[addr['data']] = value
		
	elif ins.OpCode in [ Cil.OpCodes.Stloc, Cil.OpCodes.Stloc_0, Cil.OpCodes.Stloc_1, Cil.OpCodes.Stloc_2, Cil.OpCodes.Stloc_3, Cil.OpCodes.Stloc_S ]:
		# pop stack
		se = fstack.pop()
	
		# index comes after . (e.g. stloc.0)
		if ins.Operand:
			index = ins.Operand.ToString()
		else:
			index = ins.OpCode.ToString().split('.')[1]
		
		memory["loc"+str(index)] = se
				
	elif ins.OpCode == Cil.OpCodes.Stobj:
		# pop object ref
		obj_ref = fstack.pop()
		# pop address
		addr = fstack.pop()
		
		memory[addr['data']] = obj_ref
		
	elif ins.OpCode == Cil.OpCodes.Stsfld:
		value = fstack.pop()
		
		field = ins.ToString().split(' ')[2]
		addr = generateRandomAddress()
		memory[field] = {'addr': StackElement(addr, value.isTainted()), 'data': value}
		memory[addr] = value
	
	elif ins.OpCode == Cil.OpCodes.Initblk:
		num_bytes = fstack.pop()
		init_val = fstack.pop()
		address = fstack.pop()

		memory[address['data']] = init_val
	
	elif ins.OpCode == Cil.OpCodes.Initobj:
		address = fstack.pop()
		
		memory[address['data']] = StackElement("", False)

	elif ins.OpCode == Cil.OpCodes.Endfilter:
		value = fstack.pop()

	elif ins.OpCode == Cil.OpCodes.Throw:
		obj_ref = fstack.pop()

	elif ins.OpCode == Cil.OpCodes.Pop:
		fstack.pop()

	elif ins.OpCode == Cil.OpCodes.Cpblk:
		num_bytes = fstack.pop()
		src_addr = fstack.pop()
		dst_addr = fstack.pop()
		
		memory[dst_addr['data']] = memory[src_addr['data']]

	elif ins.OpCode == Cil.OpCodes.Cpobj:
		src_obj = fstack.pop()
		dst_obj = fstack.pop()
		
		# check if src addr is tainted
		memory[dst_obj['data']] = memory[src_obj['data']]

	else:
		print "Not handling pop ins " + ins.ToString()
		
def branchIns(method, ins, ins_index, fstack, memory):
	# for branch ins, split execution one contiunuing with branch and another contiuning from the next target ins (end of branch)
	if ins.OpCode in BRANCH_INS:
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
			if value.isTainted():
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
		fstack.append(se)

	else:
		print "Not handling new ins " + ins.ToString()

def specialIns(method, ins, ins_index, fstack, memory):
	if ins.OpCode == Cil.OpCodes.Call:
		num_args = ins.Operand.Parameters.Count

		for i in range(0, num_args):
			fstack.pop()
			
		returnVal = StackElement("", False)
		fstack.append(returnVal)
		
	if ins.OpCode ==  Cil.OpCodes.Callvirt:
		num_args = ins.Operand.Parameters.Count

		for i in range(0, num_args):
			fstack.pop()
		
		fstack.pop()
			
		returnVal = StackElement("", False)
		fstack.append(returnVal)
	
	elif ins.OpCode in [ Cil.OpCodes.Add, Cil.OpCodes.Add_Ovf, Cil.OpCodes.Add_Ovf_Un ]:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", val1.isTainted() or val2.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Box:
		val1 = fstack.pop()

		result = StackElement("", val1.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Castclass:
		val1 = fstack.pop()

		result = StackElement("", val1.isTainted())
		fstack.append(result)

	elif ins.OpCode in [ Cil.OpCodes.Ceq, Cil.OpCodes.Cgt, Cil.OpCodes.Cgt_Un ]:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", val1.isTainted() or val2.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Ckfinite:
		val1 = fstack.pop()
		fstack.append(val1)

	elif ins.OpCode in [ Cil.OpCodes.Clt, Cil.OpCodes.Clt_Un ]:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", False)
		fstack.append(result)

	elif ins.OpCode in [ Cil.OpCodes.Conv_I, Cil.OpCodes.Conv_I1, Cil.OpCodes.Conv_I2, Cil.OpCodes.Conv_I4, Cil.OpCodes.Conv_I8, Cil.OpCodes.Conv_Ovf_I, Cil.OpCodes.Conv_Ovf_I_Un, Cil.OpCodes.Conv_Ovf_I1, Cil.OpCodes.Conv_Ovf_I1_Un, Cil.OpCodes.Conv_Ovf_I2, Cil.OpCodes.Conv_Ovf_I2_Un, Cil.OpCodes.Conv_Ovf_I4, Cil.OpCodes.Conv_Ovf_I4_Un, Cil.OpCodes.Conv_Ovf_I8, Cil.OpCodes.Conv_Ovf_I8_Un, Cil.OpCodes.Conv_Ovf_U, Cil.OpCodes.Conv_Ovf_U_Un, Cil.OpCodes.Conv_Ovf_U1, Cil.OpCodes.Conv_Ovf_U1_Un, Cil.OpCodes.Conv_Ovf_U2, Cil.OpCodes.Conv_Ovf_U2_Un, Cil.OpCodes.Conv_Ovf_U4, Cil.OpCodes.Conv_Ovf_U4_Un, Cil.OpCodes.Conv_Ovf_U8, Cil.OpCodes.Conv_Ovf_U8_Un, Cil.OpCodes.Conv_R_Un, Cil.OpCodes.Conv_R4, Cil.OpCodes.Conv_R8, Cil.OpCodes.Conv_U, Cil.OpCodes.Conv_U1, Cil.OpCodes.Conv_U2, Cil.OpCodes.Conv_U4, Cil.OpCodes.Conv_U8 ]:
		val1 = fstack.pop()

		result = StackElement("", val1.isTainted())
		fstack.append(result)

	elif ins.OpCode in [ Cil.OpCodes.Div, Cil.OpCodes.Div_Un ]:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", val1.isTainted() or val2.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Dup:
		val = fstack.pop()

		fstack.append(val)
		dup = StackElement("", val.isTainted())
		fstack.append(dup)

	elif ins.OpCode == Cil.OpCodes.Isinst:
		val1 = fstack.pop()

		result = StackElement("", val1.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Localloc:
		val1 = fstack.pop()

		addr = generateRandomAddress()
		result = StackElement(addr, val1.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Mkrefany:
		val1 = fstack.pop()

		result = StackElement("", val1.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Mul:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", val1.isTainted() or val2.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Not:
		val1 = fstack.pop()

		result = StackElement("", val1.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Or:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", val1.isTainted() or val2.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Refanytype:
		val1 = fstack.pop()

		result = StackElement("", False)
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Refanyval:
		val1 = fstack.pop()
		
		addr = generateRandomAddress()
		memory[addr] = val1
		result = StackElement(addr, False)
		fstack.append(result)

	elif ins.OpCode in [ Cil.OpCodes.Rem, Cil.OpCodes.Rem_Un ]:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", val1.isTainted() or val2.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Ret:
		val1 = fstack.pop()

	elif ins.OpCode in [ Cil.OpCodes.Shl, Cil.OpCodes.Shr, Cil.OpCodes.Shr_Un ]:
		val1 = fstack.pop()

		result = StackElement("", False)
		fstack.append(result)

	elif ins.OpCode in [ Cil.OpCodes.Sub, Cil.OpCodes.Sub_Ovf, Cil.OpCodes.Sub_Ovf_Un ]:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", val1.isTainted() or val2.isTainted())
		fstack.append(result)

	elif ins.OpCode in [ Cil.OpCodes.Unbox, Cil.OpCodes.Unbox_Any ]:
		val1 = fstack.pop()

		result = StackElement("", val1.isTainted())
		fstack.append(result)

	elif ins.OpCode == Cil.OpCodes.Xor:
		val1 = fstack.pop()
		val2 = fstack.pop()

		result = StackElement("", val1.isTainted() or val2.isTainted())
		fstack.append(result)

	else:
		print "Not handling special ins " + ins.ToString()

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
		
# TODO: reset memory appropriately for branch instructions
def dataFlow(method, fstack, ins_index, memory):
	cur_ins = method.Body.Instructions[ins_index]
	
	while True:
		print "============================"
		print "INS: " + cur_ins.ToString()
		opcode = cur_ins.OpCode
		if opcode in PUSH_INS:
			pushIns(method, cur_ins, ins_index, fstack, memory)
		elif opcode in POP_INS:
			popIns(method, cur_ins, ins_index, fstack, memory)
		elif opcode in SPECIAL_INS:
			specialIns(method, cur_ins, ins_index, fstack, memory)
		elif opcode in BRANCH_INS:
			branchIns(method, cur_ins, ins_index, fstack, memory)
		elif opcode in [Cil.OpCodes.Newobj, Cil.OpCodes.Newarr]:
			newIns(method, cur_ins, ins_index, fstack, memory)
		else:
			print "Don't recognize ins: " + cur_ins.ToString()
	
		print "STACK: " + str(fstack)
		print "MEMORY: " + str(memory)
		cur_ins = cur_ins.Next
		if not cur_ins:
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
	
