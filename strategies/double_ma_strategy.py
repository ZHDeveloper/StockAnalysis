import pandas as pd
import efinance as ef
from utils.logger import Logger

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
            day_data = ef.stock.get_quote_history(stock_code, beg='2022-01-01')
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
    
    def scan_stocks(self):
        """扫描所有股票"""
        selected_stocks = []
        logger = Logger()
        
        # 获取股票池
        stocks = ef.stock.get_realtime_quotes()
        logger.info(f"获取股票池完成，共 {len(stocks)} 只股票")
        
        for index, stock in stocks.iterrows():
            stock_code = stock['股票代码']
            logger.info(f"正在分析第 {index+1}/{len(stocks)} 只股票: {stock_code}")
            
            if self.process_stock_data(stock_code):
                selected_stocks.append(stock_code)
                logger.info(f"发现符合条件的股票：{stock_code}")
        
        return selected_stocks