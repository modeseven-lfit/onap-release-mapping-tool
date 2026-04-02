.. SPDX-FileCopyrightText: 2025 The Linux Foundation
.. SPDX-License-Identifier: Apache-2.0

Collectors
==========

The collectors framework gathers ONAP release data from various upstream
sources. Each collector implements the :class:`BaseCollector` interface
and is registered with the global :data:`registry`.

Framework
---------

.. automodule:: onap_release_map.collectors
   :members:
   :undoc-members:
   :show-inheritance:

OOM Collector
-------------

.. automodule:: onap_release_map.collectors.oom
   :members:
   :undoc-members:
   :show-inheritance:

Gerrit Collector
----------------

.. automodule:: onap_release_map.collectors.gerrit
   :members:
   :undoc-members:
   :show-inheritance:

Nexus Collector
---------------

.. automodule:: onap_release_map.collectors.nexus
   :members:
   :undoc-members:
   :show-inheritance:

Release Manager Collector
-------------------------

.. automodule:: onap_release_map.collectors.relman
   :members:
   :undoc-members:
   :show-inheritance:

JJB Collector
-------------

.. automodule:: onap_release_map.collectors.jjb
   :members:
   :undoc-members:
   :show-inheritance:

Integration Collector
---------------------

.. automodule:: onap_release_map.collectors.integration
   :members:
   :undoc-members:
   :show-inheritance: