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
    'DYFE': 'https://hq.smm.cn/h5/dysprosium-ferroalloy-metal-price',
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

def parse_table_price(html, keywords, price_range=None):
    """
    通用表格价格解析函数
    查找包含关键词的表格行，提取价格范围和均价
    
    keywords: 字符串或字符串列表，用于匹配表格行
    price_range: (min_price, max_price) - 价格范围过滤，可选
    """
    # 统一转换为列表格式
    if isinstance(keywords, str):
        keywords = [keywords]
    
    lines = html.split('\n')
    
    # 查找包含所有关键词的行
    for i, line in enumerate(lines):
        # 检查是否包含所有关键词
        if all(kw in line for kw in keywords):
            # 找到这一行后，往后几行查找价格数据
            table_lines = lines[i:i+20]
            text = '\n'.join(table_lines)
            
            # 查找所有5-7位数字（价格）
            prices = re.findall(r'(\d{5,7})', text)
            
            # 过滤价格范围
            if price_range:
                min_p, max_p = price_range
                prices = [p for p in prices if min_p <= int(p) <= max_p]
            
            if prices:
                # 如果有多个价格，取中间值作为均价
                avg_price = sum(int(p) for p in prices) / len(prices)
                return avg_price
    
    return None

def parse_copper(html):
    print(f"    解析铜价...")
    
    # 方法1：表格解析 - 查找"上海"和"今日铜价"
    table_price = parse_table_price(html, ['上海', '今日铜价'], (100000, 105000))
    if table_price:
        print(f"    ✓ 表格解析: {table_price:,.0f}")
        return {
            'price': table_price,
            'change': 0,
            'low': table_price,
            'high': table_price
        }
    
    # 方法2：查找所有5-6位数字，过滤合理的铜价范围
    all_prices = re.findall(r'(\d{5,6})', html)
    copper_prices = [int(p) for p in all_prices if 100000 <= int(p) <= 105000]
    print(f"    方法2: 找到 {len(copper_prices)} 个铜价")
    
    if len(copper_prices) >= 2:
        avg_price = sum(copper_prices) / len(copper_prices)
        print(f"    ✓ 方法2: {avg_price:,.0f}")
        return {
            'price': avg_price,
            'change': 0,
            'low': min(copper_prices),
            'high': max(copper_prices)
        }
    
    print(f"    ✗ 铜价解析失败")
    return None

def parse_aluminum(html):
    print(f"    解析铝价...")
    
    # 方法1：表格解析 - 查找"ADC12"和"全国均价"
    table_price = parse_table_price(html, ['ADC12', '全国均价'], (20000, 30000))
    if table_price:
        print(f"    ✓ 表格解析: {table_price:,.0f}")
        return {'price': table_price, 'change': 0, 'low': table_price, 'high': table_price}
    
    # 方法2：正则匹配
    prices = re.findall(r'>(2[4-5]\d{3})<', html)
    if prices:
        print(f"    ✓ 方法2: {prices[0]}")
        price = float(prices[0])
        return {'price': price, 'change': 0, 'low': price, 'high': price}
    
    print(f"    ✗ 铝价解析失败")
    return None

def parse_aluminum_6063(html):
    print(f"    解析6063铝价...")
    
    # 方法1：表格解析 - 查找"6063"
    table_price = parse_table_price(html, ['6063'], (20000, 30000))
    if table_price:
        print(f"    ✓ 表格解析: {table_price:,.0f}")
        return {'price': table_price, 'change': 0, 'low': table_price, 'high': table_price}
    
    print(f"    ✗ 6063铝价解析失败")
    return None

