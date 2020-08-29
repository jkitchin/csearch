# -*- coding: utf-8 -*-

import argparse
import glob
from google.colab import drive
from IPython.core.magic import (register_line_magic, register_cell_magic,
                                register_line_cell_magic)
import nbformat
import numpy as np
import re
import shlex
from subprocess import getoutput, run


print('initializing csearch')
run(['apt-get', 'install', 'xattr'])
drive.mount('/content/gdrive')


@register_line_magic
def tag(line):
    "A tag line magic. It should have space separated tags"
    return line.split()


@register_cell_magic
def properties(line, cell):
    '''A cell magic for properties.
    properties look like this:
    key: value

    returns a dictionary of {key: value} for the cell.
    value is always a string.
    '''
    lines = cell.split('\n')
    props = {}
    for line in lines:
        key, val = line.split(':')
        props[key.strip()] = val.strip()
    return props


@register_line_cell_magic
def todo(line, cell):
    '''A todo line/cell magic. It should have [optional duedate] description.

    '''
    # %todo use datetime to get an actual date object you can use
    duedate, title, description = None, line, cell

    items = line.split()
    if items[0].startswith('['):
        duedate = items[0]
        title = ' '.join(items[1:])

    return duedate, title, description


class NB:
    '''A class to represent a colab notebook.'''
    def __init__(self, nbfile):
        '''nbfile is a GDrive path to a notebook.'''
        self.nbfile = nbfile
        self.nb = nbformat.read(nbfile, as_version=4)

    def _repr_html_(self):
        '''returns an HTML link to open this colab.'''
        fid = getoutput(f"xattr -p 'user.drive.id' '{self.nbfile}' ")
        return (f"<a href=https://colab.research.google.com/drive/{fid} "
                f"target=_blank>{self.nbfile}</a>")

    def get_tags(self):
        '''Get a list of unique tags in the notebook.'''
        tags = []
        for cell in self.nb['cells']:
            if cell['cell_type'] == 'code':
                src = cell['source']
                lines = src.split('\n')
                for line in lines:
                    if line.startswith('%tag'):
                        tags += tag(line.replace('%tag', ''))
        return set(tags)

    def get_properties(self):
        '''Get a dictionary of properties in a notebook.'''
        for cell in self.nb['cells']:
            if cell['cell_type'] == 'code':
                src = cell['source']
                if src.startswith('%%properties'):
                    return properties(None, '\n'.join(src.split('\n')[1:]))
        return {}

    def search_markdown(self, pattern):
        '''Search markdown cells for pattern. Returns true if a match is found.
        PATTERN is a string that is used as a regexp for matching.'''
        for cell in self.nb['cells']:
            if cell['cell_type'] == 'markdown':
                src = cell['source']
                if re.search(pattern, src):
                    return True
        return False

    def search_tags(self, pattern):
        '''Search tags for pattern.
        if pattern starts with ! it means does not contain.'''
        tags = self.get_tags()

        if pattern.startswith('!'):
            return pattern[1:] not in tags
        else:
            return pattern in tags

    def search_headings(self, pattern):
        '''Search headings for pattern. Returns true if a match is found.
        PATTERN is a string that is used as a regexp for matching.'''
        for cell in self.nb['cells']:
            if cell['cell_type'] == 'markdown':
                src = cell['source']
                lines = src.split('\n')
                for line in lines:
                    if line.startswith('#'):
                        if re.search(pattern, line):
                            return True
        return False

    def search_code(self, pattern):
        '''Search code cells for pattern. Returns true if a match is found.
        PATTERN is a string that is used as a regexp for matching.'''
        for cell in self.nb['cells']:
            if cell['cell_type'] == 'code':
                src = cell['source']
                if re.search(pattern, src):
                    return True

        return False

    def search_todo(self, pattern='.'):
        '''Search cells for todo lines that match pattern.
        This is not very sophisticated, you cannot do a date range for example.
        This function displays the line and link to the file.
        '''
        for cell in self.nb['cells']:
            src = cell['source']
            lines = src.split('\n')
            for line in lines:
                #         %todo this is not flexible with spaces ...
                if re.search('\s*%\s*todo', line):
                    if re.search(pattern, line):
                        print(line)
                        display(self)

    def search_properties(self, key, pattern):
        '''Search properties for key matches the pattern.'''
        props = self.get_properties()
        if re.search(pattern, props.get(key, '')):
            return True
        else:
            return False


# TODO: make sure this finds what I really mean. should we use a pattern here? I
# am also unsure if I am doing paths right here.
def find_ipynb(root='', recursive=True):
    '''Find ipynb files in root.'''
    return glob.glob('/content/gdrive/' + root + '/**/*.ipynb',
                     recursive=recursive)


parser = argparse.ArgumentParser(description='Search Jupyter Notebooks')

# %todo I do not know how to get the current directory of this colab. That
# %should be the default.
parser.add_argument('root', nargs='?', default='',
                    help='Root directory to search in.')
parser.add_argument('pattern', nargs='?', default=None,
                    help='Pattern to search for.')
parser.add_argument('-l', '--list', action='store_true',
                    help='list all notebooks')
parser.add_argument('-r', '--recursive', action='store_true',
                    help='search recursively')
parser.add_argument('-t', '--tags', nargs='+',
                    help='Search for tags')
parser.add_argument('-f', '--function', nargs='+',
                    help='Search using a predicate function')
parser.add_argument('-m', '--markdown', nargs='+',
                    help='Search markdown cells')
parser.add_argument('-c', '--code', nargs='+',
                    help='Search code cells')

parser.add_argument('-p', '--property', nargs='+',
                    help='Search properties with key=pattern')
parser.add_argument('-d', '--todo', nargs='+',
                    help='Search todo with patterns')
parser.add_argument('-H', '--heading', nargs='+',
                    help='Search headings for patterns')


@register_line_magic
def csearch(line):
    '''Line magic for searching colab notebooks.'''
    args = parser.parse_args(shlex.split(line))
    nb = [NB(f) for f in find_ipynb(args.root, args.recursive)]

    P = []

    if args.list:
        for f in nb:
            display(f)
        return

    if args.tags is not None:
        for tag in args.tags:
            P += [[f.search_tags(tag) for f in nb]]

    if args.function is not None:
        pfunctions = [globals()[f] for f in args.function]
        for predicate in pfunctions:
            P += [[predicate(f) for f in nb]]

    if args.markdown is not None:
        for pattern in args.markdown:
            P += [[f.search_markdown(pattern) for f in nb]]

    if args.code is not None:
        for pattern in args.code:
            P += [[f.search_code(pattern) for f in nb]]

    if args.heading is not None:
        # TODO some context here might also be helpful, but for now I use the
        # same pattern as above.
        for pattern in args.heading:
            P += [[f.search_headings(pattern) for f in nb]]

    if args.todo is not None:
        for pattern in args.todo:
            for f in nb:
                # this will print matching patterns. It is a little different
                # than the P pattern above. maybe I will change this, it is just
                # to get some context with the todo line.
                f.search_todo(pattern)

    if args.property is not None:
        for pattern in args.property:
            key, pattern = pattern.split('=')
            P += [[f.search_properties(key.strip(), pattern.strip())
                   for f in nb]]

    # Finally show all files that match all criteria
    inds = np.all(np.array(P), axis=0)
    nb = np.array(nb)
    from collections.abc import Iterable
    if isinstance(inds, Iterable):
        for x in nb[inds]:
            display(x)


print('Done')
