=========
ChangeLog
=========

========= ========== ========================================================
Version   Date       Changes
========= ========== ========================================================
1.7.0     2020-10-02 Fixes and few new features:
                     * Allow class mappings to wildcard match against either the node name and class
                     * Support for .yaml along with .yml
                     * Support to use current node parameters as references in class name
1.6.0     2018-11-06 * Python code and parser refactoring by a-ovchinnikov
                     * Improvements in yaml_git and mixed setup by Andrew Pickford
                     * Relative paths in class names by Petr Michalec, Martin Polreich and Andrew Pickford
                     * Bug Fixes for recently added features
1.5.6     2018-07-30 * Fix, usage of integers as pillar keys
                     * Refactoring python codebase by @a-ovchinkonv
                     * New feature, "compose node name" from node subdirectory structure (by @gburiola)
1.5.5     2018-07    * Add immutable (constant) parameters
                     * Fixes
1.5.4     2018-05    * Add support for salt 2018.3
                     * Add support for python 2.7/3.x
                     * Extend tests coverage
1.5.3     2018       * Add new features + fixes
                       - last 'known' full compatible release with original reclass
                       - release shipped as well as .deb package at mirror.mirantis.com
1.5.x     2017       * Project forked under salt-formulas/reclass
                       - based on @andrewpickford fork and community fixes
                       - features against original are in README-extensions.rst
1.4.1     2014-10-28 * Revert debug logging, which wasn't fault-free and so
                       it needs more time to mature.
1.4       2014-10-25 * Add rudimentary debug logging
                     * Prevent interpolate() from overwriting merged values
                     * Look for "init" instead of "index" when being fed
                       a directory.
                     * Fix error reporting on node name collision across
                       subdirectories.
1.3       2014-03-01 * Salt: pillar data from previous pillars are now
                       available to reclass parameter interpolation
                     * yaml_fs: classes may be defined in subdirectories
                       (closes: #12, #19, #20)
                     * Migrate Salt adapter to new core API (closes: #18)
                     * Fix --nodeinfo invocation in docs (closes: #21)
1.2.2     2013-12-27 * Recurse classes obtained from class mappings
                       (closes: #16)
                     * Fix class mapping regexp rendering in docs
                       (closes: #15)
1.2.1     2013-12-26 * Fix Salt adapter wrt. class mappings
                       (closes: #14)
1.2       2013-12-10 * Introduce class mappings (see :doc:`operations`)
                       (closes: #5)
                     * Fix parameter interpolation across merged lists
                       (closes: #13).
                     * Caching of classes for performance reasons, especially
                       during the inventory runs
                     * yaml_fs: nodes may be defined in subdirectories
                       (closes: #10).
                     * Classes and nodes URI must not overlap anymore
                     * Class names must not contain spaces
1.1       2013-08-28 Salt adapter: fix interface to include minion_id, filter
                     output accordingly; fixes master_tops
1.0.2     2013-08-27 Fix incorrect versioning in setuptools
1.0.1     2013-08-27 Documentation updates, new homepage
1.0       2013-08-26 Initial release
========= ========== ========================================================
