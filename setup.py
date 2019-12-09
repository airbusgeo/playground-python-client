import io
import re
from setuptools import setup, find_packages

# Only packages the trainer and detection packages
REQUIRED_PACKAGES = [
    #'click',
    'requests',
    'numpy',
    'mercantile'
]

with io.open('playgroundclient/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(
        r'__version__ = \'(.*?)\'', f.read(), re.M).group(1)

setup(
    name='playgroundclient',
    version=version,
    packages=find_packages(),
    #entry_points='''
    #    [console_scripts]
    #    up42=up42.cli:up42
    #''',
    description='Intelligence Playground API Python Client',
    long_description='A Python client and CLI to interact with the Airbus Intelligence Playground API.',
    include_package_data=True,
    author='Jeff Faudi',
    author_email='jean-francois.faudi@airbus.com',
    license='LICENSE',
    install_requires=REQUIRED_PACKAGES,
    python_requires='>=3.6',
    zip_safe=False)

