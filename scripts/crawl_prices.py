#!/usr/bin/env python3
"""
原材料价格爬虫 - 调试版
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

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
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

def fetch(url, code):
    print(f"    请求: {url}")
    
    for attempt in range(3):
        try:
            time.sleep(random.uniform(1, 2))
            response = requests.get(url, headers=get_headers(), timeout=30)
            print(f"    状态: {response.status_code}, 长度: {len(response.text)}")
            
            if response.status_code == 200 and len(response.text) > 1000:
                return response.text
            elif response.status_code == 403:
                print(f"    ⚠️ 403被拦截")
                time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"    ✗ 错误: {e}")
    
    return None

def parse_copper(html):
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
    prices = re.findall(r'>(2[4-5]\d{3})<', html)
    if prices:
        price = float(prices[0])
        return {'price': price, 'change': 0, 'low': price, 'high': price}
    return None

def parse_silicon_steel(html):
    brands = {
        'B35A300': ['B35A300', 'B35A'],
        'B50A310': ['B50A310', 'B50A3'],
        'B50A350': ['B50A350', 'B50A35'],
        'B50A470': ['B50A470', 'B50A4'],
        'B50A600': ['B50A600', 'B50A6'],
    }
    results = {}
    for brand, keywords in brands.items():
        for keyword in keywords:
            pos = html.find(keyword)
            if pos >= 0:
                segment = html[pos:pos+500]
                match = re.search(r'<span>([4-6]\d{3})</span>', segment)
                if match:
                    results[brand] = {'price': float(match.group(1)), 'change': 0, 'low': float(match.group(1)), 'high': float(match.group(1))}
                    break
                prices = re.findall(r'>([4-6]\d{3})<', segment)
                if prices:
                    results[brand] = {'price': float(prices[0]), 'change': 0, 'low': float(prices[0]), 'high': float(prices[0])}
                    break
    return results if results else None

def parse_rare_earth(html):
    price_match = re.search(r'(\d{3,6})\s*[-～]\s*(\d{3,6})', html)
    if price_match:
        low = float(price_match.group(1))
        high = float(price_match.group(2))
        price = (low + high) / 2
        change_match = re.search(r'>([+-]\d+)<', html)
        change = float(change_match.group(1)) if change_match else 0
        return {'price': price, 'change': change, 'low': low, 'high': high}
    prices = re.findall(r'>(\d{3,6})<', html)
    if prices:
        return {'price': float(prices[0]), 'change': 0, 'low': float(prices[0]), 'high': float(prices[0])}
    return None

def load_data():
    prices_file = DATA_DIR / "prices.json"
    if prices_file.exists():
        with open(prices_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    if 'history' not in data:
                        data['history'] = {}
                    if 'today' not in data:
                        data['today'] = []
                    return data
            except:
                pass
    return {'update_time': '', 'today': [], 'history': {}}

def save_data(results, data):
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    data['update_time'] = now.strftime('%Y-%m-%d %H:%M')
    
    material_names = {
        'CU': '电解铜', 'ADC12': 'ADC12', 'AL6063': '6063铝棒',
        'B35A300': '硅钢B35A300', 'B50A310': '硅钢B50A310', 'B50A350': '硅钢B50A350',
        'B50A470': '硅钢B50A470', 'B50A600': '硅钢B50A600',
        'REO': '镨钕氧化物', 'REN': '镨钕金属', 'TB': '金属铽', 'CE': '金属铈',
        'DYFE': '镝铁合金'
    }
    
    history = data.get('history', {})
    
    for code, price_data in results.items():
        if price_data is None:
            continue
        
        if code not in history:
            history[code] = []
        
        if not any(h['date'] == today for h in history[code]):
            history[code].insert(0, {'date': today, 'price': price_data['price']})
    
    data['history'] = history
    
    today_data = []
    for code, price_data in results.items():
        if price_data is not None:
            today_data.append({
                'code': code,
                'name': material_names.get(code, code),
                'price': price_data['price'],
                'change': price_data.get('change', 0),
                'date': today
            })
    
    data['today'] = today_data
    
    with open(DATA_DIR / "prices.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 保存完成 ({len(today_data)} 种材料)")
    return data

def main():
    print("=" * 70)
    print("原材料价格爬虫 - 调试版")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {}
    data = load_data()
    
    for code, url in [
        ('CU', 'https://hq.smm.cn/h5/cu-price'),
        ('ADC12', 'https://hq.smm.cn/h5/aluminum-alloy-price'),
        ('AL6063', 'https://hq.smm.cn/h5/aluminum-alloy-price'),
    ]:
        print(f"\n{code}...")
        html = fetch(url, code)
        if html:
            if code == 'CU':
                result = parse_copper(html)
            else:
                result = parse_aluminum(html)
            
            if result:
                results[code] = result
                print(f"    ✓ {code}: {result['price']:,.0f}")
            else:
                results[code] = None
                print(f"    ✗ {code}: 解析失败")
        else:
            results[code] = None
            print(f"    ✗ {code}: 获取失败")
    
    for code, url in [
        ('REO', 'https://hq.smm.cn/h5/praseodymium-neodymium-oxide-price'),
        ('REN', 'https://hq.smm.cn/h5/praseodymium-neodymium-metal-price'),
        ('TB', 'https://hq.smm.cn/h5/terbium-metal-price'),
        ('CE', 'https://hq.smm.cn/h5/cerium-metal-price'),
    ]:
        print(f"\n{code}...")
        html = fetch(url, code)
        if html:
            result = parse_rare_earth(html)
            if result:
                results[code] = result
                print(f"    ✓ {code}: {result['price']:,.0f}")
            else:
                results[code] = None
                print(f"    ✗ {code}: 解析失败")
        else:
            results[code] = None
            print(f"    ✗ {code}: 获取失败")
    
    print(f"\n硅钢...")
    html = fetch('https://hq.smm.cn/h5/SiFe-shanghai-price', 'SI_SH')
    if html:
        silicon_results = parse_silicon_steel(html)
        if silicon_results:
            results.update(silicon_results)
            print(f"    ✓ 硅钢: {len(silicon_results)} 个品牌")
        else:
            print(f"    ✗ 硅钢: 解析失败")
    else:
        print(f"    ✗ 硅钢: 获取失败")
    
    print(f"\n镝铁合金...")
    results['DYFE'] = None
    print(f"    ⚠ SMM网页端无数据")
    
    success = len([r for r in results.values() if r is not None])
    print(f"\n{'='*70}")
    print(f"成功: {success}/{len(results)}")
    print('='*70)
    
    if success > 0:
        save_data(results, data)
        return 0
    return 1

if __name__ == '__main__':
    exit(main())
