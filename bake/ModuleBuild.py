''' 
 ModuleBuild.py
 
 This file stores the real build implementation for each one of the handled
 tools. It is this class that defines how a build with, for example, make
 will be done and how different is it from the build done with cmake 
''' 

import bake.Utils
import os
import platform
import commands
import re
import sys
from bake.Utils import ModuleAttributeBase
from bake.Exceptions import NotImplemented
from bake.Exceptions import TaskError 

class ModuleBuild(ModuleAttributeBase):
    """ Generic build, to be extended by the specialized classes, 
    one for each handled kind of tool. 
    """

    def __init__(self):
        """ Default values for the generic attributes."""
        
        ModuleAttributeBase.__init__(self)
#        self._libpaths = []
        self.add_attribute('objdir', 'no', 'Module supports objdir != srcdir.', mandatory=False)
        self.add_attribute('patch', '', 'code to patch before build', mandatory=False)
        self.add_attribute('v_PATH', '', 'Directory, or directories separated'
                           ' by a \";\", to append to PATH environment variable', mandatory=False)
        self.add_attribute('v_LD_LIBRARY', '', 'Directory, or directories'
                           ' separated by a \";\", to append LD_LIBRARY'
                           ' environment variable', mandatory=False)
        self.add_attribute('v_PKG_CONFIG', '', 'Directory, or directories'
                           ' separated by a \";\", to append to PKG_CONFIG'
                           ' environment variable', mandatory=False)
        self.add_attribute('post_installation', '', 'UNIX Command to run'
                           ' after the installation', mandatory=False)
        self.add_attribute('pre_installation', '', 'UNIX Command to run'
                           ' before the installation', mandatory=False)
        self.add_attribute('supported_os', '', 'List of supported Operating'
                           ' Systems for the module', mandatory=False)
        self.add_attribute('ignore_predefined_flags', 'False', 'True if the'
                           ' build should ignore the predefined flag settings')
        self.add_attribute('new_variable', '', 'Appends the value to the'
                           ' system variable on the format VARIABLE1=value1'
                           ';VARIABLE2=value2', mandatory=False)
        # self.add_attribute('condition_to_build', '', 'Condition that, if '
        # 'existent, should be true for allowing the instalation')

    @classmethod
    def subclasses(self):
        return ModuleBuild.__subclasses__()

    @classmethod
    def create(cls, name):
        """ Instantiates the Build class."""
        
        for subclass in ModuleBuild.subclasses():
            if subclass.name() == name:
                instance = subclass()
                return instance
        return None

    @property
    def supports_objdir(self):
        return self.attribute('objdir').value == 'yes'
    def build(self, env, jobs):
        raise NotImplemented()
    def clean(self, env):
        raise NotImplemented()
    def check_version(self, env):
        raise NotImplemented()
    
    def check_os(self, supportedOs) :
        """ Verifies the minimum OS requirements."""
        
        osName = platform.system().lower()
        
        if len(supportedOs) is 0 :
            elements = []
        else :
            elements = supportedOs.split(';')
            
        supportedOS = False
        
        for element in elements : 
            if(osName.startswith(element.lower())):
                supportedOS = True
        
        return supportedOS 

    
    def perform_pre_installation(self, env):
        """ Executes a list of Linux commands BEFORE calling the build process."""

        if self.attribute('pre_installation').value != '':
            commandList = env.replace_variables(self.attribute('pre_installation').value).split(' or ')
                        
            for comandToExecute in commandList :
                try:
                    env._logger.commands.write("    > " +env.replace_variables(comandToExecute));
                    resultStatus = commands.getstatusoutput(env.replace_variables(comandToExecute))
                    if(resultStatus[0] == 0) :
                        return True
                except Exception as e:
                    print ("   > Error executing pre installation : " + e )

        return False
    
    def perform_post_installation(self, env):
        """ Executes a list of Linux commands AFTER the build is finished """
        
        if self.attribute('post_installation').value != '':
            try:
                env._logger.commands.write(" > " + env.replace_variables(self.attribute('post_installation').value))
                var = commands.getoutput(env.replace_variables(self.attribute('post_installation').value))
                
                if env.debug:
                    print(var)
            except Exception as e:
                print ("   > Error executing post installation : " + e )

    # applies a patch if available
    def threat_patch(self, env):
        """ Applies a patch, or a series of patches, over the source code.  """
        
        hasPatch = env.check_program('patch')
        if hasPatch == False:
            raise TaskError('Path tool is not present and it is required for'
                            ' applying: %s, in: %s' 
                            % (self.attribute('patch').value, env._module_name))

        vectorPath = env.replace_variables(self.attribute('patch').value).split(';')      
        for item in vectorPath:
      
            if not env.exist_file(item) :
                raise TaskError('Path file is not present! missing file:'
                                ' %s, in: %s' % (item, env._module_name))

            try:
                env._logger.commands.write('cd ' + env.srcdir + '; patch -p1 < ' + item + '\n')
                status = commands.getstatusoutput('cd ' + env.srcdir + '; patch -p1 < ' + item) 
            except:
                raise TaskError('Patch error: %s, in: %s' % (item, env._module_name))
            
            # if there were an error
            if status[0] != 0:
                if status[0] == 256:
                    env._logger.commands.write(' > Patch problem: Ignoring'
                                               ' patch, either the patch file'
                                               ' does not exist or it was '
                                               'already applied!\n')
                else:
                    raise TaskError('Patch error %s: %s, in: %s' % 
                                    (status[0], item, env._module_name))

    # Threats the parameter variables
    def threat_variables(self, env):
        """ Append the defined variables to the internal environment.  """

        elements = []
        if self.attribute('v_PATH').value != '':
            elements = env.replace_variables(self.attribute('v_PATH').value).split(";")
            env.add_libpaths(elements)
            env.add_binpaths(elements)
            
        if self.attribute('v_LD_LIBRARY').value != '':
            elements = env.replace_variables(self.attribute('v_LD_LIBRARY').value).split(";")
            env.add_libpaths(elements)

        if self.attribute('v_PKG_CONFIG').value != '':
            elements = env.replace_variables(self.attribute('v_PKG_CONFIG').value).split(";")
            env.add_pkgpaths(elements)

        if self.attribute('new_variable').value != '':
            elements = env.replace_variables(self.attribute('new_variable').value).split(";")
            env.add_variables(elements)


    def _flags(self):
        """ Adds the defined flags as a default for the build.  """
        
        variables = []
        if self.attribute('ignore_predefined_flags').value == 'True':
            return variables
                           
        if self.attribute('CFLAGS').value != '':
            variables.append('CFLAGS=%s'% (self.attribute('CFLAGS').value))
            
        if self.attribute('CXXFLAGS').value != '':
            variables.append('CXXFLAGS=%s'% (self.attribute('CXXFLAGS').value))
        return variables


