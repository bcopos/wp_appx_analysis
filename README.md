Windows Phone 8.1 Appx Application Analysis
==========

Tool created to analyze security of Windows Phone 8.1 applications (appx format).
Specifically, the tool analyzes applications to see if a given application can be attacked by Javascripts loaded within the application's WebView.

How?
----

The analysis occurs in two steps:
1. Unpack appx and inspect manifest file for compatibility
	- check if application has WebView component
	- check if application has ScriptNotifyEvent handlers
	- if none apply, stop
2. Data and control analysis
	- for ScriptNotifyEvent handlers, build call graph
		- find all functions called by a handler (both directly and indirectly)
		- filter called functions for sensitive Windows Runtime API functions
		- if API functions found in the call graph, examine data dependency
			- check if there is data dependency between data coming from JS via handlers to API functions


What else?
------

- check if developers check `callingUri` in ScriptNotifyEvent handlers

