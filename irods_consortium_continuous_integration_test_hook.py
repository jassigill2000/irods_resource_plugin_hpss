from __future__ import print_function

import optparse
import json
import pwd
import socket
import os
import shutil
import glob
import time

import irods_python_ci_utilities


def get_build_prerequisites_apt():
    return[]

def get_build_prerequisites_yum():
    return[]

def get_build_prerequisites():
    dispatch_map = {
        'Ubuntu': get_build_prerequisites_apt,
        'Centos': get_build_prerequisites_yum,
        'Centos linux': get_build_prerequisites_yum
    }
    try:
        return dispatch_map[irods_python_ci_utilities.get_distribution()]()
    except KeyError:
        irods_python_ci_utilities.raise_not_implemented_for_distribution()


def install_build_prerequisites():
    irods_python_ci_utilities.subprocess_get_output(['sudo', '-EH', 'pip', 'install', 'unittest-xml-reporting==1.14.0'])
    configure_hpss()

def configure_hpss():
    irods_python_ci_utilities.subprocess_get_output(['sudo', 'passwd', 'irods'], data='notasecret\nnotasecret\n', check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', 'sed', '-i', '/hpss743.example.org/ s/$/ hpss743/', '/etc/hosts'], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', 'ln', '-s', '/lib64/libtirpc.so.1', '/lib64/libtirpc.so'], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', 'sed', '-i', '/^ALL:.*DENY$/d', '/etc/hosts.allow'], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', '/etc/init.d/rpcbind', 'restart'], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', '/opt/hpss/bin/rc.hpss', 'stop'], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', '/opt/hpss/bin/rc.hpss', 'start'], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', '/opt/hpss/bin/hpssadm.pl', '-U', 'hpssssm', '-A', 'unix', '-a', '/var/hpss/etc/hpss.unix.keytab'], data='server start -all\nquit\n', check_rc=True)
    pwnam = pwd.getpwnam('irods')
    irods_python_ci_utilities.subprocess_get_output(['sudo', '/opt/hpss/bin/hpssuser', '-add', 'irods', '-unix', '-gid', str(pwnam.pw_gid), '-uid', str(pwnam.pw_uid), '-group', 'irods', '-fullname', '"irods"', '-home', '/var/lib/irods', '-unixkeytab', '/var/hpss/etc/irods.keytab', '-shell', '/bin/bash', '-hpsshome', '/opt/hpss', '-password', 'notasecret'], check_rc=True)
    prepare_hpss_string = '''
unlink /irodsVault recurse top
mkdir /irodsVault
chown /irodsVault {0}
chgrp /irodsVault {1}
quit
'''.format(pwnam.pw_uid, pwnam.pw_gid)
    irods_python_ci_utilities.subprocess_get_output(['sudo', '/opt/hpss/bin/scrub', '-a', 'unix', '-k', '-t', '/var/hpss/etc/root.unix.keytab', '-p', 'root'], data=prepare_hpss_string, check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', 'service', 'irods', 'restart'])

def main():
    parser = optparse.OptionParser()
    parser.add_option('--output_root_directory')
    parser.add_option('--built_packages_root_directory')
    options, _ = parser.parse_args()

    output_root_directory = options.output_root_directory
    built_packages_root_directory = options.built_packages_root_directory
    package_suffix = irods_python_ci_utilities.get_package_suffix()
    os_specific_directory = irods_python_ci_utilities.append_os_specific_directory(built_packages_root_directory)

    irods_python_ci_utilities.install_os_packages_from_files(glob.glob(os.path.join(os_specific_directory, 'irods-resource-plugin-hpss*.{0}'.format(package_suffix))))
    install_build_prerequisites()

    time.sleep(10)

    try:
        test_output_file = 'log/test_output.log'
        irods_python_ci_utilities.subprocess_get_output(['sudo', 'su', '-', 'irods', '-c', 'python2 scripts/run_tests.py --xml_output --run_s=test_irods_resource_plugin_hpss 2>&1 | tee {0}; exit $PIPESTATUS'.format(test_output_file)], check_rc=True)
    finally:
        if output_root_directory:
            irods_python_ci_utilities.gather_files_satisfying_predicate('/var/lib/irods/log', output_root_directory, lambda x: True)
            shutil.copy('/var/lib/irods/log/test_output.log', output_root_directory)
            shutil.copytree('/var/lib/irods/test-reports', os.path.join(output_root_directory, 'test-reports'))


if __name__ == '__main__':
    main()
