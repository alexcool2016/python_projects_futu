#即日鮮策略01
# 总控：
#### 操作时间：交易日上午9:30至11:50
#### 每1分钟进行一次策略运算 （每天共140次运算，前10次运算仅进行数据积累，即9:40后才会真正可能进行交易）
#### 单股操作：Check the stock list （持仓）：
######### If have no stock in stock list: 执行 Buy 策略
######### else: 执行 Sell 策略

## 1) Buy 策略
### 1. if has NO stock in stock list and current time < 11:10 AM, then loop the good stock list
####### 1.1 check past 5 mins, check increasing:
####### 每分钟1个报价点，如果其中1点比前点价格高，得1分，反之得-1分，如果总和>=3，则判定在上升
############### if increaseing, check the 10 buy bids > 10 sell bids: 10笔买单总手数 比 10笔卖单总手数 > 20%以上
###################### if yes, then take buy action


## 2) Sell 策略
### 2. loop the stock list 持仓
####### 2.1 No.1 rule, if it's 11:50 AM, sell all
####### 2.2 No.2 rule, if the current price lower 98% buy price, sell all
####### 2.3 No.3 rule, if the current_price higher 105% buy price, sell all
####### 2.4 No.4 rule, check the 10 buy bids < 10 sell bids: 10笔买单总手数 比 10笔卖单总手数 < 50%以上, sell all

from datetime import *
from futu import *
from app.common.config import *
from app.dao.stockdb import *

#configures
class daytradeConfigures(object):
    START_TRADE_HOUR = 9
    END_TRADE_HOUR = 15
    LAST_BUY_MINUTES = 10
    LAST_SELL_MINUTES = 50
    CHECK_LAST_PRICE_COUNT = 6
    CHECK_PRICE_SCORE = 3
    BUY_BID_COUNT = 10
    BUY_OVER_BID_PERCENTAGE = 2
    BID_OVER_BUY_PERCENTAGE = 0.5
    STOP_LOST = 0.98
    STOP_WIN = 1.05

def writelog(msg):
    dbmngr = DatabaseManager()
    dbmngr.check_database()
    dbmngr.executeSQL("insert into any_logs(log_text, log_time, log_reason) values('"
                      + msg + "', datetime('now', 'localtime'), 0) ")
    dbmngr.close_connection()

##### for trail run
def dbplacebuyorder(code, price, qty):
    dbmngr = DatabaseManager()
    dbmngr.check_database()
    print(code, price, qty)
    dbmngr.executeSQL("insert into curr_stock(stock_code, buy_price, buy_qty, buy_time) values('"
                      + code + "', " + str(price) + ", " + str(qty) + ", datetime('now', 'localtime')) ")
    dbmngr.close_connection()

##### for trail run
def dbloopstockinpos():
    retrows = []
    dbmngr = DatabaseManager()
    dbmngr.check_database()
    cursor = dbmngr.querySQL("select * from curr_stock where sell_time is null")
    for row in cursor:
        retrows.append(row)
    dbmngr.close_connection()
    return retrows

##### for trail run
def dbplacesellorder(code, price, qty, rule):
    dbmngr = DatabaseManager()
    dbmngr.check_database()
    print(code, price, qty)
    dbmngr.executeSQL("update curr_stock set sell_price = " + str(price) + ", sell_qty = " + str(qty) + ", "
                      + "sell_time = datetime('now', 'localtime'), rule = '" + rule
                      + "' where stock_code = '" + code + "' and sell_time is null")
    dbmngr.close_connection()

#檢查持倉及有否未完成訂單
def haveStock():
    rethave = True
    pwd_unlock = getTradePass()
    trd_ctx = OpenHKTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    trd_ctx.unlock_trade(pwd_unlock)
    ret, data = trd_ctx.position_list_query()
    stockcnt = data['code'].count()
    if ret == RET_OK:
        if stockcnt <= 0:
            rethave = False
    else:
        print('error:', data)
    trd_ctx.close()
    return rethave

# only for trail run
def haveStockDB():
    retHave = False
    dbmngr = DatabaseManager()
    dbmngr.check_database()
    cursor = dbmngr.querySQL("select count(*) from curr_stock where sell_time is null")
    for row in cursor:
        if row[0] > 0:
            retHave = True
    dbmngr.close_connection()
    return retHave

def isincreasing(code):
    retresult = False
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        ret_sub, err_message = quote_ctx.subscribe([code], [SubType.RT_DATA], subscribe_push=False)
        # 先订阅分时数据类型。订阅成功后FutuOpenD将持续收到服务器的推送，False代表暂时不需要推送给脚本
        if ret_sub == RET_OK:  # 订阅成功
            ret, data = quote_ctx.get_rt_data(code)  # 获取一次分时数据
            if ret == RET_OK:
                # print(data)
                score = -1
                isFirstrow = True
                last_price = 0
                first_price = 0
                ## get last 11 records to calculate the score
                for item in data['cur_price'].tail(daytradeConfigures.CHECK_LAST_PRICE_COUNT):  # check last prices configure
                    #print(item)
                    if item > last_price:
                        score = score + 1
                    elif item < last_price:
                        score = score - 1

                    if isFirstrow:
                        last_price = item
                        first_price = item
                        isFirstrow = False
                    else:
                        last_price = item

                print(code, score, first_price, last_price)
                retresult = (score >= daytradeConfigures.CHECK_PRICE_SCORE and last_price > first_price) ## score configure
            else:
                print('error:', data)
        else:
            print('subscription failed', err_message)
    finally:
        quote_ctx.close()  # 关闭当条连接，FutuOpenD会在1分钟后自动取消相应股票相应类型的订阅
    return retresult

def isasklargerthanbid(code):
    retres = False
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        ret_sub = quote_ctx.subscribe([code], [SubType.ORDER_BOOK], subscribe_push=False)[0]
        # 先订阅买卖摆盘类型。订阅成功后 OpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
        if ret_sub == RET_OK:  # 订阅成功
            ret, data = quote_ctx.get_order_book(code, num=daytradeConfigures.BUY_BID_COUNT)  # 获取一次 10 档实时摆盘数据, book order configure
            if ret == RET_OK:
                #print(data)
                totalask = 0
                totalbid = 0
                for item in data['Ask']:
                    totalask = totalask + item[1]
                for item in data['Bid']:
                    totalbid = totalbid + item[1]
                print(totalask, totalbid)
                if (totalbid > 0) and ((totalask - totalbid)/totalbid > daytradeConfigures.BUY_OVER_BID_PERCENTAGE):
                    # 10笔买单总手数 比 10笔卖单总手数 > 20%以上, ask bid percentage configure
                    print('ask vol is larger than bid vol:', (totalask - totalbid)/totalbid)
                    retres = True
            else:
                print('error:', data)
        else:
            print('subscription failed')
    finally:
        quote_ctx.close()  # 关闭当条连接，OpenD 会在 1 分钟后自动取消相应股票相应类型的订阅

    return retres

def isbidlargerthanask(code):
    retres = False
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        ret_sub = quote_ctx.subscribe([code], [SubType.ORDER_BOOK], subscribe_push=False)[0]
        # 先订阅买卖摆盘类型。订阅成功后 OpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
        if ret_sub == RET_OK:  # 订阅成功
            ret, data = quote_ctx.get_order_book(code, num=daytradeConfigures.BUY_BID_COUNT)  # 获取一次 10 档实时摆盘数据, book order configure
            if ret == RET_OK:
                #print(data)
                totalask = 0
                totalbid = 0
                for item in data['Ask']:
                    totalask = totalask + item[1]
                for item in data['Bid']:
                    totalbid = totalbid + item[1]
                print(totalask, totalbid)
                if (totalask > 0) and ((totalbid - totalask)/totalask > daytradeConfigures.BID_OVER_BUY_PERCENTAGE):
                    # 10笔买单总手数 比 10笔卖单总手数 > 20%以上, ask bid percentage configure
                    print('bid vol is larger than ask vol:', (totalbid - totalask)/totalask)
                    retres = True
            else:
                print('error:', data)
        else:
            print('subscription failed')
    finally:
        quote_ctx.close()  # 关闭当条连接，OpenD 会在 1 分钟后自动取消相应股票相应类型的订阅

    return retres

def get_my_love_security(p_sec_group):
    retlist = []
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        ret, data = quote_ctx.get_user_security(p_sec_group)
        if ret == RET_OK:
            retlist = data['code']
        else:
            print('error:', data)
    finally:
        quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽

    return retlist

def getmaxbuyqty(code, currmarketprice):
    retqty = -1
    pwd_unlock = getTradePass()
    # 查询股票最大可买可卖数量
    trd_ctx = OpenHKTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        trd_ctx.unlock_trade(pwd_unlock)  # 解锁
        ret, data = trd_ctx.acctradinginfo_query(order_type=OrderType.MARKET, code=code, trd_env=TrdEnv.REAL, price=currmarketprice)
        if ret == RET_OK:
            retqty = data['max_cash_buy'][0]
            print('max qty:', retqty)
        else:
            print('error:', data)
    finally:
        trd_ctx.close()

    return retqty

def getstockquote(code):
    retprice = -1
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        ret_sub, err_message = quote_ctx.subscribe([code], [SubType.QUOTE], subscribe_push=False)
        # 先订阅K 线类型。订阅成功后FutuOpenD将持续收到服务器的推送，False代表暂时不需要推送给脚本
        if ret_sub == RET_OK:  # 订阅成功
            ret, data = quote_ctx.get_stock_quote([code])  # 获取订阅股票报价的实时数据
            if ret == RET_OK:
                if data['last_price'].count() > 0:
                    retprice = data['last_price'][0]  # get the last price
                    print('last price:', retprice)
            else:
                print('error:', data)
        else:
            print('subscription failed', err_message)
    finally:
        quote_ctx.close()  # 关闭当条连接，FutuOpenD会在1分钟后自动取消相应股票相应类型的订阅

    return retprice

def getstocklotsize(code):
    retlotsize = -1
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        ret, data = quote_ctx.get_market_snapshot(code)
        if ret == RET_OK:
            retlotsize = data['lot_size'][0] # get the lot size
            print('lot size:', retlotsize)
        else:
            print('error:', data)
    finally:
        quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽

    return retlotsize

def getstockhighestprice(code):
    rethprice = -1
    quote_ctx = OpenQuoteContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        ret, data = quote_ctx.get_market_snapshot(code)
        if ret == RET_OK:
            rethprice = data['high_price'][0] # get the lot size
            print('highest price:', rethprice)
        else:
            print('error:', data)
    finally:
        quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽

    return rethprice

def buystock(code):
    pwd_unlock = getTradePass()
    trd_ctx = OpenHKTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        trd_ctx.unlock_trade(pwd_unlock)
        #current price
        stockqty = getmaxbuyqty(code, 0) ##get max buy vol on market price
        stockqty = stockqty - getstocklotsize(code)
        if stockqty > 0:
            # real buy
            # print(trd_ctx.place_order(qty=stockqty, code=code, order_type=OrderType.MARKET, trd_side=TrdSide.BUY))
            # trail db buy
            buyprice = getstockquote(code)
            if buyprice > 0:
                dbplacebuyorder(code, buyprice, stockqty)
                print('buy stock:', code, buyprice, stockqty)
                writelog('buy stock: ' + code + ', ' + str(buyprice) + ', ' + str(stockqty))
            else:
                print('get stock price error, cannot buy the stock')
        else:
            print('Not enough money to buy the stock, buy action canceled.')
    finally:
        trd_ctx.close()

def runbuy():
    print('running buy')
    buyresult = 'No stock can buy at this minute'
    currtime = datetime.now()
    startbuytime = datetime(currtime.year, currtime.month, currtime.day, daytradeConfigures.START_TRADE_HOUR, 40, 0)  #start buy time configure
    stopbuytime = datetime(currtime.year, currtime.month, currtime.day, daytradeConfigures.END_TRADE_HOUR, daytradeConfigures.LAST_BUY_MINUTES, 0)  #last buy time configure
    if currtime >= startbuytime and currtime <= stopbuytime:
        print('time ok, can run buy')
        goodstocks = get_my_love_security('港股')
        for item in goodstocks:
            #if isincreasing(item):
            #    print(item, 'is increasing')
            if isasklargerthanbid(item):
                buystock(item)
                buyresult = 'buy stock: ' + item
    else:
        print('Buy time is closed at ', stopbuytime)

    print(buyresult)
    writelog(buyresult)

# sell functions start
def sellstock(code, qty, rule):
    pwd_unlock = getTradePass()
    trd_ctx = OpenHKTradeContext(host=getFutuAPILocalServerIP(), port=getFutuAPILocalServerPort())
    try:
        trd_ctx.unlock_trade(pwd_unlock)
        if qty > 0:
            # real buy
            # print(trd_ctx.place_order(qty=qty, code=code, order_type=OrderType.MARKET, trd_side=TrdSide.SELL))
            # trail db buy
            sellprice = getstockquote(code)
            if sellprice > 0:
                dbplacesellorder(code, sellprice, qty, rule)
                print('sell stock:', code, sellprice, qty)
                writelog('sell stock: ' + code + ', ' + str(sellprice) + ', ' + str(qty))
            else:
                print('get stock price error, cannot sell it')
    finally:
        trd_ctx.close()

def runsell():
    print('running sell')
    currtime = datetime.now()
    endtime = datetime(currtime.year, currtime.month, currtime.day, daytradeConfigures.END_TRADE_HOUR, daytradeConfigures.LAST_SELL_MINUTES, 0)  # trade end time configure
    #taril
    stocks = dbloopstockinpos()
    for row in stocks:
        code = row[0]
        buyprice = row[1]
        qty = row[2]
        # No.1 rule, if it's 11:50 AM, sell all
        if currtime >= endtime:
            sellstock(code, qty, 'RULE-01')
            print('sell stock ' + code + ' (rule 01)')
        else:
            # No.2 rule, if the current price lower 98% buy price, sell all
            currprice = getstockquote(code)
            if (currprice < buyprice * daytradeConfigures.STOP_LOST):
                sellstock(code, qty, 'RULE-02')
                print('sell stock ' + code + ' (rule 02)')
            else: # No.3 rule, if the current price higher 105% buy price, sell all
                if (currprice > buyprice * daytradeConfigures.STOP_WIN):
                    sellstock(code, qty, 'RULE-03')
                    print('sell stock ' + code + ' (rule 03)')
                else: #No.4 rule, check the 10 buy bids < 10 sell bids: 10笔买单总手数 比 10笔卖单总手数 < 20%以上, sell all
                    if isbidlargerthanask(code):
                        sellstock(code, qty, 'RULE-04')
                        print('sell stock ' + code + ' (rule 04)')

    print('running sell end')

def daytrade01_start():
    currtime = datetime.now()
    print('datetrade01 start... ', datetime.strftime(currtime, "%Y-%m-%d %H:%M:%S"))
    starttime = datetime(currtime.year, currtime.month, currtime.day, daytradeConfigures.START_TRADE_HOUR, 40, 0) # trade start time configure
    endtime = datetime(currtime.year, currtime.month, currtime.day, daytradeConfigures.END_TRADE_HOUR, 55, 0)  # trade end time configure
    while currtime < endtime:
        if currtime >= starttime and currtime <= endtime:
            ##執行策略
            if haveStockDB():    # trail
            # if haveStock():  # real
                print('Stock in position, execute sell strategy')
                runsell()
            else:
                print('No Stock in position, execute buy strategy')
                runbuy()
        currtime = datetime.now()
        nextmin = currtime + timedelta(seconds=59)
        print(currtime)
        while currtime < nextmin:
            currtime = datetime.now()
            time.sleep(1)
    print('datetrade01 end')



