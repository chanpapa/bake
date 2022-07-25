# bake
Bake: DCE-1.12 with net-next-nuse-5.10 (Native Build, Linux Kernel-5.10.0) provided by ParthPratim1.

# NS3 DCE



## 1. Build DCE

*********



DCE offers two major modes of operation:

  1. The basic mode, where DCE uses the |ns3| TCP stacks,
  2. The advanced mode, where DCE uses a Linux network stack instead





以下提供三种方法，其中前两种的dce只能使用1.11及以下的版本，因此需要切换到Ubuntu 16.04及以下。 第三种方法的DCE版本为1.12，支持Ubuntu 20.04。

### 1.1 Waf 

同样，也可以采用Bake

```shell
export GIT_NS3= git@gitlab.com:nsnam/ns-3-dev.git
#set the version you want
export LAST_VERSION= ns-3.34 
```



```shell
export HOME=`pwd`
mkdir dce
cd dce
# Download pybindgen (optional)
git clone https://github.com/gjcarneiro/pybindgen.git
cd pybindgen
./setup.py install

# Download ns-3
# git instructions
git clone GIT_NS3
cd ns3
git checkout LAST_VERSION

# Configure
./waf configure --enable-examples -d optimized --prefix=$HOME/dce/ns3_install

# Build and install in the directory specified by
# --prefix parameter
./waf build
# install the build files into the directory specified by --prefix
./waf install
```

将build file移出来放置，方便后面dce的代码对ns3库的使用。（）



若你想使用linux stack，还得进行以下步骤（net-next-use的下载，编译，链接） 

```shell
# Clone net-next-nuse
git clone https://github.com/libos-nuse/net-next-nuse.git
# or https://github.com/ParthPratim/net-next-nuse-5.10.47.git including BBR
cd net-next-nuse
# Select a kernel version
git checkout libos-v4.4
# Configure and build
make defconfig ARCH=lib
#This will download and compile git submodules from 
#https://github.com/libos-nuse/linux-libos-tools 
make library ARCH=lib
#You should see libnuse-linux.so in the directory 'arch/lib/tools'.
cd ..

# Download, configure, build and install DCE
# This is the 1.12 version for ubuntu20.04
git clone https://github.com/ParthPratim/ns-3-dce.git 
./waf configure --with-ns3=$HOME/dce/ns3_install --enable-opt  --enable-kernel-stack=$HOME/dce/net-next-nuse/arch  --prefix=$HOME/dce/dce_install
./waf build
./waf install
```

实际上，*net-next-nuse*就是我们需要的linux stack

**waf编译确实比较繁琐，而且像iperf ,wget等工具还需要自己逐个手动添加**



### 1.2 bake

采用bake工具

**if you have already downloded the bake and  want to remove older version dce:** 

```shell
./bake.py fullclean 
rm -rf bakefile.xml
```

If you do not have bake , then do the followings:

```shell
git clone https://gitlab.com/nsnam/bake.git
```

And then:

```shell
cd bake
./bake.py configure -e dce-linux-version
./bake.py check
./bake.py show
./bake.py download
./bake.py build
```

**Noted that: only 1.12 and its later version of dce supports Ubuntu 20.04**

**但是官方的bake是没有提供dce-linux-1.12的，所以你需要更换到Ubuntu16.04或者docker**





### 1.3  个人改动过的bake(有不少bug)



原文链接：GSOC2021DCE - Nsnam
https://www.nsnam.org/wiki/GSOC2021DCE



- **DCE-1.12 with net-next-nuse-5.10 (Native Build, Linux Kernel-5.10.0)**

```shell
git clone https://gitlab.com/ParthPratim1/bake.git
cd bake
git checkout dce-1.12-linux-5.10
python2 ./bake.py configure -e dce-linux-1.12
python2 ./bake.py download
python2 ./bake.py build
```

这个版本实现了BBR



#### 遇到的bug

**bug不少，需要大量时间和精力debug**

下面简单列举一下可能会遇到的问题

1.

