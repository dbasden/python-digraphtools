from distutils.core import setup

setup(
	name='digraphtools',
	version='0.1.0',
	author='David Basden',
	author_email='davidb-python@rcpt.to',
	packages=['digraphtools','digraphtools.test'],
	url='http://pypi.python.org/pypi/digraphtools/',
	license='LICENSE.txt',
	description='Some tools for working with digraphs, partial orders and topological sorting with Python',
	long_description=open('README.txt').read(),
	classifiers = [
		'Intended Audience :: Developers',
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: BSD License',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
	],
)
