import pandas as pd
import numpy as np
import efinance as ef
from datetime import datetime, timedelta
from utils.logger import Logger

class CostStrategy:
    def __init__(self):
        self.logger = Logger()
        # 定义技术指标参数
        self.ma_periods = [5, 10, 20, 60]
        self.add_position_threshold = -0.05
        self.take_profit_threshold = 0.1
        self.stop_loss_threshold = -0.1
        
        # 新增技术指标参数
        self.macd_params = {
            'fast': 12,
            'slow': 26,
            'signal': 9
        }
        self.rsi_period = 14
        self.bollinger_period = 20
        self.bollinger_std = 2

    def calculate_ma(self, data):
        """计算多个周期的均线"""
        ma_dict = {}
        for period in self.ma_periods:
            ma_dict[f'MA{period}'] = data['close'].rolling(window=period).mean()
        return ma_dict

    def calculate_macd(self, data):
        """计算MACD指标"""
        exp1 = data['close'].ewm(span=self.macd_params['fast']).mean()
        exp2 = data['close'].ewm(span=self.macd_params['slow']).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=self.macd_params['signal']).mean()
        return macd, signal

    def calculate_rsi(self, data):
        """计算RSI指标"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_bollinger_bands(self, data):
        """计算布林带"""
        middle = data['close'].rolling(window=self.bollinger_period).mean()
        std = data['close'].rolling(window=self.bollinger_period).std()
        upper = middle + (std * self.bollinger_std)
        lower = middle - (std * self.bollinger_std)
        return upper, middle, lower

    def analyze_stock(self, stock_code, cost_price):
        """分析单只股票"""
        try:
            # 获取3年的历史数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
            
            # 获取历史数据
            df = ef.stock.get_quote_history(stock_code, beg=start_date)
            if df is None or df.empty:
                self.logger.error(f"无法获取股票 {stock_code} 的历史数据")
                return None
            
            # 数据预处理
            df['date'] = pd.to_datetime(df['日期'])
            df['close'] = df['收盘'].astype(float)
            df['volume'] = df['成交量'].astype(float)
            
            # 计算技术指标
            ma_dict = self.calculate_ma(df)
            for ma_name, ma_values in ma_dict.items():
                df[ma_name] = ma_values
            
            macd, signal = self.calculate_macd(df)
            rsi = self.calculate_rsi(df)
            upper_band, middle_band, lower_band = self.calculate_bollinger_bands(df)
            
            # 获取最新数据
            latest_price = df['close'].iloc[-1]
            latest_ma5 = df['MA5'].iloc[-1]
            latest_ma10 = df['MA10'].iloc[-1]
            latest_ma20 = df['MA20'].iloc[-1]
            latest_ma60 = df['MA60'].iloc[-1]
            latest_macd = macd.iloc[-1]
            latest_signal = signal.iloc[-1]
            latest_rsi = rsi.iloc[-1]
            latest_lower_band = lower_band.iloc[-1]
            
            # 计算相对成本价的涨跌幅
            price_change_ratio = (latest_price - cost_price) / cost_price
            
            # 分析建议
            analysis_result = {
                'stock_code': stock_code,
                'current_price': latest_price,
                'cost_price': cost_price,
                'price_change_ratio': price_change_ratio,
                'suggestion': '',
                'reason': []
            }
            
            # 判断加仓条件
            if price_change_ratio <= self.add_position_threshold:
                analysis_result['suggestion'] = '建议观望'
                analysis_result['reason'].append(f'当前价格低于成本价{abs(price_change_ratio*100):.2f}%')
                if (latest_price > latest_ma60 and latest_ma5 > latest_ma10 and 
                    latest_macd > latest_signal and latest_rsi > 30):
                    analysis_result['suggestion'] = '建议加仓'
                    analysis_result['reason'].append('价格站在60日均线上方，MACD金叉，RSI回升')
                else:
                    analysis_result['reason'].append('等待技术面企稳后再考虑加仓')
            
            # 判断卖出条件
            elif price_change_ratio >= self.take_profit_threshold:
                analysis_result['suggestion'] = '建议持有'
                analysis_result['reason'].append(f'已盈利{price_change_ratio*100:.2f}%')
                if latest_macd < latest_signal and latest_price < latest_ma5:
                    analysis_result['suggestion'] = '建议卖出止盈'
                    analysis_result['reason'].append('MACD死叉，短期均线转弱')
                else:
                    analysis_result['reason'].append('走势仍然强势，可继续持有')
            
            # 判断止损条件
            elif price_change_ratio <= self.stop_loss_threshold:
                analysis_result['suggestion'] = '建议观望'
                analysis_result['reason'].append(f'已亏损{abs(price_change_ratio*100):.2f}%')
                if (latest_price < latest_ma20 and latest_rsi < 30 and 
                    latest_price < latest_lower_band):
                    analysis_result['suggestion'] = '建议止损'
                    analysis_result['reason'].append('RSI超卖，价格跌破布林带下轨，技术面严重走弱')
                else:
                    analysis_result['reason'].append('等待反弹机会再考虑操作')
            
            # 其他情况
            else:
                analysis_result['suggestion'] = '建议观望'
                analysis_result['reason'].append('当前价格波动在合理范围内')
                if latest_price > latest_ma20:
                    analysis_result['reason'].append('价格运行在20日均线上方，走势较强')
                else:
                    analysis_result['reason'].append('价格运行在20日均线下方，需要等待企稳')
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock_code} 时发生错误：{str(e)}")
            return None
    
    def format_analysis_result(self, result):
        """格式化分析结果"""
        if result is None:
            return "分析失败，无法获取有效数据"
            
        stock_name = stocks_dict.get(stock_code, '未知')
        
        output = f"\n股票代码：{result['stock_code']} ({stock_name})"
        output += f"\n当前价格：{result['current_price']:.2f}"
        output += f"\n成本价格：{result['cost_price']:.2f}"
        output += f"\n涨跌幅：{result['price_change_ratio']*100:.2f}%"
        output += f"\n投资建议：{result['suggestion']}"
        output += "\n建议理由："
        for reason in result['reason']:
            output += f"\n - {reason}"
        
        return output
