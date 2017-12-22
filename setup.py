
from setuptools import setup

setup(
    name='project_explorer',
    version='0.0.0a6',
    description='A simple file browser that uses project based concepts.',
    url='https://github.com/mfish38/project_explorer',
    author='Mark Fisher',
    license='MIT',
    packages=['project_explorer'],
    install_requires=[
        'qtpy',
        'ntfsutils'
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Desktop Environment :: File Managers',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ],
    test_suite='nose.collector',
    tests_require=['nose']
)
