import os
import re
import sys
import platform
import subprocess

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion


with open('README.rst') as f:
    readme = f.read()


class CMakeExtension(Extension):
    def __init__(self, name, modName, sourcedir=''):

        Extension.__init__(self, name, sources=[], language='c++')

        self.modName = modName
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
            if cmake_version < '3.12.0':
                raise RuntimeError("CMake >= 3.12.0 is required on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        print('ext_full_path', self.get_ext_fullpath(ext.name))
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        # required for auto-detection of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable,
                      '-DBUILD_PYTHON=ON']

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        elif platform.system() == "Darwin":
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            cmake_args += ['-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64;arm64e']
            build_args += ['--', '-j4']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j4']

        cmake_args += ['-DCMAKE_INSTALL_PREFIX=' + '.']

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.', '--target', ext.modName] + build_args, cwd=self.build_temp)

       # subprocess.check_call(['cmake', '--build', '.', '--target', 'install'], cwd=self.build_temp)


setup(
    name='pycork',
    version='0.1.3',
    author='Luke Parry',
    author_email='dev@lukeparry.uk',
    url='https://github.com/drlukeparry/pycork',
    long_description=readme,
    long_description_content_type = 'text/x-rst',
    description='pycork provides a fully compiled interface to the cork boolean library ',
    ext_modules=[CMakeExtension('pycork.pycork', 'pycork')],
    cmdclass=dict(build_ext=CMakeBuild),
    packages = ['pycork'],
    package_dir={'': 'python'},
    keywords=['Boolean CSG', 'Cork'],
    # tell setuptools that all packages will be under the 'src' directory
    # and nowhere else
    zip_safe=False,
        classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering'],
    license="",
    project_urls = {
    'Documentation': 'https://github.com/drylukeparry/pycork',
    'Source': 'https://github.com/drylukeparry/pycork',
    'Tracker': 'https://github.com/drlukeparry/pycork/issues'
    }
)

