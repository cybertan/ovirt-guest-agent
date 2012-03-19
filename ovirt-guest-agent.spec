
%define release_version 1

%define _moduledir /%{_lib}/security
%define _kdmrc /etc/kde/kdm/kdmrc

Name: ovirt-guest-agent
Version: 1.0.1
Release: %{release_version}%{?dist}
Summary: oVirt Guest Agent
Group: Applications/System
License: GPLv2+
URL: http://gerrit.ovirt.org/p/ovirt-guest-agent.git
Source0: http://ghammer.fedorapeople.org/%{name}-%{version}.tar.bz2
ExclusiveArch: i686 x86_64
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires: python
BuildRequires: automake
BuildRequires: libtool
BuildRequires: pam-devel
Requires: dbus-python
Requires: rpm-python
Requires: SysVinit
Requires: python-ethtool >= 0.4-1
Requires: udev >= 095-14.23
Requires: kernel > 2.6.18-238.5.0
Requires: usermode
Requires: selinux-policy >= 3.7.19-93.el6_1.3

%package pam-module
Summary: oVirt Guest Agent PAM module
Requires: pam ovirt-guest-agent

%package gdm-plugin
Summary: GDM oVirt plug-in
Requires: gdm ovirt-guest-agent
Requires: ovirt-guest-agent-pam-module

%package kdm-plugin
Summary: KDM oVirt plug-in
Requires: kdm ovirt-guest-agent
Requires: ovirt-guest-agent-pam-module

# No gdm-devel package is available for plug-in development. So for now
# we build the gdm package.
Source1: gdm-3.2.1.1-6.fc16.src.rpm

%define libauditver 1.0.6
%define pango_version 1.2.0
%define gtk3_version 2.99.2
%define scrollkeeper_version 0.3.4
%define pam_version 0.99.8.1-11
%define desktop_file_utils_version 0.2.90
%define nss_version 3.11.1
%define fontconfig_version 2.6.0

BuildRequires: pkgconfig(libcanberra-gtk)
BuildRequires: scrollkeeper >= 0:%{scrollkeeper_version}
BuildRequires: pango-devel >= 0:%{pango_version}
BuildRequires: gtk3-devel >= 0:%{gtk3_version}
BuildRequires: pam-devel >= 0:%{pam_version}
BuildRequires: fontconfig >= 0:%{fontconfig_version}
BuildRequires: desktop-file-utils >= %{desktop_file_utils_version}
BuildRequires: libtool automake autoconf
BuildRequires: libattr-devel
BuildRequires: gettext
BuildRequires: gnome-doc-utils
BuildRequires: libdmx-devel
BuildRequires: audit-libs-devel >= %{libauditver}
BuildRequires: gobject-introspection-devel
BuildRequires: autoconf automake libtool
BuildRequires: intltool
BuildRequires: nss-devel >= %{nss_version}
BuildRequires: ConsoleKit
BuildRequires: libselinux-devel
BuildRequires: check-devel
BuildRequires: iso-codes-devel
BuildRequires: libxklavier-devel >= 4.0
BuildRequires: upower-devel >= 0.9.7
BuildRequires: libXdmcp-devel
BuildRequires: dbus-glib-devel
BuildRequires: GConf2-devel
BuildRequires: pkgconfig(accountsservice) >= 0.6.3

# kdm-plugin's requirements.
BuildRequires: kdebase-workspace-devel

%description
This is the oVirt management agent running inside the guest. The agent
interfaces with the oVirt manager, supplying heart-beat info as well as
run-time data from within the guest itself. The agent also accepts
control commands to be run executed within the OS (like: shutdown and
restart).

%description pam-module
The oVirt PAM module provides the functionality necessary to use the
oVirt automatic login system.

%description gdm-plugin
The GDM plug-in provides the functionality necessary to use the
oVirt automatic login system.

%description kdm-plugin
The KDM plug-in provides the functionality necessary to use the
oVirt automatic login system.

%prep
%setup -q
rpmbuild --define="_topdir %{_topdir}" --recompile %{SOURCE1}
autoreconf -i -f

%build
%configure \
    --enable-securedir=%{_moduledir} \
    --includedir=%{_includedir}/security \
    --with-gdm-src-dir=%{_topdir}/BUILD/gdm-3.2.1.1 \
    --with-pam-prefix=%{_sysconfdir}
    
make %{?_smp_mflags}

%install
[ -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / ] && rm -rf $RPM_BUILD_ROOT

# libtool will look for this file when relinking during installation.
mkdir -p $RPM_BUILD_ROOT%{_libdir}
cp %{_topdir}/BUILDROOT/gdm-3.2.1.1-6.fc16.%{?_arch}%{_libdir}/libgdmsimplegreeter.so \
    $RPM_BUILD_ROOT%{_libdir}

make install DESTDIR=$RPM_BUILD_ROOT

