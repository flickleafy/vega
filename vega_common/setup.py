"""
Setup configuration for vega_common package.
"""
from setuptools import setup, find_packages

setup(
    name="vega_common",
    version="0.1.0",
    packages=find_packages(),
    description="Common utilities for Vega project components",
    author="Vega Team",
    python_requires=">=3.6",
    install_requires=[],
)

# setup(
#     name='MyModule',
#     version='0.1',
#     packages=find_packages(),
#     install_requires=[],
#     url='https://github.com/flickleafy/vega',
#     author='flickleafy',
#     author_email='flickleafy'
# )
