#!/usr/bin/python

from os import environ
from os.path import isfile, isdir
from . utils import err

def _set_symbiotic_environ(tool, env, opts):
    if opts.search_include_paths:
        from . includepaths import IncludePathsSearcher
        additional_include_paths = IncludePathsSearcher().get()
        for p in additional_include_paths:
            env.prepend('C_INCLUDE_DIR', p)

    # check whether we are in distribution directory or in the developement directory
    if isfile('{0}/build.sh'.format(env.symbiotic_dir)):
        opts.devel_mode = True
    else:
        opts.devel_mode = False

    llvm_version = tool.llvm_version()
    llvm_prefix = '{0}/llvm-{1}'.format(env.symbiotic_dir, llvm_version)

    if not isdir(llvm_prefix):
        err("Directory with LLVM binaries does not exist: '{0}'".format(llvm_prefix))

    env.prepend('C_INCLUDE_DIR', '{0}/include'.format(env.symbiotic_dir))

    if opts.devel_mode:
        env.prepend('PATH', '{0}/scripts'.format(env.symbiotic_dir))
        env.prepend('PATH', '{0}/llvm-{1}/build/bin'.format(env.symbiotic_dir, llvm_version))
        env.prepend('PATH', '{0}/dg/build-{1}/tools'.format(env.symbiotic_dir, llvm_version))
        env.prepend('PATH', '{0}/sbt-slicer/build-{1}/src'.format(env.symbiotic_dir, llvm_version))
        env.prepend('PATH', '{0}/sbt-instrumentation/build-{1}/src'.format(env.symbiotic_dir, llvm_version))

        env.prepend('LD_LIBRARY_PATH', '{0}/build/lib'.format(llvm_prefix))
        env.prepend('LD_LIBRARY_PATH', '{0}/transforms/build-{1}/'.format(env.symbiotic_dir,llvm_version))
        env.prepend('LD_LIBRARY_PATH', '{0}/dg/build-{1}/lib'.format(env.symbiotic_dir, llvm_version))
        env.prepend('LD_LIBRARY_PATH', '{0}/sbt-instrumentation/build-{1}/analyses'.format(env.symbiotic_dir, llvm_version))
        env.prepend('LD_LIBRARY_PATH', '{0}/sbt-instrumentation/ra/build-{1}/'.format(env.symbiotic_dir, llvm_version))
        opts.instrumentation_files_path = '{0}/sbt-instrumentation/instrumentations/'.format(env.symbiotic_dir)
    else:
        env.prepend('PATH', '{0}/bin'.format(env.symbiotic_dir))
        env.prepend('PATH', '{0}/llvm-{1}/bin'.format(env.symbiotic_dir, llvm_version))
        env.prepend('LD_LIBRARY_PATH', '{0}/lib'.format(env.symbiotic_dir))
        env.prepend('LD_LIBRARY_PATH', '{0}/lib'.format(llvm_prefix))
        opts.instrumentation_files_path = '{0}/share/sbt-instrumentation/'.format(llvm_prefix)

    # Get include paths again now when we have our clang in the path,
    # so that we have at least includes from our clang's instalation
    # (these has the lowest prefs., so just append them
    if opts.search_include_paths:
        additional_include_paths = IncludePathsSearcher().get()
        for p in additional_include_paths:
            env.append('C_INCLUDE_DIR', p)

    # let the tool set its specific environment
    if hasattr(tool, 'set_environment'):
        tool.set_environment(env, opts)

def _parse_environ_vars(opts):
    """
    Parse environment variables of interest and
    change running options accordingly
    """
    # FIXME: do not store these flags into opts but into environ
    if 'C_INCLUDE_DIR' in environ:
        for p in environ['C_INCLUDE_DIR'].split(':'):
            if p != '':
                opts.CPPFLAGS.append('-I{0}'.format(p))
    if 'CFLAGS' in environ:
        opts.CFLAGS += environ['CFLAGS'].split(' ')
    if 'CPPFLAGS' in environ:
        opts.CPPFLAGS += environ['CPPFLAGS'].split(' ')

class Environment:
    """
    Helper class for setting and maintaining
    evnironment for tools
    """
    def __init__(self, symb_dir):
        self.symbiotic_dir = symb_dir
        self.working_dir = None

    def prepend(self, env, what):
        """ Prepend 'what' to environment variable 'env'"""
        if env in environ:
            newenv = '{0}:{1}'.format(what, environ[env])
        else:
            newenv = what

        environ[env] = newenv

    def append(self, env, what):
        """ Append 'what' to environment variable 'env'"""
        if env in environ:
            newenv = '{0}:{1}'.format(environ[env], what)
        else:
            newenv = what

        environ[env] = newenv

    def set(self, tool, opts):
        _set_symbiotic_environ(tool, self, opts)
        _parse_environ_vars(opts)

