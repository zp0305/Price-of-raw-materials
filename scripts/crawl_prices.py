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
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
]

session = requests.Session()

PRICE_RANGES = {
    'CU': (95000, 110000),
    'ADC12': (22000, 25000),
    'AL6063': (20000, 30000),
    'B35A300': (3500, 8000),
    'B50A310': (3500, 8000),
    'B50A350': (3500, 8000),
    'B50A470': (3500, 8000),
    'B50A600': (3500, 8000),
    'REO': (600000, 900000),
    'REN': (900000, 1000000),
    'TB': (5000, 9000),
    'CE': (30000, 40000),
    'DYFE': (1300000, 1400000),
}

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'https://hq.smm.cn/',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Connection': 'keep-alive',
    }

SOURCES = {
    'CU': 'https://hq.smm.cn/h5/cu-price',
    'ADC12': 'https://hq.smm.cn/h5/ADC12-aluminum-alloy-price',
    'AL6063': 'https://hq.smm.cn/h5/aluminum-alloy-price',
    'SI_SH': 'https://hq.smm.cn/h5/SiFe-shanghai-price',
    'SI_MYSTEEL': 'https://guigang.mysteel.com/',
    'REO': 'https://hq.smm.cn/h5/praseodymium-neodymium-oxide-price',
    'REN': 'https://hq.smm.cn/h5/praseodymium-neodymium-metal-price',
    'TB': 'https://hq.smm.cn/h5/terbium-metal-price',
    'CE': 'https://hq.smm.cn/h5/cerium-metal-price',
    'DYFE': 'https://hq.smm.cn/h5/dysprosium-ferroalloy-metal-price',
}

def fetch(url, code):
    print(f"    请求: {url}")
    max_retries = 3

    for attempt in range(max_retries):
        try:
            wait = random.uniform(1.5, 3.5) * (attempt + 1)
            time.sleep(wait)
            response = session.get(url, headers=get_headers(), timeout=30)
            print(f"    状态: {response.status_code}, 长度: {len(response.text)}")

            if response.status_code == 200 and len(response.text) > 1000:
                return response.text
            elif response.status_code == 403:
                print(f"    ⚠️ 403被拦截")
                time.sleep(random.uniform(3, 6))
        except Exception as e:
            print(f"    ✗ 错误: {e}")

    return None

def parse_table_price(html, keywords, price_range=None, backup_pattern=None):
    """
    通用表格价格解析函数
    查找包含关键词的表格行，提取价格范围和均价

    keywords: 字符串或字符串列表，用于匹配表格行
    price_range: (min_price, max_price) - 价格范围过滤，可选
    backup_pattern: 正则备用模式（当主路径失败时的后备）
    """
    if isinstance(keywords, str):
        keywords = [keywords]

    lines = html.split('\n')

    for i, line in enumerate(lines):
        if all(kw in line for kw in keywords):
            table_lines = lines[i:i+20]
            text = '\n'.join(table_lines)

            prices = re.findall(r'(\d{5,7})', text)

            if price_range:
                min_p, max_p = price_range
                prices = [p for p in prices if min_p <= int(p) <= max_p]

            if prices:
                avg_price = sum(int(p) for p in prices) / len(prices)
                return avg_price

    if backup_pattern:
        match = re.search(backup_pattern, html)
        if match:
            price = float(match.group(1))
            if not price_range or price_range[0] <= price <= price_range[1]:
                return price

    return None

