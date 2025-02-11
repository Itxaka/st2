# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from StringIO import StringIO
import unittest2

from mock import (call, patch, Mock, MagicMock)
import paramiko

from st2actions.runners.ssh.paramiko_ssh import ParamikoSSHClient
from st2tests.fixturesloader import get_resources_base_path
import st2tests.config as tests_config
tests_config.parse_args()


class ParamikoSSHClientTests(unittest2.TestCase):

    @patch('paramiko.SSHClient', Mock)
    def setUp(self):
        """
        Creates the object patching the actual connection.
        """
        conn_params = {'hostname': 'dummy.host.org',
                       'port': 8822,
                       'username': 'ubuntu',
                       'key': '~/.ssh/ubuntu_ssh',
                       'timeout': '600'}
        self.ssh_cli = ParamikoSSHClient(**conn_params)

    @patch('paramiko.SSHClient', Mock)
    def test_create_with_password(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'password': 'ubuntu'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'password': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)

    @patch('paramiko.SSHClient', Mock)
    def test_deprecated_key_argument(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key': 'id_rsa'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'key_filename': 'id_rsa',
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)

    def test_key_files_and_key_material_arguments_are_mutual_exclusive(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key_files': 'id_rsa',
                       'key_material': 'key'}

        expected_msg = ('key_files and key_material arguments are mutually '
                        'exclusive')
        self.assertRaisesRegexp(ValueError, expected_msg,
                                ParamikoSSHClient, **conn_params)

    @patch('paramiko.SSHClient', Mock)
    def test_key_material_argument(self):
        path = os.path.join(get_resources_base_path(),
                            'ssh', 'dummy_rsa')

        with open(path, 'r') as fp:
            private_key = fp.read()

        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key_material': private_key}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        pkey = paramiko.RSAKey.from_private_key(StringIO(private_key))
        expected_conn = {'username': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'pkey': pkey,
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)

    @patch('paramiko.SSHClient', Mock)
    def test_key_material_argument_invalid_key(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key_material': 'id_rsa'}

        mock = ParamikoSSHClient(**conn_params)

        expected_msg = 'Invalid or unsupported key type'
        self.assertRaisesRegexp(paramiko.ssh_exception.SSHException,
                                expected_msg, mock.connect)

    @patch('paramiko.SSHClient', Mock)
    def test_create_with_key(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'key_files': 'id_rsa'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'key_filename': 'id_rsa',
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)

    @patch('paramiko.SSHClient', Mock)
    def test_create_with_password_and_key(self):
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu',
                       'password': 'ubuntu',
                       'key': 'id_rsa'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'password': 'ubuntu',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'key_filename': 'id_rsa',
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)

    @patch('paramiko.SSHClient', Mock)
    def test_create_without_credentials(self):
        """
        Initialize object with no credentials.

        Just to have better coverage, initialize the object
        without 'password' neither 'key'.
        """
        conn_params = {'hostname': 'dummy.host.org',
                       'username': 'ubuntu'}
        mock = ParamikoSSHClient(**conn_params)
        mock.connect()

        expected_conn = {'username': 'ubuntu',
                         'hostname': 'dummy.host.org',
                         'allow_agent': True,
                         'look_for_keys': True,
                         'port': 22}
        mock.client.connect.assert_called_once_with(**expected_conn)

    @patch.object(ParamikoSSHClient, '_consume_stdout',
                  MagicMock(return_value=StringIO('')))
    @patch.object(ParamikoSSHClient, '_consume_stderr',
                  MagicMock(return_value=StringIO('')))
    @patch.object(os.path, 'exists', MagicMock(return_value=True))
    @patch.object(os, 'stat', MagicMock(return_value=None))
    def test_basic_usage_absolute_path(self):
        """
        Basic execution.
        """
        mock = self.ssh_cli
        # script to execute
        sd = "/root/random_script.sh"

        # Connect behavior
        mock.connect()
        mock_cli = mock.client  # The actual mocked object: SSHClient
        expected_conn = {'username': 'ubuntu',
                         'key_filename': '~/.ssh/ubuntu_ssh',
                         'allow_agent': False,
                         'hostname': 'dummy.host.org',
                         'look_for_keys': False,
                         'timeout': '600',
                         'port': 8822}
        mock_cli.connect.assert_called_once_with(**expected_conn)

        mock.put(sd, sd, mirror_local_mode=False)
        mock_cli.open_sftp().put.assert_called_once_with(sd, sd)

        mock.run(sd)

        # Make assertions over 'run' method
        mock_cli.get_transport().open_session().exec_command \
                .assert_called_once_with(sd)

        mock.close()

    def test_delete_script(self):
        """
        Provide a basic test with 'delete' action.
        """
        mock = self.ssh_cli
        # script to execute
        sd = '/root/random_script.sh'

        mock.connect()

        mock.delete_file(sd)
        # Make assertions over the 'delete' method
        mock.client.open_sftp().unlink.assert_called_with(sd)

        mock.close()

    @patch.object(ParamikoSSHClient, 'exists', return_value=False)
    def test_put_dir(self, *args):
        mock = self.ssh_cli
        mock.connect()

        local_dir = os.path.join(get_resources_base_path(), 'packs')
        mock.put_dir(local_path=local_dir, remote_path='/tmp')

        mock_cli = mock.client  # The actual mocked object: SSHClient

        # Assert that expected dirs are created on remote box.
        calls = [call('/tmp/packs/pythonactions'), call('/tmp/packs/pythonactions/actions')]
        mock_cli.open_sftp().mkdir.assert_has_calls(calls, any_order=True)

        # Assert that expected files are copied to remote box.
        local_file = os.path.join(get_resources_base_path(),
                                  'packs/pythonactions/actions/pascal_row.py')
        remote_file = os.path.join('/tmp', 'packs/pythonactions/actions/pascal_row.py')

        calls = [call(local_file, remote_file)]
        mock_cli.open_sftp().put.assert_has_calls(calls, any_order=True)
