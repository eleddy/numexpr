#!/usr/bin/env python
###################################################################
#  Numexpr - Fast numerical array expression evaluator for NumPy.
#
#      License: MIT
#      Author:  See AUTHORS.txt
#
#  See LICENSE.txt and LICENSES/*.txt for details about copyright and
#  rights to use.
####################################################################

import shutil
import os, sys
import os.path as op
from distutils.command.clean import clean
from distutils.core import setup as dsetup
from setuptools import find_packages
import distutils.command.install


class numexpr_install(distutils.command.install):
    def run(self):
        distutils.command.install.run(self)
        setup_package()
        # Custom stuff here
        # distutils.command.install actually has some nice helper methods
        # and interfaces. I strongly suggest reading the docstrings.

setup(
    name='numexpr',
    version='',
    author='',
    author_email='',
    packages=find_packages(),
    cmdclass=dict(install=numexpr_install),
    url='',
    license='',
    description='',
    install_requires=[
        'setuptools'
        'numpy'
    ],
    zip_safe=False,
    setup_requires=[ 'setuptools'
        'numpy'],
)


DEBUG = False

def localpath(*args):
    return op.abspath(reduce(op.join, (op.dirname(__file__),)+args))

def debug(instring):
    if DEBUG:
        print " DEBUG: "+instring


def configuration():
    config = Configuration('numexpr')

    #try to find configuration for MKL, either from environment or site.cfg
    if op.exists('site.cfg'):
        mkl_config_data = config.get_info('mkl')
        # some version of MKL need to be linked with libgfortran, for this, use
        # entries of DEFAULT section in site.cfg
        default_config = system_info()
        dict_append(mkl_config_data,
                    libraries = default_config.get_libraries(),
                    library_dirs = default_config.get_lib_dirs() )
    else:
        mkl_config_data = {}

    #setup information for C extension
    if os.name == 'nt':
        pthread_win = ['numexpr/win32/pthread.c']
    else:
        pthread_win = []
    extension_config_data = {
        'sources': ['numexpr/interpreter.cpp',
                    'numexpr/module.cpp',
                    'numexpr/numexpr_object.cpp'] + pthread_win,
        'depends': ['numexpr/interp_body.cpp',
                    'numexpr/complex_functions.hpp',
                    'numexpr/interpreter.hpp',
                    'numexpr/module.hpp',
                    'numexpr/msvc_function_stubs.hpp',
                    'numexpr/numexpr_config.hpp',
                    'numexpr/numexpr_object.hpp'],
        'libraries': ['m'],
        'extra_compile_args': ['-funroll-all-loops',],
        }
    dict_append(extension_config_data, **mkl_config_data)
    if 'library_dirs' in mkl_config_data:
        library_dirs = ':'.join(mkl_config_data['library_dirs'])
        rpath_link = '-Xlinker --rpath -Xlinker %s' % library_dirs
        extension_config_data['extra_link_args'] = [rpath_link]
    config.add_extension('interpreter', **extension_config_data)

    config.make_config_py()
    config.add_subpackage('tests', 'numexpr/tests')

    #version handling
    config.make_svn_version_py()
    config.get_version('numexpr/version.py')
    return config


class cleaner(clean):

    def run(self):
        # Recursive deletion of build/ directory
        path = localpath("build")
        try:
            shutil.rmtree(path)
        except Exception:
            debug("Failed to remove directory %s" % path)
        else:
            debug("Cleaned up %s" % path)

        # Now, the extension and other files
        if os.name == 'posix':
            paths = [localpath("numexpr/interpreter.so")]
        else:
            paths = [localpath("numexpr/interpreter.pyd")]
        paths.append(localpath("numexpr/__config__.py"))
        paths.append(localpath("numexpr/__config__.pyc"))
        for path in paths:
            try:
                os.remove(path)
            except Exception:
                debug("Failed to clean up file %s" % path)
            else:
                debug("Cleaning up %s" % path)

        clean.run(self)


def setup_package():
    import os
    from numpy.distutils.core import setup

    extra_setup_opts['cmdclass'] = {'build_ext': build_ext,
                                    'clean': cleaner,
                                    }
    
    extra_setup_opts['zip_safe'] = False

    setup(#name='numexpr',  # name already set in numpy.distutils
          description='Fast numerical expression evaluator for NumPy',
          author='David M. Cooke, Francesc Alted and others',
          author_email='david.m.cooke@gmail.com, faltet@pytables.org',
          url='http://code.google.com/p/numexpr/',
          license = 'MIT',
          packages = ['numexpr'],
          configuration = configuration,
          **extra_setup_opts
          )

class build_ext():
    def build_extension(self, ext):
        from numpy.distutils.command.build_ext import build_ext as numpy_build_ext

        # at this point we know what the C compiler is.
        if self.compiler.compiler_type == 'msvc':
            ext.extra_compile_args = []
            # also remove extra linker arguments msvc doesn't understand
            ext.extra_link_args = []
            # also remove gcc math library
            ext.libraries.remove('m')
        numpy_build_ext.build_extension(self, ext)


