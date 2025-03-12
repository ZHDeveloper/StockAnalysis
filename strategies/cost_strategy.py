import pandas as pd
import numpy as np
import efinance as ef
from datetime import datetime, timedelta
from utils.logger import Logger
from utils.stock_utils import stocks_dict

class CostStrategy:
    def __init__(self, config=None):
        self.logger = Logger()
        
        # 参数默认配置
        self.default_config = {
            'ma_periods': [5, 10, 20, 60],  # 均线周期列表，分别代表5日、10日、20日和60日均线
            'macd_params': {'fast': 12, 'slow': 26, 'signal': 9},  # MACD参数：快线、慢线和信号线周期
            'rsi_period': 14,  # RSI相对强弱指标的计算周期
            'bollinger_params': {'period': 20, 'std': 2},  # 布林带参数：均线周期和标准差倍数
            'atr_period': 14,  # ATR平均真实波幅的计算周期
            'volume_multiplier': 1.2,  # 成交量放大倍数阈值，用于判断成交量突破
            'risk_ratio': 2.0,  # 风险比率，用于计算止盈止损点
            'max_position_ratio': 0.2  # 最大仓位比例，控制单只股票的最大持仓比例
        }
        
        # 合并自定义配置
        self.config = {**self.default_config, **(config or {})}

        # 风险控制模块
        self.position_size = {}
        self.total_portfolio_value = 1_000_000  # 示例初始组合规模

    # %% 增强技术指标计算方法
    def calculate_enhanced_indicators(self, df):
        """计算改进后的全套技术指标"""
        # 基本价格信息
        df['price_change'] = df['close'].pct_change()
        
        # 均线系统
        for period in self.config['ma_periods']:
            df[f'MA{period}'] = df['close'].rolling(period).mean()
        
        # MACD指标
        macd_params = self.config['macd_params']
        exp1 = df['close'].ewm(span=macd_params['fast']).mean()
        exp2 = df['close'].ewm(span=macd_params['slow']).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=macd_params['signal']).mean()
        
        # RSI指标
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(self.config['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.config['rsi_period']).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        
        # 布林带
        bb = self.config['bollinger_params']
        df['BB_Middle'] = df['close'].rolling(bb['period']).mean()
        std = df['close'].rolling(bb['period']).std()
        df['BB_Upper'] = df['BB_Middle'] + std * bb['std']
        df['BB_Lower'] = df['BB_Middle'] - std * bb['std']
        
        # ATR波动率
        high = df['high']
        low = df['low']
        close = df['close']
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        df['ATR'] = tr.rolling(self.config['atr_period']).mean()
        
        # 成交量验证指标
        df['Volume_MA5'] = df['volume'].rolling(5).mean()
        return df.dropna()

    # %% 信号检测方法
    def check_crossovers(self, df):
        """检测技术指标交叉信号"""
        signals = {}
        
        # MACD交叉检测
        latest = len(df) - 1
        if (df['MACD'].iloc[latest] > df['MACD_Signal'].iloc[latest] and
            df['MACD'].iloc[latest-1] <= df['MACD_Signal'].iloc[latest-1]):
            signals['MACD_Golden'] = True
        if (df['MACD'].iloc[latest] < df['MACD_Signal'].iloc[latest] and
            df['MACD'].iloc[latest-1] >= df['MACD_Signal'].iloc[latest-1]):
            signals['MACD_Death'] = True
            
        # 价格与均线关系
        signals['Price_Above_MA20'] = df['close'].iloc[-1] > df['MA20'].iloc[-1]
        signals['MA5_Above_MA10'] = df['MA5'].iloc[-1] > df['MA10'].iloc[-1]
        
        return signals

    def check_volume_breakout(self, df):
        """检测成交量突破"""
        latest_vol = df['volume'].iloc[-1]
        vol_ma = df['Volume_MA5'].iloc[-1]
        return latest_vol > vol_ma * self.config['volume_multiplier']

    # %% 风险管理模块
    def calculate_position_size(self, stock_code, atr, price):
        """基于凯利公式和波动率计算仓位"""
        if stock_code not in self.position_size:
            # 计算波动率调整系数
            vol_adj = atr / price
            # 最大仓位限制
            max_capital = self.total_portfolio_value * self.config['max_position_ratio']
            # 凯利公式计算理论仓位（简化版）
            kelly_fraction = 0.2 / vol_adj if vol_adj > 0 else 0
            position_size = min(kelly_fraction * self.total_portfolio_value, max_capital)
            self.position_size[stock_code] = position_size
        return self.position_size[stock_code]

    def update_portfolio_value(self, new_value):
        """更新组合总市值"""
        self.total_portfolio_value = new_value

    # %% 核心分析方法
    def analyze_stock(self, stock_code, cost_price):
        try:
            # 获取历史数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')
            df = ef.stock.get_quote_history(
                stock_code, 
                beg=start_date, 
                end=end_date
            )
            if df.empty:
                return None
            
            # 数据预处理
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume'
            })
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # 计算技术指标
            df = self.calculate_enhanced_indicators(df)
            if df.empty:
                return None
            
            # 获取最新数据
            latest = df.iloc[-1]
            price_change_ratio = (latest['close'] - cost_price) / cost_price
            dynamic_thresholds = self.calculate_dynamic_thresholds(latest['ATR'], cost_price)
            
            # 生成基础分析结果
            analysis = {
                'stock_code': stock_code,
                'current_price': latest['close'],
                'cost_price': cost_price,
                'price_change': price_change_ratio,
                'suggestion': '持有',
                'reasons': [],
                'position_size': self.calculate_position_size(stock_code, latest['ATR'], latest['close'])
            }
            
            # 信号检测
            signals = self.check_crossovers(df)
            volume_breakout = self.check_volume_breakout(df)
            
            # %% 动态决策逻辑
            # 亏损场景
            if price_change_ratio <= dynamic_thresholds['add_position']:
                analysis['suggestion'] = '观望'
                analysis['reasons'].append(f'【价格】亏损幅度 {price_change_ratio*100:.1f}% 已达到预警线')
                
                if all([
                    signals.get('MACD_Golden', False),
                    signals['Price_Above_MA20'],
                    volume_breakout,
                    latest['RSI'] > 35
                ]):
                    analysis['suggestion'] = '加仓'
                    analysis['reasons'] = [
                        f'【价格】虽然亏损 {price_change_ratio*100:.1f}%，但技术面转好',
                        '【技术】MACD金叉（短期动能转强）',
                        '【趋势】股价站上20日均线（中期趋势向好）',
                        '【成交】成交量明显放大（市场认可度提升）'
                    ]

            # 止盈场景
            elif price_change_ratio >= dynamic_thresholds['take_profit']:
                analysis['reasons'].append(f'【盈利】当前盈利 {price_change_ratio*100:.1f}% 已达到目标')
                
                if any([
                    signals.get('MACD_Death', False),
                    latest['close'] < latest['MA5'],
                    latest['RSI'] > 70
                ]):
                    analysis['suggestion'] = '止盈'
                    analysis['reasons'] = [
                        f'【盈利】已获利 {price_change_ratio*100:.1f}%，达到目标',
                        '【风险】' + (
                            'MACD死叉（动能减弱）' if signals.get('MACD_Death', False) else 
                            '股价跌破5日均线（短期走弱）' if latest['close'] < latest['MA5'] else 
                            'RSI超买（技术指标过热）'
                        )
                    ]
                    
            # 止损场景
            elif price_change_ratio <= dynamic_thresholds['stop_loss']:
                analysis['suggestion'] = '止损'
                analysis['reasons'] = [
                    f'【风险】亏损幅度 {price_change_ratio*100:.1f}% 已超过止损线',
                    '【技术】价格跌破布林带下轨（超卖但下跌趋势强）' if latest['close'] < latest['BB_Lower'] else '【建议】控制风险，及时止损'
                ]
                
            # 正常波动场景
            else:
                if signals['Price_Above_MA20'] and signals['MA5_Above_MA10']:
                    analysis['reasons'].append('【趋势】均线多头排列，短中期走势良好')
                else:
                    analysis['reasons'].append('【行情】价格处于正常波动区间，暂无明确信号')
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析 {stock_code} 时出错: {str(e)}")
            return None

    # %% 实用工具方法
    def calculate_dynamic_thresholds(self, atr_value, cost_price):
        """计算动态阈值"""
        return {
            'take_profit': self.config['risk_ratio'] * (atr_value / cost_price),
            'stop_loss': -self.config['risk_ratio'] * (atr_value / cost_price),
            'add_position': -0.8 * self.config['risk_ratio'] * (atr_value / cost_price)
        }

    def format_analysis_result(self, analysis):
        """格式化分析结果"""
        if not analysis:
            return "分析结果不可用"

        stock_name = stocks_dict.get(analysis['stock_code'], '未知股票')
        output = [
            f"\n股票代码：{analysis['stock_code']} ({stock_name})",
            f"当前价格：{analysis['current_price']:.2f}",
            f"成本价格：{analysis['cost_price']:.2f}",
            f"盈亏比例：{analysis['price_change']*100:+.1f}%",
            f"建议操作：{analysis['suggestion']}",
            "主要依据：",
        ]
        output.extend([f" • {r}" for r in analysis['reasons'] if r])
        return "\n".join(output)

# %% 使用示例
if __name__ == "__main__":
    strategy = CostStrategy(config={'max_position_ratio': 0.15})
    
    # 示例股票分析
    sample_analysis = strategy.analyze_stock('600519', 1800)  # 以茅台为例假设成本价1800
    if sample_analysis:
        print(strategy.format_analysis_result(sample_analysis))
    else:
        print("分析失败")