import pymysql
print('pymysql imported', pymysql.__version__)
try:
    conn = pymysql.connect(host='127.0.0.1', port=33060, user='root', password='Dharsan@07', autocommit=True)
    print('CONNECTION_OK')
    conn.close()
except Exception as e:
    import traceback
    traceback.print_exc()
    print('CONNECTION_FAIL', repr(e))
