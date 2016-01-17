#!/usr/bin/python3
"""Setup
"""
from setuptools import find_packages
from distutils.core import setup

version = "0.0.1"

with open('README.rst') as f:
    long_description = f.read()

setup(name='ofxstatement-latvian',
      version=version,
      author="Gints Murans",
      author_email="gm@gm.lv",
      url="https://github.com/gintsmurans/ofxstatement-latvian",
      description=("Statement parsers for banks operating in Latvia"),
      long_description=long_description,
      license="GPLv3",
      keywords=["ofx", "ofxstatement", "banking", "statement", "latvia"],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3',
          'Natural Language :: English',
          'Topic :: Office/Business :: Financial :: Accounting',
          'Topic :: Utilities',
          'Environment :: Console',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU Affero General Public License v3'],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=["ofxstatement", "ofxstatement.plugins"],
      entry_points={
          'ofxstatement':
          ['swedbankLV = ofxstatement.plugins.swedbankLV:SwedbankLVPlugin',
           'dnbLV = ofxstatement.plugins.dnbLV:dnbLVPlugin']
          },
      install_requires=['ofxstatement'],
      include_package_data=True,
      zip_safe=True
      )
