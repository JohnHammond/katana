Documentation
============

Katana's documentation is built with [Sphinx](http://www.sphinx-doc.org/).

We use docstrings so that we can take advantage of the `autodoc` extension. When you build the documentation, you can view it in a web browser with the very pretty [ReadTheDocs](https://readthedocs.org/) theme.

Building Documentation
----------------------

The auto-generated documention pulls can be created with the `Makefile` included in this folder. 
**Inside of your virtual environment and in this /docs directory**, you can run the command:

```
make html
```

When that is finished, you can `firefox build/html/index.html` to view the documentation.

You may or may not need some Sphinx dependencies to run that. Theoretically, everything will be installed when running the script.

**Note:** Not all the units and every piece of code may be documented just yet. Sorry. 