#!/usr/bin/env python3
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
    
    for attempt in range(2):
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
    print(f"    解析铜价...")
    
    # 方式1：查找所有5位数字，过滤70000-100000范围
    all_prices = re.findall(r'>(\d{5})<', html)
    copper_prices = [p for p in all_prices if 70000 <= int(p) <= 100000]
    print(f"    方式1: 找到 {len(copper_prices)} 个铜价: {copper_prices[:10]}")
    
    if len(copper_prices) >= 3:
        # 取最后一个（最新的）
        price = float(copper_prices[-1])
        return {
            'price': price,
            'change': 0,
            'low': float(copper_prices[0]),
            'high': float(copper_prices[-1])
        }
    
    # 方式2：查找data-price属性
    data_prices = re.findall(r'data-price="(\d+)"', html)
    data_copper = [p for p in data_prices if 70000 <= int(p) <= 100000]
    print(f"    方式2: data-price匹配到 {len(data_copper)} 个铜价")
    
    if data_copper:
        price = float(data_copper[0])
        return {
            'price': price,
            'change': 0,
            'low': price,
            'high': price
        }
    
    # 方式3：关键词+精确匹配（只匹配以7/8/9/10开头的5-6位数字，避免匹配到0开头的数字）
    # 使用更精确的正则：[789]\d{4} 或 10\d{4}
    keyword_prices = re.findall(r'(现货均价|现货|均价)[^>]*>([789]\d{4}|10\d{4})<', html)
    if keyword_prices:
        print(f"    方式3: 关键词匹配: {keyword_prices}")
        price = float(keyword_prices[0][1])
        if 70000 <= price <= 100000:
            return {'price': price, 'change': 0, 'low': price, 'high': price}
    
    # 方式4：精确格式"元/吨"（同样只匹配7-10万的数字）
    precise_prices = re.findall(r'>([789]\d{4}|10\d{4})\s*元/吨', html)
    print(f"    方式4: 精确格式: {precise_prices[:10]}")
    
    if precise_prices:
        price = float(precise_prices[0])
        if 70000 <= price <= 100000:
            return {'price': price, 'change': 0, 'low': price, 'high': price}
    
    # 方式5：更宽松的匹配，查找所有数字后手动过滤
    all_digits = re.findall(r'>(\d{5,6})<', html)
    print(f"    方式5: 找到 {len(all_digits)} 个5-6位数字")
    # 过滤掉明显的小数字（如2950、3100等）和超大数字
    filtered = [p for p in all_digits if 70000 <= int(p) <= 100000]
    print(f"    方式5: 过滤后 {len(filtered)} 个铜价: {filtered}")
    
    if filtered:
        price = float(filtered[-1])
        return {'price': price, 'change': 0, 'low': price, 'high': price}
    
    print(f"    ✗ 铜价解析失败")
    return None

def parse_aluminum(html):
    print(f"    解析铝价...")
    
    prices = re.findall(r'>(2[4-5]\d{3})<', html)
    if prices:
        print(f"    ✓ 方式1: {prices[0]}")
        price = float(prices[0])
        return {'price': price, 'change': 0, 'low': price, 'high': price}
    
    all_prices = re.findall(r'>(\d{5})<', html)
    al_prices = [p for p in all_prices if 20000 <= int(p) <= 30000]
    print(f"    方式2: 找到 {len(al_prices)} 个铝价: {al_prices}")
    
    if al_prices:
        price = float(al_prices[0])
        return {'price': price, 'change': 0, 'low': price, 'high': price}
    
    print(f"    ✗ 铝价解析失败")
    return None

