# Copyright 2015-2019 John Kitchin
# (see accompanying license files for details).
from setuptools import setup
from glob import glob

setup(name='csearch',
      version='0.0.8',
      description='colab utilities for searching notebooks in gdrive',
      url='',
      maintainer='John Kitchin',
      maintainer_email='jkitchin@andrew.cmu.edu',
      license='GPL',
      packages=['csearch'],
      package_dir={'csearch': 'csearch'},
      package_data={'csearch': ['examples/*.ipynb']},
      long_description='''\
Search colabs in gdrive with IPython magic.
===========================================

%csearch "some path" -m Search
      ''')

# [2020-08-30 Sun] Leaving this here in case I decide to register this.
# For now this will be installed from github.
# (shell-command "python setup.py register") to setup user
# to push to pypi - (shell-command "python setup.py sdist upload")


# Set TWINE_USERNAME and TWINE_PASSWORD in .bashrc
# python setup.py sdist bdist_wheel
# twine upload dist/*
