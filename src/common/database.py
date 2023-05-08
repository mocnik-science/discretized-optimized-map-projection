import sqlite3
import traceback

class Like:
  def __init__(self, string):
    self.__string = string

  def __str__(self):
    return self.__string

class Database:
  def __init__(self, filename):
    self.__filename = filename

  def __enter__(self):
    if not self.__filename:
      return None
    else:
      self.__connection = sqlite3.connect(self.__filename)
      return self

  def cursor(self):
    return self.__connection.cursor()

  def commit(self):
    self.__connection.commit()

  @staticmethod
  def __escape(string):
    return string.replace('\'', '\'\'')

  @staticmethod
  def __keyValue(data):
    return ' AND '.join([f"{key} LIKE '{Database.__escape(str(value))}'" if isinstance(value, Like) else f"{key} = '{Database.__escape(value)}'" for key, value in data.items()])

  @staticmethod
  def like(string):
    return Like(string)

  def insert(self, table, data, ignoreIfExists=False, ifNotExists=None):
    if not data:
      raise Exception('No data provided')
    try:
      if ifNotExists and self.exists(table, ifNotExists):
        return
      self.cursor().execute(f'''
        INSERT{' OR IGNORE' if ignoreIfExists else ''} INTO {table} (
          '{"', '".join(data.keys())}'
        ) VALUES (
          '{"', '".join([Database.__escape(str(value)) for value in data.values()])}'
        );
      ''')
    except Exception as e:
      traceback.print_exc()
      raise e

  def delete(self, table, where):
    try:
      self.cursor().execute(f'''
        DELETE FROM {table} WHERE {Database.__keyValue(where)};
      ''')
    except Exception as e:
      traceback.print_exc()
      raise e

  def exists(self, table, where):
    return self.cursor().execute(f'''
      SELECT COUNT(*) AS count FROM {table} WHERE {Database.__keyValue(where)};
    ''').fetchone()[0]

  def select(self, table, columns, where):
    return self.cursor().execute(f'''
      SELECT {", ".join(columns)} FROM {table} WHERE {Database.__keyValue(where)};
    ''').fetchall()

  def __exit__(self, *args):
    self.__connection.close()
