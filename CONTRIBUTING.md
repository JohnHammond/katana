Contributing
============

If you have not contributed to a project before, don't fret! GitHub has an
[awesome guide](https://guides.github.com/activities/forking/) for helping 
support open-source projects. Basically the steps are:

1. [Fork the repository](https://guides.github.com/activities/forking/#fork)
2. [Clone your fork](https://guides.github.com/activities/forking/#clone)
3. [Make and push your changes](https://guides.github.com/activities/forking/#making-changes)
4. [Make a Pull Request](https://guides.github.com/activities/forking/#making-a-pull-request)
5. [And you're done!](https://guides.github.com/activities/forking/#huzzah)

Tabs vs. Spaces
---------------

PEP8 says spaces, so we are going to comply. Please set your IDE and/or editor
to use spaces vice tab characters.

Documentation
-------------

If you do add code to Katana, __we require documentation.__ We use simple 
[reStructuredText](http://docutils.sourceforge.net/rst.html) to produce some
helpful ReadTheDocs pages. Please use [Google Style Python Docstrings] in your
code, and generally things will look good!

Testing
--------

Unit tests are implemented under the `tests` directory. The unit tests are
organized exactly the same as the builtin units within Katana. There is a 
`KatanaTest` class which inherits from UnitTest within the `tests` directory.
It provides a convenient function called `katana_test` which makes it easy to
setup and run Katana for a unit test. Ideally, create your test data on the 
fly, and don't rely on files on the file system. Where possible, dynamically 
create the test files using Python's `tempfile`. If you must use an external 
file, submit it to one of the maintainers of the repository, and we can add it 
to the Dropbox where we keep test cases.

Thank You!
----------

Lastly, _thank you_. This project has been a labor of love, and too often we 
simply do not have the time to continue to maintain and add to the project. 
We are grateful for everything little thing you do, from correcting our 
accidentals typos to adding new units and functionality.

[Google Style Python Docstrings]: https://sphinxcontrib-napoleon.readthedocs.org/en/latest/example_google.html#example-google