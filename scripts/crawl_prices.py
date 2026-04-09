#!/usr/bin/env python3
"""
原材料价格爬虫 - GitHub Actions版
直接输出JSON，无需数据库
"""

import requests
import re
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

SOURCES = {
    'CU': 'https://hq.smm.cn/h5/cu-price',
    'ADC12': 'https://hq.smm.cn/h5/aluminum-alloy-price',
    'AL6063': 'https://hq.smm.cn/h5/aluminum-alloy-price',
    'SI_SH': 'https://hq.smm.cn/h5/SiFe-shanghai-price',
    'SI_FACTORY': 'https://hq.smm.cn/h5/SiFe-factory-price',
    'REO': 'https://hq.smm.cn/h5/praseodymium-neodymium-oxide-price',
    'REN': 'https://hq.smm.cn/h5/praseodymium-neodymium-metal-price',
    'TB': 'https://hq.smm.cn/h5/terbium-oxide-price',
    'CE': 'https://hq.smm.cn/h5/cerium-oxide-price',
    'DYFE': 'https://hq.smm.cn/h5/dysprosium-price',
}

def fetch(url):
    """获取网页内容"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text
        print(f"  ✗ HTTP {response.status_code}")
        return None
    except Exception as e:
        print(f"  ✗ 请求失败: {e}")
        return None

def parse_copper(html):
    """解析铜价"""
    prices = re.findall(r'>([7-9]\d{4})<', html)
    changes = re.findall(r'>([+-]\d+)<', html)
    if len(prices) >= 3:
        return {
            'price': float(prices[2]),
            'change': float(changes[0]) if changes else 0,
            'low': float(prices[0]),
            'high': float(prices[1])
        }
    return None

def parse_aluminum(html):
    """解析铝价"""
    prices = re.findall(r'>(2[4-5]\d{3})<', html)
    if prices:
        price = float(prices[0])
        return {'price': price, 'change': 0, 'low': price, 'high': price}
    return None

def parse_silicon_steel(html, keywords):
    """解析硅钢价格"""
    for keyword in keywords:
        pos = html.find(keyword)
        if pos >= 0:
            segment = html[pos:pos+500]
            match = re.search(r'<span>([4-6]\d{3})</span>', segment)
            if match:
                price = float(match.group(1))
                return {'price': price, 'change': 0, 'low': price, 'high': price}
            prices = re.findall(r'>([4-6]\d{3})<', segment)
            if prices:
                price = float(prices[0])
                return {'price': price, 'change': 0, 'low': price, 'high': price}
    return None

def parse_rare_earth(html):
    """解析稀土价格"""
    prices = re.findall(r'>([7-9]\d{5})<', html)
    changes = re.findall(r'>([+-]\d+)<', html)
    if len(prices) >= 3:
        return {
            'price': float(prices[2]),
            'change': float(changes[0]) if changes else 0,
            'low': float(prices[0]),
            'high': float(prices[1])
        }
    return None

def load_history():
    """加载历史数据"""
    prices_file = DATA_DIR / "prices.json"
    if prices_file.exists():
        with open(prices_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # 如果已有正确格式的数据，保留它
                if isinstance(data, dict) and 'today' in data:
                    return data
                # 否则返回空结构
                return {'update_time': '', 'today': []}
            except:
                return {'update_time': '', 'today': []}
    return {'update_time': '', 'today': []}

def save_data(results):
    """保存数据到JSON - 兼容原有格式"""
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    # 加载历史数据
    history = load_history()
    
    # 更新update_time
    history['update_time'] = now.strftime('%Y-%m-%d %H:%M')
    
    # 材料名称映射
    material_names = {
        'CU': '电解铜',
        'ADC12': 'ADC12',
        'AL6063': '6063铝棒',
        'B35A300': '硅钢B35A300',
        'B50A350': '硅钢B50A350',
        'B50A470': '硅钢B50A470',
        'B50A600': '硅钢B50A600',
        '35WW300': '硅钢35WW300',
        '50WW310': '硅钢50WW310',
        '50WW470': '硅钢50WW470',
        '50WW600': '硅钢50WW600',
        'REO': '镨钕氧化物',
        'REN': '镨钕金属',
        'TB': '金属铽',
        'CE': '铈金属',
        'DYFE': '镝铁合金'
    }
    
    # 构建新的today数组
    today_data = []
    for code, data in results.items():
        today_data.append({
            'code': code,
            'name': material_names.get(code, code),
            'price': data['price'],
            'change': data.get('change', 0),
            'date': today
        })
    
    history['today'] = today_data
    
    # 保存
    with open(DATA_DIR / "prices.json", 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 数据已保存到 data/prices.json")
    return history

def main():
    print("=" * 60)
    print("原材料价格爬虫 - GitHub Actions版")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # 1. 电解铜
    print("\n1. 电解铜 (CU)...")
    html = fetch(SOURCES['CU'])
    if html:
        data = parse_copper(html)
        if data:
            results['CU'] = data
            print(f"  ✓ CU: {data['price']:,.0f} ({data['change']:+.0f})")
    
    # 2. ADC12
    print("\n2. ADC12...")
    html = fetch(SOURCES['ADC12'])
    if html:
        data = parse_aluminum(html)
        if data:
            results['ADC12'] = data
            print(f"  ✓ ADC12: {data['price']:,.0f}")
    
    # 3. 6063铝棒
    print("\n3. 6063铝棒...")
    html = fetch(SOURCES['AL6063'])
    if html:
        data = parse_aluminum(html)
        if data:
            results['AL6063'] = data
            print(f"  ✓ AL6063: {data['price']:,.0f}")
    
    # 4. 硅钢-上海（宝钢系列）
    print("\n4. 硅钢-上海（宝钢系列）...")
    html = fetch(SOURCES['SI_SH'])
    if html:
        brands = {
            'B35A300': ['B35A300', 'B35A'],
            'B50A350': ['B50A350', 'B50A3'],
            'B50A470': ['B50A470', 'B50A4'],
            'B50A600': ['B50A600', 'B50A6'],
        }
        for brand, keywords in brands.items():
            data = parse_silicon_steel(html, keywords)
            if data:
                results[brand] = data
                print(f"  ✓ {brand}: {data['price']:,.0f}")
    
    # 5. 硅钢-武钢
    print("\n5. 硅钢-武钢系列...")
    html = fetch(SOURCES['SI_FACTORY'])
    if html:
        brands = {
            '35WW300': ['35WW300', '35WW3'],
            '50WW310': ['50WW310', '50WW3'],
            '50WW470': ['50WW470', '50WW4'],
            '50WW600': ['50WW600', '50WW6'],
        }
        for brand, keywords in brands.items():
            data = parse_silicon_steel(html, keywords)
            if data:
                results[brand] = data
                print(f"  ✓ {brand}: {data['price']:,.0f}")
    
    # 6. 稀土系列
    print("\n6. 稀土系列...")
    for code, url in [
        ('REO', SOURCES['REO']),
        ('REN', SOURCES['REN']),
        ('TB', SOURCES['TB']),
        ('CE', SOURCES['CE']),
        ('DYFE', SOURCES['DYFE'])
    ]:
        print(f"  {code}...")
        html = fetch(url)
        if html:
            data = parse_rare_earth(html)
            if data:
                results[code] = data
                print(f"    ✓ {code}: {data['price']:,.0f}")
    
    # 保存数据
    print("\n" + "=" * 60)
    print(f"爬取完成: {len(results)}/16 种材料")
    print("=" * 60)
    
    if results:
        history = save_data(results)
        
        # 同时生成今日快照
        snapshot = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'update_time': datetime.now().strftime('%H:%M:%S'),
            'materials': results
        }
        with open(DATA_DIR / "today.json", 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
        return 0
    else:
        print("✗ 未获取到任何数据")
        return 1

if __name__ == '__main__':
    exit(main())
