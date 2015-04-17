'''

1. Find scriptNotify handlers (for both WebView and WebBrowser)
2. Find methods called by handlers
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
import subprocess

apps_dir = "C:\\Users\\b\\Downloads\\apps"
unzipped_apps_dir = "C:\\Users\\b\\Downloads\\apps\\unzipped"
UNZIP = "C:\\Users\\b\\Downloads\\7za920\\7za.exe"
OUTFILE = "output.txt"

def main():
	of = open(OUTFILE, 'w')
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
					of = open(OUTFILE, 'a')
					of.write("FILE: " + str(f_dir) + " " + str(f) + "\n")
					of.close()
					
					try:
						asm = AssemblyDefinition.ReadAssembly(os.path.join(f_dir, f))
					except SystemError:
						print "FAILED: " + str(os.path.join(f_dir, f))
						continue

					handlers = searchScriptNotifyHandler(asm)
					
					for handler in handlers:
						of = open(OUTFILE, "a")
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
					of = open(OUTFILE, "a")
					of.write("\t" + str(i.Operand.Name) + "\n")
					of.close()
					getMethodsCalled(i.Operand.GetElementMethod())
					
def test():
	# TEST USING WEBVIEW EXAMPLE
	
	of = open(OUTFILE, 'w')
	of.write('')
	of.close()

	f = "Controls_WebView.WindowsPhone.exe"
	f_dir = "C:\\Users\\b\\Downloads\\XAML WebView control sample\\C#\\WindowsPhone\\bin\\Debug"
	of = open(OUTFILE, 'a')
	of.write("FILE: " + str(f_dir) + " " + str(f) + "\n")
	of.close()
					
	try:
		asm = AssemblyDefinition.ReadAssembly(os.path.join(f_dir, f))
	except SystemError:
		print "FAILED: " + str(os.path.join(f_dir, f))

	searchScriptNotifyHandler(asm)
	for handler in handlers:
		of = open(OUTFILE, "a")
		of.write("HANDLER: " + str(handler.Name) + "\n")
		of.write("METHODS CALLED: \n")
		of.close()
		getMethodsCalled(handler)
	