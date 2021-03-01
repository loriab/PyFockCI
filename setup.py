from distutils.core import setup
import setuptools

setup(
    name='sf_ip_ea',
    version='0.1.0',
    author='Shannon E. Houck',
    author_email='shouck@vt.edu',
    #packages=['sf_ip_ea', 'sf_ip_ea.test'],
    packages=setuptools.find_packages(),
    include_package_data=True,
    scripts=[],
    url='',
    license='LICENSE.txt',
    install_requires=[
        "numpy>=1.7",
        "scipy",
    ],
    extras_require={
        "tests": ["pytest",],
    },
    tests_require=["pytest",],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
    ],
    zip_safe=False,
    description='Stand-alone RAS-SF-IP/EA code.',
    long_description=open('README.md').read(),
)
