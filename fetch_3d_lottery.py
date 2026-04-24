#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取中彩网福彩3D开奖数据
数据来源: https://www.zhcw.com/c/2019-08-19/580353.shtml
"""

import urllib.request
import re
import html as html_module
import csv
import os


def fetch_3d_data(select=100, order="asc"):
    """
    抓取福彩3D开奖数据
    
    Args:
        select: 获取期数 (30/50/100)
        order: 排序方式 asc(旧到新) 或 desc(新到旧)
    
    Returns:
        list of tuples: [(期号, 开奖号码, 百位, 十位, 个位), ...]
    """
    jsp_name = "3dZongHeZouShiTuAsc.jsp" if order == "asc" else "3dZongHeZouShiTuDesc.jsp"
    url = f"https://tubiao.zhcw.com/tubiao/zhcw_agent.jsp?url=3d/3dJsp/{jsp_name}?select={select}"
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    html_text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html_text, re.DOTALL)
    
    data = []
    for row in rows[3:]:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        if len(tds) >= 2:
            issue_raw = html_module.unescape(re.sub(r"<[^>]+", "", tds[0])).strip()
            issue_raw = re.sub(r"<[^>]+", "", issue_raw)  # remove any remaining tags
            issue_raw = re.sub(r"[<>]", "", issue_raw).strip()
            
            num_raw = html_module.unescape(re.sub(r"<[^>]+>", "", tds[1])).strip()
            num_clean = re.sub(r"\s+", "", num_raw)
            
            if issue_raw.isdigit() and len(num_clean) == 3 and num_clean.isdigit():
                data.append((
                    issue_raw,
                    num_clean,
                    num_clean[0],
                    num_clean[1],
                    num_clean[2]
                ))
    
    return data


def save_to_csv(data, filepath="3d_lottery_data.csv"):
    """保存数据到CSV文件"""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["期号", "开奖号码", "百位", "十位", "个位"])
        for row in data:
            writer.writerow(row)
    print(f"已保存 {len(data)} 条记录到: {os.path.abspath(filepath)}")


def main():
    print("正在抓取中彩网福彩3D开奖数据...")
    
    # 抓取最近100期 (旧到新排序)
    data = fetch_3d_data(select=100, order="asc")
    
    if not data:
        print("未抓取到任何数据")
        return
    
    print(f"成功抓取 {len(data)} 期数据")
    print(f"   范围: 期号 {data[0][0]} ~ {data[-1][0]}")
    print(f"   最新一期: 期号 {data[-1][0]}, 号码 {data[-1][1]} ({data[-1][2]} {data[-1][3]} {data[-1][4]})")
    
    # 保存到CSV
    save_to_csv(data, "3d_lottery_data.csv")
    
    # 打印前10期预览
    print("\n数据预览 (前10期):")
    print("-" * 35)
    for row in data[:10]:
        print(f"  期号 {row[0]} | 开奖号: {row[2]} {row[3]} {row[4]}")


if __name__ == "__main__":
    main()
