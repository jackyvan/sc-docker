"""
Starcraft BW docker launcher.
"""

# To use a consistent encoding
from codecs import open
from os import path

# Always prefer setuptools over distutils
from setuptools import setup

from scbw import VERSION

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='scbw',
    version=VERSION,
    description='Multi-platform Version of StarCraft: Brood War in a Docker Container',
    long_description=long_description,
    url='https://github.com/Games-and-Simulations/sc-docker',
    author='Michal Sustr',
    author_email='michal.sustr@aic.fel.cvut.cz',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.4',
    ],
    keywords='starcraft docker broodwar ai bot',
    install_requires=['requests',
                      'coloredlogs',
                      'numpy',
                      'tqdm',
                      'requests',
                      'python-dateutil'],
    extras_require={
    },
    packages=['scbw'],
    entry_points={  # Optional
        'console_scripts': [
            'scbw=scbw:main',
        ],
    },
    python_requires='>=3.4',

    data_files=[('scbw_local_docker', ['scbw/local_docker/game.dockerfile',
                                       'scbw/local_docker/default.mpc',
                                       'scbw/local_docker/default.spc',
                                       ])
                ]
)
