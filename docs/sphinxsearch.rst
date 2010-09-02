Sphinx Search Engine
====================

Firefox Input uses Sphinx Search 0.9.9 to power search.

For developers
--------------

If you are working on a component of Firefox Input that requires search,
you'll need to be able to:

1. Install Sphinx Search
2. Index opinions.
3. Run the search daemon.

To install sphinx on OS X using ``homebrew`` run the following command: ::

    brew install sphinx

This gives you ``indexer`` and ``searchd``.

Run this command to index and run the search daemon (from the project root): ::

    indexer -c **/sphinx.conf --all && searchd -c **/sphinx.conf --console

You may want to put this in an alias.  This command will show the searches as
they hit the search engine, and allow you to shut down the daemon using
``^C``.
