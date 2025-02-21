import efinance as ef
import pandas as pd
import datetime
import time
import logging
import os

def setup_logger():
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 配置日志格式
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    log_file = f'logs/stock_analysis_{current_date}.log'
    
    # 如果日志文件存在，先清空内容
    if os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            f.truncate(0)
    
    # 配置logging
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def check_condition():
    setup_logger()
    logging.info("开始执行选股程序...")
    
    # 获取股票池
    stocks = ef.stock.get_realtime_quotes()
    logging.info(f"获取股票池完成，共 {len(stocks)} 只股票")
    
    # 存储符合条件的股票
    selected_stocks = []
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    logging.info(f"开始分析每只股票（当前日期：{current_date}）...")
    
    for index, stock in stocks.iterrows():
        try:
            stock_code = stock['股票代码']
            logging.info(f"正在分析第 {index+1}/{len(stocks)} 只股票: {stock_code}")
            
            # 获取日线数据
            day_data = ef.stock.get_quote_history(stock_code, beg='2022-01-01')
            if day_data is None or day_data.empty:
                continue
            
            # 转换日期格式并设置收盘价
            day_data['date'] = pd.to_datetime(day_data['日期'])
            day_data['close'] = day_data['收盘'].astype(float)
            
            # 获取周线数据
            week_data = day_data.set_index('date').resample('W').agg({
                'close': 'last'
            }).reset_index()
            
            if len(day_data) < 120 or len(week_data) < 120:
                continue
                
            # 计算日线均线
            day_ma = {
                '5':  day_data['close'][-5:].mean(),
                '10': day_data['close'][-10:].mean(),
                '20': day_data['close'][-20:].mean(),
                '40': day_data['close'][-40:].mean(),
                '60': day_data['close'][-60:].mean(),
                '120': day_data['close'][-120:].mean()
            }
            
            # 计算周线均线
            week_ma = {
                '5':  week_data['close'][-5:].mean(),
                '10': week_data['close'][-10:].mean(),
                '20': week_data['close'][-20:].mean(),
                '40': week_data['close'][-40:].mean(),
                '60': week_data['close'][-60:].mean(),
                '120': week_data['close'][-120:].mean()
            }
            
            # 检查日线多头排列条件
            day_condition = (day_ma['5'] > day_ma['10'] and
                            day_ma['10'] > day_ma['20'] and
                            day_ma['20'] > day_ma['40'] and
                            day_ma['40'] > day_ma['60'] and
                            day_ma['60'] > day_ma['120'])
            
            # 检查周线多头排列条件
            week_condition = (week_ma['5'] > week_ma['10'] and
                            week_ma['10'] > week_ma['20'] and
                            week_ma['20'] > week_ma['40'] and
                            week_ma['40'] > week_ma['60'] and
                            week_ma['60'] > week_ma['120'])
            
            # 同时满足日线和周线条件
            if day_condition and week_condition:
                selected_stocks.append(stock_code)
                logging.info(f"发现符合条件的股票：{stock_code}")
                
        except Exception as e:
            logging.error(f"处理股票 {stock_code} 时发生错误：{str(e)}")
            continue
            
        time.sleep(0.1)
    
    logging.info("\n分析完成！")
    # 输出选股结果
    if selected_stocks:
        # 创建 stocks 目录（如果不存在）
        if not os.path.exists('stocks'):
            os.makedirs('stocks')
            
        # 将结果保存到文件
        result_file = f'stocks/stocks_{current_date}.txt'
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f'符合双重多头排列的股票({current_date}):\n')
            for stock in selected_stocks:
                f.write(f'股票代码：{stock}\n')
            f.write(f'\n共找到 {len(selected_stocks)} 只符合条件的股票')
        
        logging.info(f"符合双重多头排列的股票({current_date}):")
        for stock in selected_stocks:
            logging.info(f"股票代码：{stock}")
        logging.info(f"共找到 {len(selected_stocks)} 只符合条件的股票")
        logging.info(f"筛选结果已保存到文件：{result_file}")
    else:
        logging.info(f"当日无符合条件股票({current_date})")

if __name__ == '__main__':
    check_condition()