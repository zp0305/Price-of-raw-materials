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
            return json.load(f)
    return {}

def save_data(results):
    """保存数据到JSON"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 加载历史数据
    history = load_history()
    
    # 更新今日数据
    for code, data in results.items():
        if code not in history:
            history[code] = []
        
        # 检查是否已有今日数据
        existing = [d for d in history[code] if d['date'] == today]
        if existing:
            existing[0]['price'] = data['price']
            existing[0]['change'] = data['change']
        else:
            history[code].append({
                'date': today,
                'price': data['price'],
                'change': data['change']
            })
        
        # 只保留最近90天数据
        history[code] = sorted(history[code], key=lambda x: x['date'])[-90:]
    
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
