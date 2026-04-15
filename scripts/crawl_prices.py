#!/usr/bin/env python3
"""
原材料价格爬虫 - 完整版
支持：历史数据追加、随机UA、重试机制
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
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
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
    for attempt in range(max_retries):
        try:
            delay = random.uniform(1, 3)
            time.sleep(delay)
            headers = get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                print(f"    ⚠️ 403被拦截，重试中... ({attempt+1}/{max_retries})")
                time.sleep(random.uniform(2, 5))
            else:
                print(f"    ✗ HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"    ⚠️ 超时，重试中... ({attempt+1}/{max_retries})")
        except Exception as e:
            print(f"    ✗ 请求失败: {e}")
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

def parse_silicon_steel(html, keywords):
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
    price_match = re.search(r'(\d{3,6})\s*-\s*(\d{3,6})', html)
    if price_match:
        low = float(price_match.group(1))
        high = float(price_match.group(2))
        price = (low + high) / 2
        change_match = re.search(r'>([+-]\d+)<', html)
        change = float(change_match.group(1)) if change_match else 0
        return {'price': price, 'change': change, 'low': low, 'high': high}
    prices = re.findall(r'>(\d{3,6})<', html)
    if len(prices) >= 1:
        price = float(prices[0])
        return {'price': price, 'change': 0, 'low': price, 'high': price}
    return None

def load_data():
    """加载完整数据（包含history）"""
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

def get_last_price(code, data):
    """从历史数据获取最近一次价格"""
    history = data.get('history', {}).get(code, [])
    if history:
        return {
            'price': history[0]['price'],
            'change': 0,
            'low': history[0]['price'],
            'high': history[0]['price']
        }
    # 从today获取
    for item in data.get('today', []):
        if item['code'] == code:
            return {
                'price': item['price'],
                'change': item.get('change', 0),
                'low': item['price'],
                'high': item['price']
            }
    return None

def append_to_history(data, results, today_str):
    """将今日数据追加到历史记录"""
    history = data.get('history', {})
    
    for code, price_data in results.items():
        if not price_data:
            continue
            
        if code not in history:
            history[code] = []
        
        # 检查今天是否已有记录
        today_exists = any(h['date'] == today_str for h in history[code])
        
        if not today_exists:
            # 插入到开头（最新的在前面）
            history[code].insert(0, {
                'date': today_str,
                'price': price_data['price']
            })
            print(f"    ✓ {code}: 已追加到历史记录")
        else:
            # 更新今天的记录
            for h in history[code]:
                if h['date'] == today_str:
                    h['price'] = price_data['price']
                    break
            print(f"    ✓ {code}: 已更新今日记录")
    
    data['history'] = history
    return data

def save_data(results, data):
    """保存数据"""
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    # 更新时间
    data['update_time'] = now.strftime('%Y-%m-%d %H:%M')
    
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
    
    # 追加到历史记录
    data = append_to_history(data, results, today)
    
    # 构建today数组
    today_data = []
    for code, price_data in results.items():
        if price_data:
            today_data.append({
                'code': code,
                'name': material_names.get(code, code),
                'price': price_data['price'],
                'change': price_data.get('change', 0),
                'date': today
            })
    
    data['today'] = today_data
    
    # 保存
    with open(DATA_DIR / "prices.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 数据已保存")
    return data

def main():
    print("=" * 60)
    print("原材料价格爬虫 - 完整版")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    data = load_data()
    
    # 1. 电解铜
    print("\n1. 电解铜 (CU)...")
    html = fetch(SOURCES['CU'])
    if html:
        result = parse_copper(html)
        if result:
            results['CU'] = result
            print(f"  ✓ CU: {result['price']:,.0f} ({result['change']:+.0f})")
        else:
            last = get_last_price('CU', data)
            if last:
                results['CU'] = last
                print(f"  ⚠ CU: 使用上次数据 {last['price']:,.0f}")
    
    # 2. ADC12
    print("\n2. ADC12...")
    html = fetch(SOURCES['ADC12'])
    if html:
        result = parse_aluminum(html)
        if result:
            results['ADC12'] = result
            print(f"  ✓ ADC12: {result['price']:,.0f}")
        else:
            last = get_last_price('ADC12', data)
            if last:
                results['ADC12'] = last
                print(f"  ⚠ ADC12: 使用上次数据")
    
    # 3. 6063铝棒
    print("\n3. 6063铝棒...")
    html = fetch(SOURCES['AL6063'])
    if html:
        result = parse_aluminum(html)
        if result:
            results['AL6063'] = result
            print(f"  ✓ AL6063: {result['price']:,.0f}")
        else:
            last = get_last_price('AL6063', data)
            if last:
                results['AL6063'] = last
                print(f"  ⚠ AL6063: 使用上次数据")
    
    # 4. 硅钢
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
            result = parse_silicon_steel(html, keywords)
            if result:
                results[brand] = result
                print(f"  ✓ {brand}: {result['price']:,.0f}")
            else:
                last = get_last_price(brand, data)
                if last:
                    results[brand] = last
                    print(f"  ⚠ {brand}: 使用上次数据")
    
    # 5. 稀土
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
            result = parse_rare_earth(html)
            if result:
                results[code] = result
                print(f"    ✓ {code}: {result['price']:,.0f}")
            else:
                last = get_last_price(code, data)
                if last:
                    results[code] = last
                    print(f"    ⚠ {code}: 使用上次数据")
        else:
            last = get_last_price(code, data)
            if last:
                results[code] = last
                print(f"    ⚠ {code}: 获取失败，使用上次数据")
    
    # 6. 镝铁合金
    print("\n6. 镝铁合金...")
    last = get_last_price('DYFE', data)
    if last:
        results['DYFE'] = last
        print(f"  ⚠ DYFE: SMM网页端无数据，使用上次数据")
    
    # 保存
    print("\n" + "=" * 60)
    success = len([r for r in results.values() if r])
    print(f"爬取完成: {success}/13 种材料")
    print("=" * 60)
    
    if results:
        save_data(results, data)
        return 0
    else:
        print("✗ 未获取到任何数据")
        return 1

if __name__ == '__main__':
    exit(main())