class NoneModuleBuild(ModuleBuild):
    """ Class defined for the modules that do not need a build mechanism, 
    e.g system dependencies.
    """
        
    def __init__(self):
        ModuleBuild.__init__(self)
    @classmethod
    def name(cls):
        return 'none'
    def build(self, env, jobs):
        pass
    def clean(self, env):
        pass
    def check_version(self, env):
        return True


class InlineModuleBuild(ModuleBuild):
    """ Class defined for the modules that will use a Python code to be 
    installed. The build may be programmed in Python using all the Bake 
    functionalities.
    """
    
    def __init__(self):
        ModuleBuild.__init__(self)
    @classmethod
    def name(cls):
        return 'inline'
    
    @classmethod
    def className(self, code): 
        if code :
            myre = re.compile(".*class (?P<class_name>[a-zA-Z0-9_-]*)\(.*")
            m = myre.match(code)
            if m :
                return m.groupdict()['class_name']
        
        return self.__class__.__name__

class PythonModuleBuild(ModuleBuild):
    """ Performs the build for python based projects."""
    
    def __init__(self):
        ModuleBuild.__init__(self)
    @classmethod
    def name(cls):
        """ Specific build type identifier."""
        
        return 'python'
    
    def build(self, env, jobs):
        """ Specific build implementation method. Basically call the setup.py 
        program passed as parameter."""
        
        if self.attribute('patch').value != '':
            self.threat_patch(env)
       
        # TODO: Add the options, there is no space for the configure_arguments
        env.run(['python', os.path.join(env.srcdir, 'setup.py'), 'build',
                  '--build-base=' + env.objdir,
                  'install', '--prefix=' + env.installdir],
                 directory=env.srcdir)

    def clean(self, env):
        """ Call the code with the setup.py with the clean option, 
        to remove the older code.
        """
        
        env.run(['python', os.path.join(env.srcdir, 'setup.py'), 'clean',
                 '--build-base=' + env.objdir],
                directory=env.srcdir)
        
    def check_version(self, env):
        """Verifies only if python exists in the machine."""
        
        try: 
            env.run(['python', '--version'])
        except TaskError as e:
            return False
            
        return True

