# 股票分析工具

## 项目简介
这是一个基于Python的股票分析工具，用于自动化筛选符合特定技术指标条件的股票。目前支持两种选股策略：双均线多头排列和均线金叉策略。

## 功能特性
1. 双均线多头排列策略
   - 同时分析日线和周线数据
   - 计算5、10、20、40、60、120日均线
   - 筛选同时满足日线和周线多头排列的股票

2. 均线金叉策略
   - 分析短期均线（默认5日）上穿长期均线（默认20日）
   - 结合成交量放大指标
   - 确保股价位于均线上方

## 安装说明
1. 克隆项目到本地
```bash
git clone [项目地址]
cd StockAnalysis
```

2. 安装依赖包
```bash
pip install -r requirements.txt
```

## 使用方法
1. 运行双均线多头排列策略（默认策略）
```bash
python main.py
# 或者显式指定策略
python main.py --strategy double_ma
```

2. 运行均线金叉策略
```bash
python main.py --strategy ma
```

## 输出说明
1. 日志文件
   - 位置：`logs/stock_analysis_当前日期.log`
   - 内容：包含程序运行的详细日志，包括分析进度和发现的符合条件的股票

2. 选股结果
   - 位置：
     - 双均线策略：`stocks/double_ma_stocks_当前日期.txt`
     - 均线金叉策略：`stocks/ma_stocks_当前日期.txt`
   - 内容：列出当天所有符合条件的股票代码

## 自动化运行
项目已配置GitHub Actions工作流，实现每个交易日（周一至周五）下午3点自动运行分析并更新结果：

1. 均线金叉策略自动分析
   - 配置文件：`.github/workflows/ma_analysis.yml`
   - 执行时间：每个交易日下午3点
   - 自动更新：`stocks/ma_stocks.txt`和相关日志

2. 双均线多头排列策略自动分析
   - 配置文件：`.github/workflows/double_ma_analysis.yml`
   - 执行时间：每个交易日下午3点
   - 自动更新：`stocks/double_ma_stocks.txt`和相关日志

所有分析结果都会自动提交到仓库，您可以在GitHub上查看每日更新的选股结果。

## 注意事项
1. 本工具仅供学习和参考，不构成任何投资建议
2. 使用前请确保安装了所有必要的依赖包
3. 建议在A股交易时段运行，以获取最新的市场数据