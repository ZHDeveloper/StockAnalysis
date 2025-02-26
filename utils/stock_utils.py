import akshare as ak

# 获取A股所有股票的实时行情
stocks = ak.stock_zh_a_spot_em()
stock_list = stocks['代码'].tolist()
stocks_dict = dict(zip(stocks['代码'], stocks['名称']))

def convert_stock_code(stock_code):
    """
    将股票代码转换为 yfinance 支持的格式
    - A 股: 600519 -> 600519.SS（上交所），000001 -> 000001.SZ（深交所）
    - 港股: 0700 -> 0700.HK
    - 美股: 直接使用（如 AAPL）
    """
    if stock_code.isdigit():
        if stock_code.startswith('6'):  # 上交所
            return f"{stock_code}.SS"
        elif stock_code.startswith('0') or stock_code.startswith('3'):  # 深交所
            return f"{stock_code}.SZ"
        elif len(stock_code) == 4:  # 港股
            return f"{stock_code}.HK"
    return stock_code  # 默认使用原代码（如美股）
