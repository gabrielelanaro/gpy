#!/usr/bin/env pythona

from setuptools import setup, find_packages

setup(name='gpy',
      version='1.0',
      description='Gromacs Project Management',
      author='Gabriele Lanaro',
      author_email='gabriele.lanaro@gmail.com',
      url='',
      packages=find_packages(),
      entry_points = {
        'console_scripts' : ['gpy=gpy.main:cli']
      }
)
