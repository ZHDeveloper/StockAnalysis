import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
from utils.logger import Logger
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

class MAStrategy:
    def __init__(self, short_period=5, long_period=20, volume_ma_period=5, volume_multiplier=1.5, confirmation_days=1, use_rsi=True, rsi_period=14, rsi_threshold=70):
        """
        初始化策略参数
        :param short_period: 短期均线周期，默认5天
        :param long_period: 长期均线周期，默认20天
        :param volume_ma_period: 成交量均线周期，默认5天
        :param volume_multiplier: 成交量放大倍数，默认1.5
        :param confirmation_days: 金叉确认天数，默认1天
        :param use_rsi: 是否使用RSI指标，默认True
        :param rsi_period: RSI计算周期，默认14天
        :param rsi_threshold: RSI超买阈值，默认70
        """
        self.short_period = short_period
        self.long_period = long_period
        self.volume_ma_period = volume_ma_period
        self.volume_multiplier = volume_multiplier
        self.confirmation_days = confirmation_days
        self.use_rsi = use_rsi
        self.rsi_period = rsi_period
        self.rsi_threshold = rsi_threshold

    def calculate_rsi(self, df, period):
        """计算RSI指标"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_ma(self, df):
        """计算均线、成交量MA和RSI（如启用）"""
        df[f'MA{self.short_period}'] = df['close'].rolling(window=self.short_period).mean()
        df[f'MA{self.long_period}'] = df['close'].rolling(window=self.long_period).mean()
        df[f'volume_ma{self.volume_ma_period}'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        if self.use_rsi:
            df['RSI'] = self.calculate_rsi(df, self.rsi_period)
        return df

    def calculate_macd(self, df, short_period=12, long_period=26, signal_period=9):
        """计算MACD指标"""
        df['EMA12'] = df['close'].ewm(span=short_period, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=long_period, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
        return df

    def check_stock(self, stock_code):
        """分析单只股票"""
        try:
            # 获取最近60个交易日数据
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=(datetime.now() - timedelta(days=90)).strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
            if df is None or df.empty or len(df) < max(self.long_period, self.rsi_period if self.use_rsi else 0):
                return False

            # 转换数据格式
            df['close'] = df['收盘'].astype(float)
            df['volume'] = df['成交量'].astype(float)
            
            # 计算技术指标
            df = self.calculate_ma(df)
            
            # 剔除NaN值
            df = df.dropna()
            
            # 确保有足够的确认天数
            if len(df) < self.confirmation_days + 1:
                return False
            
            # 获取最近confirmation_days+1天数据
            recent_data = df.tail(self.confirmation_days + 1)
            
            # 计算MACD指标
            df = self.calculate_macd(df)
            
            # 增加止损机制
            stop_loss = recent_data['close'].iloc[-1] * 0.95  # 设定止损点为当前价格的95%
            
            # 增加趋势确认机制
            trend_confirmation = (recent_data['close'].iloc[-3:] > recent_data[f'MA{self.short_period}'].iloc[-3:]).all()
            
            # 策略条件
            # 1. 短期均线上穿长期均线（金叉确认）
            golden_cross = (recent_data[f'MA{self.short_period}'].iloc[:-1] <= recent_data[f'MA{self.long_period}'].iloc[:-1]).all() and \
                           recent_data[f'MA{self.short_period}'].iloc[-1] > recent_data[f'MA{self.long_period}'].iloc[-1]
            
            # 2. 今日成交量放大
            volume_increase = recent_data['volume'].iloc[-1] > recent_data[f'volume_ma{self.volume_ma_period}'].iloc[-1] * self.volume_multiplier
            
            # 3. 今日股价位于均线上方
            price_above_ma = recent_data['close'].iloc[-1] > recent_data[f'MA{self.short_period}'].iloc[-1] and \
                             recent_data['close'].iloc[-1] > recent_data[f'MA{self.long_period}'].iloc[-1]
            
            # 4. RSI条件（如果启用）
            rsi_condition = True
            if self.use_rsi:
                rsi_condition = recent_data['RSI'].iloc[-1] < self.rsi_threshold  # 避免超买
            
            return golden_cross and volume_increase and price_above_ma and rsi_condition and trend_confirmation and recent_data['close'].iloc[-1] > stop_loss

        except Exception as e:
            print(f"分析股票 {stock_code} 时出错: {str(e)}")
            return False

    def process_stock_batch(self, stock_codes):
        """批量处理股票数据"""
        results = []
        
        for stock_code in tqdm(stock_codes, desc="处理当前批次", leave=False):
            try:
                df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=(datetime.now() - timedelta(days=90)).strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
                if df is None or df.empty or len(df) < max(self.long_period, self.rsi_period if self.use_rsi else 0):
                    continue

                # 转换数据格式
                df['close'] = df['收盘'].astype(float)
                df['volume'] = df['成交量'].astype(float)
                
                # 计算技术指标
                df = self.calculate_ma(df)
                
                # 剔除NaN值
                df = df.dropna()
                
                # 确保有足够的确认天数
                if len(df) < self.confirmation_days + 1:
                    continue
                
                # 获取最近confirmation_days+1天数据
                recent_data = df.tail(self.confirmation_days + 1)
                
                # 策略条件
                golden_cross = (recent_data[f'MA{self.short_period}'].iloc[:-1] <= recent_data[f'MA{self.long_period}'].iloc[:-1]).all() and \
                               recent_data[f'MA{self.short_period}'].iloc[-1] > recent_data[f'MA{self.long_period}'].iloc[-1]
                
                volume_increase = recent_data['volume'].iloc[-1] > recent_data[f'volume_ma{self.volume_ma_period}'].iloc[-1] * self.volume_multiplier
                
                price_above_ma = recent_data['close'].iloc[-1] > recent_data[f'MA{self.short_period}'].iloc[-1] and \
                                 recent_data['close'].iloc[-1] > recent_data[f'MA{self.long_period}'].iloc[-1]
                
                rsi_condition = True
                if self.use_rsi:
                    rsi_condition = recent_data['RSI'].iloc[-1] < self.rsi_threshold
                
                if golden_cross and volume_increase and price_above_ma and rsi_condition:
                    results.append(stock_code)
                    
            except Exception as e:
                print(f"分析股票 {stock_code} 时出错: {str(e)}")
                continue
                
        return results

    def scan_stocks(self, stock_list):
        """扫描股票池"""
        logger = Logger()
        
        # 将股票列表分成多个批次
        num_processes = min(cpu_count(), len(stock_list))  # 确保进程数不超过股票数量
        batch_size = max(1, len(stock_list) // num_processes)  # 确保批处理大小至少为1
        batches = [stock_list[i:i + batch_size] for i in range(0, len(stock_list), batch_size)]
        
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