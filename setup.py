import yaml

from setuptools import setup, find_packages
from os import path

# read the contents of README file
this_dir = path.abspath(path.dirname(__file__))

with open(path.join(this_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="Polydung",
    version=yaml.load(open("changelog.yml"))['versions'][-1]['name'],
    packages=find_packages(),
    
    # metadata to display on PyPI
    author="Gustavo6046",
    author_email="gugurehermann@gmail.com",
    description="A 2D oldschool multiplayer realtime topdown roguelite project.",
    license="MIT",
    keywords="2d oldschool multiplayer realtime topdown roguelite game",
    url="https://github.com/Gustavo6046/Polydung",
    package_data={
        '': ['*.nbc', '*.nbe', ''],
    },
    
    long_description=long_description,
    long_description_content_type='text/markdown'
)