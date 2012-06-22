from setuptools import setup, find_packages
import os

version = '1.1a1'

setup(name='seantis.dir.base',
      version=version,
      description="Directory module for Plone using Dexterity",
      long_description=open("README.md").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='directory plone dexterity',
      author='Seantis GmbH',
      author_email='info@seantis.ch',
      url='https://github.com/seantis/seantis.dir.base',
      license='GPL v2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['seantis', 'seantis.dir'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Plone',
          'plone.app.dexterity',
          'collective.autopermission',
          'collective.testcaselayer',
          'plone.behavior',
          'plone.directives.form',
          'collective.dexteritytextindexer',
          'xlrd',
          'xlwt',
          'collective.geo.geographer',
          'collective.geo.contentlocations',
          'collective.geo.settings',
          'collective.geo.mapwidget',
          'collective.geo.openlayers',
          'collective.geo.settings',
          'collective.geo.kml',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
