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
	- for ScriptNotifyEvent handlers
		- find all functions called by a handler (both directly and indirectly)
		- filter called functions for sensitive Windows Runtime API functions
		- if API functions found in the call graph, examine data dependency
			- check if there is data dependency between data coming from JS via handlers to API functions

Data Dependency
-----

- obtain all instructions of a given method (e.g. handler)
- step through instructions simulating stack (and memory)
- determine if the sensitive API function call takes in tainted data
	- tainted data = data that may be (or contain) data from the handler's parameters

What else?
------

- check if developers check `callingUri` in ScriptNotifyEvent handlers


Code Example of handlers
------

`handleScriptNotifyEvents()` - it checks the calling Uri

```
webview.addEventListener("MSWebViewScriptNotify", handleScriptNotifyEvents);
function handleScriptNotifyEvents(e) {
        if (e.callingUri === "https://msgnotify.example.net/") {
            if(e.value === "msg1")
            {
                // Process the message.);
            }
        }
    }
```

Get Started
------

Prerequisites:
- Mono.Cecil
- IronPython
- zip utility (by default it uses `7za`)

To run:
1) Check `analyze\_apps` script (mainly the `sys.path.append` at the top)
2) Run with IronPython: `ipy.exe analyze_apps`