# Update timestamps on Python files in order to avoid differences between
# .pyc/.pyo files.
touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/%{name}/*.py

# No longer needed and is provided by the gdm package.
rm -f $RPM_BUILD_ROOT%{_libdir}/libgdmsimplegreeter.so

rm -f $RPM_BUILD_ROOT%{_libdir}/gdm/simple-greeter/extensions/libovirtcred.a
rm -f $RPM_BUILD_ROOT%{_libdir}/gdm/simple-greeter/extensions/libovirtcred.la

rm -f $RPM_BUILD_ROOT%{_moduledir}/pam_ovirt_cred.a
rm -f $RPM_BUILD_ROOT%{_moduledir}/pam_ovirt_cred.la

mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/%{name}
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/run/%{name}
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lock/subsys/%{name}

%clean
[ -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / ] && rm -rf $RPM_BUILD_ROOT

%pre
getent passwd ovirtagent > /dev/null || /usr/sbin/useradd -u 175 -o -r ovirtagent -c "oVirt Guest Agent" -d / -s /sbin/nologin

%post

ln -s /usr/bin/consolehelper %{_datadir}/%{name}/ovirt-locksession
ln -s /usr/bin/consolehelper %{_datadir}/%{name}/ovirt-shutdown
ln -s /usr/bin/consolehelper %{_datadir}/%{name}/ovirt-hibernate

/sbin/udevadm trigger /dev/vport*

/bin/systemctl daemon-reload

%post kdm-plugin
if ! grep -q "^PluginsLogin=" "%{_kdmrc}";
then
    sed -i "s~^#PluginsLogin=winbind~PluginsLogin=ovirtcred,classic~" "%{_kdmrc}"
fi

%preun
if [ "$1" -eq 0 ]
then
    /bin/systemctl stop %{name}.service > /dev/null 2>&1

    # Send an "uninstalled" notification to vdsm.
    VIRTIO=`grep "^device" %{_sysconfdir}/%{name}.conf | awk '{ print $3; }'`
    if [ -w $VIRTIO ]
    then
        echo '{ "__name__" : "uninstalled" }' >> $VIRTIO
    fi
fi

%postun
if [ "$1" -eq 0 ]
then
    /bin/systemctl daemon-reload

    rm -f %{_datadir}/%{name}/ovirt-locksession
    rm -f %{_datadir}/%{name}/ovirt-shutdown
    rm -f %{_datadir}/%{name}/ovirt-hibernate
fi

%postun kdm-plugin
if [ "$1" -eq 0 ]
then
    sed -i "s~PluginsLogin=ovirtcred,classic~#PluginsLogin=winbind~" "%{_kdmrc}"
fi

%files
%defattr(-,root,root,-)
%dir %attr (755,ovirtagent,ovirtagent) %{_localstatedir}/log/%{name}
%dir %attr (755,root,root) %{_datadir}/%{name}
%config %{_sysconfdir}/%{name}.conf
%{_sysconfdir}/dbus-1/system.d/org.ovirt.vdsm.Credentials.conf
%{_sysconfdir}/security/console.apps/ovirt-locksession
%{_sysconfdir}/security/console.apps/ovirt-shutdown
%{_sysconfdir}/security/console.apps/ovirt-hibernate
%{_sysconfdir}/pam.d/ovirt-locksession
%{_sysconfdir}/pam.d/ovirt-shutdown
%{_sysconfdir}/pam.d/ovirt-hibernate
%attr (644,root,root) %{_sysconfdir}/udev/rules.d/55-%{name}.rules
%attr (755,root,root) %{_datadir}/%{name}/%{name}.py*
%{_datadir}/%{name}/OVirtAgentLogic.py*
%{_datadir}/%{name}/VirtIoChannel.py*
%{_datadir}/%{name}/CredServer.py*
%{_datadir}/%{name}/GuestAgentLinux2.py*
%attr (755,root,root) %{_datadir}/%{name}/LockActiveSession.py*
%attr (755,root,root) %{_datadir}/%{name}/hibernate
/lib/systemd/system/ovirt-guest-agent.service

%doc AUTHORS COPYING NEWS README

%files pam-module
%defattr(-,root,root,-)
%{_moduledir}/pam_ovirt_cred.so

%files gdm-plugin
%defattr(-,root,root,-)
%config %{_sysconfdir}/pam.d/gdm-ovirtcred
%{_datadir}/icons/hicolor/*/*/*.png
%dir %{_datadir}/gdm/simple-greeter/extensions/ovirtcred
%{_datadir}/gdm/simple-greeter/extensions/ovirtcred/page.ui
%{_libdir}/gdm/simple-greeter/extensions/libovirtcred.so

%files kdm-plugin
%defattr(-,root,root,-)
%config %{_sysconfdir}/pam.d/kdm-ovirtcred
%attr (755,root,root) %{_libdir}/kde4/kgreet_ovirtcred.so

%changelog
* Thu Sep 27 2011 Gal Hammer <ghammer@redhat.com> - 2.3.15-1
- fixed disk usage report when mount point include spaces.
- added a minimum version for python-ethtool.
Resolves: BZ#736426

* Thu Sep 22 2011 Gal Hammer <ghammer@redhat.com> - 2.3.14-1
- added a new 'echo' command to support testing.
Resolves: BZ#736426

* Thu Sep 15 2011 Gal Hammer <ghammer@redhat.com> - 2.3.13-1
- report new network interaces information (ipv4, ipv6 and
  mac address).
- added disks usage report.
- a new json-based protocol with the vdsm.
Resolves: BZ#729252 BZ#736426

* Mon Aug  8 2011 Gal Hammer <ghammer@redhat.com> - 2.3.12-1
- replaced password masking with a fixed-length string.
Resolves: BZ#727506 

* Thu Aug  4 2011 Gal Hammer <ghammer@redhat.com> - 2.3.11-1
- send an 'uninstalled' notification to vdsm
- mask the user's password in the credentials block
Resolves: BZ#727647 BZ#727506

* Mon Aug  1 2011 Gal Hammer <ghammer@redhat.com> - 2.3.10-2
- fixed selinux-policy required version.
Resolves: BZ#694088

* Mon Jul 25 2011 Gal Hammer <ghammer@redhat.com> - 2.3.10-1
- various fixes after failing the errata's rpmdiff.
- added selinux-policy dependency.
Resolves: BZ#720144 BZ#694088

* Thu Jun 16 2011 Gal Hammer <ghammer@redhat.com> - 2.3.9-1
- read report rate values from configuration file.
- replaced executing privilege commands from sudo to
  consolehelper.
Resolves: BZ#713079 BZ#632959

* Tue Jun 14 2011 Gal Hammer <ghammer@redhat.com> - 2.3.8-1
- execute the agent with a non-root user.
- changed the shutdown timeout value to work in minutes.
- update pam config files to work with selinux.
- fixed the local user check when stripping the domain part.
Resolves: BZ#632959 BZ#711428 BZ#694088 BZ#661713 BZ#681123

* Tue May 25 2011 Gal Hammer <ghammer@redhat.com> - 2.3.7-1
- stopped removing the domain part from the user name.
- show only network interfaces that are up and running.
Resolves: BZ#661713 BZ#681123 BZ#704845

* Mon Apr 4 2011 Gal Hammer <ghammer@redhat.com> - 2.3.6-1
- added kdm greeter plug-in.
Resolves: BZ#681123

* Mon Mar 14 2011 Gal Hammer <ghammer@redhat.com> - 2.3.5-1
- replaced rhevcredserver execution from blocking main loop to
  context's iteration (non-blocking).
Resolves: BZ#683493

* Thu Mar 10 2011 Gal Hammer <ghammer@redhat.com> - 2.3.4-1
- added some sleep-ing to init script in order to give udev
  some time to create the symbolic links.
- changed the kernel version condition.
Resolves: BZ#676625 BZ#681527

* Wed Mar 2 2011 Gal Hammer <ghammer@redhat.com> - 2.3.3-1
- removed unused file (rhevcredserver) from rhel-5 build.
- added udev and kernel minimum version requirment.
- fixed pid file location in spec file.
Resolves: BZ#681524 BZ#681527 BZ#681533

* Tue Mar 1 2011 Gal Hammer <ghammer@redhat.com> - 2.3.2-1
- updated the agent's makefile to work with auto-tools.
- added sub packages to support the single-sign-on feature.
- added -h parameter to shutdown command in order to halt the vm
  after shutdown.
- converted configuration file to have unix-style line ending.
- added redhat-rpm-config to build requirements in order to
  include *.pyc and *.pyo in the rpm file.
Resolves: BZ#680107 BZ#661713 BZ#679470 BZ#679451

* Wed Jan 19 2011 Gal Hammer <ghammer@redhat.com> - 2.3-7
- fixed files' mode to include execution flag.
Resolves: BZ#670476

* Mon Jan 17 2011 Gal Hammer <ghammer@redhat.com> - 2.3-6
- fixed the way the exit code was returned. the script always
  return 0 (success) because the main program ended and errors
  from the child process were lost.
Resolves: BZ#658092

* Thu Dec 23 2010 Gal Hammer <ghammer@redhat.com> - 2.3-5
- added description to startup/shutdown script in order to support
  chkconfig.
- a temporary fix to the 100% cpu usage when the vdsm doesn't
  listen to the virtio-serial.
Resolves: BZ#639702

* Sun Dec 19 2010 Gal Hammer <ghammer@redhat.com> - 2.3-4
- BZ#641886: lock command now handle both gnome and kde.
Resolves: BZ#641886

* Tue Dec 07 2010 Barak Azulay <bazulay@redhat.com> - 2.3-3
- BZ#660343 load virtio_console module before starting the daemon.
- BZ#660231 register daemon for startup.
Resolves: BZ#660343 BZ#660231

* Wed Dec 05 2010 Barak Azulay <bazulay@redhat.com> - 2.3-2
- initial build for RHEL-6
- works over vioserial 
- Agent reports only heartbeats, IPs, app list
- performs: shutdown & lock (the lock works only on gnome - when 
  ConsoleKit & gnome-screensaver is installed)
Resolves: BZ#613059
  
* Thu Aug 27 2010 Gal Hammer <ghammer@redhat.com> - 2.3-1
- Initial build.
