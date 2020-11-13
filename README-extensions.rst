Escaping of References and Inventory Queries
--------------------------------------------

Reference and inventory queries can be escaped to produce literal strings, for example:

.. code-block:: yaml

  parameters:
    colour: Blue
    unescaped: The colour is ${colour}
    escaped: The colour is \${colour}
    double_escaped: The colour is \\${colour}


This would produce:

.. code-block:: yaml

  parameters:
    colour: Blue
    unescaped: The colour is Blue
    escaped: The colour is ${colour}
    double_escaped: The colour is \Blue



Ignore class not found
----------------------

At some cases (bootstrapping, development) it can be convenient to ignore some missing classes.
To control the feature there are two options available:

.. code-block:: yaml

  ignore_class_notfound: False
  ignore_class_notfound_regexp: ['.*']

If you set regexp pattern to ``service.*`` all missing classes starting 'service.' will be logged with warning, but will not
fail to return rendered reclass. Assuming all parameter interpolation passes.



Merging Referenced Lists and Dictionaries
-----------------------------------------

Referenced lists or dicts can now be merged:

.. code-block:: yaml

  # nodes/test.yml
  classes:
    - test1
    - test2
  parameters:
    one:
      a: 1
      b: 2
    two:
      c: 3
      d: 4
    three:
      e: 5

  # classes/test1.yml
  parameters:
    three: ${one}

  # classes/test2.yml
  parameters:
    three: ${two}

``running reclass.py --nodeinfo node1`` then gives:

.. code-block:: yaml

  parameters:
    one:
      a: 1
      b: 2
    three:
      a: 1
      b: 2
      c: 3
      d: 4
      e: 5
    two:
      c: 3
      d: 4

This first sets the parameter three to the value of parameter one (class test1) then merges parameter two into
parameter three (class test2) and finally merges the parameter three definition given in the node definition into
the final value.


Allow override list and dicts by empty entity,None instead of merge
-------------------------------------------------------------------

With settings:

.. code-block:: yaml

  allow_none_override: True       # default True

  # note dict,list over None is allowed and not configurable

Referenced lists or dicts can now be overriden by None or empty type of dict, list:

.. code-block:: yaml

  # nodes/test.yml
  parameters:
    one:
      a: 1
      b: 2
    two: {}
    three: None

  # classes/test1.yml
  parameters:
    one: ${two}

  # classes/test2.yml
  parameters:
    three: ${one}


Constant Parameters
--------------------------

Parameters can be labeled as constant by using the prefix ``=``

.. code-block:: yaml

  parameters:
    =one: 1

If in the normal parameter merging a constant parameter would be changed then depending
on the setting of ``strict_constant_parameters`` either an exception is raised (``strict_constant_parameters`` true)
or the parameter is left unchanged and no notification or error is given (``strict_constant_parameters`` false)

For example with:

.. code-block:: yaml

  # nodes/node1.yml
  classes:
  - first
  - second

  # classes/first.yml
  parameters:
    =one: 1

  # classes/second.yml
  parameters:
    one: 2

``reclass.py --nodeinfo node1`` then gives an ''Attempt to change constant value'' error if ``strict_constant_parameters``
is true or gives:

.. code-block:: yaml

  parameters:
    alpha:
      one: 1

if ``strict_constant_parameters`` is false

Default value for ``strict_constant_parameters`` is True

.. code-block:: yaml

  strict_constant_parameters: True


Nested References
-----------------

References can now be nested, for example:

.. code-block:: yaml

  # nodes/node1.yml
  parameters:
    alpha:
      one: ${beta:${alpha:two}}
      two: a
    beta:
      a: 99

``reclass.py --nodeinfo node1`` then gives:

.. code-block:: yaml

  parameters:
    alpha:
      one: 99
      two: a
    beta:
      a: 99

The ``${beta:${alpha:two}}`` construct first resolves the ``${alpha:two}`` reference to the value 'a', then resolves
the reference ``${beta:a}`` to the value 99.


Ignore overwritten missing references
-------------------------------------

Given the following classes:

.. code-block:: yaml

  # node1.yml
  classes:
  - class1
  - class2
  - class3

  # class1.yml
  parameters:
    a: ${x}

  # class2.yml
  parameters:
    a: ${y}

  # class3.yml
  parameters:
    y: 1


