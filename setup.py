from setuptools import setup



def _get_version():
    with open('VERSION') as fd:
        return fd.read().strip()


setup(
    name='planets',
    version=_get_version(),
    packages=['planets'],
    package_dir={'': './'},
    py_modules=['planets.app'],
    entry_points={
        'console_scripts': [
            'planets-serve=planets.app:main',
        ]
    }
)