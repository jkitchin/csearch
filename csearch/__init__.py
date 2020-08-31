# -*- coding: utf-8 -*-

import argparse
import glob
from google.colab import drive
from IPython.display import HTML
from IPython.core.magic import (register_line_magic, register_cell_magic,
                                register_line_cell_magic)
import nbformat
import numpy as np
import os
import re
import shlex
from subprocess import getoutput, run


print('initializing csearch')

import shutil

if not shutil.which('xattr'):
    print('Installing xattr.')
    run(['apt-get', 'install', 'xattr'])

MOUNT = '/content/gdrive/'

if not os.path.isdir(MOUNT):
    print('Mounting your GDrive. You will need to click on the link to get an authentication token.')
    drive.mount(MOUNT)


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
def todo(line, cell=None):
    '''A todo line/cell magic. It should have [optional duedate] description.
    This is a line/cell magic.
    %todo [optional duedate] title

    %%todo [optional duedate] title
    description

    Note there is not state to indicate if it is done.
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
        self.fid = getoutput(f"xattr -p 'user.drive.id' '{self.nbfile}' ")

    def get_url(self, target=None, tooltip=None):
        '''Return an HTML URL to this file with an optional target.'''
        url = f'https://colab.research.google.com/drive/{self.fid}'
        if target:
            url += f'#scrollTo={target}'

        if tooltip:
            title = f'title="{tooltip}"'
        else:
            title = ''
        return f"<a href=\"{url}\" {title} target=_blank>{self.nbfile}</a>"

    def _repr_html_(self):
        '''Returns an HTML link to open this colab.'''
        return self.get_url()

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
                id = cell['metadata'].get('id', None)
                if re.search(pattern, src):
                    return self.get_url(id, tooltip=f'Markdown matched {pattern}')

    def search_tags(self, pattern):
        '''Search tags for pattern.
        if pattern starts with ! it means does not contain.'''
        tags = self.get_tags()

        if pattern.startswith('!'):
            if pattern[1:] not in tags:
                return self.get_url(tooltip=f'Did not match tag: {pattern[1:]}')
        else:
            if pattern in tags:
                return self.get_url(tooltip=f'Matched tag: {pattern}')

    def search_headings(self, pattern):
        '''Search headings for pattern. Returns true if a match is found.
        PATTERN is a string that is used as a regexp for matching.'''
        for cell in self.nb['cells']:
            if cell['cell_type'] == 'markdown':
                src = cell['source']
                id = cell['metadata'].get('id', None)
                lines = src.split('\n')
                for line in lines:
                    if line.startswith('#'):
                        if re.search(pattern, line):
                            return self.get_url(id, tooltip=line)

    def search_code(self, pattern):
        '''Search code cells for pattern. Returns true if a match is found.
        PATTERN is a string that is used as a regexp for matching.'''
        for cell in self.nb['cells']:
            if cell['cell_type'] == 'code':
                src = cell['source']
                id = cell['metadata'].get('id', None)
                if re.search(pattern, src):
                    return self.get_url(id, tooltip=f'Code matched {pattern}')

    def search_todo(self, pattern='.'):
        '''Search cells for todo lines that match pattern.
        This is not very sophisticated, you cannot do a date range for example.
        This function displays the line and link to the file.
        '''
        for cell in self.nb['cells']:
            src = cell['source']
            id = cell['metadata'].get('id', None)
            lines = src.split('\n')
            for line in lines:
                #         %todo this is not flexible with spaces ...
                if re.search('\s*%\s*todo', line):
                    if re.search(pattern, line):
                        return self.get_url(id, tooltip=line)

    def search_properties(self, key, pattern):
        '''Search properties for key matches the pattern.'''
        props = self.get_properties()
        if re.search(pattern, props.get(key, '')):
            return self.get_url(tooltip=f'Matched property {key} = {pattern}')


def find_ipynb(root='', recursive=True):
    '''Find ipynb files in root.
    If you want to search in your Drive, start the root with My Drive.
    '''
    if not root.startswith('/'):
        root = MOUNT + root

    found = glob.glob(root + '/**/*.ipynb',
                      recursive=recursive)

    return found


parser = argparse.ArgumentParser(description='Search Jupyter Notebooks')

# %todo I do not know how to get the current directory of this colab. That
# %should be the default.
parser.add_argument('root', nargs='?', default='',
                    help='Root directory to search in.')

parser.add_argument('-l', '--list', action='store_true',
                    help='list all notebooks')
parser.add_argument('-t', '--tags', nargs='+',
                    help='Search for tags')

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
    nb = [NB(f) for f in find_ipynb(args.root)]

    if args.list:
        for f in nb:
            display(f)
        return

    # The strategy here is to accumulate a list of lists for each criteria
    # Each p function will return a url or None
    P = []

    if args.tags is not None:
        for tag in args.tags:
            P += [[f.search_tags(tag) for f in nb]]

    if args.markdown is not None:
        for pattern in args.markdown:
            P += [[f.search_markdown(pattern) for f in nb]]

    if args.code is not None:
        for pattern in args.code:
            P += [[f.search_code(pattern) for f in nb]]

    if args.heading is not None:
        for pattern in args.heading:
            P += [[f.search_headings(pattern) for f in nb]]

    if args.todo is not None:
        for pattern in args.todo:
            P += [[f.search_todo(pattern) for f in nb]]

    if args.property is not None:
        for pattern in args.property:
            key, pattern = pattern.split('=')
            P += [[f.search_properties(key.strip(), pattern.strip())
                   for f in nb]]

    # Now, P is a list of arrays of None or urls. One problem now is how to
    # decide what to show. I can convert to a boolean array, and see

    bP = np.array(P, dtype=bool)

    # Any element of inds that is True means we have a file that matches.
    inds = np.all(np.array(bP), axis=0)

    # This will display all the matches.
    for i, match in enumerate(inds):
        if match:
            for row in P:
                if row[i]:
                    display(HTML(row[i]))


def csearchf(root, *funcs):
    '''Search root using predicate funcs.
    Each func takes one argument, an NB instance, and returns True for a match.
    '''
    nb = [NB(f) for f in find_ipynb(root)]
    P = []

    for func in funcs:
        P += [[func(x) for x in nb]]

    bP = np.array(P, dtype=bool)

    # Any element of inds that is True means we have a file that matches.
    inds = np.all(np.array(bP), axis=0)

    # This will display all the matches.
    for i, match in enumerate(inds):
        if match:
            for row in P:
                if row[i]:
                    display(HTML(row[i]))

print('Done loading csearch')