class WafModuleBuild(ModuleBuild):
    """ Performs the build for Waf based projects."""

    def __init__(self):
        """ Instantiate the list of specific attributes for the waf build."""
        
        ModuleBuild.__init__(self)
        self.add_attribute('CC', '', 'C compiler to use')
        self.add_attribute('CXX', '', 'C++ compiler to use')
        self.add_attribute('CFLAGS', '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS', '', 'Flags to use for Linker')
        self.add_attribute('configure_arguments', '', 'Arguments to pass to'
                           ' "waf configure"')
        self.add_attribute('build_arguments', '', 'Arguments to pass to "waf"')
        self.add_attribute('install_arguments', '', 'Command-line arguments'
                           ' to pass to waf install')

    @classmethod
    def name(cls):
        """ Specific build type identifier."""
    
        return 'waf'
    
    def _binary(self, srcdir):
        """ Searches for the waf program."""

        if os.path.isfile(os.path.join(srcdir, 'waf')):
            waf_binary = os.path.join(srcdir, 'waf')
        else:
            waf_binary = 'waf'
        return waf_binary
    
    def _env(self, objdir):
        """ Verifies if the main environment variables where defined and 
        sets them accordingly.
        """
        
        env = dict()
        for a, b in [['CC', 'CC'],
                    ['CXX', 'CXX'],
                    ['CFLAGS', 'CFLAGS'],
                    ['CXXFLAGS', 'CXXFLAGS'],
                    ['LDFLAGS', 'LINKFLAGS']]:
            if self.attribute(a).value != '':
                env[b] = self.attribute(a).value
