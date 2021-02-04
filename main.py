# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from datetime import *
from futu import *
from app.dao.stockdb import *
from app.common.config import *
from app.dao.stockdata import *
from app.winmoney.daytrade01 import *
from app.common.email import *


# test procedures
def test_quote():
    # test code to get quote via FUTU API
    # OpenQuoteContext, get_market_snapshot, close quote
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())  # 创建行情对象
    print(quote_ctx.get_market_snapshot('HK.00700'))  # 获取港股 HK.00700 的快照数据
    quote_ctx.close()  # 关闭对象，防止连接条数用尽

def my_subscription():
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())  # 创建行情对象
    ret, data = quote_ctx.query_subscription()
    if ret == RET_OK:
        print(data)
    else:
        print('error:', data)
    quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽

def trade_account_info():
    trd_ctx = OpenHKTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    print(trd_ctx.get_acc_list())
    trd_ctx.close()

def check_trade_account_balance():
    pwd_unlock = getTradePass()
    trd_ctx = OpenHKTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    trd_ctx.unlock_trade(pwd_unlock)
    print(trd_ctx.accinfo_query())
    trd_ctx.close()

def get_my_love_security(p_sec_group):
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    ret, data = quote_ctx.get_user_security(p_sec_group)
    if ret == RET_OK:
        print(data)
        print(data['code'][0])  # 取第一条的股票代码
        print(data['code'].values.tolist())  # 转为list
    else:
        print('error:', data)
    quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽

def get_my_love_security_groups():
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    ret, data = quote_ctx.get_user_security_group(group_type=UserSecurityGroupType.ALL)
    if ret == RET_OK:
        print(data)
    else:
        print('error:', data)
    quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽

def filter_stocks_example01():
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())

    # 可以選擇SimpleFilter, AccumulateFilter, FinancialFilter, 此處AccumulateFilter是累積過濾
    accumulate_filter = AccumulateFilter()
    accumulate_filter.stock_field = StockField.AMPLITUDE  # 選擇相應Stock Field， AMPLITUDE是振幅
    accumulate_filter.filter_min = 30  # 記得調整相應數字
    accumulate_filter.filter_max = 31  # 記得調整相應數字
    accumulate_filter.days = 5  # 累計天數
    accumulate_filter.is_no_filter = False
    accumulate_filter.sort = SortDir.ASCEND
    ret, ls = quote_ctx.get_stock_filter(Market.HK, [accumulate_filter])  # 对香港市场的股票做简单筛选

    Our_stock_list = []  # 名字能夠自己更改

    if ret == RET_OK:
        last_page, all_count, stock_list = ls
        print(len(stock_list), stock_list)
        for item in stock_list:
            Our_stock_list.append(item.stock_code)
            print(item.stock_code, item.stock_name)
    else:
        print('error: ', ls)

    quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽

def getstockrealtimedata(code):
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    ret_sub, err_message = quote_ctx.subscribe([code], [SubType.RT_DATA], subscribe_push=False)
    # 先订阅分时数据类型。订阅成功后FutuOpenD将持续收到服务器的推送，False代表暂时不需要推送给脚本
    if ret_sub == RET_OK:  # 订阅成功
        ret, data = quote_ctx.get_rt_data(code)  # 获取一次分时数据
        if ret == RET_OK:
            # print(data)
            score = -1
            last_price = 0
            first_price = 0
            ## get last 11 records to calculate the score
            for item in data['cur_price'].tail(90):
                print(item)
                if score >= 0:
                    if item > last_price:
                        score = score + 1
                    elif item < last_price:
                        score = score - 1

                    last_price = item
                else:
                    score = 0
                    last_price = item
                    first_price = item
            print(score)
            print(first_price, last_price)
        else:
            print('error:', data)
    else:
        print('subscription failed', err_message)
    quote_ctx.close()  # 关闭当条连接，FutuOpenD会在1分钟后自动取消相应股票相应类型的订阅

