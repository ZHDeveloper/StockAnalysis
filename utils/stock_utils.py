import efinance as ef

# 获取A股所有股票的实时行情
stocks = ef.stock.get_realtime_quotes()
stock_list = stocks['股票代码'].tolist()
stocks_dict = dict(zip(stocks['股票代码'], stocks['股票名称']))
