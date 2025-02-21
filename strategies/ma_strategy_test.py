import efinance as ef
from ma_strategy import MAStrategy

# 初始化策略
strategy = MAStrategy(short_period=5, long_period=20)

# 获取所有A股股票
stocks = ef.stock.get_realtime_quotes()
stock_list = stocks['股票代码'].tolist()  # 获取所有股票代码

# 执行选股
selected_stocks = strategy.scan_stocks(stock_list)

# 打印结果
print("选股结果:")
for stock in selected_stocks:
    print(stock)