def parse_silicon_steel(html):
    print(f"    解析硅钢...")
    
    brands = {
        'B35A300': 'B35A300',
        'B50A310': 'B50A310',
        'B50A350': 'B50A350',
        'B50A470': 'B50A470',
        'B50A600': 'B50A600',
    }
    
    results = {}
    
    # 方法1：表格解析
    lines = html.split('\n')
    for brand, keyword in brands.items():
        for i, line in enumerate(lines):
            if keyword in line and '硅钢' in line:
                table_lines = lines[i:i+15]
                text = '\n'.join(table_lines)
                
                # 查找4位数价格（硅钢价格）
                prices = re.findall(r'(\d{4})', text)
                prices = [p for p in prices if 4000 <= int(p) <= 7000]
                
                if prices:
                    price = float(prices[0])
                    results[brand] = {'price': price, 'change': 0, 'low': price, 'high': price}
                    print(f"      ✓ 表格解析 {brand}: {price:,.0f}")
                    break
        if brand in results:
            continue
        
        # 方法2：关键词搜索
        for i, line in enumerate(lines):
            if keyword in line:
                segment = html[i:i+800]
                match = re.search(r'<span[^>]*(\d{4,5})</span>', segment)
                if match:
                    price = float(match.group(1))
                    results[brand] = {'price': price, 'change': 0, 'low': price, 'high': price}
                    print(f"      ✓ 方法2 {brand}: {price:,.0f}")
                    break
                
                prices = re.findall(r'>(\d{4,5})<', segment)
                prices = [p for p in prices if 4000 <= int(p) <= 7000]
                if prices:
                    price = float(prices[0])
                    results[brand] = {'price': price, 'change': 0, 'low': price, 'high': price}
                    print(f"      ✓ 方法2 {brand}: {price:,.0f}")
                    break
            if brand in results:
                break
    
    if results:
        print(f"    ✓ 硅钢: {len(results)} 个品牌")
    else:
        print(f"    ✗ 硅钢解析失败")
    
    return results if results else None

def parse_rare_earth(html, price_range):
    """
    通用稀土价格解析函数
    price_range: (min_price, max_price) - 价格范围过滤
    """
    # 方法1：表格解析 - 查找价格范围和均价
    # 稀土价格通常是7位数（万元/吨）或3-6位数（元/千克）
    lines = html.split('\n')
    
    for i, line in enumerate(lines):
        if '价格范围' in line and '均价' in line:
            table_lines = lines[i:i+20]
            text = '\n'.join(table_lines)
            
            # 查找价格范围（通常是 "xxxxx - xxxxx" 格式）
            range_match = re.search(r'(\d{4,7})\s*-\s*(\d{4,7})', text)
            if range_match:
                low = float(range_match.group(1))
                high = float(range_match.group(2))
                
                # 根据价格范围过滤
                if price_range:
                    min_p, max_p = price_range
                    if not (min_p <= low <= max_p and min_p <= high <= max_p):
                        continue
                
                # 计算均价
                avg_price = (low + high) / 2
                return {
                    'price': avg_price,
                    'change': 0,
                    'low': low,
                    'high': high
                }
    
    return None

def parse_reo(html):
    print(f"    解析镨钕氧化物...")
    
    # 方法1：表格解析 - 镨钕氧化物价格范围约700000-800000元/吨
    result = parse_rare_earth(html, (700000, 800000))
    if result:
        print(f"    ✓ 表格解析: {result['price']:,.0f}")
        return result
    
    print(f"    ✗ 镨钕氧化物解析失败")
    return None

def parse_ren(html):
    print(f"    解析镨钕金属...")
    
    # 方法1：表格解析 - 镨钕金属价格范围约900000-1000000元/吨
    result = parse_rare_earth(html, (900000, 1000000))
    if result:
        print(f"    ✓ 表格解析: {result['price']:,.0f}")
        return result
    
    print(f"    ✗ 镨钕金属解析失败")
    return None

def parse_tb(html):
    print(f"    解析金属铽...")
    
    # 方法1：表格解析 - 金属铽价格约7000-8000元/千克（=7000000-8000000元/吨）
    result = parse_rare_earth(html, (7000, 8000))
    if result:
        # 将元/千克转换为元/吨
        price_per_ton = result['price'] * 1000
        print(f"    ✓ 表格解析: {result['price']:,.0f}元/千克 = {price_per_ton:,.0f}元/吨")
        return {
            'price': price_per_ton,
            'change': 0,
            'low': result['low'] * 1000,
            'high': result['high'] * 1000
        }
    
    print(f"    ✗ 金属铽解析失败")
    return None

def parse_ce(html):
    print(f"    解析金属铈...")
    
    # 方法1：表格解析 - 金属铈价格约30000-40000元/吨
    result = parse_rare_earth(html, (30000, 40000))
    if result:
        print(f"    ✓ 表格解析: {result['price']:,.0f}")
        return result
    
    print(f"    ✗ 金属铈解析失败")
    return None

