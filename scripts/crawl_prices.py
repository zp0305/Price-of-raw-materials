#!/usr/bin/env python3
"""
原材料价格爬虫 - 增强版
支持：随机UA、随机延时、多轮重试、失败降级
"""

import requests
import re
import json
import random
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# 随机User-Agent池
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def get_headers():
    """生成随机请求头"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }

SOURCES = {
    'CU': 'https://hq.smm.cn/h5/cu-price',
    'ADC12': 'https://hq.smm.cn/h5/aluminum-alloy-price',
    'AL6063': 'https://hq.smm.cn/h5/aluminum-alloy-price',
    'SI_SH': 'https://hq.smm.cn/h5/SiFe-shanghai-price',
    'REO': 'https://hq.smm.cn/h5/praseodymium-neodymium-oxide-price',
    'REN': 'https://hq.smm.cn/h5/praseodymium-neodymium-metal-price',
    'TB': 'https://hq.smm.cn/h5/terbium-metal-price',
    'CE': 'https://hq.smm.cn/h5/cerium-metal-price',
}

def fetch(url, max_retries=3):
    """获取网页内容 - 带重试机制"""
    for attempt in range(max_retries):
        try:
            # 随机延时 1-3 秒
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            headers = get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                print(f"    ⚠️ 403被拦截，尝试更换UA重试... (尝试 {attempt+1}/{max_retries})")
                time.sleep(random.uniform(2, 5))  # 被拦截时等待更久
            else:
                print(f"    ✗ HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"    ⚠️ 超时，重试中... (尝试 {attempt+1}/{max_retries})")
        except Exception as e:
            print(f"    ✗ 请求失败: {e}")
            
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
    """解析稀土价格 - 支持各种价位"""
    # 尝试匹配价格范围格式：6070 - 6100
    price_match = re.search(r'(\d{3,6})\s*-\s*(\d{3,6})', html)
    if price_match:
        low = float(price_match.group(1))
        high = float(price_match.group(2))
        price = (low + high) / 2
        
        # 尝试找涨跌
        change_match = re.search(r'>([+-]\d+)<', html)
        change = float(change_match.group(1)) if change_match else 0
        
        return {
            'price': price,
            'change': change,
            'low': low,
            'high': high
        }
    
    # 备用：匹配单个价格
    prices = re.findall(r'>(\d{3,6})<', html)
    if len(prices) >= 1:
        price = float(prices[0])
        return {
            'price': price,
            'change': 0,
            'low': price,
            'high': price
        }
    return None

def load_history():
    """加载历史数据"""
    prices_file = DATA_DIR / "prices.json"
    if prices_file.exists():
        with open(prices_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, dict) and 'today' in data:
                    return data
            except:
                pass
    return {'update_time': '', 'today': []}

def get_last_price(code, history):
    """获取某个材料的上次价格"""
    if history and 'today' in history:
        for item in history['today']:
            if item['code'] == code:
                return {
                    'price': item['price'],
                    'change': item.get('change', 0),
                    'low': item['price'],
                    'high': item['price']
                }
    return None

def save_data(results, history):
    """保存数据到JSON - 兼容原有格式"""
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    # 更新update_time
    history['update_time'] = now.strftime('%Y-%m-%d %H:%M')
    
    # 材料名称映射
    material_names = {
        'CU': '电解铜',
        'ADC12': 'ADC12',
        'AL6063': '6063铝棒',
        'B35A300': '硅钢B35A300',
        'B50A310': '硅钢B50A310',
        'B50A350': '硅钢B50A350',
        'B50A470': '硅钢B50A470',
        'B50A600': '硅钢B50A600',
        'REO': '镨钕氧化物',
        'REN': '镨钕金属',
        'TB': '金属铽',
        'CE': '金属铈',
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
    print("原材料价格爬虫 - 增强版")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    history = load_history()
    
    # 1. 电解铜
    print("\n1. 电解铜 (CU)...")
    html = fetch(SOURCES['CU'])
    if html:
        data = parse_copper(html)
        if data:
            results['CU'] = data
            print(f"  ✓ CU: {data['price']:,.0f} ({data['change']:+.0f})")
        else:
            # 使用上次数据
            last = get_last_price('CU', history)
            if last:
                results['CU'] = last
                print(f"  ⚠ CU: 使用上次数据 {last['price']:,.0f}")
    
    # 2. ADC12
    print("\n2. ADC12...")
    html = fetch(SOURCES['ADC12'])
    if html:
        data = parse_aluminum(html)
        if data:
            results['ADC12'] = data
            print(f"  ✓ ADC12: {data['price']:,.0f}")
        else:
            last = get_last_price('ADC12', history)
            if last:
                results['ADC12'] = last
                print(f"  ⚠ ADC12: 使用上次数据 {last['price']:,.0f}")
    
    # 3. 6063铝棒
    print("\n3. 6063铝棒...")
    html = fetch(SOURCES['AL6063'])
    if html:
        data = parse_aluminum(html)
        if data:
            results['AL6063'] = data
            print(f"  ✓ AL6063: {data['price']:,.0f}")
        else:
            last = get_last_price('AL6063', history)
            if last:
                results['AL6063'] = last
                print(f"  ⚠ AL6063: 使用上次数据 {last['price']:,.0f}")
    
    # 4. 硅钢-上海（宝钢系列）
    print("\n4. 硅钢-上海（宝钢系列）...")
    html = fetch(SOURCES['SI_SH'])
    if html:
        brands = {
            'B35A300': ['B35A300', 'B35A'],
            'B50A310': ['B50A310', 'B50A3'],
            'B50A350': ['B50A350', 'B50A35'],
            'B50A470': ['B50A470', 'B50A4'],
            'B50A600': ['B50A600', 'B50A6'],
        }
        for brand, keywords in brands.items():
            data = parse_silicon_steel(html, keywords)
            if data:
                results[brand] = data
                print(f"  ✓ {brand}: {data['price']:,.0f}")
            else:
                last = get_last_price(brand, history)
                if last:
                    results[brand] = last
                    print(f"  ⚠ {brand}: 使用上次数据 {last['price']:,.0f}")
    
    # 5. 稀土系列
    print("\n5. 稀土系列...")
    for code, url in [
        ('REO', 'https://hq.smm.cn/h5/praseodymium-neodymium-oxide-price'),
        ('REN', 'https://hq.smm.cn/h5/praseodymium-neodymium-metal-price'),
        ('TB', 'https://hq.smm.cn/h5/terbium-metal-price'),
        ('CE', 'https://hq.smm.cn/h5/cerium-metal-price')
    ]:
        print(f"  {code}...")
        html = fetch(url)
        if html:
            data = parse_rare_earth(html)
            if data:
                results[code] = data
                print(f"    ✓ {code}: {data['price']:,.0f}")
            else:
                last = get_last_price(code, history)
                if last:
                    results[code] = last
                    print(f"    ⚠ {code}: 使用上次数据 {last['price']:,.0f}")
        else:
            last = get_last_price(code, history)
            if last:
                results[code] = last
                print(f"    ⚠ {code}: 获取失败，使用上次数据 {last['price']:,.0f}")
    
    # 6. 镝铁合金（SMM网页端不可用）
    print("\n6. 镝铁合金...")
    last = get_last_price('DYFE', history)
    if last:
        results['DYFE'] = last
        print(f"  ⚠ DYFE: SMM网页端无数据，使用上次数据 {last['price']:,.0f}")
    else:
        print("  ⚠ DYFE: 无历史数据，请从APP手动录入")
    
    # 保存数据
    print("\n" + "=" * 60)
    success_count = len([r for r in results.values() if r])
    print(f"爬取完成: {success_count}/13 种材料成功获取数据")
    print("=" * 60)
    
    if results:
        save_data(results, history)
        
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