#        todo: Evaluate the situations where a waf lock may be required, and if so
#        implement something on this line
#        env['WAFLOCK'] = '.lock-waf_%s_build'%sys.platform #'.lock-%s' % os.path.basename(objdir)
        return env
    
    def _is_1_6_x(self, env):
        """ Searches for the waf version, it should be bigger than 1.6.0."""
        
        return env.check_program(self._binary(env.srcdir), version_arg='--version',
                                 version_regexp='(\d+)\.(\d+)\.(\d+)',
                                 version_required=(1, 6, 0))
        
    def build(self, env, jobs):
        """ Specific build implementation method. In order: 
        1. It apply possible patches, 
        2. Call waf configuration, if the configuration is set, 
        3. Call waf with the set build arguments, 
        4. Call waf with the install parameter. 
        """
        
        if self.attribute('patch').value != '':
            self.threat_patch(env)
        
        extra_configure_options = []
        if self.attribute('configure_arguments').value != '':
            extra_configure_options = [env.replace_variables(tmp) for tmp in
                                       bake.Utils.split_args(env.replace_variables(self.attribute('configure_arguments').value))]
            
            if self._is_1_6_x(env):
                env.run([self._binary(env.srcdir)] + extra_configure_options,
                        directory=env.srcdir,
                        env=self._env(env.objdir))
            else:
                env.run([self._binary(env.srcdir)] + extra_configure_options,
                        directory=env.srcdir,
                        env=self._env(env.objdir))

        extra_build_options = []
        if self.attribute('build_arguments').value != '':
            extra_build_options = [env.replace_variables(tmp) for tmp in
                                   bake.Utils.split_args(env.replace_variables(self.attribute('build_arguments').value))]
            
        env.run([self._binary(env.srcdir)] + extra_build_options + ['-j', str(jobs)],
                directory=env.srcdir,
                env=self._env(env.objdir))
        
        try :
            options = bake.Utils.split_args(env.replace_variables(self.attribute('install_arguments').value))
            env.run([self._binary(env.srcdir), 'install'] + options,
                directory=env.srcdir,
                env=self._env(env.objdir))
        except TaskError as e:
            print('Could not install, probably you have no permission to'
                  ' install  %s: Try to run bake with sudo. Original'
                  ' message: %s' % (env._module_name, e._reason))
       
        
    def clean(self, env):
        """ Call waf with the clean option to remove the results of the 
        last build.
        """

        wlockfile = '.lock-%s' % os.path.basename(env.objdir)
        if os.path.isfile(os.path.join(env.srcdir, wlockfile)):
            env.run([self._binary(env.srcdir), '-k', 'clean'],
                    directory=env.srcdir,
                    env=self._env(env.objdir))
            
    def check_version(self, env):
        """ Verifies the waf version."""
        
        for path in [os.path.join(env.srcdir, 'waf'), 'waf']:
            if env.check_program(path, version_arg='--version',
                                 version_regexp='(\d+)\.(\d+)\.(\d+)',
                                 version_required=(1, 5, 9)):
                return True
            
        return False


class Cmake(ModuleBuild):
    """ Performs the build for CMake based projects."""
    
    def __init__(self):
        """ Instantiate the list of specific attributes for the CMake build."""

        ModuleBuild.__init__(self)
        self.add_attribute('CC', '', 'C compiler to use')
        self.add_attribute('CXX', '', 'C++ compiler to use')
        self.add_attribute('CFLAGS', '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS', '', 'Flags to use for Linker')
        self.add_attribute('build_arguments', '', 'Targets to make before'
                           ' install')
        self.add_attribute('cmake_arguments', '', 'Command-line arguments'
                           ' to pass to cmake')
        self.add_attribute('configure_arguments', '', 'Command-line arguments'
                           ' to pass to cmake')
        self.add_attribute('install_arguments', '', 'Command-line arguments'
                           ' to pass to make install')

    @classmethod
    def name(cls):
        """ Specific build type identifier."""
        
        return 'cmake'

    def _variables(self):
        """ Verifies if the main environment variables where defined and 
        sets them accordingly.
        """

        variables = []
        for a, b in [['CC', 'C_COMPILER'],
                    ['CXX', 'CXX_COMPILER'],
                    ['CFLAGS', 'CFLAGS'],
                    ['CXXFLAGS', 'CXXFLAGS'],
                    ['LDFLAGS', 'EXE_LINKER_FLAGS']]:
            if self.attribute(a).value != '':
                variables.append('-DCMAKE_%s=%s' % (b, self.attribute(a).value))
                
        return variables

    def build(self, env, jobs):
        """ Specific build implementation method. In order: 
        1. Call cmake to create the make files
        2. It apply possible patches, 
        3. Call make to build the code, 
        4. Call make with the set build arguments 
        5. Call make with the install parameters. 
        """

        if self.attribute('patch').value != '':
            self.threat_patch(env)

        options = []
        if self.attribute('cmake_arguments').value != '':
            options = bake.Utils.split_args(
                          env.replace_variables(self.attribute('cmake_arguments').value))
        
        # if the object directory does not exist, it should create it, to
        # avoid build error, since the cmake does not create the directory
        # it also makes it orthogonal to waf, that creates the target object dir
        try:
            env.run(['mkdir', env.objdir],
                    directory=env.srcdir)
        except TaskError as e:
            # assume that if an error is thrown is because the directory already 
            # exist, otherwise re-propagates the error
            if not "error 1" in e._reason :
                raise TaskError(e._reason)

        env.run(['cmake', env.srcdir, '-DCMAKE_INSTALL_PREFIX=' + env.objdir] + 
                self._variables() + options,
                directory=env.objdir)
        env.run(['make', '-j', str(jobs)], directory=env.objdir)
        
        if self.attribute('build_arguments').value != '':
            env.run(['make'] + bake.Utils.split_args(env.replace_variables(self.attribute('build_arguments').value)),
                    directory=env.objdir)
            
        try:
            options = bake.Utils.split_args(env.replace_variables(self.attribute('install_arguments').value))
            env.run(['make', 'install'] + options, directory=env.objdir)
        except TaskError as e:
            print('Could not install, probably you have no permission to'
                  ' install  %s: Try to run bake with sudo. Original'
                  ' message: %s' % (env._module_name, e._reason))
            #raise TaskError('Could not install, probably you have no'
            #' permission to install  %s: Try to run bake with sudo.'
            #' Original message: %s' % (env._module_name, e._reason))
            

    def clean(self, env):
        """ Call make clean to remove the results of the last build."""

        if not os.path.isfile(os.path.join(env.objdir, 'Makefile')):
            return
        
        env.run(['make', 'clean'], directory=env.objdir)
        
    def check_version(self, env):
        """ Verifies if CMake and Make are available and their versions."""

        if not env.check_program('cmake', version_arg='--version',
                                 version_regexp='(\d+)\.(\d+)\.(\d+)',
                                 version_required=(2, 8, 2)):
            return False
        
        if not env.check_program('make', version_arg='--version',
                                 version_regexp='(\d+)\.(\d+)',
                                 version_required=(3, 80)):
            return False
        
        return True

