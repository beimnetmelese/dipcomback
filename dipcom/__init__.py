import pymysql

# Django 5.2+ checks MySQLdb client version and expects >= 2.2.1.
# When using PyMySQL as a drop-in replacement, expose compatible version
# metadata before install_as_MySQLdb() so startup and migrations work.
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"

pymysql.install_as_MySQLdb()