def getaskbiddata(code):
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    ret_sub = quote_ctx.subscribe([code], [SubType.ORDER_BOOK], subscribe_push=False)[0]
    # 先订阅买卖摆盘类型。订阅成功后 OpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
    if ret_sub == RET_OK:  # 订阅成功
        ret, data = quote_ctx.get_order_book(code, num=10)  # 获取一次 3 档实时摆盘数据
        if ret == RET_OK:
            #print(data)
            totalask = 0
            totalbid = 0
            for item in data['Ask']:
                totalask = totalask + item[1]
            for item in data['Bid']:
                totalbid = totalbid + item[1]
            print(totalask, totalbid)
        else:
            print('error:', data)
    else:
        print('subscription failed')
    quote_ctx.close()  # 关闭当条连接，OpenD 会在 1 分钟后自动取消相应股票相应类型的订阅

def emailtraderecords():
    traderecs = ""
    dbmngr = DatabaseManager()
    dbmngr.check_database()
    cursor = dbmngr.querySQL("select * from curr_stock where buy_time >= date('now', 'localtime') order by buy_time")
    for row in cursor:
        traderecs = traderecs + row[0] + ': ' + '\n' + '    BUY: ' + str(row[1]) + '@' + str(row[2]) + ', ' + str(row[3])
        traderecs = traderecs  + '\n' + '   SELL: ' + str(row[4]) + '@' + str(row[5]) + ', ' + str(row[6]) + '\n'

    cursor = dbmngr.querySQL("SELECT DATE(buy_time), COUNT (*), SUM (sell_price*sell_qty-buy_price*buy_qty) FROM curr_stock WHERE buy_time >= date('now', 'localtime') GROUP  BY DATE ([buy_time])")
    for row in cursor:
        traderecs = traderecs + '\n' + 'GP = ' + str(row[2]) + ', total trade times: ' + str(row[1]) + '\n'

    dbmngr.close_connection()
    sendEmail('Daily Trading Records [' + str(date.today()) + ']', traderecs)

# test procedures end

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Main Start...', datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))
    ####futu api testing####
    #test_quote()
    #my_subscription()
    #trade_account_info()
    #check_trade_account_balance()
    #get_my_love_security('港股')
    #get_my_love_security_groups()

    ####db tesitng#####
    #dbmngr = DatabaseManager()
    #dbmngr.check_database()
    #dbmngr.executeSQL("insert into any_logs(log_text, log_time, log_reason) values('test insert sql', datetime('now'), 0) ")
    #cursor = dbmngr.querySQL("select * from any_logs order by log_id")
    #for row in cursor:
    #    print('LOG_ID=', row[0])
    #    print('LOG_TEXT=', row[1])
    #    print('LOG_DATETIME=', row[2])
    #    print('LOG_REASON=', row[3])
    #dbmngr.close_connection()

    #stock data refreshing
    #refreshGoodStocks()
    #refreshMyStocks()
    #refreshMyAccounts()
    #refreshMyUSStocks()
    #refreshMyUSAccounts()

    #stock analysis
    #filter_stocks_example01()
    #getstockrealtimedata('HK.03800')
    #getaskbiddata('HK.00700')

    #trade
    #getmaxbuyqty('HK.07200', 1)
    #getstockquote('HK.02500')
    #buystock('HK.07200')
    #runbuy()
    #print(haveStock())
    #print(haveStockDB())
    #daytrade01_start()
    #writelog('buy log local time')
    #dbplacebuyorder('HK.03800', 2.4, 800)
    #sellstock('HK.03800', 800)
    #runsell()
    #print(isasklargerthanbid('HK.07200'))
    #print(isincreasing('HK.07200'))


    daytrade01_start()

    #sendEmail('test from alex python program', 'Hello Alex! I''m from a python program.')
    emailtraderecords()


    print('Main End', datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))


