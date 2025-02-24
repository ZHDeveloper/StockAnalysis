import datetime
import time
import os
import argparse
from utils.dingtalk import DingTalkBot
from strategies.double_ma_strategy import DoubleMaStrategy
from strategies.ma_strategy import MAStrategy
from strategies.cost_strategy import CostStrategy
from utils.logger import Logger
# 从stock_utils导入股票列表相关变量
from utils.stock_utils import stock_list, stocks_dict

def check_double_ma_strategy():
    logger = Logger()
    logger.info("开始执行选股程序...")
    
    # 初始化策略
    strategy = DoubleMaStrategy()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 执行选股策略
    selected_stocks = strategy.scan_stocks(stock_list)
    
    logger.info("分析完成！")
    # 输出选股结果
    if selected_stocks:
        # 创建 stocks 目录（如果不存在）
        if not os.path.exists('stocks'):
            os.makedirs('stocks')
            
        # 定义结果文件路径
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
    strategy = MAStrategy()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    # 执行选股策略
    selected_stocks = strategy.scan_stocks(stock_list)
    
    logger.info("分析完成！")
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

def analyze_stock_cost():
    logger = Logger()
    logger.info("开始执行成本分析...")
    
    # 定义股票配置数组
    stocks_config = [
        {"code": "600004", "cost": 9.6, "notify_dingtalk": True},
        {"code": "002384", "cost": 34.31, "notify_dingtalk": False},
        {"code": "601868", "cost": 2.31, "notify_dingtalk": False},
        {"code": "002461", "cost": 9.25, "notify_dingtalk": False},
        {"code": "000860", "cost": 17.65, "notify_dingtalk": False},
        {"code": "600710", "cost": 10.50, "notify_dingtalk": False},
        {"code": "000949", "cost": 4.50, "notify_dingtalk": False},
    ]
    
    # 初始化策略
    strategy = CostStrategy()
    
    # 分析每只股票
    for stock in stocks_config:
        logger.info(f"分析股票 {stock['code']} 的成本情况...")
        result = strategy.analyze_stock(stock['code'], stock['cost'])
        
        # 输出分析结果
        if result:
            formatted_result = strategy.format_analysis_result(result)
            logger.info(formatted_result)
            
            # 根据配置决定是否发送钉钉消息
            if stock['notify_dingtalk']:
                dingtalk_message = f"股票分析结果\n{formatted_result.rstrip()}"
                if DingTalkBot().send_text_message(dingtalk_message):
                    logger.info(f"股票 {stock['code']} 的分析结果已发送到钉钉群")
                else:
                    logger.error(f"股票 {stock['code']} 的钉钉消息发送失败")
        else:
            error_message = f"股票 {stock['code']} 分析失败，请检查股票代码是否正确"
            logger.error(error_message)
            if stock['notify_dingtalk']:
                DingTalkBot().send_dingtalk_message(f"股票分析失败\n{error_message}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='股票分析工具')
    parser.add_argument('--strategy', choices=['ma', 'double_ma', 'cost'], default='double_ma', 
                        help='选择策略：ma(均线金叉)、double_ma(双均线多头排列)或cost(成本分析)')
    args = parser.parse_args()
    
    if args.strategy == 'ma':
        check_ma_strategy()
    elif args.strategy == 'cost':
        analyze_stock_cost()
    else:
        check_double_ma_strategy()