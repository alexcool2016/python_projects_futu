#stock data refreshing from futu api
from futu import *
from app.dao.stockdb import *
from app.common.config import *

def refreshGoodStocks():
    #get good stocks from futu api
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    ret, data = quote_ctx.get_user_security('港股')
    if ret == RET_OK:
        dbmngr = DatabaseManager()
        dbmngr.check_database()
        #exeInsSQL = 'insert into good_stock_list (code, name, lot_size, stock_type, update_datetime) values('
        #for row in data:
        #    exeSQL = exeInsSQL + "'" + row['code'] + "', " + "'" + row['name'] + "', " + "'" + row['stock_type'] + "', datetime('now'))"
        #    print(exeSQL)
        data.to_sql('good_stocks', con=dbmngr.getConnection(), if_exists='replace')
        dbmngr.close_connection()
    else:
        print('error:', data)
    quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽

def refreshMyStocks():
    pwd_unlock = getTradePass()
    trd_ctx = OpenHKTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    trd_ctx.unlock_trade(pwd_unlock)
    ret, data = trd_ctx.position_list_query()
    if ret == RET_OK:
        dbmngr = DatabaseManager()
        dbmngr.check_database()
        data.to_sql('my_stocks', con=dbmngr.getConnection(), if_exists='replace')
        print(data)
        dbmngr.close_connection()
    else:
        print('error:', data)
    trd_ctx.close()

def refreshMyAccounts():
    trd_ctx = OpenHKTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    ret, data = trd_ctx.get_acc_list()
    if ret == RET_OK:
        dbmngr = DatabaseManager()
        dbmngr.check_database()
        data.to_sql('my_accounts', con=dbmngr.getConnection(), if_exists='replace')
        print(data)
        dbmngr.close_connection()
    else:
        print('error:', data)
    #print(trd_ctx.get_acc_list())
    trd_ctx.close()


def refreshMyUSStocks():
    pwd_unlock = getTradePass()
    trd_ctx = OpenUSTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    trd_ctx.unlock_trade(pwd_unlock)
    ret, data = trd_ctx.position_list_query()
    if ret == RET_OK:
        dbmngr = DatabaseManager()
        dbmngr.check_database()
        data.to_sql('my_us_stocks', con=dbmngr.getConnection(), if_exists='replace')
        print(data)
        dbmngr.close_connection()
    else:
        print('error:', data)
    trd_ctx.close()

def refreshMyUSAccounts():
    trd_ctx = OpenUSTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    ret, data = trd_ctx.get_acc_list()
    if ret == RET_OK:
        dbmngr = DatabaseManager()
        dbmngr.check_database()
        data.to_sql('my_us_accounts', con=dbmngr.getConnection(), if_exists='replace')
        print(data)
        dbmngr.close_connection()
    else:
        print('error:', data)
    #print(trd_ctx.get_acc_list())
    trd_ctx.close()