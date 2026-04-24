#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩3D 胆码规律触发条件遗漏期数分析器
统计9条规则在历史数据中的触发情况及未来1-3期命中/遗漏
"""

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime

# Windows PowerShell GBK 编码修复
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("警告: 未安装 requests 或 beautifulsoup4，将使用本地数据模式")
    print("如需自动抓数据，请运行: pip install requests beautifulsoup4")

# ===================== 规则定义 =====================
RULES = [
    {
        "id": 1,
        "name": "规则1: 百位=6 → 后两位∈{50,51,53}",
        "trigger": lambda h, t, g: h == 6,
        "target":  lambda h, t, g: (t == 5 and g in [0, 1, 3]),
    },
    {
        "id": 2,
        "name": "规则2: 百位=8 → 包含胆码5",
        "trigger": lambda h, t, g: h == 8,
        "target":  lambda h, t, g: 5 in [h, t, g],
    },
    {
        "id": 3,
        "name": "规则3: 百位=9 → 包含胆码2",
        "trigger": lambda h, t, g: h == 9,
        "target":  lambda h, t, g: 2 in [h, t, g],
    },
    {
        "id": 4,
        "name": "规则4: 十位=3 → 包含胆码2或9",
        "trigger": lambda h, t, g: t == 3,
        "target":  lambda h, t, g: 2 in [h, t, g] or 9 in [h, t, g],
    },
    {
        "id": 5,
        "name": "规则5: 十位=0 → 出现组三",
        "trigger": lambda h, t, g: t == 0,
        "target":  lambda h, t, g: is_zusan(h, t, g),
    },
    {
        "id": 6,
        "name": "规则6: 出现组三 → 跨度=9",
        "trigger": lambda h, t, g: is_zusan(h, t, g),
        "target":  lambda h, t, g: (max(h, t, g) - min(h, t, g)) == 9,
    },
    {
        "id": 7,
        "name": "规则7: 十位=1 → 冷码8回补",
        "trigger": lambda h, t, g: t == 1,
        "target":  lambda h, t, g: 8 in [h, t, g],
    },
    {
        "id": 8,
        "name": "规则8: 百位=0 → 包含胆码4或5,或十位=5",
        "trigger": lambda h, t, g: h == 0,
        "target":  lambda h, t, g: (4 in [h, t, g]) or (5 in [h, t, g]) or (t == 5),
    },
    {
        "id": 9,
        "name": "规则9: 百位=5 → 包含胆码4或7",
        "trigger": lambda h, t, g: h == 5,
        "target":  lambda h, t, g: 4 in [h, t, g] or 7 in [h, t, g],
    },
]


def is_zusan(h, t, g):
    """判断是否为组三（有且仅有两个数字相同，豹子不算）"""
    nums = [h, t, g]
    # 组三：恰好两个相同
    return len(set(nums)) == 2


def parse_number(num_str):
    """解析号码字符串为百位、十位、个位"""
    num_str = str(num_str).strip()
    if len(num_str) == 3:
        return int(num_str[0]), int(num_str[1]), int(num_str[2])
    elif len(num_str) == 2:
        return 0, int(num_str[0]), int(num_str[1])
    elif len(num_str) == 1:
        return 0, 0, int(num_str[0])
    return None


# ===================== 数据抓取 =====================

def fetch_zhcw_data(max_pages=10):
    """尝试从中彩网抓取福彩3D历史数据"""
    if not HAS_REQUESTS:
        return None
    
    data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://www.zhcw.com/",
    }
    
    # 数据源1: 中彩网
    urls_to_try = [
        ("http://www.zhcw.com/kaijiang/3d.html", "zhcw"),
        ("https://datachart.500.com/sd/history/history.shtml", "500"),
    ]
    
    for url, src in urls_to_try:
        try:
            print(f"尝试抓取: {url} ({src})")
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")
            
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:
                    cols = row.find_all(["td", "th"])
                    if len(cols) >= 3:
                        period = cols[0].get_text(strip=True)
                        num_text = cols[1].get_text(strip=True)
                        nums = re.findall(r"\d+", num_text)
                        if nums and len(nums[0]) == 3:
                            data.append({"period": period, "number": nums[0]})
            
            if data:
                print(f"从 {src} 成功抓取 {len(data)} 期数据")
                return data
        except Exception as e:
            print(f"{src} 抓取失败: {e}")
    
    # 数据源2: 中彩网 datachart 历史数据
    try:
        print("尝试中彩网 datachart...")
        dc_url = "https://datachart.zhcw.com/chart/3d/jbzs/jbzs_zst.php"
        resp = requests.get(dc_url, headers=headers, timeout=15, verify=False)
        resp.encoding = "utf-8"
        # 解析页面中的开奖号码表格
        soup = BeautifulSoup(resp.text, "html.parser")
        tables = soup.find_all("table", {"class": "zstable"})
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    period = cols[0].get_text(strip=True)
                    num_text = cols[1].get_text(strip=True) + cols[2].get_text(strip=True) + cols[3].get_text(strip=True)
                    if len(num_text) == 3 and num_text.isdigit():
                        data.append({"period": period, "number": num_text})
        if data:
            print(f"从 datachart 成功抓取 {len(data)} 期数据")
            return data
    except Exception as e:
        print(f"datachart 抓取失败: {e}")
    
    # 数据源3: 尝试公开API
    try:
        print("尝试彩票数据API...")
        api_url = "https://www.mxnzp.com/api/lottery/common/aim_lottery?app_id=ni89kxn5qsmlhpoj&app_secret=MXNrV0Jnemg1d1B5clpFdFM1c1ZzUT09&page=1&limit=100"
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            json_data = resp.json()
            if json_data.get("code") == 1 and "data" in json_data:
                for item in json_data["data"]["list"]:
                    period = item.get("period", "")
                    number = item.get("openCode", "").replace(",", "")
                    if len(number) == 3:
                        data.append({"period": period, "number": number})
            if data:
                print(f"从API成功获取 {len(data)} 期数据")
                return data
    except Exception as e:
        print(f"API获取失败: {e}")
    
    # 数据源4: 使用硬编码的最近真实数据（手动维护的最近100期）
    # 如果以上都失败，生成200期模拟数据
    return None


def fetch_cwl_gov_data():
    """尝试从彩票中心API获取（如果有公开接口）"""
    return None


def load_local_data(filepath):
    """从本地文件加载数据，支持CSV、TXT、JSON"""
    data = []
    
    if filepath.endswith(".csv"):
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 自动识别列名
                period = row.get("期号", row.get("period", ""))
                number = row.get("开奖号", row.get("number", row.get("开奖号码", "")))
                data.append({"period": period, "number": str(number).strip()})
    
    elif filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if isinstance(raw, list):
                data = raw
            elif isinstance(raw, dict) and "data" in raw:
                data = raw["data"]
    
    elif filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    data.append({"period": parts[0], "number": parts[1]})
                elif len(parts) == 1 and parts[0].isdigit():
                    data.append({"period": "", "number": parts[0]})
    
    return data


def generate_demo_data(count=200):
    """生成模拟数据用于演示（随机生成，仅供测试脚本逻辑）"""
    import random
    data = []
    start_period = 2024100
    for i in range(count):
        num = f"{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}"
        data.append({
            "period": str(start_period + i),
            "number": num
        })
    return data


# ===================== 核心统计逻辑 =====================

def analyze_rules(history_data):
    """
    统计9条规则在历史数据中的触发情况及未来1-3期命中/遗漏
    history_data: 按时间排序的列表，从早到晚 [{period, number}, ...]
    """
    # 过滤有效数据
    valid_data = []
    for item in history_data:
        num_str = str(item.get("number", "")).strip()
        parsed = parse_number(num_str)
        if parsed:
            valid_data.append({
                "period": item.get("period", ""),
                "number": num_str,
                "h": parsed[0],
                "t": parsed[1],
                "g": parsed[2],
            })
    
    if len(valid_data) < 10:
        print(f"有效数据仅 {len(valid_data)} 期，不足以分析")
        return None
    
    # 自动检测排序：如果期号递减，则反转
    # 尝试按期号排序（从早到晚）
    def period_key(x):
        p = str(x['period'])
        return int(p) if p.isdigit() else 0
    
    valid_data.sort(key=period_key)
    
    print(f"分析数据范围: 共 {len(valid_data)} 期")
    if valid_data:
        print(f"  起始: {valid_data[0]['period']} {valid_data[0]['number']}")
        print(f"  结束: {valid_data[-1]['period']} {valid_data[-1]['number']}")
    
    # 初始化统计结果
    results = []
    
    for rule in RULES:
        stat = {
            "id": rule["id"],
            "name": rule["name"],
            "trigger_count": 0,
            "hit_1": 0,   # 未来1期命中
            "hit_2": 0,   # 未来2期命中（含1期）
            "hit_3": 0,   # 未来3期命中（含1、2期）
            "miss_1": 0,
            "miss_2": 0,
            "miss_3": 0,
            "details": [],
        }
        
        # 遍历每一期，检查触发条件
        for i in range(len(valid_data)):
            curr = valid_data[i]
            h, t, g = curr["h"], curr["t"], curr["g"]
            
            if rule["trigger"](h, t, g):
                stat["trigger_count"] += 1
                
                # 检查未来1、2、3期
                hit_1 = False
                hit_2 = False
                hit_3 = False
                
                if i + 1 < len(valid_data):
                    next1 = valid_data[i + 1]
                    hit_1 = rule["target"](next1["h"], next1["t"], next1["g"])
                    
                    if i + 2 < len(valid_data):
                        next2 = valid_data[i + 2]
                        hit_2 = hit_1 or rule["target"](next2["h"], next2["t"], next2["g"])
                        
                        if i + 3 < len(valid_data):
                            next3 = valid_data[i + 3]
                            hit_3 = hit_2 or rule["target"](next3["h"], next3["t"], next3["g"])
                        else:
                            hit_3 = hit_2
                    else:
                        hit_2 = hit_1
                        hit_3 = hit_1
                
                stat["hit_1"] += 1 if hit_1 else 0
                stat["hit_2"] += 1 if hit_2 else 0
                stat["hit_3"] += 1 if hit_3 else 0
                
                stat["miss_1"] += 0 if hit_1 else 1
                stat["miss_2"] += 0 if hit_2 else 1
                stat["miss_3"] += 0 if hit_3 else 1
                
                # 记录详情（只记录前10条）
                if len(stat["details"]) < 10:
                    stat["details"].append({
                        "trigger_period": curr["period"],
                        "trigger_num": curr["number"],
                        "hit_1": hit_1,
                        "hit_2": hit_2,
                        "hit_3": hit_3,
                    })
        
        results.append(stat)
    
    return results


def print_results(results):
    """打印统计结果"""
    print("\n" + "=" * 80)
    print("福彩3D 胆码规律触发条件 - 遗漏期数数据分析报告")
    print("=" * 80)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n统计说明:")
    print("  - 触发次数: 历史数据中满足触发条件的期数")
    print("  - 1期命中: 触发后第1期即出现目标特征")
    print("  - 2期命中: 触发后前2期内出现目标特征")
    print("  - 3期命中: 触发后前3期内出现目标特征")
    print("  - 遗漏次数: 在对应期数内未出现目标特征的次数")
    print("  - 命中率 = 命中次数 / 触发次数")
    print("=" * 80)
    
    for stat in results:
        tc = stat["trigger_count"]
        if tc == 0:
            print(f"\n【{stat['name']}】")
            print(f"  触发次数: 0 (无统计数据)")
            continue
        
        print(f"\n【{stat['name']}】")
        print(f"  触发次数: {tc}")
        print(f"  未来1期 - 命中: {stat['hit_1']:3d} | 遗漏: {stat['miss_1']:3d} | 命中率: {stat['hit_1']/tc*100:.1f}%")
        print(f"  未来2期 - 命中: {stat['hit_2']:3d} | 遗漏: {stat['miss_2']:3d} | 命中率: {stat['hit_2']/tc*100:.1f}%")
        print(f"  未来3期 - 命中: {stat['hit_3']:3d} | 遗漏: {stat['miss_3']:3d} | 命中率: {stat['hit_3']/tc*100:.1f}%")
        
        print(f"  最近触发记录(前10条):")
        for d in stat["details"]:
            status = "✓" if d["hit_1"] else ("✓2" if d["hit_2"] else ("✓3" if d["hit_3"] else "✗"))
            print(f"    {d['trigger_period']} {d['trigger_num']} → {status}")
    
    print("\n" + "=" * 80)


def export_csv(results, filename="lottery_3d_rule_analysis.csv"):
    """导出结果为CSV"""
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["规则", "触发次数", "1期命中", "1期遗漏", "1期命中率", 
                         "2期命中", "2期遗漏", "2期命中率",
                         "3期命中", "3期遗漏", "3期命中率"])
        for stat in results:
            tc = stat["trigger_count"]
            if tc == 0:
                writer.writerow([stat["name"], 0, "-", "-", "-", "-", "-", "-", "-", "-", "-"])
            else:
                writer.writerow([
                    stat["name"],
                    tc,
                    stat["hit_1"], stat["miss_1"], f"{stat['hit_1']/tc*100:.1f}%",
                    stat["hit_2"], stat["miss_2"], f"{stat['hit_2']/tc*100:.1f}%",
                    stat["hit_3"], stat["miss_3"], f"{stat['hit_3']/tc*100:.1f}%",
                ])
    print(f"\n结果已导出到: {filename}")


# ===================== 主程序 =====================

def main():
    data = None
    
    # 1. 检查命令行参数（本地文件）
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"正在加载本地文件: {filepath}")
        data = load_local_data(filepath)
    
    # 2. 尝试自动抓取
    if not data:
        print("未提供本地数据，尝试自动从网上抓取...")
        data = fetch_zhcw_data()
        if not data:
            data = fetch_cwl_gov_data()
    
    # 3. 使用演示数据
    if not data:
        print("\n自动抓取失败。请提供本地历史数据文件（CSV/TXT/JSON格式）")
        print("数据格式示例: 期号,开奖号")
        print("             2024101,123")
        print("             2024102,456")
        print("\n使用方式: python lottery_3d_rule_analyzer.py 数据文件.csv")
        print("\n正在生成200期模拟数据进行演示...")
        data = generate_demo_data(200)
        print("(注意: 模拟数据为随机生成，结果仅供验证脚本逻辑，非真实统计)")
    
    # 分析
    results = analyze_rules(data)
    if results:
        print_results(results)
        export_csv(results)
    else:
        print("分析失败，请检查数据格式")


if __name__ == "__main__":
    main()
