#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩3D开奖数据分析
- 遗漏期数分析
- 胆码规律触发条件分析
"""

import csv
import os
from collections import defaultdict


def load_data(filepath="3d_lottery_data.csv"):
    """加载开奖数据"""
    data = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "issue": row.get("\u671f\u53f7", row.get(list(row.keys())[0])),
                "number": row.get("\u5f00\u5956\u53f7\u7801", ""),
                "hundreds": row.get("\u767e\u4f4d", ""),
                "tens": row.get("\u5341\u4f4d", ""),
                "ones": row.get("\u4e2a\u4f4d", ""),
            })
    # 尝试用列索引读取（兼容不同编码的表头）
    if not data or not data[0]["number"]:
        data = []
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) >= 5:
                    data.append({
                        "issue": row[0],
                        "number": row[1],
                        "hundreds": row[2],
                        "tens": row[3],
                        "ones": row[4],
                    })
    # 按期号排序（旧到新）
    data.sort(key=lambda x: x["issue"])
    return data


def analyze_missing(data):
    """
    遗漏期数分析
    统计每个位置每个数字当前遗漏期数，以及历史最大遗漏、平均遗漏
    """
    positions = {
        "\u767e\u4f4d": [d["hundreds"] for d in data],
        "\u5341\u4f4d": [d["tens"] for d in data],
        "\u4e2a\u4f4d": [d["ones"] for d in data],
    }
    
    results = {}
    
    for pos_name, digits in positions.items():
        pos_result = {}
        for num in range(10):
            num_str = str(num)
            
            # 当前遗漏（从最新一期往前数）
            current_missing = 0
            for d in reversed(digits):
                if d == num_str:
                    break
                current_missing += 1
            
            # 历史遗漏数据
            missing_periods = []
            current_streak = 0
            for d in digits:
                if d == num_str:
                    if current_streak > 0:
                        missing_periods.append(current_streak)
                    current_streak = 0
                else:
                    current_streak += 1
            
            max_missing = max(missing_periods) if missing_periods else 0
            avg_missing = round(sum(missing_periods) / len(missing_periods), 1) if missing_periods else 0
            total_appearances = sum(1 for d in digits if d == num_str)
            
            pos_result[num] = {
                "current": current_missing,
                "max": max_missing,
                "avg": avg_missing,
                "appearances": total_appearances,
                "frequency": round(total_appearances / len(digits) * 100, 1),
            }
        results[pos_name] = pos_result
    
    return results


def analyze_danma_rules(data):
    """
    胆码规律触发条件分析
    """
    positions = {
        "\u767e\u4f4d": [d["hundreds"] for d in data],
        "\u5341\u4f4d": [d["tens"] for d in data],
        "\u4e2a\u4f4d": [d["ones"] for d in data],
    }
    
    all_numbers = [d["number"] for d in data]
    
    results = {}
    
    for pos_name, digits in positions.items():
        pos_result = {}
        for num in range(10):
            num_str = str(num)
            
            # 1. 连出次数（连续出现2期及以上）
            consecutive_count = 0
            max_consecutive = 0
            current_consecutive = 0
            for i, d in enumerate(digits):
                if d == num_str:
                    current_consecutive += 1
                    if current_consecutive >= 2:
                        consecutive_count += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
            
            # 2. 间隔1期出现次数
            gap1_count = 0
            for i in range(len(digits) - 2):
                if digits[i] == num_str and digits[i+2] == num_str and digits[i+1] != num_str:
                    gap1_count += 1
            
            # 3. 间隔2期出现次数
            gap2_count = 0
            for i in range(len(digits) - 3):
                if digits[i] == num_str and digits[i+3] == num_str and digits[i+1] != num_str and digits[i+2] != num_str:
                    gap2_count += 1
            
            # 4. 热号判定（近10期出现3次及以上）
            recent_10 = digits[-10:]
            recent_count = sum(1 for d in recent_10 if d == num_str)
            is_hot = recent_count >= 3
            
            # 5. 冷号判定（近20期出现2次及以下）
            recent_20 = digits[-20:]
            recent_20_count = sum(1 for d in recent_20 if d == num_str)
            is_cold = recent_20_count <= 2
            
            pos_result[num] = {
                "consecutive_count": consecutive_count,
                "max_consecutive": max_consecutive,
                "gap1_count": gap1_count,
                "gap2_count": gap2_count,
                "recent_10": recent_count,
                "is_hot": is_hot,
                "recent_20": recent_20_count,
                "is_cold": is_cold,
            }
        results[pos_name] = pos_result
    
    # 整体号码分析（不区分位置）
    overall = {}
    for num in range(10):
        num_str = str(num)
        # 统计该数字在最近10期开奖号中出现次数（任意位置）
        recent_10_numbers = all_numbers[-10:]
        count_in_recent = sum(n.count(num_str) for n in recent_10_numbers)
        overall[num] = {
            "recent_10_any_position": count_in_recent,
        }
    results["\u4efb\u610f\u4f4d"] = overall
    
    return results


def print_missing_report(missing_data, data):
    """打印遗漏期数报告"""
    print("=" * 60)
    print("  \u9057\u6f0f\u671f\u6570\u5206\u6790\u62a5\u544a")
    print("=" * 60)
    print(f"\u5206\u6790\u671f\u6570: {len(data)} \u671f  |  \u6700\u65b0\u671f\u53f7: {data[-1]['issue']}  |  \u6700\u65b0\u5f00\u5956\u53f7: {data[-1]['number']}")
    print("-" * 60)
    
    for pos_name in ["\u767e\u4f4d", "\u5341\u4f4d", "\u4e2a\u4f4d"]:
        print(f"\n【{pos_name}】")
        print(f"{'\u6570\u5b57':<4} {'\u5f53\u524d\u9057\u6f0f':<8} {'\u5386\u53f2\u6700\u5927':<8} {'\u5e73\u5747\u9057\u6f0f':<8} {'\u51fa\u73b0\u6b21\u6570':<8} {'\u51fa\u73b0\u7387':<6}")
        print("-" * 50)
        
        # 按当前遗漏降序排列
        items = sorted(missing_data[pos_name].items(), key=lambda x: x[1]["current"], reverse=True)
        for num, info in items:
            print(f"{num:<6} {info['current']:<10} {info['max']:<10} {info['avg']:<10} {info['appearances']:<10} {info['frequency']}%")


def print_danma_report(danma_data, data):
    """打印胆码规律报告"""
    print("\n" + "=" * 60)
    print("  \u80c6\u7801\u89c4\u5f8b\u89e6\u53d1\u6761\u4ef6\u5206\u6790")
    print("=" * 60)
    
    for pos_name in ["\u767e\u4f4d", "\u5341\u4f4d", "\u4e2a\u4f4d"]:
        print(f"\n【{pos_name}】")
        print(f"{'\u6570\u5b57':<4} {'\u8fd110\u671f':<8} {'\u70ed\u53f7':<6} {'\u8fd120\u671f':<8} {'\u51b7\u53f7':<6} {'\u8fde\u51fa\u6b21':<8} {'\u6700\u5927\u8fde\u51fa':<8} {'\u95f4\u96941\u671f':<8} {'\u95f4\u96942\u671f':<8}")
        print("-" * 70)
        
        # 按近10期出现次数降序排列
        items = sorted(danma_data[pos_name].items(), key=lambda x: x[1]["recent_10"], reverse=True)
        for num, info in items:
            hot_mark = "*" if info["is_hot"] else ""
            cold_mark = "*" if info["is_cold"] else ""
            print(f"{num:<6} {info['recent_10']:<10} {hot_mark:<6} {info['recent_20']:<10} {cold_mark:<6} {info['consecutive_count']:<10} {info['max_consecutive']:<10} {info['gap1_count']:<10} {info['gap2_count']:<10}")
    
    # 推荐胆码
    print("\n" + "=" * 60)
    print("  \u80c6\u7801\u63a8\u8350")
    print("=" * 60)
    
    for pos_name in ["\u767e\u4f4d", "\u5341\u4f4d", "\u4e2a\u4f4d"]:
        hot_nums = [n for n, info in danma_data[pos_name].items() if info["is_hot"]]
        cold_nums = [n for n, info in danma_data[pos_name].items() if info["is_cold"]]
        print(f"\n【{pos_name}】")
        if hot_nums:
            print(f"  \u70ed\u53f7 (\u8fd110\u671f\u51fa\u73b03+\u6b21): {', '.join(map(str, hot_nums))}")
        else:
            print(f"  \u70ed\u53f7: \u6682\u65e0")
        if cold_nums:
            print(f"  \u51b7\u53f7 (\u8fd120\u671f\u51fa\u73b02-\u6b21): {', '.join(map(str, cold_nums))}")
        else:
            print(f"  \u51b7\u53f7: \u6682\u65e0")
    
    # 遗漏触发建议
    print("\n" + "=" * 60)
    print("  \u9057\u6f0f\u89e6\u53d1\u5efa\u8bae")
    print("=" * 60)
    
    for pos_name in ["\u767e\u4f4d", "\u5341\u4f4d", "\u4e2a\u4f4d"]:
        print(f"\n【{pos_name}】")
        for num, info in danma_data[pos_name].items():
            # 如果间隔1期规律较明显（出现2次以上）
            if info["gap1_count"] >= 2:
                print(f"  \u6570\u5b57 {num}: \u95f4\u96941\u671f\u89c4\u5f8b\u660e\u663e (\u51fa\u73b0{info['gap1_count']}\u6b21)")


def save_analysis_report(missing_data, danma_data, data, filepath="3d_analysis_report.txt"):
    """保存分析报告到文件"""
    import sys
    from io import StringIO
    
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    
    print_missing_report(missing_data, data)
    print_danma_report(danma_data, data)
    
    sys.stdout = old_stdout
    report = buffer.getvalue()
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n\u5206\u6790\u62a5\u544a\u5df2\u4fdd\u5b58\u5230: {os.path.abspath(filepath)}")


def main():
    filepath = "3d_lottery_data.csv"
    
    if not os.path.exists(filepath):
        print(f"\u6570\u636e\u6587\u4ef6\u4e0d\u5b58\u5728: {filepath}")
        print("\u8bf7\u5148\u8fd0\u884c fetch_3d_lottery.py \u6293\u53d6\u6570\u636e")
        return
    
    data = load_data(filepath)
    print(f"\u5df2\u52a0\u8f7d {len(data)} \u671f\u5f00\u5956\u6570\u636e")
    
    missing_data = analyze_missing(data)
    danma_data = analyze_danma_rules(data)
    
    print_missing_report(missing_data, data)
    print_danma_report(danma_data, data)
    
    save_analysis_report(missing_data, danma_data, data, "3d_analysis_report.txt")


if __name__ == "__main__":
    main()
