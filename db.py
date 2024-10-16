import pymysql

def get_db_connection():
    """Establishes and returns a connection to the database."""
    return pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='',
        db='duetracker',
        cursorclass=pymysql.cursors.DictCursor
    )

def iud(qry, val):
    """Executes an INSERT, UPDATE, or DELETE query."""
    con = get_db_connection()
    with con.cursor() as cmd:
        cmd.execute(qry, val)
        id = cmd.lastrowid
        con.commit()
    con.close()
    return id

def selectone(qry, val):
    """Executes a SELECT query that returns a single result."""
    con = get_db_connection()
    with con.cursor() as cmd:
        cmd.execute(qry, val)
        res = cmd.fetchone()
    con.close()
    return res

def selectall(qry):
    """Executes a SELECT query that returns multiple results."""
    con = get_db_connection()
    with con.cursor() as cmd:
        cmd.execute(qry)
        res = cmd.fetchall()
    con.close()
    return res

def selectall2(qry, val):
    """Executes a SELECT query with parameters that returns multiple results."""
    con = get_db_connection()
    with con.cursor() as cmd:
        cmd.execute(qry, val)
        res = cmd.fetchall()
    con.close()
    return res
