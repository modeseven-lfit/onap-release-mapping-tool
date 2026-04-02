.. SPDX-FileCopyrightText: 2025 The Linux Foundation
.. SPDX-License-Identifier: Apache-2.0

Exceptions
==========

Custom exception hierarchy for ``onap-release-map``.

All exceptions inherit from :class:`~onap_release_map.exceptions.OnapReleaseMapError`,
making it easy to catch any tool-specific error with a single ``except`` clause.

.. automodule:: onap_release_map.exceptions
   :members:
   :undoc-members:
   :show-inheritance: