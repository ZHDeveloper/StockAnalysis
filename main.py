import datetime
import time
import os
import efinance as ef
import argparse
from strategies.double_ma_strategy import DoubleMaStrategy
from strategies.ma_strategy import MAStrategy
from utils.logger import Logger

def check_double_ma_strategy():
    logger = Logger()
    logger.info("开始执行选股程序...")
    
    # 初始化策略
    strategy = DoubleMaStrategy()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 执行选股策略
    selected_stocks = strategy.scan_stocks()
    
    logger.info("\n分析完成！")
    # 输出选股结果
    if selected_stocks:
        # 创建 stocks 目录（如果不存在）
        if not os.path.exists('stocks'):
            os.makedirs('stocks')
            
        # 获取实时行情数据以获取股票名称
        stocks_info = ef.stock.get_realtime_quotes()
        stocks_dict = dict(zip(stocks_info['股票代码'], stocks_info['股票名称']))
            
        # 将结果保存到文件
        result_file = 'stocks/double_ma_stocks.txt'
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f'符合双重多头排列的股票({current_date}):\n')
            for stock_code in selected_stocks:
                stock_name = stocks_dict.get(stock_code, '未知')
                f.write(f'股票代码：{stock_code}  股票名称：{stock_name}\n')
            f.write(f'\n共找到 {len(selected_stocks)} 只符合条件的股票')
        
        logger.info(f"符合双重多头排列的股票({current_date}):")
        for stock_code in selected_stocks:
            stock_name = stocks_dict.get(stock_code, '未知')
            logger.info(f"股票代码：{stock_code}  股票名称：{stock_name}")
        logger.info(f"共找到 {len(selected_stocks)} 只符合条件的股票")
        logger.info(f"筛选结果已保存到文件：{result_file}")
    else:
        logger.info(f"当日无符合条件股票({current_date})")

def check_ma_strategy():
    logger = Logger()
    logger.info("开始执行均线金叉选股程序...")
    
    # 初始化策略
    strategy = MAStrategy(short_period=5, long_period=20)
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 获取所有A股股票
    stocks = ef.stock.get_realtime_quotes()
    stock_list = stocks['股票代码'].tolist()
    stocks_dict = dict(zip(stocks['股票代码'], stocks['股票名称']))
    
    # 执行选股策略
    selected_stocks = strategy.scan_stocks(stock_list)
    
    logger.info("\n分析完成！")
    # 输出选股结果
    if selected_stocks:
        # 创建 stocks 目录（如果不存在）
        if not os.path.exists('stocks'):
            os.makedirs('stocks')
            
        # 将结果保存到文件
        result_file = 'stocks/ma_stocks.txt'
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f'符合均线金叉条件的股票({current_date}):\n')
            for stock_code in selected_stocks:
                stock_name = stocks_dict.get(stock_code, '未知')
                f.write(f'股票代码：{stock_code}  股票名称：{stock_name}\n')
            f.write(f'\n共找到 {len(selected_stocks)} 只符合条件的股票')
        
        logger.info(f"符合均线金叉条件的股票({current_date}):")
        for stock_code in selected_stocks:
            stock_name = stocks_dict.get(stock_code, '未知')
            logger.info(f"股票代码：{stock_code}  股票名称：{stock_name}")
        logger.info(f"共找到 {len(selected_stocks)} 只符合条件的股票")
        logger.info(f"筛选结果已保存到文件：{result_file}")
    else:
        logger.info(f"当日无符合条件股票({current_date})")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='股票分析工具')
    parser.add_argument('--strategy', choices=['ma', 'double_ma'], default='double_ma', help='选择策略：ma(均线金叉) 或 double_ma(双均线多头排列)')
    args = parser.parse_args()
    
    if args.strategy == 'ma':
        check_ma_strategy()
    else:
        check_double_ma_strategy()