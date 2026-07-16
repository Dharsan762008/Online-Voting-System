import pymysql
print('pymysql version:', pymysql.__version__)
conn = pymysql.connect(host='127.0.0.1', port=33060, user='root', password='Dharsan@07', autocommit=True)
print('conn ok', conn)
conn.close()