bake/bakeconf.xml配置文件中dce-linux-1.12的依赖的modul版本错写为net-next-nuse-5.10.0应改为如下 5.10.47

```xml
<module name="dce-linux-1.12">
      <source type="git">
        <attribute name="url" value="https://github.com/ParthPratim/ns-3-dce.git"/>        
        <attribute name="module_directory" value="ns-3-dce"/>
        <attribute name="revision" value="glibc-build"/>
      </source>
      <depends_on name="dce-meta-1.12" optional="False"/>
      <depends_on name="net-next-nuse-5.10.47" optional="False"/>
      <depends_on name="iproute2-5.10.0" optional="False"/>
      <depends_on name="lksctp-dev" optional="True"/>
      <build type="waf" objdir="objdir" sourcedir="ns-3-dce">
        <attribute name="supported_os" value="linux;linux2"/>
        <attribute name="configure_arguments" value="configure --prefix=$INSTALLDIR --with-ns3=$INSTALLDIR --with-elf-loader=$INSTALLDIR/lib --with-glibc=$INSTALLDIR/glibc --with-libaspect=$INSTALLDIR --enable-kernel-stack=$SRCDIR/../net-next-nuse-5.10.47/arch"/>
      </build>
    </module>
```

2.如果，在 download阶段遇到 net-next-nuse下载失败，或者net-next-nuse build失败的报错可以手下载编译：

```shell
# Clone net-next-nuse
git clone https://github.com/libos-nuse/net-next-nuse.git
cd net-next-nuse
# Select a kernel version
git checkout libos-v4.4
```

```shell
cd net-next-nuse
make defconfig ARCH=lib
make library ARCH=lib
```

如果遇到 libc-2.31报错的相关信息：可以将bakeconf.xml里的libc的版本改为你的linux内核的版本。

因为他这里强制要求是2.31，但实际上其他版本也是允许的，根据你的linux内核的版本更改就好



### 1.4 docker image