def parse_silicon_steel(html):
    print(f"    解析硅钢...")
    
    brands = {
        'B35A300': ['B35A300', 'B35A'],
        'B50A310': ['B50A310', 'B50A3'],
        'B50A350': ['B50A350', 'B50A35'],
        'B50A470': ['B50A470', 'B50A4'],
        'B50A600': ['B50A600', 'B50A6'],
    }
    
    results = {}
    for brand, keywords in brands.items():
        print(f"      {brand}...")
        for keyword in keywords:
            pos = html.find(keyword)
            if pos >= 0:
                segment = html[pos:pos+800]
                match = re.search(r'<span[^>*>([4-6]\d{3})</span>', segment)
                if match:
                    print(f"        ✓ 方式1: {match.group(1)}")
                    results[brand] = {'price': float(match.group(1)), 'change': 0, 'low': float(match.group(1)), 'high': float(match.group(1))}
                    break
                
                prices = re.findall(r'>([4-6]\d{3})<', segment)
                if prices:
                    print(f"        ✓ 方式2: {prices[0]}")
                    results[brand] = {'price': float(prices[0]), 'change': 0, 'low': float(prices[0]), 'high': float(prices[0])}
                    break
    
    if results:
        print(f"    ✓ 硅钢: {len(results)} 个品牌")
    else:
        print(f"    ✗ 硅钢解析失败")
    
    return results if results else None

def parse_rare_earth(html):
    print(f"    解析稀土...")
    
    price_match = re.search(r'(\d{3,6})\s*[-～—]\s*(\d{3,6})', html)
    if price_match:
        low = float(price_match.group(1))
        high = float(price_match.group(2))
        price = (low + high) / 2
        print(f"    ✓ 方式1: {low}-{high} = {price}")
        return {'price': price, 'change': 0, 'low': low, 'high': high}
    
    all_prices = re.findall(r'>(\d{3,6})<', html)
    print(f"    方式2: 找到 {len(all_prices)} 个数字")
    
    rare_prices = [p for p in all_prices if 3000 <= int(p) <= 2000000]
    if rare_prices:
        print(f"    ✓ 方式2: {rare_prices[0]}")
        price = float(rare_prices[0])
        return {'price': price, 'change': 0, 'low': price, 'high': price}
    
    print(f"    ✗ 稀土解析失败")
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

def get_last_price(code, data):
    history = data.get('history', {}).get(code, [])
    if history:
        return {
            'price': history[0]['price'],
            'change': 0,
            'low': history[0]['price'],
            'high': history[0]['price']
        }
    return None

def append_to_history(data, results, today_str):
    """
    将当天数据追加到历史记录。
    如果当天已有记录，删除旧记录，插入新记录（实现多次刷新更新为最新价格）。
    """
    history = data.get('history', {})
    
    for code, price_data in results.items():
        if price_data is None:
            continue
        
        if code not in history:
            history[code] = []
        
        # 检查当天是否已有记录
        # 找到同一天的所有记录索引
        same_day_indices = [i for i, h in enumerate(history[code]) if h['date'] == today_str]
        
        if same_day_indices:
            # 删除同一天的所有旧记录
            for idx in sorted(same_day_indices, reverse=True):
                del history[code][idx]
        
        # 在开头插入新的当天记录
        history[code].insert(0, {'date': today_str, 'price': price_data['price']})
    
    data['history'] = history
    return data

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
    
    data = append_to_history(data, results, today)
    
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
    print("原材料价格爬虫 - 修复版 v3")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {}
    data = load_data()
    
    for code, url in [
        ('CU', SOURCES['CU']),
        ('ADC12', SOURCES['ADC12']),
        ('AL6063', SOURCES['AL6063']),
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
        ('REO', SOURCES['REO']),
        ('REN', SOURCES['REN']),
        ('TB', SOURCES['TB']),
        ('CE', SOURCES['CE']),
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
    html = fetch(SOURCES['SI_SH'], 'SI_SH')
    if html:
        silicon_results = parse_silicon_steel(html)
        if silicon_results:
            results.update(silicon_results)
        else:
            print(f"    ✗ 硅钢解析失败")
    else:
        print(f"    ✗ 硅钢获取失败")
    
    print(f"\n镝铁合金...")
    print(f"    ⚠ SMM网页端无数据，使用历史数据")
    last_dyfe = get_last_price('DYFE', data)
    if last_dyfe:
        results['DYFE'] = last_dyfe
        print(f"    ✓ DYFE: {last_dyfe['price']:,.0f}（历史数据）")
    else:
        results['DYFE'] = None
        print(f"    ✗ DYFE: 无历史数据")
    
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