def parse_dyfe(html):
    print(f"    解析镝铁合金...")
    
    # 方法1：表格解析 - 镝铁合金价格范围约1300000-1400000元/吨
    result = parse_rare_earth(html, (1300000, 1400000))
    if result:
        print(f"    ✓ 表格解析: {result['price']:,.0f}")
        return result
    
    print(f"    ✗ 镝铁合金解析失败")
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
        same_day_indices = [i for i, h in enumerate(history[code]) if h['date'] == today_str]
        
        if same_day_indices:
            # 删除同一天的所有旧记录
            for idx in sorted(same_day_indices, reverse=True):
                del history[code][idx]
        
        # 在开头插入新的当天记录
        history[code].insert(0, {'date': today_str, 'price': price_data['price']})
    
    data['history'] = history
    return data

def calc_change(code, price, data):
    """根据历史记录计算今日相较于最近一条记录的涨跌"""
    history = data.get('history', {}).get(code, [])
    if history:
        last_price = round(history[0]['price'])
        return round(price) - last_price
    return 0

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
    
    # 写入前统一取整
    for code in results:
        if results[code] is not None:
            results[code]['price'] = round(results[code]['price'])
    
    data = append_to_history(data, results, today)
    
    today_data = []
    for code, price_data in results.items():
        if price_data is not None:
            change = calc_change(code, price_data['price'], data)
            today_data.append({
                'code': code,
                'name': material_names.get(code, code),
                'price': price_data['price'],
                'change': change,
                'date': today
            })
    
    data['today'] = today_data
    
    with open(DATA_DIR / "prices.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 保存完成 ({len(today_data)} 种材料)")
    return data

def main():
    print("=" * 70)
    print("原材料价格爬虫 - v6 (表格解析优化版)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {}
    data = load_data()
    
    # 铜价
    print(f"\nCU (电解铜)...")
    html = fetch(SOURCES['CU'], 'CU')
    if html:
        result = parse_copper(html)
        results['CU'] = result
    else:
        results['CU'] = None
        print(f"    ✗ CU: 获取失败")
    
    # 铝合金
    print(f"\nADC12 (铝合金)...")
    html = fetch(SOURCES['ADC12'], 'ADC12')
    if html:
        result = parse_aluminum(html)
        results['ADC12'] = result
    else:
        results['ADC12'] = None
        print(f"    ✗ ADC12: 获取失败")
    
    print(f"\nAL6063 (6063铝棒)...")
    html = fetch(SOURCES['AL6063'], 'AL6063')
    if html:
        result = parse_aluminum_6063(html)
        results['AL6063'] = result
    else:
        results['AL6063'] = None
        print(f"    ✗ AL6063: 获取失败")
    
    # 硅钢
    print(f"\n硅钢...")
    html = fetch(SOURCES['SI_SH'], 'SI_SH')
    if html:
        silicon_results = parse_silicon_steel(html)
        if silicon_results:
            results.update(silicon_results)
    else:
        print(f"    ✗ 硅钢获取失败")
    
    # 稀土
    print(f"\nREO (镨钕氧化物)...")
    html = fetch(SOURCES['REO'], 'REO')
    if html:
        result = parse_reo(html)
        results['REO'] = result
    else:
        results['REO'] = None
        print(f"    ✗ REO: 获取失败")
    
    print(f"\nREN (镨钕金属)...")
    html = fetch(SOURCES['REN'], 'REN')
    if html:
        result = parse_ren(html)
        results['REN'] = result
    else:
        results['REN'] = None
        print(f"    ✗ REN: 获取失败")
    
    print(f"\nTB (金属铽)...")
    html = fetch(SOURCES['TB'], 'TB')
    if html:
        result = parse_tb(html)
        results['TB'] = result
    else:
        results['TB'] = None
        print(f"    ✗ TB: 获取失败")
    
    print(f"\nCE (金属铈)...")
    html = fetch(SOURCES['CE'], 'CE')
    if html:
        result = parse_ce(html)
        results['CE'] = result
    else:
        results['CE'] = None
        print(f"    ✗ CE: 获取失败")
    
    # 镝铁合金
    print(f"\nDYFE (镝铁合金)...")
    html = fetch(SOURCES['DYFE'], 'DYFE')
    if html:
        result = parse_dyfe(html)
        results['DYFE'] = result
    else:
        results['DYFE'] = None
        print(f"    ✗ DYFE: 获取失败")
    
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
