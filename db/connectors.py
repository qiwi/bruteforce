from __future__ import unicode_literals

from db.exceptions import DbConnectException
from django.conf import settings
import logging

import pymssql
import cx_Oracle
import psycopg2


conn_loggers = logging.getLogger("connectors")


def get_user_data(host, db_type, **kwargs):
    connectors = {
        "postgres": PgConnector,
        "oracle": OracleConnector,
        "mssql": MssqlConnector,
    }
    connector = connectors.get(db_type)
    conn = connector(host, **kwargs)
    data = conn.get_user_auth_data()
    conn.close()
    return data


def connection_keeper(connect):
    def inner(self):
        from main.models import Database
        from datetime import datetime
        from pytz import timezone

        db = Database.objects.get(host=self._db_name)
        tz = timezone("Europe/Moscow")
        db.last_connect_ts = datetime.now(tz=tz)
        try:
            connect(self)
            db.is_connected = True
            db.save()
        except (DbConnectException, Exception) as e:
            db.is_connected = False
            db.save()
            raise e

    return inner


def pull_keeper(pull):
    def inner(self):
        from main.models import Database
        from datetime import datetime
        from pytz import timezone

        db = Database.objects.get(host=self._db_name)
        tz = timezone("Europe/Moscow")
        db.last_pull_ts = datetime.now(tz=tz)
        try:
            data = pull(self)
            db.is_pulled = True
            db.save()
        except (DbConnectException, Exception) as e:
            db.is_pulled = False
            db.save()
            raise e
        return data

    return inner


class DbConnector:
    def __init__(self, db_name, schema=False, autocommit=True, **kwargs):
        self._db_name = db_name
        self._schema = schema
        self._autocommit = autocommit
        self._logger = conn_loggers
        self._driver = None
        self._conn_params = None
        self._opt_conn_kwargs = {}

        self.db = None

    @connection_keeper
    def _connect(self):
        try:
            if isinstance(self._conn_params, str):
                self.db = self._driver.connect(
                    self._conn_params, **self._opt_conn_kwargs
                )
            else:
                self.db = self._driver.connect(
                    **self._conn_params, **self._opt_conn_kwargs
                )
        except Exception as e:
            self._logger.exception(e, exc_info=True)
            raise DbConnectException(f"Connection is not established")
        else:
            try:
                self.db.autocommit = self._autocommit
            except:
                pass
            if self._schema:
                self.db.current_schema = self._schema

    def close(self):
        self.db.close()


class DbReaderConnector(DbConnector):
    def get_user_auth_data(self):
        raise NotImplementedError

    def _execute_and_fetchall(self, sql):
        cur = self.db.cursor()
        cur.execute(sql)
        data = cur.fetchall()
        return data


class OracleConnector(DbReaderConnector):
    def __init__(self, db_name, schema=False, autocommit=True, dsn=None, **kwargs):
        super(OracleConnector, self).__init__(db_name, schema, autocommit, **kwargs)
        self._driver = cx_Oracle
        if db_name in settings.CUSTOM_CREDENTIALS:
            username = settings.CUSTOM_CREDENTIALS[db_name]["USERNAME"]
            password = settings.CUSTOM_CREDENTIALS[db_name]["PASSWORD"]
            dsn = settings.CUSTOM_CREDENTIALS[db_name]["DSN"]
        else:
            username = settings.CONN_CREDENTIALS["ORACLE"]["USERNAME"]
            password = settings.CONN_CREDENTIALS["ORACLE"]["PASSWORD"]
            if dsn is None:
                raise DbConnectException("DSN is None")
        self._conn_params = f"{username}/{password}@{dsn}"
        self._opt_conn_kwargs = {"threaded": True}
        self._connect()

    @pull_keeper
    def get_user_auth_data(self):
        try:
            sql = "SELECT version FROM PRODUCT_COMPONENT_VERSION WHERE product LIKE 'Oracle%'"
            version = self._execute_and_fetchall(sql)[0][0]
        except IndexError as e:
            conn_loggers.exception(e, exc_info=True)
            raise DbConnectException("Oracle version is not recognized")
        else:
            if version.startswith("10"):
                target_field = "password"
            else:
                target_field = "spare4"
            sql = f"SELECT name, {target_field}, '...' FROM sys.user$ WHERE {target_field} IS NOT NULL"
            data = self._execute_and_fetchall(sql)
            try:
                sql = f"SELECT username, account_status FROM dba_users"
                statuses = self._execute_and_fetchall(sql)
            except Exception as e:
                conn_loggers.exception(e, exc_info=True)
                raise DbConnectException(
                    f"Error with statuses from oracle db: {self._db_name}"
                )
            full_data = []
            for name, hash_, _ in data:
                status = None
                for username, account_status in statuses:
                    if username == name:
                        status = account_status
                        break
                full_data.append((name, hash_, str(status)))
            return full_data


