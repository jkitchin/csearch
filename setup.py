# Copyright 2015-2019 John Kitchin
# (see accompanying license files for details).
from setuptools import setup

setup(name='csearch',
      version='0.0.1',
      description='colab utilities for searching notebooks in gdrive',
      url='',
      maintainer='John Kitchin',
      maintainer_email='jkitchin@andrew.cmu.edu',
      license='GPL',
      packages=['csearch'],
      long_description='''\
Search colabs in gdrive with Ipython magic.
===========================================

%csearch "some path" -m Search
      ''')

# (shell-command "python setup.py register") to setup user
# to push to pypi - (shell-command "python setup.py sdist upload")


# Set TWINE_USERNAME and TWINE_PASSWORD in .bashrc
# python setup.py sdist bdist_wheel
# twine upload dist/*