# Class to handle the make build tool
class Make(ModuleBuild):
    def __init__(self):
        """ Instantiate the list of specific attributes for the make build."""

        ModuleBuild.__init__(self)
        self.add_attribute('CFLAGS', '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS', '', 'Flags to use for Linker')
        self.add_attribute('build_arguments', '', 'Targets to make before install')
        self.add_attribute('configure_arguments', '', 'Command-line arguments'
                           ' to pass to make')
        self.add_attribute('install_arguments', '', 'Command-line arguments'
                           ' to pass to make install')
        
    @classmethod
    def name(cls):
        """ Specific build type identifier."""

        return 'make'
    
    def build(self, env, jobs):
        """ Specific build implementation method. In order: 
        1. It apply possible patches, 
        2. Call make configure, if the configurations are available, 
        3. Call make with the set build arguments 
        4. Call make with the install arguments.
        """

        if self.attribute('patch').value != '':
            self.threat_patch(env)
    
        # if the object directory does not exist, it should create it, to
        # avoid build error, since the make does not create the directory
        # it also makes it orthogonal to waf, that creates the target object dir
        try:
            env.run(['mkdir', env.objdir],
                    directory=env.srcdir)
        except TaskError as e:
            # assume that if an error is thrown is because the directory already 
            # exist, otherwise re-propagates the error
            if not "error 1" in e._reason :
                raise TaskError(e._reason)

        # Configures make, if there is a configuration argument that was passed as parameter
        options = []      
        if self.attribute('configure_arguments').value != '':
            options = bake.Utils.split_args(env.replace_variables(self.attribute('configure_arguments').value))
            env.run(['make'] + self._flags() + options,  directory=env.srcdir)
        
        options = bake.Utils.split_args(env.replace_variables(self.attribute('build_arguments').value))
        env.run(['make', '-j', str(jobs)] + self._flags() + options, directory=env.srcdir)
           
        try:
            options = bake.Utils.split_args(env.replace_variables(self.attribute('install_arguments').value))
            env.run(['make', 'install']  + self._flags() + options, directory=env.srcdir)
        except TaskError as e:
            raise TaskError('Could not install, probably you have no'
                            ' permission to install  %s: Try to run bake with'
                            ' sudo. Original message: %s' 
                            % (env._module_name, e._reason))

    def clean(self, env):
        """ Call make clean to remove the results of the last build ."""

        if not os.path.isfile(os.path.join(env.objdir, 'Makefile')):
            return
        
        env.run(['make', '-i', 'clean'], directory=env.objdir)
        
    def check_version(self, env):
        """ Verifies if Make are available and its versions."""
        
        if not env.check_program('make', version_arg='--version',
                                 version_regexp='(\d+)\.(\d+)',
                                 version_required=(3, 80)):
            return False
        return True