The parameter ``a`` only depends on the parameter ``y`` through the reference set in class2. The fact that the parameter ``x`` referenced
in class1 is not defined does not affect the final value of the parameter ``a``. For such overwritten missing references by default a warning is
printed but no error is raised, providing the final value of the parameter being evaluated is a scalar. If the final value is a dictionary or list
an error will always be raised in the case of a missing reference.

Default value is True to keep backward compatible behavior.

.. code-block:: yaml

  ignore_overwritten_missing_reference: True


Print summary of missed references
----------------------------------

Instead of failing on the first undefinded reference error all missing reference errors are printed at once.

.. code-block:: yaml

  reclass --nodeinfo mynode
  -> dontpanic
     Cannot resolve ${_param:kkk}, at mkkek3:tree:to:fail, in yaml_fs:///test/classes/third.yml
     Cannot resolve ${_param:kkk}, at mkkek3:tree:another:xxxx, in yaml_fs:///test/classes/third.yml
     Cannot resolve ${_param:kkk}, at mykey2:tree:to:fail, in yaml_fs:///test/classes/third.yml

.. code-block:: yaml

  group_errors: True


Use references in class names
-----------------------------

Allows to use references in the class names.

References pointed to in class names cannot themselves reference another key, they should be simple strings.

To avoid pitfalls do not over-engineer your class references. They should be used only for core conditions and only for them.
A short example: `- system.wrodpress.db.${_class:database_backend}`.

Best practices:
- use references in class names always load your global class specification prior the reference is used.
- structure your class references under parameters under one key (for example `_class`).
- use class references as a kind of "context" or "global" available options you always know what they are set.

Class referencing for existing reclass users. Frequently when constructing your models you had to load or not load some
classes based on your setup. In most cases this lead to fork of a model or introducing kind of template generator (like cookiecutter) to
create a model based on the base "context" or "global" variables. Class referencing is a simple way how to avoid
"pre-processors" like this and if/else conditions around class section.


Assuming following class setup:

* node is loading `third.yml` class only


Classes:

.. code-block:: yaml

  #/etc/reclass/classes/global.yml
  parameters:
    _class:
      env:
        override: 'env.dev'
    lab:
      name: default

  #/etc/reclass/classes/lab/env/dev.yml
  parameters:
    lab:
      name: dev

  #/etc/reclass/classes/second.yml
  classes:
    - global
    - lab.${_class:env:override}

  #/etc/reclass/classes/third.yml
  classes:
    - global
    - second


Reclass --nodeinfo then returns:

.. code-block:: yaml

  ...
  ...
  applications: []
  environment: base
  exports: {}
  classes:
  - global
  - lab.${_class:env:override}
  - second
  parameters:
    _class:
      env:
        override: env.dev
    lab:
      name: dev
    ...
    ...


Load classes with relative names
--------------------------------

Load referenced class from a relative location to the current class.
To load class from relative location start the class uri with "." or ".." char.
The only supported reference is to nested tree structure below the current class.

You are allowed to use syntax for relative uri to required class on any place on your model (first class loaded, init.yml, regular class .yml).

The feature is expected to improve flexibility while sharing classes between your models.

Please mpte that you can't use '..' without any calss following. If you want simply up in the sctructure, type in '..init'.

It's a new feature use it with care and mind that using "relative syntax" lower traceability of
your pillar composition.

Example usage of relative class name using '.' and '..':

.. code-block:: yaml

  #/etc/reclass/classes/component/defaults.yml
  classes:
    component:
      config:
        a: b

.. code-block:: yaml

  #/etc/reclass/classes/component/init.yml
  classes:
    - .defaults

.. code-block:: yaml

  #/etc/reclass/classes/component/configuration/init.yml
  classes:
    - ..defaults


Inventory Queries
-----------------

Inventory querying works using a new key type - exports to hold values which other node definitions can read using a $[] query, for example with:

.. code-block:: yaml

  # nodes/node1.yml
  exports:
    test_zero: 0
    test_one:
      name: ${name}
      value: 6
    test_two: ${dict}

  parameters:
    name: node1
    dict:
      a: 1
      b: 2
    exp_value_test: $[ exports:test_two ]
    exp_if_test0: $[ if exports:test_zero == 0 ]
    exp_if_test1: $[ exports:test_one if exports:test_one:value == 7 ]
    exp_if_test2: $[ exports:test_one if exports:test_one:name == self:name ]

  # nodes/node2.yml
  exports:
    test_zero: 0
    test_one:
      name: ${name}
      value: 7
    test_two: ${dict}

  parameters:
    name: node2
    dict:
      a: 11
      b: 22


