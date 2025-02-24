import pandas as pd
import akshare as ak
from utils.logger import Logger
from multiprocessing import Pool, cpu_count
from functools import partial
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm

class DoubleMaStrategy:
    def __init__(self):
        # 定义均线周期
        self.ma_periods = [5, 10, 20, 40, 60, 120]
        
    def calculate_ma(self, data, periods):
        """计算多个周期的均线"""
        ma_dict = {}
        for period in periods:
            ma_dict[str(period)] = data['close'][-period:].mean()
        return ma_dict
    
    def check_ma_alignment(self, ma_dict):
        """检查均线多头排列条件"""
        return (ma_dict['5'] > ma_dict['10'] and
                ma_dict['10'] > ma_dict['20'] and
                ma_dict['20'] > ma_dict['40'] and
                ma_dict['40'] > ma_dict['60'] and
                ma_dict['60'] > ma_dict['120'])
    
    def process_stock_data(self, stock_code):
        """处理单个股票数据"""
        try:
            # 获取日线数据
            day_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
            if day_data is None or day_data.empty:
                return False
            
            # 转换日期格式并设置收盘价
            day_data['date'] = pd.to_datetime(day_data['日期'])
            day_data['close'] = day_data['收盘'].astype(float)
            
            # 获取周线数据
            week_data = day_data.set_index('date').resample('W').agg({
                'close': 'last'
            }).reset_index()
            
            if len(day_data) < 120 or len(week_data) < 120:
                return False
                
            # 计算日线和周线均线
            day_ma = self.calculate_ma(day_data, self.ma_periods)
            week_ma = self.calculate_ma(week_data, self.ma_periods)
            
            # 检查日线和周线条件
            day_condition = self.check_ma_alignment(day_ma)
            week_condition = self.check_ma_alignment(week_ma)
            
            # 返回是否同时满足条件
            return day_condition and week_condition
            
        except Exception as e:
            logger = Logger()
            logger.error(f"处理股票 {stock_code} 时发生错误：{str(e)}")
            return False
    
    def process_stock_batch(self, stock_codes):
        """批量处理股票数据"""
        results = []
        
        for stock_code in tqdm(stock_codes, desc="处理当前批次", leave=False):
            try:
                if self.process_stock_data(stock_code):
                    results.append(stock_code)
            except Exception as e:
                logger = Logger()
                logger.error(f"处理股票 {stock_code} 时发生错误：{str(e)}")
                continue
                
        return results

    def scan_stocks(self, stock_list):
        """扫描所有股票"""
        logger = Logger()
        
        # 获取股票池
        stock_codes = stock_list if isinstance(stock_list, list) else stock_list['股票代码'].tolist()
        logger.info(f"获取股票池完成，共 {len(stock_codes)} 只股票")
        
        # 将股票列表分成多个批次
        num_processes = min(cpu_count(), len(stock_codes))  # 确保进程数不超过股票数量
        batch_size = max(1, len(stock_codes) // num_processes)  # 确保批处理大小至少为1
        batches = [stock_codes[i:i + batch_size] for i in range(0, len(stock_codes), batch_size)]
        
        # 使用多进程处理
        with Pool(num_processes) as pool:
            results = list(tqdm(
                pool.imap(self.process_stock_batch, batches),
                total=len(batches),
                desc="分析股票批次进度"
            ))
        
        # 合并结果
        selected_stocks = []
        for batch_result in results:
            selected_stocks.extend(batch_result)
            
        for stock_code in selected_stocks:
            logger.info(f"发现符合条件的股票：{stock_code}")
        
        return selected_stocks