class Autotools(ModuleBuild):
    def __init__(self):
        """ Instantiate the list of specific attributes for the Autotools build."""
        
        ModuleBuild.__init__(self)
        self.add_attribute('CC', '', 'C compiler to use')
        self.add_attribute('CXX', '', 'C++ compiler to use')
        self.add_attribute('CFLAGS', '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS', '', 'Flags to use for Linker')
        self.add_attribute('maintainer', 'no', 'Maintainer mode ?')
        self.add_attribute('configure_arguments', '', 'Command-line arguments'
                           ' to pass to configure')
        self.add_attribute('install_arguments', '', 'Command-line arguments'
                           ' to pass to make install')
        
    @classmethod
    def name(cls):
        """ Specific build type identifier."""
  
        return 'autotools'

    def _variables(self):
        """ Verifies if the main environment variables where defined and 
        sets them accordingly."""

        variables = []
        for tmp in ['CC', 'CXX', 'CFLAGS', 'CXXFLAGS', 'LDFLAGS']:
            if self.attribute(tmp).value != '':
                variables.append('%s=%s' % (tmp, self.attribute(tmp).value))
                
        return variables
    
    def build(self, env, jobs):
        """ Specific build implementation method. In order: 
        1. It apply possible patches, 
        2. Call autoreconf, if on maintainer mode
        2. Call make configure, if the configure arguments are available, 
        3. Call make to perform the build 
        4. Call make with the install arguments.
        """

        if self.attribute('patch').value != '':
            self.threat_patch(env)

        if self.attribute('maintainer').value != 'no':
            env.run(['autoreconf', '--install'],
                    directory=env.srcdir)
            
        options = []
        if self.attribute('configure_arguments').value != '':
            command= (env.replace_variables(env.replace_variables(self.attribute('configure_arguments').value))
                       + ' --prefix=' + env.objdir)
            command= bake.Utils.split_args(command)
            env.run(command, directory=env.objdir)
            
        env.run(['make', '-j', str(jobs)], directory=env.objdir)
        
        try :
            options = bake.Utils.split_args(env.replace_variables(self.attribute('install_arguments').value))
            env.run(['make', 'install'] + options, directory=env.objdir)
        except TaskError as e:
            print('Could not install, probably you have no permission to'
                  ' install  %s: Try to run bake with sudo. Original message:'
                  ' %s' % (env._module_name, e._reason))
            #raise TaskError('Could not install, probably you have no'
            #' permission to install  %s: Try to run bake with sudo. '
            #'Original message: %s' % (env._module_name, e._reason))
        

    def clean(self, env):
        """ Call make maintainerclean or distclean to remove the results of 
        the last build.
        """

        if not os.path.isfile(os.path.join(env.objdir, 'Makefile')):
            return
        
        if self.attribute('maintainer').value != 'no':
            env.run(['make', '-k', 'maintainerclean'], directory=env.objdir)
        else:
            env.run(['make', '-k', 'distclean'], directory=env.objdir)
            
        try:
            os.remove(os.path.join(env.objdir, 'config.cache'))
        except OSError:
            pass
        
    def check_version(self, env):
        """ Verifies if Autoreconf and Make are available and their versions."""

        if not env.check_program('autoreconf', version_arg='--version',
                                 version_regexp='(\d+)\.(\d+)',
                                 version_required=(2, 66)):
            return False
        
        if not env.check_program('make', version_arg='--version',
                                 version_regexp='(\d+)\.(\d+)',
                                 version_required=(3, 80)):
            return False
        
        return True
            

