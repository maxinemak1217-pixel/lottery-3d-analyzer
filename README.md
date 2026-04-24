# 福彩3D数据分析器

自动抓取中彩网福彩3D开奖数据，进行遗漏期数分析、胆码规律分析，并生成可视化HTML报告。

## 文件说明

| 文件 | 说明 |
|---|---|
| fetch_3d_lottery.py | 数据抓取脚本 |
| analyze_3d_lottery.py | 基础分析脚本 |
| analyze_3d_advanced.py | 高级分析+投注+可视化脚本 |
| run_3d_daily.bat | 每日自动运行批处理 |
| 3d_lottery_data.csv | 开奖原始数据 |
| 3d_analysis_report.txt | 文字版分析报告 |
| index.html | 可视化HTML报告 |

## 在线报告

https://maxinemak1217-pixel.github.io/lottery-3d-analyzer/

## 使用方法

`ash
# 抓取数据
python fetch_3d_lottery.py

# 高级分析+可视化
python analyze_3d_advanced.py
`

## 数据来源

中彩网 3D 开奖走势图: https://www.zhcw.com/c/2019-08-19/580353.shtml
