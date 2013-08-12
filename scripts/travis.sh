#! /bin/bash

# Run the unit tests (use phantomjs for javascript unit tests)
rake test

# Generate pylint and pep8 reports
rake pep8
rake pylint

# Generate coverage reports
rake coverage

# Generate quality reports
rake quality
