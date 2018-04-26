from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
	name='simplegitbyBieganski',
	version='1.14',
	description='A simple git-like version control',
	long_description=long_description,
	author='Mateusz Biegański',
	author_email='bieganski.m@wp.pl',
	packages=['simplegit'],
	install_requires=[],
	url='https://www.github.com/bieganski',
	entry_points = {
        "console_scripts": ['simplegit = simplegit.simplegit:main']
        },
)
