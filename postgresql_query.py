#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright © 2017-2018 Mohamed El Morabity
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <http://www.gnu.org/licenses/>.


import datetime
from decimal import Decimal

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.parsing.convert_bool import BOOLEANS
import ansible.module_utils.postgres as postgres_utils


DOCUMENTATION = '''
---
module: postgresql_query
author: Mohamed El Morabity
short_description: Run a SQL query on a PostgreSQL database.
description:
  - Run a SQL query on a PostgreSQL database.
options:
  login_user:
    description:
      - The username used to authenticate with.
    required: false
    default: postgres
  login_password:
    description:
      - The password used to authenticate with.
    required: false
    default: null
  login_host:
    description:
      - Host running the database.
    required: false
    default: null
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
    required: false
    default: null
  port:
    description:
      - Database port to connect to.
    type: int
    required: false
    default: 5432
  db:
    description:
      - Name of database.
    required: false
    default: null
  query:
    description:
      - SQL query to run.
    required: True
  as_dict:
    description:
      - if true, return results as a list of dictionaries.
    type: bool
    required: false
    default: false
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
      - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
      - Default of prefer matches libpq default.
    required: false
    default: prefer
    choices: [disable, allow, prefer, require, verify-ca, verify-full]
  ssl_rootcert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA) certificate(s).
      - If the file exists, the server's certificate will be verified to be signed by one of these authorities.
    required: false
    default: null
notes:
- The default authentication assumes that you are either logging in as or sudo'ing to the postgres account on the host.
- This module uses psycopg2, a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on
  the host before using this module. If the remote host is the PostgreSQL server which is the default case, then
  PostgreSQL must also be installed on the remote host.
- The ssl_rootcert parameter requires at least Postgres version 8.4 and psycopg2 version 2.4.3.

requirements: ['psycopg2']
'''

EXAMPLES = '''
# Run SQL query
- local_action:
    module: postgresql_query
    db: mydatabase
    query: SELECT * from myschema.mytable
'''


try:
    import psycopg2
    from psycopg2.extras import DictCursor, RealDictCursor

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


# http://initd.org/psycopg/docs/usage.html#adaptation-of-python-values-to-sql-types
def _json_serialize(obj):
    if isinstance(obj, (datetime.date, datetime.datetime, datetime.time, datetime.timedelta)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (list, tuple)):
        return map(_json_serialize, obj)
    if isinstance(obj, dict):
        return dict([(key, _json_serialize(value)) for key, value in obj.items()])
    # Primitive types
    if not hasattr(obj, '__dict__'):
        return obj
    return str(obj)


def main():
    """Main execution path."""

    argument_spec = postgres_utils.postgres_common_argument_spec()
    argument_spec.update({'db': {'type': 'str', 'default': ''},
                          'query': {'required': True, 'type': 'str'},
                          'as_dict': {'type': 'bool', 'choices': BOOLEANS, 'default': False}})
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_LIB:
        module.fail_json(msg='psycopg2 is required for this module')

    psycopg_connect_map = {
        'login_host': 'host',
        'port': 'port',
        'login_user': 'user',
        'login_password': 'password',
        'ssl_mode': 'sslmode',
        'ssl_rootcert': 'sslrootcert',
        'db': 'dbname'
    }

    # Taken from postgresql_db module
    psycopg_connect_args = dict(
        (psycopg_connect_map[k], v) for (k, v) in module.params.iteritems()
        if k in psycopg_connect_map and v is not None and v != ''
    )
    if ('host' not in psycopg_connect_args or psycopg_connect_args['host'] == 'localhost') and \
       module.params['login_unix_socket'] != '':
        psycopg_connect_args['host'] = module.params['login_unix_socket']

    try:
        postgres_utils.ensure_libs(sslrootcert=module.params.get('ssl_rootcert'))
        db_connection = psycopg2.connect(**psycopg_connect_args)
        if module.params['as_dict']:
            cursor_factory = RealDictCursor
        else:
            cursor_factory = DictCursor
        cursor = db_connection.cursor(cursor_factory=cursor_factory)
    except TypeError as ex:
        if 'sslrootcert' in ex.args[0]:
            module.fail_json(
                msg='Postgresql server must be at least version 8.4 to support sslrootcert'
            )
        module.fail_json(msg='Unable to connect to database: {}'.format(ex))
    except (postgres_utils.LibraryError, psycopg2.Error) as ex:
        module.fail_json(msg='Unable to connect to database: {}'.format(ex))

    try:
        cursor.execute(module.params['query'])
        db_connection.commit()
        result = None
        if cursor.description is not None:
            result = _json_serialize(cursor.fetchall())
        statusmessage = cursor.statusmessage
        changed = cursor.rowcount != 0
        cursor.close()
    except psycopg2.Error as ex:
        module.fail_json(msg='Unable to execute query: {}'.format(ex), errno=ex.pgcode)
    finally:
        if db_connection is not None:
            db_connection.close()

    module.exit_json(changed=changed, result=result, statusmessage=statusmessage)


if __name__ == '__main__':
    main()
