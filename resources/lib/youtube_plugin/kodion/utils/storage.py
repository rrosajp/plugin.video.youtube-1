# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtube)
    Copyright (C) 2016-2019 plugin.video.youtube

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only for more information.
"""

from six import PY2
from six.moves import range
# noinspection PyPep8Naming
from six.moves import cPickle as pickle

import datetime
import os
import sqlite3
import time
import traceback

from .. import logger


class Storage(object):
    def __init__(self, filename, max_item_count=0, max_file_size_kb=-1):
        self._table_name = 'storage'
        self._filename = filename
        if not self._filename.endswith('.sqlite'):
            self._filename = ''.join([self._filename, '.sqlite'])
        self._file = None
        self._cursor = None
        self._max_item_count = max_item_count
        self._max_file_size_kb = max_file_size_kb

        self._table_created = False
        self._needs_commit = False

    def set_max_item_count(self, max_item_count):
        self._max_item_count = max_item_count

    def set_max_file_size_kb(self, max_file_size_kb):
        self._max_file_size_kb = max_file_size_kb

    def __del__(self):
        self._close()

    def _open(self):
        if self._file is None:
            self._optimize_file_size()

            path = os.path.dirname(self._filename)
            if not os.path.exists(path):
                os.makedirs(path)

            self._file = sqlite3.connect(self._filename, check_same_thread=False,
                                         detect_types=0, timeout=1)

            self._file.isolation_level = None
            self._cursor = self._file.cursor()
            self._cursor.execute('PRAGMA journal_mode=MEMORY')
            self._cursor.execute('PRAGMA busy_timeout=20000')
            # self._cursor.execute('PRAGMA synchronous=OFF')
            self._create_table()

    def _execute(self, needs_commit, query, values=None):
        if values is None:
            values = []
        if not self._needs_commit and needs_commit:
            self._needs_commit = True
            self._cursor.execute('BEGIN')

        """
        Tests revealed that sqlite has problems to release the database in time. This happens no so often, but just to
        be sure, we try at least 3 times to execute out statement.
        """
        for _ in range(3):
            try:
                return self._cursor.execute(query, values)
            except TypeError:
                return None
        return None

    def _close(self):
        if self._file is not None:
            self.sync()
            self._file.commit()
            self._cursor.close()
            self._cursor = None
            self._file.close()
            self._file = None

    def _optimize_file_size(self):
        # do nothing - only we have given a size
        if self._max_file_size_kb <= 0:
            return

        # do nothing - only if this folder exists
        path = os.path.dirname(self._filename)
        if not os.path.exists(path):
            return

        if not os.path.exists(self._filename):
            return

        try:
            file_size_kb = (os.path.getsize(self._filename) // 1024)
            if file_size_kb >= self._max_file_size_kb:
                os.remove(self._filename)
        except OSError:
            pass

    def _create_table(self):
        self._open()
        if not self._table_created:
            query = f'CREATE TABLE IF NOT EXISTS {self._table_name} (key TEXT PRIMARY KEY, time TIMESTAMP, value BLOB)'

            self._execute(True, query)
            self._table_created = True

    def sync(self):
        if self._cursor is not None and self._needs_commit:
            self._needs_commit = False
            return self._execute(False, 'COMMIT')

    def _set(self, item_id, item):
        def _encode(obj):
            return sqlite3.Binary(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))

        if self._max_file_size_kb < 1 and self._max_item_count < 1:
            self._optimize_item_count()
        else:
            self._open()
            now = datetime.datetime.now() + datetime.timedelta(microseconds=1)  # add 1 microsecond, required for dbapi2
            query = f'REPLACE INTO {self._table_name} (key,time,value) VALUES(?,?,?)'
            self._execute(True, query, values=[item_id, now, _encode(item)])
            self._close()
            self._optimize_item_count()

    def _optimize_item_count(self):
        if self._max_item_count < 1:
            if not self._is_empty():
                self._clear()
        else:
            self._open()
            query = 'SELECT key FROM %s ORDER BY time DESC LIMIT -1 OFFSET %d' % (self._table_name, self._max_item_count)
            result = self._execute(False, query)
            if result is not None:
                for item in result:
                    self._remove(item[0])
            self._close()

    def _clear(self):
        self._open()
        query = f'DELETE FROM {self._table_name}'
        self._execute(True, query)
        self._create_table()
        self._close()
        self._open()
        self._execute(False, 'VACUUM')
        self._close()

    def _is_empty(self):
        self._open()
        query = f'SELECT exists(SELECT 1 FROM {self._table_name} LIMIT 1);'
        result = self._execute(False, query)
        is_empty = True
        if result is not None:
            for item in result:
                is_empty = item[0] == 0
                break
        self._close()
        return is_empty

    def _get_ids(self, oldest_first=True):
        self._open()
        # self.sync()
        query = f'SELECT key FROM {self._table_name}'
        if oldest_first:
            query = f'{query} ORDER BY time ASC'
        else:
            query = f'{query} ORDER BY time DESC'

        query_result = self._execute(False, query)

        result = []
        if query_result:
            result.extend(item[0] for item in query_result)
        self._close()
        return result

    def _get(self, item_id):
        def _decode(obj):
            return pickle.loads(str(obj)) if PY2 else pickle.loads(obj, encoding='utf-8')

        self._open()
        query = f'SELECT time, value FROM {self._table_name} WHERE key=?'
        result = self._execute(False, query, [item_id])
        if result is None:
            self._close()
            return None

        item = result.fetchone()
        if item is None:
            self._close()
            return None

        self._close()
        return _decode(item[1]), item[0]

    def _remove(self, item_id):
        self._open()
        query = f'DELETE FROM {self._table_name} WHERE key = ?'
        self._execute(True, query, [item_id])

    @staticmethod
    def strptime(stamp, stamp_fmt):
        # noinspection PyUnresolvedReferences
        import _strptime
        try:
            time.strptime('01 01 2012', '%d %m %Y')  # dummy call
        except:
            pass
        return time.strptime(stamp, stamp_fmt)

    def get_seconds_diff(self, current_stamp):
        stamp_format = '%Y-%m-%d %H:%M:%S.%f'
        current_datetime = datetime.datetime.now()
        if not current_stamp:
            return 86400  # 24 hrs
        try:
            stamp_datetime = datetime.datetime(
                *self.strptime(current_stamp, stamp_format)[:6]
            )

        except ValueError:  # current_stamp has no microseconds
            stamp_format = '%Y-%m-%d %H:%M:%S'
            stamp_datetime = datetime.datetime(
                *self.strptime(current_stamp, stamp_format)[:6]
            )

        except TypeError:
            logger.log_error('Exception while calculating timestamp difference: '
                             'current_stamp |{cs}|{cst}| stamp_format |{sf}|{sft}| \n{tb}'
                             .format(cs=current_stamp, cst=type(current_stamp),
                                     sf=stamp_format, sft=type(stamp_format),
                                     tb=traceback.print_exc())
                             )
            return 604800  # one week

        return (
            ((time_delta.seconds + time_delta.days * 24 * 3600) * 10**6)
            // (10**6)
            if (time_delta := current_datetime - stamp_datetime)
            else 0
        )
