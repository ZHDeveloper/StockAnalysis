import pandas as pd
import yfinance as yf
from utils.logger import Logger
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
            # 根据市场调整后缀
            if stock_code.startswith('6'):
                suffix = '.SS'  # 沪市
            elif stock_code.startswith('0') or stock_code.startswith('3'):
                suffix = '.SZ'  # 深市
            else:
                suffix = '.BJ'  # 北交所或新三板（需进一步验证）
            yf_code = stock_code + suffix
            
            # 获取股票数据
            stock = yf.Ticker(yf_code)
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            day_data = stock.history(start=start_date, end=end_date, interval='1d')
            
            if day_data is None or day_data.empty:
                return False
            
            # 设置日期和收盘价
            day_data = day_data.reset_index()
            day_data['date'] = day_data['Date']
            day_data['close'] = day_data['Close']
            
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

    def scan_stocks(self, stock_list):
        """扫描所有股票"""
        logger = Logger()
        selected_stocks = []
        
        # 获取股票池
        stock_codes = stock_list if isinstance(stock_list, list) else stock_list['股票代码'].tolist()
        logger.info(f"获取股票池完成，共 {len(stock_codes)} 只股票")
        
        # 顺序处理每只股票
        for stock_code in tqdm(stock_codes, desc="分析股票进度"):
            try:
                if self.process_stock_data(stock_code):
                    selected_stocks.append(stock_code)
                    logger.info(f"发现符合条件的股票：{stock_code}")
            except Exception as e:
                logger.error(f"处理股票 {stock_code} 时发生错误：{str(e)}")
                continue
        
        return selected_stocks