``running reclass.py --nodeinfo node1``  gives (listing only the exports and parameters):

.. code-block:: yaml

  exports:
    test_one:
      name: node1
      value: 6
    test_two:
      a: 1
      b: 2
  parameters:
    dict:
      a: 1
      b: 2
    exp_if_test0:
      - node1
      - node2
    exp_if_test1:
      node2:
        name: node2
        value: 7
    exp_if_test2:
      node1:
        name: node1
        value: 6
    exp_value_test:
      node1:
        a: 1
        b: 2
      node2:
        a: 11
        b: 22
    name: node1


Exports defined for a node can be a simple value or a reference to a parameter in the node definition.
The ``$[]`` inventory queries are calculated for simple value expressions, ``$[ exports:key ]``, by returning
a dictionary with an element (``{ node_name: key value }``) for each node which defines 'key' in the exports
section. For tests with a preceeding value, ``$[ exports:key if exports:test_key == test_value ]``, the
element (``{ node_name: key value }``) is only added to the returned dictionary if the test_key defined in
the node exports section equals the test value. For tests without a preceeding value,
``$[ if exports:test_key == test_value ]``, a list of nodes which pass the test is returned. For either test
form the test value can either be a simple value or a node parameter. And as well as an equality test
a not equals test (``!=``) can also be used.


**Inventory query options**

By default inventory queries only look at nodes in the same environment as the querying node. This can be
overriden using the +AllEnvs option:

.. code-block:: yaml

  $[ +AllEnvs exports:test ]

Any errors in rendering the export parameters for a node will give an error for the inventory query as a whole.
This can be overriden using the ``+IgnoreErrors`` option:

.. code-block:: yaml

  $[ +IgnoreErrors exports:test ]

With the ``+IgnoreErrors`` option nodes which generate an error evaluating ``exports:test`` will be ignored.

Inventory query options can be combined:

.. code-block:: yaml

  $[ +AllEnvs +IgnoreErrors exports:test ]

**Logical operators and/or**

The logical operators and/or can be used in inventory queries:

.. code-block:: yaml

  $[ exports:test_value if exports:test_zero == 0 and exports:test_one == self:value ]

The individual elements of the if statement are evaluated and combined with the logical operators starting from the
left and working to the right.


**Inventory query example**

Defining a cluster of machines using an inventory query, for example to open access to a database server to a
group of nodes. Given exports/parameters for nodes of the form:

.. code-block:: yaml

  # for all nodes requiring access to the database server
    exports:
      host:
        ip_address: aaa.bbb.ccc.ddd
      cluster: _some_cluster_name_

.. code-block:: yaml

  # for the database server
  parameters:
    cluster_name: production-cluster
    postgresql:
      server:
        clients: $[ exports:host:ip_address if exports:cluster == self:cluster_name ]

This will generate a dictionary with an entry for node where the ``export:cluster`` key for a node is equal to the
``parameter:cluster_name`` key of the node on which the inventory query is run on. Each entry in the generated dictionary
will contain the value of the ``exports:host:ip_address`` key. The output dictionary (depending on node definitions)
would look like:

.. code-block:: yaml

  node1:
    ip_address: aaa.bbb.ccc.ddd
  node2:
    ip_address: www.xxx.yyy.zzz

For nodes where exports:cluster key is not defined or where the key is not equal to self:cluster_name no entry is made
in the output dictionary.

In practise the exports:cluster key can be set using a parameter reference:

.. code-block:: yaml

  exports:
    cluster: ${cluster_name}
  parameters:
    cluster_name: production-cluster

The above exports and parameter definitions could be put into a separate class and then included by nodes which require
access to the database and included by the database server as well.


Compose node name
---------------------------

Nodes can be defined in subdirectories. However, node names (filename) must be unique across all subdirectories.

For example, the following file structure is invalid:

.. code-block:: yaml

  inventory/nodes/prod/mysql.yml
  inventory/nodes/staging/mysql.yml

With setting:

.. code-block:: yaml

  compose_node_name: True       # default False

This adds the subfolder to the node name and the structure above can then be used. It generates the following reclass objects:

.. code-block:: yaml

  nodes:
    prod.mysql:
      ...
    staging.mysql:
      ...

If the subfolder path starts with the underscore character ``_``, then the subfolder path is NOT added to the node name.


