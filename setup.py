from distutils.core import setup
import py2exe, sys, os

sys.argv.append('py2exe')

py2exe_options = dict(
    bundle_files=2,
    compressed=True,
    includes=['pygubu.builder.tkstdwidgets',
              'pygubu.builder.ttkstdwidgets',
              'pygubu.builder.widgets', ]
)

data_files = [
    ('data', ['data/application.ui',
              'data/flightdb.sqlite'])
]

setup(
    name='FlightFinder',
    windows=[{'script': 'main.py'}],
    options={'py2exe': py2exe_options},
    zipfile=None,
    data_files=data_files,
)