class PgConnector(DbReaderConnector):
    def __init__(self, host, schema=False, autocommit=True, port=None, **kwargs):
        super(PgConnector, self).__init__(host, schema, autocommit, **kwargs)
        self._driver = psycopg2
        if not port:
            port = 5432
        if host in settings.CUSTOM_CREDENTIALS:
            username = settings.CUSTOM_CREDENTIALS[host]["USERNAME"]
            password = settings.CUSTOM_CREDENTIALS[host]["PASSWORD"]
        else:
            username = settings.CONN_CREDENTIALS["POSTGRES"]["USERNAME"]
            password = settings.CONN_CREDENTIALS["POSTGRES"]["PASSWORD"]
        self._conn_params = f"user={username} password={password} host={host} port={port} dbname=postgres"
        self._connect()

    @pull_keeper
    def get_user_auth_data(self):
        sql = "SELECT rolname, rolpassword, rolcanlogin FROM pg_authid WHERE rolpassword IS NOT NULL;"
        return self._execute_and_fetchall(sql)


class MssqlConnector(DbReaderConnector):
    def __init__(self, host, schema=False, autocommit=True, port=None, **kwargs):
        super(MssqlConnector, self).__init__(host, schema, autocommit, **kwargs)
        self._driver = pymssql
        if not port:
            port = 1433
        if host in settings.CUSTOM_CREDENTIALS:
            username = settings.CUSTOM_CREDENTIALS[host]["USERNAME"]
            password = settings.CUSTOM_CREDENTIALS[host]["PASSWORD"]
        else:
            username = settings.CONN_CREDENTIALS["MSSQL"]["USERNAME"]
            password = settings.CONN_CREDENTIALS["MSSQL"]["PASSWORD"]
        self._conn_params = {
            "database": "master",
            "user": username,
            "password": password,
            "host": host,
            "port": port,
        }
        self._connect()

    @pull_keeper
    def get_user_auth_data(self):
        sql = """
            DECLARE @ver nvarchar(128)
            set @ver = (select(CAST(serverproperty('ProductVersion') AS nvarchar)))
            SET @ver = SUBSTRING(@ver, 1, CHARINDEX('.', @ver) - 1)
            IF (@ver = 8)
            BEGIN
            select l.name, master.dbo.fn_VarBinToHexStr(x.password) as value, ''
            from master..syslogins l, master..sysxlogins x
            where l.sid=x.sid and x.password is not null
            UNION
            select name, '0x0100142FCF0A08943382239B9DDEA37F46600F1373225FCBDA3308943382239B9DDEA37F46600F1373225FCBDA33', ''
            from master..syslogins
            where password is null and isntname <> 1
            END
            ELSE
            BEGIN
            select name, master.dbo.fn_VarBinToHexStr(password_hash), case when is_disabled=1 then 'disabled' else 'active' end FROM master.sys.sql_logins
            END
        """
        return self._execute_and_fetchall(sql)
