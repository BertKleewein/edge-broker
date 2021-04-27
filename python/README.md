# Architecture Principles

1. We're building "helpers", not a framework.
2. No direct dependencies on the transport.  If any of our helper code needs to include transport code, we've failed.
3. Helpers should be as independent as possible.  Customers should be able to chose components a-la-carte.

# The picture

![](./architecture.svg)

* Customer code calls Paho directly
* This means extra boilerplate code for customers.  We can make this better later by adding "convenience layers"

* 3 topic helpers (on right) have no dependencies on Paho.  They are string manipulation objects.
* Message Waiters (on right) are tied to topic helpers. They are not tied to Paho, but they make Paho easier to use.

* Auth objects (on left) are used to get MQTT connect args.
* Auth objects are not tied to Paho.
* SAS renewal code is very simple.  Relies on customer plumbing.

* 3 circles at top are missing code that we may want to add later.

# The tours

To explore this code, use the [Visual Studio Code CodeTour Extension](https://marketplace.visualstudio.com/items?itemName=vsls-contrib.codetour).  You will find various tours in the outline pane of VS Code.


