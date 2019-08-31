Documentation
============

Katana's documentation is built with [Sphinx](http://www.sphinx-doc.org/).

We use docstrings so that we can take advantage of the `autodoc` extension. When you build the documentation, you can view it in a web browser with the very pretty [ReadTheDocs](https://readthedocs.org/) theme.

Building Documentation
----------------------

The auto-generated documention pulls from Katana _as a module_... not the flat `.py` file. This means that if you want the absolute latest documentation (even when you are adding new code and your own documentation), you need to "re-install" Katana each time.

We streamline this with the bash script included here. **Ensure you run this while inside of your virtual environment.**

```
./regenerate_docs.sh
```

When that is finished, you can `firefox build/html/index.html` to view the documentation.

You may or may not need some Sphinx dependencies to run that. Theoretically, everything will be installed when running the script.

**Note:** Not all the units and every piece of code may be documented just yet. Sorry. 