[thehajime/ns-3-dce - Docker Image | Docker Hub](https://hub.docker.com/r/thehajime/ns-3-dce)

是现成的，但ns3-dce的wsrcipt有少量bug，根据报错自己debug就好。

缺点：**无BBR**，暂时不知道该咋解决



```xml
 <module name="bc">
      <source type="system_dependency">
        <attribute name="dependency_test" value="bc"/>
        <attribute name="name_yum" value="bc"/>
        <attribute name="name_yast" value="bc"/>
        <attribute name="name_apt-get" value="bc"/>
        <attribute name="more_information" value="Didn't find: the bc calculator language, try to install it!"/>
      </source>
      <build type="none">
      </build>
    </module>
```



```xml-dtd
 <module name="net-next-nuse-5.10.47">
       <source type="git">
         <attribute name="url" value="https://github.com/ParthPratim/net-next-nuse-5.10.47.git"/>
         <attribute name="module_directory" value="net-next-nuse-5.10.47"/>
         <attribute name="fetch_option" value=""/>
       </source>
       <depends_on name="bc" optional="False"/>
       <build type="make" objdir="no">
         <attribute name="supported_os" value="linux;linux2"/>
         <attribute name="configure_arguments" value="defconfig ARCH=lib"/>
         <attribute name="build_arguments" value="library ARCH=lib"/>
         <attribute name="no_installation" value="True"/>
         <attribute name="post_installation" value="mkdir -p $INSTALLDIR/bin_dce; cd $INSTALLDIR/bin_dce; cp $SRCDIR/arch/lib/tools/libsim-linux-5.10.47.so ./; ln -s -f libsim-linux-5.10.47.so liblinux.so"/>
       </build>
     </module>
```



## 2.  provide an easy way to build DCE



为我们的实验提供一种简单的安装dce的方法：

经过筛选：



bake的方法是最简便的，而且经过简化后，去掉许多不必要的module。只需要把bakeconf.xml改成如下即可：



```xml
<module name="net-next-nuse-5.10.47">
       <source type="git">
         <attribute name="url" value="https://github.com/ParthPratim/net-next-nuse-5.10.47.git"/>
         <attribute name="module_directory" value="net-next-nuse-5.10.47"/>
         <attribute name="fetch_option" value=""/>
       </source>
       <depends_on name="bc" optional="False"/>
       <build type="make" objdir="no">
         <attribute name="supported_os" value="linux;linux2"/>
         <attribute name="configure_arguments" value="defconfig ARCH=lib"/>
         <attribute name="build_arguments" value="library ARCH=lib"/>
         <attribute name="no_installation" value="True"/>
         <attribute name="post_installation" value="mkdir -p $INSTALLDIR/bin_dce; cd $INSTALLDIR/bin_dce; cp $SRCDIR/arch/lib/tools/libsim-linux-5.10.47.so ./; ln -s -f libsim-linux-5.10.47.so liblinux.so"/>
       </build>
     </module>

 <module name="bc">
      <source type="system_dependency">
        <attribute name="dependency_test" value="bc"/>
        <attribute name="name_yum" value="bc"/>
        <attribute name="name_yast" value="bc"/>
        <attribute name="name_apt-get" value="bc"/>
        <attribute name="more_information" value="Didn't find: the bc calculator language, try to install it!"/>
      </source>
      <build type="none">
      </build>
    </module>

<module name="dce-linux-1.12">
      <source type="git">
        <attribute name="url" value="https://github.com/ParthPratim/ns-3-dce.git"/>        
        <attribute name="module_directory" value="ns-3-dce"/>
        <attribute name="revision" value="glibc-build"/>
      </source>
      <depends_on name="dce-meta-1.12" optional="False"/>
      <depends_on name="net-next-nuse-5.10.47" optional="False"/>
      <depends_on name="iproute2-5.10.0" optional="False"/>
      <depends_on name="lksctp-dev" optional="True"/>
      <build type="waf" objdir="objdir" sourcedir="ns-3-dce">
        <attribute name="supported_os" value="linux;linux2"/>
        <attribute name="configure_arguments" value="configure --prefix=$INSTALLDIR --with-ns3=$INSTALLDIR --with-elf-loader=$INSTALLDIR/lib --with-glibc=$INSTALLDIR/glibc --with-libaspect=$INSTALLDIR --enable-kernel-stack=$SRCDIR/../net-next-nuse-5.10.47/arch"/>
      </build>
    </module>
    <module name="glibc-2.31">
      <source type="git">
        <attribute name="url" value="https://sourceware.org/git/glibc.git" />
        <attribute name="revision" value="release/2.31/master" />
        <attribute name="module_directory" value="glibc" />
      </source>
      <depends_on name="gawk" optional="False"/>
      <build type="inline" classname="GlibcModuleBuild">
        <attribute name="patch" value="$SRCDIR/../ns-3-dce/utils/glibc-2.31-disable-security-checks.patch"/>
        <code>class GlibcModuleBuild(InlineModuleBuild):
    def __init__(self):
        InlineModuleBuild.__init__(self)
    def build(self, env, jobs):
           build_dir = env.installdir + '/glibc-build'
           install_dir = env.installdir + '/glibc'
           dest_dir = 'DESTDIR=' + install_dir
           env.run(['mkdir', '-p', install_dir], directory=env.srcdir)
           env.run(['make'], directory=build_dir)
           env.run(['make', 'install', dest_dir], directory=build_dir)
    def clean(self, env):
           build_dir = env.installdir + '/glibc-build'
           env.run(['make', 'clean'], directory=build_dir)
    def check_version(self, env):
           return True</code>
      </build>
     </module>
 <module name="linux-dev">
      <source type="git">
        <attribute name="url" value="git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git" />
        <attribute name="revision" value="master" />
        <attribute name="module_directory" value="linux" />
      </source>
      <depends_on name="glibc-2.31" optional="False" />
      <build type="make" objdir="yes">
        <attribute name="build_arguments" value="headers_install INSTALL_HDR_PATH=$INSTALLDIR/glibc/usr" />
        <attribute name="no_installation" value="True"/>
      </build>
     </module> 
          
     <!-- dce-1.12 -->
    <module name="dce-meta-1.12">
      <source type="git">
	<attribute name="url" value="https://github.com/ParthPratim/ns-3-dce.git"/>        
        <attribute name="module_directory" value="ns-3-dce"/>
        <attribute name="revision" value="glibc-build"/>
      </source>
      <depends_on name="ns-3.35" optional="False"/>
      <depends_on name="glibc-2.31" optional="False"/>
      <depends_on name="linux-dev" optional="False"/>
      <build type="none">
      </build>
    </module>
          
 <module name="ns-3.35" type="ns">
      <source type="git">
        <attribute name="url" value="https://gitlab.com/nsnam/ns-3-dev.git"/>
        <attribute name="module_directory" value="ns-3.35"/>
        <attribute name="branch" value="master"/>
        <attribute name="revision" value="ns-3.35"/>
      <build type="waf">
        <attribute name="configure_arguments" value="configure --prefix=$INSTALLDIR --enable-examples --enable-tests"/>
      </build>
    </module>
     
     <!-- System dependency -->
  
```



### 报错及解决方法：

### 1.ld cannot find -libxyz (或具体的文件如libgcc_s.so.1)

[c++ - usr/bin/ld: cannot find -l - Stack Overflow](https://stackoverflow.com/questions/16710047/usr-bin-ld-cannot-find-lnameofthelibrary)

[usr/bin/ld: cannot find 错误解决方法和 /etc/ld.so.conf - youxin - 博客园 (cnblogs.com)](https://www.cnblogs.com/youxin/p/4757352.html)

- 把ld -libxyz --verbose的失败文件用你的特定版本的libxyz（可以用locate直接找一个带版本号的 如： libxyz.so.0.8.6）软连接替换掉
- 如果是libgcc_s.so.1文件找不到，那可能是/usr/lib中缺失或不是正确版本的文件，拷贝一份正确的放在那就好
- 如果拷贝不能解决问题或者文件数量过多，那就 往/etc/ld.so.conf添加库文件路径再用sudo ldconfig刷新
- 或者在环境变量LD_LIBRARY_PATH加上库文件所在路径







[How to build ns3-dce in ubuntu20.04 using Bake? (google.com)](https://groups.google.com/g/ns-3-users/c/i9EZqhldqKk)

[Glibc 2.7 Build Error "ld: cannot find -lgcc" (linuxquestions.org)](https://www.linuxquestions.org/questions/linux-from-scratch-13/glibc-2-7-build-error-ld-cannot-find-lgcc-657560/)

building dce-linux-1.12 problem

```
configure --prefix=/home/chenrh/dce/bake/build --with-ns3=/home/chenrh/dce/bake/build --with-glibc=/home/chenrh/dce/bake/build/glibc --enable-kernel-stack=/home/chenrh/dce/bake/source/ns-3-dce/../net-next-nuse-5.10.47/arch
```



```
git clone https://gitlab.com/tomhenderson/bake.git
cd bake
git checkout -b dce-1.12 origin/dce-1.12
export PATH=$PATH:`pwd`/build/bin
export DCE_PATH=`pwd`/build/bin_dce:`pwd`/build/sbin
export LD_LIBRARY_PATH=`pwd`/build/lib
export PYTHONPATH=`pwd`/build/lib

python2 ./bake.py configure -e dce-linux-1.12
python2 ./bake.py download
python2 ./bake.py build
python2 cd source/ns-3-dce
python2 ./test.py
```

```
git clone https://gitlab.com/tomhenderson/bake.git
cd bake
git checkout -b dce-1.11 origin/dce-1.11
export PATH=$PATH:`pwd`/build/bin
export DCE_PATH=`pwd`/build/bin_dce:`pwd`/build/sbin
export LD_LIBRARY_PATH=`pwd`/build/lib
export PYTHONPATH=`pwd`/build/lib

python2 ./bake.py configure -e dce-linux-1.11
python2 ./bake.py download
python2 ./bake.py build
python2 cd source/ns-3-dce
python2 ./test.py
```