Override node environment
-------------------------

The environment of a node is defined in it's node file. This can be overridden on the command line with the option
'--environment'. For example:

``reclass.py --nodeinfo node1 --environment test``

will return the node information for node1 as if the node was in the test environment, regardless of the environment value
in the node file.

When the node envrionment is overridden inventory queries that do not have the AllEnvs flag set will still return data for
other nodes matching the original, none overridden, environment.

When using reclass with salt the reclass node environment can be overridden on the salt command line. This is controlled by the
configuration option allow_adapter_env_override. When False (the default) no override is done. If allow_adapter_env_override is
true and either saltenv or pillarenv (depending on the salt command) is set on the salt command line the node environment will
be overridden and set to the value of either saltenv oe pillarenv. Should a salt command allow both saltenv and pillarenv to be
set the value of pillarenv takes precedence.

Currently in order to use this functionality the default salt reclass adapter provided with salt must be overridden. Place the
file contrib/modules/pillar/reclass_adapter.py in the pillar directory of the salt master extension_modules directory and the
file contrib/modules/tops/reclass_adapter.py in the tops directory of the salt master extension_modules directory.


Git storage type
----------------

Reclass node and class yaml files can be read from a remote git repository with the yaml_git storage type. Use nodes_uri and
classes_uri to define the git repos to use for nodes and classes. These can be the same repo.

For salt masters using ssh connections the private and public keys must be readable by the salt daemon, which requires the
private key NOT be password protected. For stand alone reclass using ssh connections if the privkey and pubkey options
are not defined then any in memory key (from ssh-add) will be used.

Salt master reclass config example:

.. code-block:: yaml

  storage_type:yaml_git
  nodes_uri:
    # branch to use
    branch: master

    # cache directory (default: ~/.reclass/git/cache)
    cache_dir: /var/cache/reclass/git

    # lock directory (default: ~/.reclass/git/lock)
    lock_dir: /var/cache/reclass/lock

    # private key for ssh connections (no default, but will used keys stored
    # by ssh-add in memory if privkey and pubkey are not set)
    privkey: /root/salt_rsa
    # public key for ssh connections
    pubkey: /root/salt_rsa.pub

    repo: git+ssh://gitlab@remote.server:salt/nodes.git

  classes_uri:
    # branch to use or __env__ to use the branch matching the node
    # environment name
    branch: __env__

    # cache directory (default: ~/.reclass/git/cache)
    cache_dir: /var/cache/reclass/git

    # lock directory (default: ~/.reclass/git/lock)
    lock_dir: /var/cache/reclass/lock

    # private key for ssh connections (no default, but will used keys stored
    # by ssh-add in memory if privkey and pubkey are not set)
    privkey: /root/salt_rsa
    # public key for ssh connections
    pubkey: /root/salt_rsa.pub

    # branch/env overrides for specific branches
    env_overrides:
    # prod env uses master branch
    - prod:
        branch: master
    # use master branch for nodes with no environment defined
    - none:
        branch: master

    repo: git+ssh://gitlab@remote.server:salt/site.git

    # root directory of the class hierarcy in git repo
    # defaults to root directory of git repo if not given
    root: classes


Mixed storage type
------------------

Use a mixture of storage types.

Salt master reclass config example, which by default uses yaml_git storage but overrides the location for
classes for the pre-prod environment to use a directory on the local disc:

.. code-block:: yaml

  storage_type: mixed
  nodes_uri:
    # storage type to use
    storage_type: yaml_git

    # yaml_git storage options
    branch: master
    cache_dir: /var/cache/reclass/git
    lock_dir: /var/cache/reclass/lock
    privkey: /root/salt_rsa
    pubkey: /root/salt_rsa.pub
    repo: git+ssh://gitlab@remote.server:salt/nodes.git

  classes_uri:
    # storage type to use
    storage_type: yaml_git

    # yaml_git storage options
    branch: __env__
    cache_dir: /var/cache/reclass/git
    lock_dir: /var/cache/reclass/lock
    privkey: /root/salt_rsa
    pubkey: /root/salt_rsa.pub
    repo: git+ssh://gitlab@remote.server:salt/site.git
    root: classes

    env_overrides:
    - prod:
        branch: master
    - none:
        branch: master
    - pre-prod:
        # override storage type for this environment
        storage_type: yaml_fs
        # options for yaml_fs storage type
        uri: /srv/salt/env/pre-prod/classes
