# postgresql_query

Run a SQL query on a PostgreSQL database.

## Synopsis

Run a SQL query on a PostgreSQL database.

## Requirements

The below requirements are needed on the host that executes this module.

* psycopg2

## Options

| parameter         | required | default  | choices                                                                                                      | comments                                                                                                                                                                                                                                                   |
| ----------------- | -------- | -------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ssl_rootcert      | no       |          |                                                                                                              | Specifies the name of a file containing SSL certificate authority (CA) certificate(s). If the file exists, the server's certificate will be verified to be signed by one of these authorities.                                                             |
| ssl_mode          | no       | prefer   | <ul><li>disable</li><li>allow</li><li>prefer</li><li>require</li><li>verify-ca</li><li>verify-full</li></ul> | Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.  See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes. Default of prefer matches libpq default. |
| login_user        | no       | postgres |                                                                                                              | The username used to authenticate with.                                                                                                                                                                                                                    |
| login_host        | no       |          |                                                                                                              | Host running the database.                                                                                                                                                                                                                                 |
| as_dict           | no       | False    |                                                                                                              | If true, return results as a list of dictionaries.                                                                                                                                                                                                         |
| db                | no       |          |                                                                                                              | Name of database.                                                                                                                                                                                                                                          |
| login_unix_socket | no       |          |                                                                                                              | Path to a Unix domain socket for local connections.                                                                                                                                                                                                        |
| login_password    | no       |          |                                                                                                              | The password used to authenticate with.                                                                                                                                                                                                                    |
| query             | yes      |          |                                                                                                              | SQL query to run.                                                                                                                                                                                                                                          |
| port              | no       | 5432     |                                                                                                              | Database port to connect to.                                                                                                                                                                                                                               |

## Examples

```
# Run SQL query
- local_action:
    module: postgresql_query
    db: mydatabase
    query: SELECT * from myschema.mytable
```

## Notes

* The default authentication assumes that you are either logging in as or sudo'ing to the postgres account on the host.
* This module uses psycopg2, a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL must also be installed on the remote host.
* The ssl_rootcert parameter requires at least Postgres version 8.4 and psycopg2 version 2.4.3.
