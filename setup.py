import os
from distutils.core import setup
from distutils.extension import Extension



setup(
    name='vaultfly',
    version='1.0.11',
    packages=['vaultfly'],
    include_package_data=True,
    url='https://github.com/chris17453/vaultfly/',
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",

    author='Charles Watkins',
    author_email='charles@titandws.com',
    description='Ansible vault automation for ssh connections which may also require a token',
    install_requires=['pyyaml', 'flextable'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
    ],
    entry_points="""
        [console_scripts]
        vaultfly = vaultfly.cli:cli_main
        """,



)
