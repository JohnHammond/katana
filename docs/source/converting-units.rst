Converting Units
================

.. toctree::
    :maxdepth: -1

When rewriting the Katana framework, a lot of changes were made to the :class:`katana.unit.Unit` interface. We tried
to keep the changes to a minimum, however some changes were inevitable. This should guide you through the changes
in order to either write a new unit or convert an old one.

While most of the interface remains unchanged, a few new features were added. Specifically, the
:class:`katana.manager.Manager` class now takes the place of the old `Katana` object. :class:`katana.target.Target`
has largely been unchanged from the previous version.

Dependency Changes
------------------

All properties of a Unit are now contained within the class. The `DEPENDENCIES` variable is now a property,
however it functions in the same capacity. The dependency mechanism can now be overridden through the
:func:`katana.unit.Unit.check_deps` method, however this is almost never needed.

Groups
------

Units are now parts of `groups` which allow you to arbitrarily group units into logical sections. By default
all converted units should be added to a group in conjunction with their package (e.g. "stego" or "crypto").
This allows old functionality like excluding those groups to remain. These group names can be specified
when interfacing with the :class:`katana.unit.Finder` class and therefore also with the Manager's ``units``
and ``exclude`` options. Those options can all either take a unit name or one of it's groups.

Recursion Preferences
---------------------

The old `PROTECTED_RECURSE` and `RECURSE` properties have been changed and a new recursion protection
mechanism is now in place. To modify recursion rules, you can now use the `katana.unit.Unit.RECURSE_SELF`,
`katana.unit.Unit.NO_RECURSE` and `katana.unit.Unit.BLOCKED_GROUPS`.

BLOCKED_GROUPS allows you to outlaw recursion into entire groups of units. For example, you may outlaw
recursion into any unit which is in the `crypto` group to prevent excessive recursion.

Reporting Data
--------------

The old data reporting mechanisms were part of the Katana class. In the new framework, these were moved to
the :class:`katana.manager.Manager` class and are all named as ``register_*``. For example, to register
arbitrary data as a result of this unit, you would call::

    data = {"Wow": "This is really cool. FLAG{flag}"}
    self.manager.register_data(self, data)

The manager will iterate through your data, and look for flags. It will also report the data to the
:class:`katana.monitor.Monitor`.

Generating and Reporting Artifacts
----------------------------------

Artifact creation used to be handled by the Katana class, but has been moved to :class:`katana.unit.Unit`.
However, the interface is largely the same for creating an artifact. To create an artifact, use the
:func:`katana.unit.Unit.generate_artifact` method. The interface and parameters are the same as the old
`katana.generate_artifact` method. The biggest difference is that the artifact will not automatically be
registered with the Manager or reported to the Monitor. To do that, call :func:`katana.manager.Manager.register_artifact`.
As an example, if you have some data you think is a file::

    data = b"Something that's probably a file!"
    name, stream = self.generate_artifact("interesting", create=True)
    stream.write(data)
    stream.close()
    self.manager.register_artifact(self, name)


