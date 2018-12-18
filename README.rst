Reclass README
=========================

This is the fork of original **reclass** that is available at:
https://github.com/madduck/reclass

Extentions
==========

List of the core features:

* Escaping of References and Inventory Queries
* Merging Referenced Lists and Dictionaries
* Nested References
* Inventory Queries
* Ignore class notfound/regexp option


Documentation
=============

.. _README-extensions: README-extensions.rst

Documentation covering the original version is in the doc directory.
See the `README-extensions`_ file for documentation on the extentions.


.. include:: ./README-extensions.rst


Reclass related projects/tools
==============================

Queries:

* yg, yaml grep with 'jq' syntax - https://gist.github.com/epcim/f1c5b748fa7c942de50677aef04f29f8, (https://asciinema.org/a/84173)
* reclass-graph - https://github.com/tomkukral/reclass-graph

Introspection, manupulation:

* reclass-tools, for manipulating reclass models - https://github.com/dis-xcom/reclass_tools

YAML merge tools:

* spruce, general purpose YAML & JSON merging tool - https://github.com/geofffranks/spruce

Other:

* saltclass, new pillar/master_tops module for salt with the behaviour of reclass - https://github.com/saltstack/salt/pull/42349

