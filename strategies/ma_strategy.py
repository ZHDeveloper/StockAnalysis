import pandas as pd
import numpy as np
import efinance as ef
from datetime import datetime, timedelta
from utils.logger import Logger

class MAStrategy:
    def __init__(self, short_period=5, long_period=20):
        self.short_period = short_period  # 短期均线周期
        self.long_period = long_period    # 长期均线周期

    def calculate_ma(self, df):
        """计算均线"""
        df[f'MA{self.short_period}'] = df['close'].rolling(window=self.short_period).mean()
        df[f'MA{self.long_period}'] = df['close'].rolling(window=self.long_period).mean()
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        return df

    def check_stock(self, stock_code):
        """分析单只股票"""
        try:
            # 获取最近60个交易日数据
            df = ef.stock.get_quote_history(stock_code)
            if df is None or df.empty or len(df) < self.long_period:
                return False

            # 转换数据格式
            df['close'] = df['收盘'].astype(float)
            df['volume'] = df['成交量'].astype(float)
            
            # 计算技术指标
            df = self.calculate_ma(df)
            
            # 获取最近两个交易日数据
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 策略条件:
            # 1. 短期均线上穿长期均线
            # 2. 成交量放大
            # 3. 股价位于均线上方
            golden_cross = (yesterday[f'MA{self.short_period}'] <= yesterday[f'MA{self.long_period}']) and \
                         (today[f'MA{self.short_period}'] > today[f'MA{self.long_period}'])
            
            volume_increase = today['volume'] > today['volume_ma5'] * 1.5
            
            price_above_ma = today['close'] > today[f'MA{self.short_period}'] and \
                           today['close'] > today[f'MA{self.long_period}']            
            
            return golden_cross and volume_increase and price_above_ma

        except Exception as e:
            print(f"分析股票 {stock_code} 时出错: {str(e)}")
            return False

    def scan_stocks(self, stock_list):
        """扫描股票池"""
        selected_stocks = []
        logger = Logger()
        
        for index, stock in enumerate(stock_list):
            logger.info(f"正在分析第 {index+1}/{len(stock_list)} 只股票: {stock}")
            if self.check_stock(stock):
                selected_stocks.append(stock)
                logger.info(f"发现符合条件的股票：{stock}")
                
        return selected_stocks