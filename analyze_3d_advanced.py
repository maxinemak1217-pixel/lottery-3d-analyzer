#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩3D高级分析系统
- 遗漏期数分析
- 胆码规律触发条件
- 和值、跨度、奇偶比、大小比、012路、和尾统计
- 投注号码组合生成
- 可视化HTML报告
"""

import csv
import os
import json
from collections import defaultdict
from datetime import datetime


def load_data(filepath="3d_lottery_data.csv"):
    """加载开奖数据"""
    data = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) >= 5:
                data.append({
                    "issue": row[0],
                    "number": row[1],
                    "hundreds": int(row[2]),
                    "tens": int(row[3]),
                    "ones": int(row[4]),
                    "a": int(row[2]),
                    "b": int(row[3]),
                    "c": int(row[4]),
                })
    data.sort(key=lambda x: x["issue"])
    return data


def calc_sum_value(d):
    """和值 = 三个数字之和"""
    return d["a"] + d["b"] + d["c"]


def calc_span(d):
    """跨度 = 最大数字 - 最小数字"""
    nums = [d["a"], d["b"], d["c"]]
    return max(nums) - min(nums)


def calc_odd_even(d):
    """奇偶比，返回 (奇数个数, 偶数个数)"""
    nums = [d["a"], d["b"], d["c"]]
    odd = sum(1 for n in nums if n % 2 == 1)
    even = 3 - odd
    return odd, even


def calc_big_small(d):
    """大小比，0-4为小，5-9为大，返回 (大数个数, 小数个数)"""
    nums = [d["a"], d["b"], d["c"]]
    big = sum(1 for n in nums if n >= 5)
    small = 3 - big
    return big, small


def calc_012(d):
    """012路，返回 (0路个数, 1路个数, 2路个数)"""
    nums = [d["a"], d["b"], d["c"]]
    r0 = sum(1 for n in nums if n % 3 == 0)
    r1 = sum(1 for n in nums if n % 3 == 1)
    r2 = sum(1 for n in nums if n % 3 == 2)
    return r0, r1, r2


def calc_prime_composite(d):
    """质合比，质数: 2,3,5,7，返回 (质数个数, 合数个数)"""
    primes = {2, 3, 5, 7}
    nums = [d["a"], d["b"], d["c"]]
    prime = sum(1 for n in nums if n in primes)
    composite = sum(1 for n in nums if n not in primes and n > 1)
    # 0 和 1 不算质数也不算合数
    neither = sum(1 for n in nums if n in (0, 1))
    return prime, composite, neither


def analyze_advanced(data):
    """计算所有高级统计指标"""
    stats = []
    sum_values = []
    spans = []
    odd_even = []
    big_small = []
    routes_012 = []
    sum_tails = []
    prime_composite = []

    for d in data:
        s = calc_sum_value(d)
        sp = calc_span(d)
        oe = calc_odd_even(d)
        bs = calc_big_small(d)
        r012 = calc_012(d)
        st = s % 10
        pc = calc_prime_composite(d)

        stats.append({
            "issue": d["issue"],
            "number": d["number"],
            "sum": s,
            "span": sp,
            "odd_even": f"{oe[0]}奇{oe[1]}偶",
            "big_small": f"{bs[0]}大{bs[1]}小",
            "route_012": f"{r012[0]}路{r012[1]}路{r012[2]}路",
            "sum_tail": st,
            "prime_composite": f"{pc[0]}质{pc[1]}合",
            "a": d["a"], "b": d["b"], "c": d["c"],
        })
        sum_values.append(s)
        spans.append(sp)
        odd_even.append(oe)
        big_small.append(bs)
        routes_012.append(r012)
        sum_tails.append(st)
        prime_composite.append(pc)

    # 汇总统计
    sum_dist = defaultdict(int)
    span_dist = defaultdict(int)
    oe_dist = defaultdict(int)
    bs_dist = defaultdict(int)
    r012_dist = defaultdict(int)
    tail_dist = defaultdict(int)

    for s in sum_values:
        sum_dist[s] += 1
    for sp in spans:
        span_dist[sp] += 1
    for oe in odd_even:
        oe_dist[f"{oe[0]}奇{oe[1]}偶"] += 1
    for bs in big_small:
        bs_dist[f"{bs[0]}大{bs[1]}小"] += 1
    for r in routes_012:
        r012_dist[f"{r[0]}:{r[1]}:{r[2]}"] += 1
    for t in sum_tails:
        tail_dist[t] += 1

    return stats, {
        "sum_dist": dict(sum_dist),
        "span_dist": dict(span_dist),
        "oe_dist": dict(oe_dist),
        "bs_dist": dict(bs_dist),
        "r012_dist": dict(r012_dist),
        "tail_dist": dict(tail_dist),
    }


def generate_bets(data):
    """生成投注号码组合"""
    positions = {
        "bai": [d["a"] for d in data],
        "shi": [d["b"] for d in data],
        "ge": [d["c"] for d in data],
    }

    bets = {
        "strategy_missing": [],
        "strategy_hot": [],
        "strategy_gap": [],
        "strategy_combined": [],
        "straight_bets": [],
    }

    # 策略1: 大遗漏号码（超过历史最大或接近）
    for pos_name, digits in positions.items():
        for num in range(10):
            # 当前遗漏
            current_missing = 0
            for d in reversed(digits):
                if d == num:
                    break
                current_missing += 1
            # 历史最大遗漏
            missing_periods = []
            streak = 0
            for d in digits:
                if d == num:
                    if streak > 0:
                        missing_periods.append(streak)
                    streak = 0
                else:
                    streak += 1
            max_missing = max(missing_periods) if missing_periods else 0

            if current_missing > max_missing:
                bets["strategy_missing"].append({
                    "pos": pos_name,
                    "num": num,
                    "current": current_missing,
                    "max": max_missing,
                    "reason": f"遗漏{current_missing}期，超历史最大{max_missing}期",
                })

    # 策略2: 热号（近10期出现3次以上）
    for pos_name, digits in positions.items():
        recent = digits[-10:]
        for num in range(10):
            count = sum(1 for d in recent if d == num)
            if count >= 3:
                bets["strategy_hot"].append({
                    "pos": pos_name,
                    "num": num,
                    "recent_count": count,
                    "reason": f"近10期出现{count}次，热号",
                })

    # 策略3: 间隔1期规律（近100期出现2次以上）
    for pos_name, digits in positions.items():
        for num in range(10):
            gap1_count = 0
            for i in range(len(digits) - 2):
                if digits[i] == num and digits[i+2] == num and digits[i+1] != num:
                    gap1_count += 1
            if gap1_count >= 2:
                # 检查当前是否刚出现，间隔1期后可能再次出现
                last_idx = -1
                for i in range(len(digits) - 1, -1, -1):
                    if digits[i] == num:
                        last_idx = i
                        break
                gap_from_end = len(digits) - 1 - last_idx if last_idx >= 0 else 999
                bets["strategy_gap"].append({
                    "pos": pos_name,
                    "num": num,
                    "gap1_count": gap1_count,
                    "last_gap": gap_from_end,
                    "reason": f"间隔1期规律出现{gap1_count}次",
                })

    # 策略4: 综合胆码（结合遗漏+热号）
    for pos_name, digits in positions.items():
        for num in range(10):
            score = 0
            reasons = []

            # 大遗漏加分
            current_missing = 0
            for d in reversed(digits):
                if d == num:
                    break
                current_missing += 1
            missing_periods = []
            streak = 0
            for d in digits:
                if d == num:
                    if streak > 0:
                        missing_periods.append(streak)
                    streak = 0
                else:
                    streak += 1
            max_missing = max(missing_periods) if missing_periods else 0
            if current_missing > max_missing:
                score += 5
                reasons.append(f"大遗漏+{current_missing}")

            # 热号加分
            recent = digits[-10:]
            count = sum(1 for d in recent if d == num)
            if count >= 3:
                score += 3
                reasons.append(f"热号{count}")
            elif count >= 2:
                score += 1
                reasons.append(f"温号{count}")

            # 间隔规律加分
            gap1_count = 0
            for i in range(len(digits) - 2):
                if digits[i] == num and digits[i+2] == num and digits[i+1] != num:
                    gap1_count += 1
            if gap1_count >= 3:
                score += 2
                reasons.append(f"间隔{gap1_count}")

            if score >= 4:
                bets["strategy_combined"].append({
                    "pos": pos_name,
                    "num": num,
                    "score": score,
                    "reason": ", ".join(reasons),
                })

    # 生成直选号码组合（每位选3个胆码组合）
    def get_top_candidates(pos_name, digits, n=3):
        candidates = []
        for num in range(10):
            score = 0
            current_missing = 0
            for d in reversed(digits):
                if d == num:
                    break
                current_missing += 1
            # 遗漏越大越值得关注
            score += min(current_missing, 20)
            recent = digits[-10:]
            count = sum(1 for d in recent if d == num)
            score += count * 3
            gap1 = 0
            for i in range(len(digits) - 2):
                if digits[i] == num and digits[i+2] == num and digits[i+1] != num:
                    gap1 += 1
            score += gap1 * 2
            candidates.append((num, score))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates[:n]]

    bai_candidates = get_top_candidates("bai", positions["bai"])
    shi_candidates = get_top_candidates("shi", positions["shi"])
    ge_candidates = get_top_candidates("ge", positions["ge"])

    straight = []
    for a in bai_candidates:
        for b in shi_candidates:
            for c in ge_candidates:
                straight.append(f"{a}{b}{c}")
    bets["straight_bets"] = straight[:27]
    bets["bai_candidates"] = bai_candidates
    bets["shi_candidates"] = shi_candidates
    bets["ge_candidates"] = ge_candidates

    return bets


def build_html_report(data, stats, summary, bets, missing_data, danma_data, filepath="3d_visual_report.html"):
    """生成可视化HTML报告（使用ECharts）"""

    # 准备图表数据
    issues = [s["issue"] for s in stats]
    sums = [s["sum"] for s in stats]
    spans = [s["span"] for s in stats]
    sum_tails = [s["sum_tail"] for s in stats]

    # 遗漏数据
    miss_bai = [missing_data["\u767e\u4f4d"][i]["current"] for i in range(10)]
    miss_shi = [missing_data["\u5341\u4f4d"][i]["current"] for i in range(10)]
    miss_ge = [missing_data["\u4e2a\u4f4d"][i]["current"] for i in range(10)]

    # 和值分布
    sum_labels = list(range(0, 28))
    sum_values_chart = [summary["sum_dist"].get(str(i), 0) for i in sum_labels]

    # 跨度分布
    span_labels = list(range(0, 10))
    span_values_chart = [summary["span_dist"].get(str(i), 0) for i in span_labels]

    # 和尾分布
    tail_labels = list(range(0, 10))
    tail_values_chart = [summary["tail_dist"].get(str(i), 0) for i in tail_labels]

    # 奇偶分布
    oe_labels = list(summary["oe_dist"].keys())
    oe_values = list(summary["oe_dist"].values())

    # 大小分布
    bs_labels = list(summary["bs_dist"].keys())
    bs_values = list(summary["bs_dist"].values())

    # 012路分布
    r012_labels = list(summary["r012_dist"].keys())
    r012_values = list(summary["r012_dist"].values())

    # 投注推荐
    bet_html = ""
    if bets["strategy_missing"]:
        bet_html += "<h3>大遗漏号码</h3><table><tr><th>位置</th><th>数字</th><th>当前遗漏</th><th>历史最大</th><th>说明</th></tr>"
        for b in bets["strategy_missing"]:
            pos_map = {"bai": "\u767e\u4f4d", "shi": "\u5341\u4f4d", "ge": "\u4e2a\u4f4d"}
            bet_html += f"<tr><td>{pos_map.get(b['pos'], b['pos'])}</td><td><b>{b['num']}</b></td><td>{b['current']}</td><td>{b['max']}</td><td>{b['reason']}</td></tr>"
        bet_html += "</table>"

    if bets["strategy_hot"]:
        bet_html += "<h3>热号号码</h3><table><tr><th>位置</th><th>数字</th><th>近10期出现</th><th>说明</th></tr>"
        for b in bets["strategy_hot"]:
            pos_map = {"bai": "\u767e\u4f4d", "shi": "\u5341\u4f4d", "ge": "\u4e2a\u4f4d"}
            bet_html += f"<tr><td>{pos_map.get(b['pos'], b['pos'])}</td><td><b>{b['num']}</b></td><td>{b['recent_count']}</td><td>{b['reason']}</td></tr>"
        bet_html += "</table>"

    if bets["strategy_combined"]:
        bet_html += "<h3>综合推荐胆码</h3><table><tr><th>位置</th><th>数字</th><th>评分</th><th>说明</th></tr>"
        for b in sorted(bets["strategy_combined"], key=lambda x: x["score"], reverse=True):
            pos_map = {"bai": "\u767e\u4f4d", "shi": "\u5341\u4f4d", "ge": "\u4e2a\u4f4d"}
            bet_html += f"<tr><td>{pos_map.get(b['pos'], b['pos'])}</td><td><b>{b['num']}</b></td><td>{b['score']}</td><td>{b['reason']}</td></tr>"
        bet_html += "</table>"

    if bets["straight_bets"]:
        bet_html += f"<h3>直选号码组合（每位候选: 百位{bets['bai_candidates']}, 十位{bets['shi_candidates']}, 个位{bets['ge_candidates']}）</h3>"
        bet_html += "<div style='display:flex;flex-wrap:wrap;gap:8px;'>"
        for num in bets["straight_bets"]:
            bet_html += f"<span class='bet-num'>{num}</span>"
        bet_html += "</div>"

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>福彩3D高级分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
body {{ font-family: "Microsoft YaHei", Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
.container {{ max-width: 1400px; margin: 0 auto; }}
h1 {{ text-align: center; color: #c41e3a; }}
h2 {{ color: #333; border-left: 4px solid #c41e3a; padding-left: 12px; margin-top: 30px; }}
h3 {{ color: #555; }}
.info {{ background: #fff; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.chart-box {{ background: #fff; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.chart {{ width: 100%; height: 350px; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; background: #fff; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: center; }}
th {{ background: #c41e3a; color: white; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.bet-num {{ display: inline-block; padding: 8px 16px; background: #c41e3a; color: white; border-radius: 20px; font-weight: bold; font-size: 16px; }}
.highlight {{ color: #c41e3a; font-weight: bold; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
<h1>福彩3D 高级数据分析报告</h1>
<div class="info">
    <b>生成时间：</b>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
    <b>分析期数：</b>{len(data)} 期（期号 {data[0]["issue"]} ~ {data[-1]["issue"]}）<br>
    <b>最新开奖：</b>期号 <span class="highlight">{data[-1]["issue"]}</span>，号码 <span class="highlight">{data[-1]["number"][0]} {data[-1]["number"][1]} {data[-1]["number"][2]}</span>
</div>

<h2>一、投注号码推荐</h2>
<div class="info">
{bet_html}
</div>

<h2>二、遗漏期数可视化</h2>
<div class="grid">
    <div class="chart-box"><div id="missBai" class="chart"></div></div>
    <div class="chart-box"><div id="missShi" class="chart"></div></div>
    <div class="chart-box"><div id="missGe" class="chart"></div></div>
</div>

<h2>三、走势图表</h2>
<div class="chart-box"><div id="sumTrend" class="chart"></div></div>
<div class="chart-box"><div id="spanTrend" class="chart"></div></div>

<h2>四、分布统计</h2>
<div class="grid">
    <div class="chart-box"><div id="sumDist" class="chart"></div></div>
    <div class="chart-box"><div id="spanDist" class="chart"></div></div>
    <div class="chart-box"><div id="tailDist" class="chart"></div></div>
    <div class="chart-box"><div id="oeDist" class="chart"></div></div>
    <div class="chart-box"><div id="bsDist" class="chart"></div></div>
    <div class="chart-box"><div id="r012Dist" class="chart"></div></div>
</div>

<h2>五、近20期详细数据</h2>
<table>
<tr><th>期号</th><th>开奖号</th><th>和值</th><th>跨度</th><th>奇偶比</th><th>大小比</th><th>012路</th><th>和尾</th><th>质合比</th></tr>
'''
    for s in stats[-20:]:
        html += f"<tr><td>{s['issue']}</td><td><b>{s['number'][0]} {s['number'][1]} {s['number'][2]}</b></td><td>{s['sum']}</td><td>{s['span']}</td><td>{s['odd_even']}</td><td>{s['big_small']}</td><td>{s['route_012']}</td><td>{s['sum_tail']}</td><td>{s['prime_composite']}</td></tr>"

    html += f'''
</table>
</div>
<script>
// 遗漏期数 - 百位
var missBai = echarts.init(document.getElementById('missBai'));
missBai.setOption({{
    title: {{ text: '百位遗漏期数', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {json.dumps([str(i) for i in range(10)])} }},
    yAxis: {{ type: 'value', name: '遗漏期数' }},
    series: [{{ data: {json.dumps(miss_bai)}, type: 'bar', itemStyle: {{ color: function(p) {{ return p.value > 20 ? '#c41e3a' : '#5470c6'; }} }} }}]
}});

// 遗漏期数 - 十位
var missShi = echarts.init(document.getElementById('missShi'));
missShi.setOption({{
    title: {{ text: '十位遗漏期数', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {json.dumps([str(i) for i in range(10)])} }},
    yAxis: {{ type: 'value', name: '遗漏期数' }},
    series: [{{ data: {json.dumps(miss_shi)}, type: 'bar', itemStyle: {{ color: function(p) {{ return p.value > 20 ? '#c41e3a' : '#91cc75'; }} }} }}]
}});

// 遗漏期数 - 个位
var missGe = echarts.init(document.getElementById('missGe'));
missGe.setOption({{
    title: {{ text: '个位遗漏期数', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {json.dumps([str(i) for i in range(10)])} }},
    yAxis: {{ type: 'value', name: '遗漏期数' }},
    series: [{{ data: {json.dumps(miss_ge)}, type: 'bar', itemStyle: {{ color: function(p) {{ return p.value > 20 ? '#c41e3a' : '#fac858'; }} }} }}]
}});

// 和值走势
var sumTrend = echarts.init(document.getElementById('sumTrend'));
sumTrend.setOption({{
    title: {{ text: '和值走势', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {json.dumps(issues[-30:])}, axisLabel: {{ rotate: 45 }} }},
    yAxis: {{ type: 'value', name: '和值', min: 0, max: 27 }},
    series: [{{ data: {json.dumps(sums[-30:])}, type: 'line', smooth: true, itemStyle: {{ color: '#c41e3a' }}, areaStyle: {{ opacity: 0.1 }} }}]
}});

// 跨度走势
var spanTrend = echarts.init(document.getElementById('spanTrend'));
spanTrend.setOption({{
    title: {{ text: '跨度走势', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {json.dumps(issues[-30:])}, axisLabel: {{ rotate: 45 }} }},
    yAxis: {{ type: 'value', name: '跨度', min: 0, max: 9 }},
    series: [{{ data: {json.dumps(spans[-30:])}, type: 'line', smooth: true, itemStyle: {{ color: '#5470c6' }} }}]
}});

// 和值分布
var sumDist = echarts.init(document.getElementById('sumDist'));
sumDist.setOption({{
    title: {{ text: '和值分布', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {json.dumps(sum_labels)} }},
    yAxis: {{ type: 'value', name: '次数' }},
    series: [{{ data: {json.dumps(sum_values_chart)}, type: 'bar', itemStyle: {{ color: '#c41e3a' }} }}]
}});

// 跨度分布
var spanDist = echarts.init(document.getElementById('spanDist'));
spanDist.setOption({{
    title: {{ text: '跨度分布', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {json.dumps(span_labels)} }},
    yAxis: {{ type: 'value', name: '次数' }},
    series: [{{ data: {json.dumps(span_values_chart)}, type: 'bar', itemStyle: {{ color: '#5470c6' }} }}]
}});

// 和尾分布
var tailDist = echarts.init(document.getElementById('tailDist'));
tailDist.setOption({{
    title: {{ text: '和尾分布', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: {json.dumps(tail_labels)} }},
    yAxis: {{ type: 'value', name: '次数' }},
    series: [{{ data: {json.dumps(tail_values_chart)}, type: 'bar', itemStyle: {{ color: '#91cc75' }} }}]
}});

// 奇偶分布
var oeDist = echarts.init(document.getElementById('oeDist'));
oeDist.setOption({{
    title: {{ text: '奇偶比分布', left: 'center' }},
    tooltip: {{ trigger: 'item' }},
    series: [{{ type: 'pie', radius: '60%', data: {json.dumps([{"name": k, "value": v} for k, v in zip(oe_labels, oe_values)])} }}]
}});

// 大小分布
var bsDist = echarts.init(document.getElementById('bsDist'));
bsDist.setOption({{
    title: {{ text: '大小比分布', left: 'center' }},
    tooltip: {{ trigger: 'item' }},
    series: [{{ type: 'pie', radius: '60%', data: {json.dumps([{"name": k, "value": v} for k, v in zip(bs_labels, bs_values)])} }}]
}});

// 012路分布
var r012Dist = echarts.init(document.getElementById('r012Dist'));
r012Dist.setOption({{
    title: {{ text: '012路分布', left: 'center' }},
    tooltip: {{ trigger: 'item' }},
    series: [{{ type: 'pie', radius: '60%', data: {json.dumps([{"name": k, "value": v} for k, v in zip(r012_labels, r012_values)])} }}]
}});

window.addEventListener('resize', function() {{
    missBai.resize(); missShi.resize(); missGe.resize();
    sumTrend.resize(); spanTrend.resize();
    sumDist.resize(); spanDist.resize(); tailDist.resize();
    oeDist.resize(); bsDist.resize(); r012Dist.resize();
}});
</script>
</body>
</html>
'''

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\u53ef\u89c6\u5316\u62a5\u544a\u5df2\u751f\u6210: {os.path.abspath(filepath)}")


def main():
    filepath = "3d_lottery_data.csv"
    if not os.path.exists(filepath):
        print(f"\u6570\u636e\u6587\u4ef6\u4e0d\u5b58\u5728: {filepath}")
        return

    data = load_data(filepath)
    print(f"\u5df2\u52a0\u8f7d {len(data)} \u671f\u5f00\u5956\u6570\u636e")

    # 高级统计
    stats, summary = analyze_advanced(data)
    print("\u9ad8\u7ea7\u7edf\u8ba1\u6307\u6807\u8ba1\u7b97\u5b8c\u6210")

    # 加载之前的遗漏和胆码分析
    from analyze_3d_lottery import analyze_missing, analyze_danma_rules
    missing_data = analyze_missing(data)
    danma_data = analyze_danma_rules(data)

    # 生成投注号码
    bets = generate_bets(data)
    print("\u6295\u6ce8\u53f7\u7801\u7ec4\u5408\u751f\u6210\u5b8c\u6210")

    # 打印投注推荐
    print("\n" + "=" * 60)
    print("  \u6295\u6ce8\u53f7\u7801\u63a8\u8350")
    print("=" * 60)

    if bets["strategy_missing"]:
        print("\n\u3010\u5927\u9057\u6f0f\u53f7\u7801\u3011")
        for b in bets["strategy_missing"]:
            print(f"  {b['pos']} \u6570\u5b57 {b['num']}: {b['reason']}")

    if bets["strategy_hot"]:
        print("\n\u3010\u70ed\u53f7\u7801\u7801\u3011")
        for b in bets["strategy_hot"]:
            print(f"  {b['pos']} \u6570\u5b57 {b['num']}: {b['reason']}")

    if bets["strategy_combined"]:
        print("\n\u3010\u7efc\u5408\u80c6\u7801\u63a8\u8350\u3011")
        for b in sorted(bets["strategy_combined"], key=lambda x: x["score"], reverse=True)[:15]:
            print(f"  {b['pos']} \u6570\u5b57 {b['num']}: \u8bc4\u5206{b['score']}, {b['reason']}")

    print(f"\n\u3010\u76f4\u9009\u53f7\u7801\u7ec4\u5408\u3011")
    print(f"  \u767e\u4f4d\u5019\u9009: {bets['bai_candidates']}")
    print(f"  \u5341\u4f4d\u5019\u9009: {bets['shi_candidates']}")
    print(f"  \u4e2a\u4f4d\u5019\u9009: {bets['ge_candidates']}")
    print(f"  \u76f4\u9009\u7ec4\u5408 ({len(bets['straight_bets'])} \u6ce8):")
    for i in range(0, len(bets['straight_bets']), 9):
        print("  " + "  ".join(bets['straight_bets'][i:i+9]))

    # 生成HTML报告
    build_html_report(data, stats, summary, bets, missing_data, danma_data, "3d_visual_report.html")

    print("\n\u5206\u6790\u5b8c\u6210\uff01\u8bf7\u7528\u6d4f\u89c8\u5668\u6253\u5f00 3d_visual_report.html \u67e5\u770b\u53ef\u89c6\u5316\u62a5\u544a\u3002")


if __name__ == "__main__":
    main()
