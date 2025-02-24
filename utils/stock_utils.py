import akshare as ak

# 获取A股所有股票的实时行情
stocks = ak.stock_zh_a_spot_em()
stock_list = stocks['代码'].tolist()
stocks_dict = dict(zip(stocks['代码'], stocks['名称']))