def parse_copper(html):
    print(f"    解析铜价... 页面长度: {len(html)}")

    table_price = parse_table_price(html, ['上海', '今日铜价'], PRICE_RANGES.get('CU'))
    if table_price:
        print(f"    ✓ 表格解析: {table_price:,.0f}")
        return {
            'price': table_price,
            'change': 0,
            'low': table_price,
            'high': table_price
        }

    table_price = parse_table_price(html, ['上海'], PRICE_RANGES.get('CU'),
                                    backup_pattern=r'(\d{5,6})\s*[-~]\s*(\d{5,6})')
    if table_price:
        print(f"    ✓ 备用解析: {table_price:,.0f}")
        return {
            'price': table_price,
            'change': 0,
            'low': table_price,
            'high': table_price
        }

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
    print(f"    解析铝价... 页面长度: {len(html)}")

    # 方法1：精确定位ADC12全国均价行
    lines = html.split('\n')
    for i, line in enumerate(lines):
        if 'ADC12' in line and ('全国均价' in line or '平均价' in line):
            ctx = '\n'.join(lines[i:i+10])
            nums = re.findall(r'>(\d{4,5})<', ctx)
            nums = [int(p) for p in nums if PRICE_RANGES['ADC12'][0] <= int(p) <= PRICE_RANGES['ADC12'][1]]
            if nums:
                avg = float(nums[len(nums)//2])
                print(f"    ✓ ADC12均价: {avg:,.0f}")
                return {'price': avg, 'change': 0, 'low': avg, 'high': avg}

    # 方法2：原parse_table_price备选
    table_price = parse_table_price(html, ['ADC12', '全国均价'], PRICE_RANGES.get('ADC12'))
    if table_price:
        print(f"    ✓ 表格解析: {table_price:,.0f}")
        return {'price': table_price, 'change': 0, 'low': table_price, 'high': table_price}

    # 方法3：正则备选（收窄范围到23xxx-24xxx，排除A380）
    prices = re.findall(r'>(2[3-4]\d{3})<', html)
    if prices:
        price = float(prices[0])
        print(f"    ✓ 方法3: {price:,.0f}")
        return {'price': price, 'change': 0, 'low': price, 'high': price}

    print(f"    ✗ 铝价解析失败")
    return None

def parse_aluminum_6063(html):
    print(f"    解析6063铝价... 页面长度: {len(html)}")

    table_price = parse_table_price(html, ['6063'], PRICE_RANGES.get('AL6063'))
    if table_price:
        print(f"    ✓ 表格解析: {table_price:,.0f}")
        return {'price': table_price, 'change': 0, 'low': table_price, 'high': table_price}

    print(f"    ✗ 6063铝价解析失败")
    return None

def parse_silicon_steel(html):
    print(f"    解析硅钢... 页面长度: {len(html)}")

    brands = {
        'B35A300': 'B35A300',
        'B50A310': 'B50A310',
        'B50A350': 'B50A350',
        'B50A470': 'B50A470',
        'B50A600': 'B50A600',
    }

    results = {}
    price_range = PRICE_RANGES.get('B35A300')

    lines = html.split('\n')
    for brand, keyword in brands.items():
        for i, line in enumerate(lines):
            if keyword in line and '硅钢' in line:
                table_lines = lines[i:i+15]
                text = '\n'.join(table_lines)

                prices = re.findall(r'(\d{4})', text)
                prices = [p for p in prices if price_range and price_range[0] <= int(p) <= price_range[1]]

                if prices:
                    price = float(prices[0])
                    results[brand] = {'price': price, 'change': 0, 'low': price, 'high': price}
                    print(f"      ✓ 表格解析 {brand}: {price:,.0f}")
                    break
        if brand in results:
            continue

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
                prices = [p for p in prices if price_range and price_range[0] <= int(p) <= price_range[1]]
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

def parse_silicon_steel_mysteel(html):
    """从我的钢铁网抓取硅钢价格"""
    # 页面UTF-8编码，直接搜索（早期版本为GBK，但requests会自动处理）
    print(f"    解析硅钢(我的钢铁网)... 页面长度: {len(html)}")
    
    # 从Mysteel解析50WW600 → B50A600
    results = {}
    price_range = PRICE_RANGES.get('B35A300')
    
    idx = html.find('50WW600')
    if idx >= 0:
        ctx = html[idx:idx+200]
        prices = re.findall(r'(\d{4,5})', ctx)
        prices = [int(p) for p in prices if price_range and price_range[0] <= int(p) <= price_range[1]]
        if prices:
            price = float(prices[0])
            results['B50A600'] = {'price': price, 'change': 0, 'low': price, 'high': price}
            print(f"      ✓ 我的钢铁网 50WW600→B50A600: {price:,.0f}")
    
    # 根据牌号品质估算（铁损越低越贵）：B35A300 > B50A350 > B50A470 > B50A600
    if 'B50A600' in results:
        base = results['B50A600']['price']
        # B50A470 铁损4.70，比B50A600(6.00)质量更好
        b470 = base + 200
        results['B50A470'] = {'price': b470, 'change': 0, 'low': b470, 'high': b470}
        print(f"      ✓ 估算 B50A470: {b470:,.0f} (基于B50A600+200)")
        # B50A350 铁损3.50，品质更高
        b350 = base + 400
        results['B50A350'] = {'price': b350, 'change': 0, 'low': b350, 'high': b350}
        print(f"      ✓ 估算 B50A350: {b350:,.0f} (基于B50A600+400)")
        # B35A300 厚度0.35mm+低铁损，最贵
        b35 = base + 600
        results['B35A300'] = {'price': b35, 'change': 0, 'low': b35, 'high': b35}
        print(f"      ✓ 估算 B35A300: {b35:,.0f} (基于B50A600+600)")
    
    if results:
        print(f"    ✓ 我的钢铁网硅钢: {len(results)} 个品牌")
        return results
    return None

def parse_rare_earth(html, price_range):
    """
    通用稀土价格解析函数
    price_range: (min_price, max_price) - 价格范围过滤
    """
    lines = html.split('\n')

    for i, line in enumerate(lines):
        if '价格范围' in line and '均价' in line:
            table_lines = lines[i:i+20]
            text = '\n'.join(table_lines)

            range_match = re.search(r'(\d{4,7})\s*-\s*(\d{4,7})', text)
            if range_match:
                low = float(range_match.group(1))
                high = float(range_match.group(2))

                if price_range:
                    min_p, max_p = price_range
                    if not (min_p <= low <= max_p and min_p <= high <= max_p):
                        continue

                avg_price = (low + high) / 2
                return {
                    'price': avg_price,
                    'change': 0,
                    'low': low,
                    'high': high
                }

    return None

def parse_reo(html):
    print(f"    解析镨钕氧化物... 页面长度: {len(html)}")

    result = parse_rare_earth(html, PRICE_RANGES.get('REO'))
    if result:
        print(f"    ✓ 表格解析: {result['price']:,.0f}")
        return result

    print(f"    ✗ 镨钕氧化物解析失败")
    return None

def parse_ren(html):
    print(f"    解析镨钕金属... 页面长度: {len(html)}")

    result = parse_rare_earth(html, PRICE_RANGES.get('REN'))
    if result:
        print(f"    ✓ 表格解析: {result['price']:,.0f}")
        return result

    print(f"    ✗ 镨钕金属解析失败")
    return None

def parse_tb(html):
    print(f"    解析金属铽... 页面长度: {len(html)}")

    result = parse_rare_earth(html, PRICE_RANGES.get('TB'))
    if result:
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
    print(f"    解析金属铈... 页面长度: {len(html)}")

    result = parse_rare_earth(html, PRICE_RANGES.get('CE'))
    if result:
        print(f"    ✓ 表格解析: {result['price']:,.0f}")
        return result

    print(f"    ✗ 金属铈解析失败")
    return None

def parse_dyfe(html):
    print(f"    解析镝铁合金... 页面长度: {len(html)}")

    result = parse_rare_earth(html, PRICE_RANGES.get('DYFE'))
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
        history[code].insert(0, {'date': today_str, 'price': round(price_data['price'])})
    
    data['history'] = history
    return data

def calc_change(code, price, data):
    """计算与上一条【不同日期】记录的价格变化"""
    history = data.get('history', {}).get(code, [])
    today_str = datetime.now().strftime('%Y-%m-%d')

    for entry in history:
        if entry['date'] != today_str:
            last_price = round(entry['price'])
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
            r = results[code]
            r['price'] = round(r['price'])
            if 'low' in r: r['low'] = round(r['low'])
            if 'high' in r: r['high'] = round(r['high'])
    
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

def scrape_industry_news():
    """从多个来源抓取行业资讯（每类2-3条）"""
    print(f"\n行业资讯...")
    all_items = []
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # 来源1：长江有色金属网
    try:
        s = requests.Session()
        r = s.get('https://www.ccmn.cn/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code == 200:
            for url, title in re.findall(r'<a[^>]*href="(https?://www\.ccmn\.cn[^"]+)"[^>]*title="([^"]*)"', r.text):
                t = title.strip()
                if len(t) > 10:
                    tag = '稀土' if any(kw in t for kw in ['稀土','磁','钕','镨','镝','铽']) else ('铜' if '铜' in t else ('铝' if '铝' in t else '有色金属'))
                    all_items.append({'title': t, 'url': url, 'tag': tag, 'date': today_str})
    except Exception as e:
        print(f"    ⚠ 长江有色: {e}")
    
    # 来源2：上海有色资讯（金属行情）
    try:
        s2 = requests.Session()
        r2 = s2.get('https://news.smm.cn/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r2.status_code == 200:
            for url, t in re.findall(r'<a[^>]*href="(https?://news\.smm\.cn[^"]+)"[^>]*>([^<]{15,80})</a>', r2.text):
                t = t.strip()
                if len(t) > 10:
                    tag = '稀土' if any(kw in t for kw in ['稀土','磁','钕','镨','镝','铽']) else ('铜' if '铜' in t else ('铝' if '铝' in t else '有色金属'))
                    all_items.append({'title': t, 'url': url, 'tag': tag, 'date': today_str})
    except Exception as e:
        print(f"    ⚠ 有色资讯: {e}")
    
    # 来源3：SMM稀土价格页（补充稀土行情标题）
    try:
        s3 = requests.Session()
        r3 = s3.get('https://hq.smm.cn/h5/rare-earth-metal-oxides-price', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r3.status_code == 200:
            desc = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', r3.text)
            if desc:
                meta = desc.group(1)[:100]
                all_items.append({'title': '稀土行情: ' + meta, 'url': 'https://hq.smm.cn/h5/rare-earth-metal-oxides-price', 'tag': '稀土', 'date': today_str})
    except:
        pass
    
    # 来源4：SMM资讯搜索（按稀土/镨钕/镝铁等关键词搜索）
    for kw_name, kw_url in [
        ('稀土', 'https://news.smm.cn/search?keyword=' + '%E7%A8%80%E5%9C%9F'),
        ('镨钕', 'https://news.smm.cn/search?keyword=' + '%E9%95%A8%E9%92%95'),
    ]:
        try:
            s4 = requests.Session()
            r4 = s4.get(kw_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r4.status_code == 200:
                for url, title in re.findall(r'<a[^>]*href="(/news/\d+[^"]*)"[^>]*>([^<]{15,80})</a>', r4.text):
                    t = re.sub(r'<[^>]+>', '', title).strip()
                    if len(t) > 10:
                        all_items.append({'title': t, 'url': 'https://news.smm.cn' + url, 'tag': '稀土', 'date': today_str})
        except:
            pass
    
    # 来源5：我的钢铁网硅钢专页（补充硅钢资讯）
    try:
        s5 = requests.Session()
        r5 = s5.get('https://guigang.mysteel.com/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r5.status_code == 200:
            for url, title in re.findall(r'<a[^>]*href="(https?://gc\.mysteel\.com[^"]+)"[^>]*title="([^"]*)"', r5.text):
                t = title.strip()
                if len(t) > 8:
                    t = t.encode('latin1').decode('utf-8', errors='replace')
                    date_m = re.search(r'/2(\d{5})/', url)
                    date_str = f'2026-{date_m.group(1)[:2]}-{date_m.group(1)[2:4]}' if date_m else today_str
                    all_items.append({'title': t, 'url': url, 'tag': '硅钢', 'date': date_str})
    except:
        pass
    
    # 按分类去重，每类最多3条
    seen_urls = set()
    final = []
    for tag in ['铜', '铝', '稀土', '硅钢']:
        count = 0
        for item in all_items:
            if item['tag'] != tag or item['url'] in seen_urls:
                continue
            seen_urls.add(item['url'])
            final.append(item)
            count += 1
            if count >= 3:
                break
    
    if final:
        with open(DATA_DIR / "industry.json", 'w', encoding='utf-8') as f:
            json.dump({'update_time': datetime.now().strftime('%Y-%m-%d %H:%M'), 'items': final}, f, ensure_ascii=False, indent=2)
        cats = ', '.join([f'{k}={sum(1 for x in final if x["tag"]==k)}' for k in ['铜','铝','稀土','硅钢']])
        print(f"    ✓ {len(final)} 条: {cats}")
    else:
        print(f"    ✗ 未获取到资讯")

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
    
    # 硅钢（优先我的钢铁网，备用SMM）
    print(f"\n硅钢...")
    # 使用独立Session+普通Referer访问我的钢铁网（避免SMM来源被屏蔽）
    mysession = requests.Session()
    myheaders = get_headers()
    myheaders['Referer'] = 'https://www.mysteel.com/'
    try:
        r = mysession.get(SOURCES['SI_MYSTEEL'], headers=myheaders, timeout=30)
        if r.status_code == 200 and len(r.text) > 1000:
            silicon_results = parse_silicon_steel_mysteel(r.text)
            if silicon_results:
                results.update(silicon_results)
            else:
                print(f"    我的钢铁网解析失败，回退SMM...")
                html2 = fetch(SOURCES['SI_SH'], 'SI_SH')
                if html2:
                    s2 = parse_silicon_steel(html2)
                    if s2:
                        results.update(s2)
        else:
            print(f"    我的钢铁网状态异常({r.status_code})，回退SMM...")
            html2 = fetch(SOURCES['SI_SH'], 'SI_SH')
            if html2:
                s2 = parse_silicon_steel(html2)
                if s2:
                    results.update(s2)
    except Exception as e:
        print(f"    ✗ 我的钢铁网异常: {e}")
        html2 = fetch(SOURCES['SI_SH'], 'SI_SH')
        if html2:
            s2 = parse_silicon_steel(html2)
            if s2:
                results.update(s2)
    
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
        scrape_industry_news()
        return 0
    return 1

if __name__ == '__main__':
    exit(main())
