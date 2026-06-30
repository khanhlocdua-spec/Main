import subprocess
import sys
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['XNNPACK_DELEGATE_LOG_LEVEL'] = '0'
os.environ['TF_LITE_LOG_LEVEL'] = '3' 
os.environ['WDM_LOG_LEVEL'] = '0'
sys.stderr = open(os.devnull, 'w')

def install_module(module_name, import_name=None):
    """Tự động cài module nếu chưa có"""
    if import_name is None:
        import_name = module_name
    try:
        __import__(import_name)
        print(f"✅ Module {module_name} đã có")
        return True
    except ImportError:
        print(f"📦 Đang cài {module_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        print(f"✅ Đã cài {module_name} thành công!")
        return True

modules_to_install = [
    ("requests", "requests"),
    ("Pillow", "PIL"),
    ("pytesseract", "pytesseract"),
    ("selenium", "selenium"),
    ("webdriver-manager", "webdriver_manager"),
    ("beautifulsoup4", "bs4")
]

for pip_name, import_name in modules_to_install:
    install_module(pip_name, import_name)

import requests
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
import threading
import time
import re
import signal
from datetime import datetime
import json
import random
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, unquote
import mimetypes

class CookieHandler:
    @staticmethod
    def to_dict(cookie_str: str) -> Dict[str, str]:
        return {k.strip(): v.strip() for item in cookie_str.split(";") 
                if "=" in item for k, v in [item.split("=", 1)]}

class NumberEncoder:
    @staticmethod
    def to_base36(num: int) -> str:
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        if num == 0:
            return "0"
        result = ""
        while num:
            num, remainder = divmod(num, 36)
            result = chars[remainder] + result
        return result

class HTMLExtractor:
    @staticmethod
    def find_pattern(html: str, pattern: str) -> Optional[str]:
        match = re.search(pattern, html)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_token(html: str) -> Optional[str]:
        patterns = [
            r'DTSGInitialData".*?"token":"([^"]+)"',
            r'"token":"([^"]+)"',
        ]
        for pattern in patterns:
            result = HTMLExtractor.find_pattern(html, pattern)
            if result:
                return result
        return None
    
    @staticmethod
    def extract_lsd(html: str) -> Optional[str]:
        patterns = [
            r'LSD".*?"token":"([^"]+)"',
            r'"token":"([^"]+)"',
        ]
        for pattern in patterns:
            result = HTMLExtractor.find_pattern(html, pattern)
            if result:
                return result
        return None
    
    @staticmethod
    def extract_user_id(html: str) -> Optional[str]:
        patterns = [
            r'"actorID":"(\d+)"',
            r'"USER_ID":"(\d+)"',
            r'c_user=(\d+)',
        ]
        for pattern in patterns:
            result = HTMLExtractor.find_pattern(html, pattern)
            if result:
                return result
        return None
    
    @staticmethod
    def extract_revision(html: str) -> Optional[str]:
        pattern = r'client_revision["\s:]+(\d+)'
        return HTMLExtractor.find_pattern(html, pattern)
    
    @staticmethod
    def extract_jazoest(html: str) -> Optional[str]:
        pattern = r'jazoest=(\d+)'
        return HTMLExtractor.find_pattern(html, pattern)

class FacebookSession:
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.token = None
        self.user_id = None
        self.revision = None
        self.jazoest = None
        self.lsd = None
    
    def authenticate(self) -> bool:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "cookie": self.cookie,
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(
                "https://www.facebook.com/",
                headers=headers,
                cookies=CookieHandler.to_dict(self.cookie),
                timeout=30
            )
            
            html = response.text
            self.token = HTMLExtractor.extract_token(html)
            self.user_id = HTMLExtractor.extract_user_id(html)
            self.revision = HTMLExtractor.extract_revision(html) or "1000000"
            self.jazoest = HTMLExtractor.extract_jazoest(html) or "0"
            self.lsd = HTMLExtractor.extract_lsd(html) or "0"
            
            if self.token and self.user_id:
                return True
            return False
        except Exception as e:
            return False

class GenData:
    def __init__(self, session: FacebookSession):
        self.session = session
        self.request_counter = 0
    
    def build(self, bio: str, name: str) -> Dict[str, Any]:
        self.request_counter += 1   
        category_id = [169421023103905, 2347428775505624, 2347428775505624, 2347428775505624, 
                       192614304101075, 145118935550090, 1350536325044173, 471120789926333, 
                       180410821995109, 145118935550090, 357645644269220, 2705]
        category = random.choice(category_id) 
        payload = {
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'AdditionalProfilePlusCreationMutation',
            'server_timestamps': 'true',
            "fb_dtsg": self.session.token,
            "jazoest": self.session.jazoest,
            "__a": "1",
            "__user": self.session.user_id,
            "__req": NumberEncoder.to_base36(self.request_counter),
            "__rev": self.session.revision,
            "av": self.session.user_id,
            "lsd": self.session.lsd,
            'variables': '{"input":{"bio":"'+bio+'","categories":["'+str(category)+'"],"creation_source":"comet","name":"'+name+'","off_platform_creator_reachout_id":null,"page_referrer":"launch_point","actor_id":"'+self.session.user_id+'","client_mutation_id":"1"}}',
            'doc_id': '23863457623296585'
        }
        return payload

class REGPRO5:
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.session = FacebookSession(cookie)
        self.payload_builder = None
        self.ready = False
    
    def login(self) -> bool:
        if self.session.authenticate():
            self.payload_builder = GenData(self.session)
            self.ready = True
            return True
        return False
    
    def REG(self, bio: str, name: str):
        if not self.ready:
            return False, "Not logged in"
        
        payload = self.payload_builder.build(bio, name)
        headers = {
            "accept": "*/*",
            "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.facebook.com",
            "referer": "https://www.facebook.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "x-fb-lsd": self.session.lsd,
            "cookie": self.cookie,
            'x-fb-friendly-name': 'AdditionalProfilePlusCreationMutation',
        }
        
        try:
            response = requests.post('https://www.facebook.com/api/graphql/', headers=headers, data=payload, timeout=30)
            
            if response.status_code != 200:
                return False, f"HTTP Error: {response.status_code}"
            
            if not response.text:
                return False, "Empty response"
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                return False, f"Invalid JSON response: {response.text[:200]}"
            
            if "errors" in data:
                return False, f"GraphQL errors: {data['errors']}"
            
            if "data" not in data:
                return False, f"Missing 'data' field: {data}"
            
            profile_data = data.get("data", {}).get("additional_profile_plus_create")
            if profile_data is None:
                return False, f"Missing profile data: {data}"
            
            if profile_data.get("name_error"):
                return False, profile_data["name_error"]
            
            if profile_data.get("error_message"):
                return False, profile_data["error_message"]
            
            additional_profile = profile_data.get("additional_profile")
            if additional_profile is None:
                return False, "Không thể tạo trang. Vui lòng thử tên khác."
            
            profile_id = additional_profile.get("id")
            if profile_id:
                return True, profile_id
            else:
                return False, f"No profile ID: {profile_data}"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except Exception as e:
            return False, f"Error: {str(e)}"

class BuffShareTool:
    """Tool Buff Share Facebook - Tự động lấy ID + Share bài viết"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    @staticmethod
    def get_random_headers(cookie=None):
        headers = {
            'User-Agent': random.choice(BuffShareTool.USER_AGENTS),
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'upgrade-insecure-requests': '1'
        }
        if cookie:
            headers['cookie'] = cookie
        return headers
    
    @staticmethod
    def extract_from_url(url: str):
        """Trích xuất Post ID trực tiếp từ URL"""
        url = url.strip()
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            path = parsed.path
        except Exception:
            return None

        for key in ('story_fbid', 'fbid', 'id'):
            if key in qs and qs[key][0].isdigit():
                val = qs[key][0]
                if len(val) >= 10:
                    return val

        if 'v' in qs and qs['v'][0].isdigit() and len(qs['v'][0]) >= 10:
            return qs['v'][0]

        patterns = [
            r'/posts/(?:[^/]+/)?(\d{10,})',
            r'/videos/(?:[^/]+/)?(\d{10,})',
            r'/photos/(?:[^/]+/)?(\d{10,})',
            r'/photo/(?:[^/]+/)?(\d{10,})',
            r'/reel/(?:[^/]+/)?(\d{10,})',
            r'/reels/(?:[^/]+/)?(\d{10,})',
            r'/groups/[^/]+/posts/(?:[^/]+/)?(\d{10,})',
            r'/groups/[^/]+/permalink/(?:[^/]+/)?(\d{10,})',
            r'/permalink/(?:[^/]+/)?(\d{10,})',
            r'/story\.php.*story_fbid=(\d{10,})',
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                return m.group(1)

        m = re.search(r'/(\d{13,19})(?:/|$|\?)', path)
        if m:
            return m.group(1)

        return None

    @staticmethod
    def parse_id_from_html(html: str):
        """Trích xuất Post ID từ HTML"""
        patterns = [
            r'"top_level_post_id"\s*:\s*"(\d{10,})"',
            r'"post_id"\s*:\s*"(\d{10,})"',
            r'story_fbid[=:]"?(\d{10,})',
            r'"story_fbid"\s*:\s*"(\d{10,})"',
            r'"fbid"\s*:\s*"(\d{10,})"',
            r'/posts/(\d{10,})',
        ]
        for pat in patterns:
            m = re.search(pat, html)
            if m:
                return m.group(1)

        m = re.search(r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            og_url = unquote(m.group(1))
            result = BuffShareTool.extract_from_url(og_url)
            if result:
                return result

        return None

    @staticmethod
    def get_post_id_from_url(url: str, cookie: str = None):
        """Lấy Post ID từ URL"""
        result = BuffShareTool.extract_from_url(url)
        if result:
            return result

        headers = BuffShareTool.get_random_headers(cookie)
        
        try:
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            result = BuffShareTool.extract_from_url(resp.url) or BuffShareTool.parse_id_from_html(resp.text)
            if result:
                return result
        except:
            pass

        try:
            mbasic_url = url
            for domain in ('www.facebook.com', 'm.facebook.com', 'web.facebook.com'):
                mbasic_url = mbasic_url.replace(domain, 'mbasic.facebook.com')
            headers = BuffShareTool.get_random_headers(cookie)
            resp = requests.get(mbasic_url, headers=headers, timeout=15, allow_redirects=True)
            result = BuffShareTool.extract_from_url(resp.url) or BuffShareTool.parse_id_from_html(resp.text)
            if result:
                return result
        except:
            pass

        return None

    @staticmethod
    def get_token_from_cookie(cookie):
        """Lấy token EAAG từ cookie"""
        headers = BuffShareTool.get_random_headers(cookie)
        headers.update({
            'authority': 'business.facebook.com',
            'referer': 'https://www.facebook.com/',
        })
        
        try:
            home_business = requests.get('https://business.facebook.com/content_management', headers=headers, timeout=15).text
            token = home_business.split('EAAG')[1].split('","')[0]
            return f'{cookie}|EAAG{token}'
        except:
            return None

    @staticmethod
    def share_post(token_data, post_id, mode='private'):
        """Thực hiện share bài viết"""
        cookie = token_data.split('|')[0]
        token = token_data.split('|')[1]
        
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate',
            'connection': 'keep-alive',
            'content-length': '0',
            'cookie': cookie,
            'host': 'graph.facebook.com',
            'User-Agent': random.choice(BuffShareTool.USER_AGENTS)
        }
        
        published = '0' if mode == 'private' else '1'
        
        try:
            time.sleep(1.5)
            response = requests.post(
                f'https://graph.facebook.com/me/feed?link=https://m.facebook.com/{post_id}&published={published}&access_token={token}', 
                headers=headers, 
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
buffshare_success_count = 0
buffshare_fail_count = 0
buffshare_print_lock = threading.Lock()

def buffshare_worker(token_data, post_id, share_id, mode='private'):
    """Worker chạy trong mỗi luồng"""
    global buffshare_success_count, buffshare_fail_count
    
    result = BuffShareTool.share_post(token_data, post_id, mode)
    
    with buffshare_print_lock:
        if result:
            buffshare_success_count += 1
            print(f"{Colors.PURPLE3}[{share_id}] {Colors.YELLOW_LIGHT}➤ SHARE ➤ {Colors.GREEN_LIGHT} SUCCESS {Colors.WHITE_BRIGHT}➤ ID: {post_id}{Colors.RESET}")
        else:
            buffshare_fail_count += 1
            print(f"{Colors.PURPLE3}[{share_id}] {Colors.YELLOW_LIGHT}➤ SHARE ➤ {Colors.RED_LIGHT} FAILED {Colors.WHITE_BRIGHT}➤ ID: {post_id}{Colors.RESET}")
    
    return result
class KsxKoji:
    """Class Buff Follow - GIỮ NGUYÊN CODE GỐC"""
    def __init__(self) -> None:
        self.author = 'Vu Hai Lam'
        self.facebook = 'https://facebook.com/tola.hailam.cute'
        self.youtube = 'https://www.youtube.com/@pautous789'
    
    def __Get_ThongTin__(self, cookie):
        id_ck = cookie.split('c_user=')[1].split(';')[0]
        a = requests.get('https://mbasic.facebook.com/profile.php?='+id_ck, headers={'cookie': cookie}).text
        try:
            self.name = a.split('<title>')[1].split('</title>')[0]
            self.fb_dtsg = a.split('<input type="hidden" name="fb_dtsg" value="')[1].split('"')[0]
            self.jazoest = a.split('<input type="hidden" name="jazoest" value="')[1].split('"')[0]
            return True
        except:
            return False
    
    def __Get_Page__(self, cookie):
        self.dem = 0
        data = {
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest,
            'variables': '{"showUpdatedLaunchpointRedesign":true,"useAdminedPagesForActingAccount":false,"useNewPagesYouManage":true}',
            'doc_id': '5300338636681652'
        }
        try:
            getidpro5 = requests.post('https://www.facebook.com/api/graphql/', headers={'cookie': cookie}, data=data).json()['data']['viewer']['actor']['profile_switcher_eligible_profiles']['nodes']
            for uidd in getidpro5:
                self.dem += 1
                uid_page = uidd['profile']['id']
                list_page.append(uid_page)
            return True
        except:
            return False
    
    def __Follow__(self, cookie, id, taget):
        self.headers = {
            'accept': '*/*',
            'accept-language': 'vi,vi-VN;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': f'{cookie} i_user={id};',
            'origin': 'https://www.facebook.com',
            'referer': 'https://www.facebook.com',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        data = {
            'av': id,
            '__user': id,
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'CometUserFollowMutation',
            'variables': '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,tap_search_bar,1713671419755,394049,190055527696468,,","is_tracking_encrypted":false,"subscribe_location":"PROFILE","subscribee_id":"'+taget+'","tracking":null,"actor_id":"'+id+'","client_mutation_id":"19"},"scale":1}',
            'server_timestamps': 'true',
            'doc_id': '7393793397375006',
        }

        follow = requests.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data)
        try:
            check = follow.json()['errors']
            for i in check:
                if i['summary'] == 'Tài khoản của bạn hiện bị hạn chế':
                    return 'block'
        except:
            if 'IS_SUBSCRIBED' in follow.text:
                return True
            else:
                return False

list_page = []

is_shutting_down = False
driver_instance = None

FIREBASE_URL = "https://serverkeys-85135-default-rtdb.asia-southeast1.firebasedatabase.app"

def signal_handler(sig, frame):
    global is_shutting_down, driver_instance, popup_killer_running
    
    if is_shutting_down:
        os._exit(0)
    
    is_shutting_down = True
    print(f"\n\n{Colors.YELLOW_LIGHT}Đang TẮT...{Colors.RESET}")
    
    popup_killer_running = False
    
    if driver_instance:
        try:
            driver_instance.quit()
        except:
            pass
    
    print(f"{Colors.GREEN_LIGHT}ĐÃ TẮT!{Colors.RESET}")
    
    time.sleep(0.5)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

class Rainbow:
    @staticmethod
    def text(text):
        colors = [
            '\033[38;2;255;100;100m',
            '\033[38;2;255;180;100m',
            '\033[38;2;255;255;150m',
            '\033[38;2;150;255;150m',
            '\033[38;2;100;255;200m',
            '\033[38;2;100;180;255m',
            '\033[38;2;200;150;255m',
        ]
        result = ""
        for i, char in enumerate(text):
            result += colors[i % len(colors)] + char
        return result + Colors.RESET

class Colors:
    PURPLE1 = '\033[38;2;128;0;255m'
    PURPLE2 = '\033[38;2;138;43;226m'
    PURPLE3 = '\033[38;2;153;50;204m'
    PURPLE4 = '\033[38;2;186;85;211m'
    PURPLE5 = '\033[38;2;218;112;214m'
    PURPLE6 = '\033[38;2;221;160;221m'
    GREEN_LIGHT = '\033[38;2;100;255;100m'
    YELLOW_LIGHT = '\033[38;2;255;255;150m'
    RED_LIGHT = '\033[38;2;255;100;100m'
    BLUE_LIGHT = '\033[38;2;100;200;255m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    ORANGE2 = '\033[38;2;255;150;50m'
    WHITE_BRIGHT = '\033[38;2;255;255;255m'

popup_killer_running = True

def print_info_table():
    """In bảng thông tin với hiệu ứng từng ký tự"""
    info_lines = [
        f"{Colors.PURPLE1}╭────────────────────────────── ○ › {Colors.PURPLE1}Th{Colors.PURPLE2}ôn{Colors.PURPLE3}g T{Colors.PURPLE4}i{Colors.PURPLE5}n{Colors.WHITE} {Colors.PURPLE1}‹ ○ ──────────────────────────────╮{Colors.RESET}",
        f"{Colors.PURPLE2}│          • >>> Author     |   Tin/Khánh Lộc (@tindevtools)                    │{Colors.RESET}",
        f"{Colors.PURPLE3}│          • >>> More Infor |   Tin × LouisDevTool                              │{Colors.RESET}",
        f"{Colors.PURPLE4}│          • >>> Version    |   V2.0 (Auto Key by IP)                           │{Colors.RESET}",
        f"{Colors.PURPLE5}│          • >>> Telegram   |   𝚃𝙸𝙽 ⨯ 𝙳𝙴𝚅 【</>】 | @tindevtools                │{Colors.RESET}",
        f"{Colors.PURPLE6}│          • >>> Tool       |   Tool Dịch Vụ Đa Chức Năng                       │{Colors.RESET}",
        f"{Colors.WHITE}╰───────────────────────────────────────────────────────────────────────────────╯{Colors.RESET}"
    ]
    for line in info_lines:
        type_line_quick(line, 0.002)
        time.sleep(0.003)
    print()
    
def get_ip():
    """Lấy IP public"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return "unknown"

def find_key_by_ip(ip):
    """Tìm key trong database theo IP"""
    try:
        resp = requests.get(f"{FIREBASE_URL}/keys.json")
        
        if resp.status_code != 200:
            return None
        
        all_keys = resp.json()
        
        if not all_keys:
            return None
        
        for key_id, key_data in all_keys.items():
            if key_data and key_data.get('ip') == ip:
                if 'deadTime' in key_data:
                    dead_time = datetime.fromisoformat(key_data['deadTime'])
                    if datetime.now() <= dead_time:
                        return key_id
        
        return None
    except Exception as e:
        return None

def check_and_use_key(key, ip):
    """
    Kiểm tra key - cho phép IP đã đăng ký dùng nhiều lần
    Trả về: "VALID", "WRONG_IP", "INVALID", "EXPIRED", "ERROR"
    """
    try:
        resp = requests.get(f"{FIREBASE_URL}/keys/{key}.json")
        
        if resp.status_code != 200:
            return "ERROR"
        
        key_data = resp.json()
        
        if not key_data:
            return "INVALID"

        if 'deadTime' not in key_data:
            return "INVALID"
        
        dead_time = datetime.fromisoformat(key_data['deadTime'])
        if datetime.now() > dead_time:
            return "EXPIRED"

        if 'ip' not in key_data or key_data['ip'] is None:
            update_data = {
                'ip': ip,
                'usedAt': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            requests.patch(f"{FIREBASE_URL}/keys/{key}.json", json=update_data)
            return "VALID"

        if key_data['ip'] != ip:
            return "WRONG_IP"
            
        requests.patch(f"{FIREBASE_URL}/keys/{key}.json", json={'usedAt': datetime.now().isoformat()})
        return "VALID"
        
    except Exception as e:
        print(f"Lỗi: {e}")
        return "ERROR"
    
def key_auth_screen():
    """Màn hình nhập key - tự động kiểm tra IP đã có key chưa"""
    global current_used_key
    
    clear_screen()
    show_loading_banner()
    print_info_table()
    
    ip = get_ip()
    existing_key = find_key_by_ip(ip)
    
    if existing_key:
        print(f"{Colors.BLUE_LIGHT}Key: {existing_key}{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}Đang xác thực...{Colors.RESET}\n")
        
        result = check_and_use_key(existing_key, ip)
        
        if result == "VALID":
            current_used_key = existing_key
            print(f"{Colors.GREEN_LIGHT}✅ XÁC THỰC THÀNH CÔNG!{Colors.RESET}")
            time.sleep(2)
            return True
        elif result == "EXPIRED":
            print(f"{Colors.RED_LIGHT}⏰ Key đã hết hạn! Vui lòng nhập key mới.{Colors.RESET}")
            time.sleep(2)
        else:
            print(f"{Colors.RED_LIGHT}❌ Key không còn hiệu lực! Vui lòng nhập key mới.{Colors.RESET}")
            time.sleep(2)
    
    print(f"\n{Colors.YELLOW_LIGHT}{'═'*36}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT} VUI LÒNG NHẬP KEY ĐỂ SỬ DỤNG TOOL{Colors.RESET}")
    print(f"{Colors.YELLOW_LIGHT}{'═'*36}{Colors.RESET}\n")
    
    key = input(f"{Rainbow.text('Nhập key: ')}").strip().upper()
    
    if not key:
        print(f"{Colors.RED_LIGHT}❌ Key không được để trống!{Colors.RESET}")
        time.sleep(2)
        return False
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang kiểm tra key...{Colors.RESET}\n")
    
    result = check_and_use_key(key, ip)

    if result == "VALID":
        current_used_key = key
        print(f"{Colors.GREEN_LIGHT}✅ THÀNH CÔNG! Key hợp lệ.{Colors.RESET}")
        time.sleep(2)
        return True
    elif result == "WRONG_IP":
        print(f"{Colors.RED_LIGHT}❌ Key này đang được sử dụng bởi IP khác!{Colors.RESET}")
        print(f"{Colors.RED_LIGHT}Mỗi key chỉ dùng cho 1 IP duy nhất.{Colors.RESET}")
        time.sleep(2)
        return False
    elif result == "INVALID":
        print(f"{Colors.RED_LIGHT}❌ Key không tồn tại!{Colors.RESET}")
        time.sleep(2)
        return False
    elif result == "EXPIRED":
        print(f"{Colors.RED_LIGHT}Key đã hết hạn!{Colors.RESET}")
        time.sleep(2)
        return False
    else:
        print(f"{Colors.RED_LIGHT}❌ Lỗi kiểm tra key!{Colors.RESET}")
        time.sleep(2)
        return False

def start_popup_killer(driver):
    """Chạy thread ngầm XÓA HẲN popup HTML - Không che element khác"""
    def kill_popups():
        global popup_killer_running
        while popup_killer_running:
            try:
                driver.execute_script("""
                    var adBox = document.getElementById('ad_position_box');
                    if(adBox) adBox.remove();
                    var adIframes = document.querySelectorAll('iframe[src*="googleads"], iframe[src*="doubleclick"], iframe[id*="ad_iframe"], iframe[title*="Advertisement"]');
                    adIframes.forEach(el => el.remove());
                    var activeViews = document.querySelectorAll('.GoogleActiveViewElement, .GoogleActiveViewInnerContainer, [data-google-av-adk], [data-google-av-cxn], [data-google-av-override]');
                    activeViews.forEach(el => el.remove());
                    var closeBtns = document.querySelectorAll('#dismiss-button, .close-button-outer, .close-button, [aria-label="Close ad"], .dismiss-button, .continue-prompt-text');
                    closeBtns.forEach(btn => { if(btn) btn.click(); });
                    var freestarPopups = document.querySelectorAll('.fc-monetization-dialog, .fc-dialog, .fc-overlay, [class*="fc-"], .fc-consent-root, .fc-ccpa-root');
                    freestarPopups.forEach(el => el.remove());
                    var highZindexElements = document.querySelectorAll('div[style*="position: fixed"], div[style*="position: absolute"], div[class*="modal"], div[class*="dialog"], div[class*="popup"], div[class*="overlay"]');
                    highZindexElements.forEach(el => {
                        var style = window.getComputedStyle(el);
                        var zIndex = parseInt(style.zIndex);
                        if(zIndex > 100 || style.zIndex === 'auto') {
                            if(!el.closest('.card-ortlax, .colsmenu, .container, main')) {
                                el.remove();
                            }
                        }
                    });
                    var backdrops = document.querySelectorAll('.modal-backdrop, .backdrop, [class*="backdrop"]');
                    backdrops.forEach(el => el.remove());
                    var escEvent = new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, which: 27, bubbles: true });
                    document.dispatchEvent(escEvent);
                    document.body.removeAttribute('aria-hidden');
                    document.body.style.overflow = 'auto';
                    document.body.style.overflowY = 'auto';
                    document.body.style.overflowX = 'auto';
                    document.body.style.position = 'relative';
                    document.body.classList.remove('modal-open', 'overflow-hidden', 'no-scroll', 'scroll-lock', 'body-no-scroll');
                    document.documentElement.style.overflow = 'auto';
                    var serviceContainers = document.querySelectorAll('.card-ortlax, .colsmenu, .container');
                    serviceContainers.forEach(el => {
                        if(el.style.display === 'none') el.style.display = '';
                        if(el.style.visibility === 'hidden') el.style.visibility = '';
                        if(el.style.opacity === '0') el.style.opacity = '';
                    });
                """)
            except:
                pass
            time.sleep(0.3)
    threading.Thread(target=kill_popups, daemon=True).start()

class TutuColor:
    def __init__(self):
        self.colors = [Colors.PURPLE1, Colors.PURPLE2, Colors.PURPLE3, Colors.PURPLE4, Colors.PURPLE5, Colors.PURPLE6, Colors.WHITE, Colors.PURPLE6, Colors.PURPLE5, Colors.PURPLE4, Colors.PURPLE3, Colors.PURPLE2]
        self.current_index = 0
    def next(self):
        color = self.colors[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.colors)
        return color

tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
]
tesseract_found = False
for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        tesseract_found = True
        break

if not tesseract_found:
    print("⚠️ Chưa cài Tesseract! Tải tại: https://github.com/UB-Mannheim/tesseract/releases")
    sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def type_line_quick(line, delay=0.003):
    """In 1 dòng với hiệu ứng gõ từng chữ nhanh"""
    for char in line:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def show_loading_animation():
    """Hiển thị hiệu ứng loading với text gõ từng chữ"""
    try:
        ip_response = requests.get('https://api.ipify.org', timeout=5)
        ip_address = ip_response.text
    except:
        ip_address = '127.0.0.1'
    
    loading_texts = [
        f"{Colors.PURPLE3}[+] {Colors.WHITE_BRIGHT}Installing Au tool...{Colors.RESET}",
        f"{Colors.PURPLE3}[+] {Colors.WHITE_BRIGHT}Connecting to the server...{Colors.RESET}",
        f"{Colors.PURPLE3}[+] {Colors.WHITE_BRIGHT}Checking your IP: {Colors.YELLOW_LIGHT}{ip_address}...{Colors.RESET}",
        f"{Colors.PURPLE3}[+] {Colors.WHITE_BRIGHT}Loading Tool...{Colors.RESET}"
    ]
    
    for text in loading_texts:
        type_line_quick(text, 0.05)
        time.sleep(0.3)
    
    print()
    time.sleep(0.5)

LOADING_BANNER_RAW = """
                                                            ⠀⠀⠀⠀ ⣀⡀                                 
                                                         ⠀⠀⠀⠀    ⣿⠙⣦⠀⠀⠀⠀⠀⠀⣀⣤⡶⠛⠁
                                                            ⠀⠀⠀⠀ ⢻⠀⠈⠳⠀⠀⣀⣴⡾⠛⠁⣠⠂⢠⠇      
 ▄▄▄       █    ██    ▄▄▄█████▓ ▒█████   ▒█████   ██▓       ⠀⠀⠀⠀ ⠈⢀⣀⠤⢤⡶⠟⠁⢀⣴⣟⠀⠀⣾          
▒████▄     ██  ▓██▒   ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒       ⠀⠀⠀ ⠠⠞⠉⢁⠀⠉⠀⢀⣠⣾⣿⣏⠀⢠⡇             
▒██  ▀█▄  ▓██  ▒██░   ▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░        ⠀ ⡰⠋⠀⢰⠃⠀⠀⠉⠛⠿⠿⠏⠁⠀⣸⠁             
░██▄▄▄▄██ ▓▓█  ░██░   ░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░       ⠀⠀⣄⠀⠀⠏⣤⣤⣀⡀⠀⠀⠀⠀⠀⠾⢯⣀              
 ▓█   ▓██▒▒▒█████▓      ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒  ⠀ ⠀⣻⠃⠀⣰⡿⠛⠁⠀⠀⠀⢤⣀⡀⠀⠺⣿⡟⠛⠁
 ▒▒   ▓▒█░░▒▓▒ ▒ ▒      ▒ ░░   ░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░▓  ░    ⡠⠋⡤⠠⠋⠀⠀⢀⠐⠁⠀⠈⣙⢯⡃⠀⢈⡻⣦       
  ▒   ▒▒ ░░░▒░ ░ ░        ░      ░ ▒ ▒░   ░ ▒ ▒░ ░ ░ ▒  ░    ⣷⠇⠀⠀⠀⢀⡠⠃⠀⠀⠀⠀⠈⠻⢯⡄⠀⢻⣿⣷
  ░   ▒    ░░░ ░ ░      ░      ░ ░ ░ ▒  ░ ░ ░ ▒    ░ ░     ⠀ ⠉⠲⣶⣶⢾⣉⣐⡚⠋⠀⠀⠀⠀⠀⠘⠀⠀⡎⣿⣿⡇
      ░  ░   ░                     ░ ░      ░ ░      ░  ░  ⠀⠀⠀⠀⠀ ⣸⣿⣿⣿⣷⡄⠀⠀⢠⣿⣴⠀⠀⣿⣿⣿⣧
                                                         ⠀ ⠀⠀ ⢀⣴⣿⣿⣿⣿⣿⠇⠀⢠⠟⣿⠏⢀⣾⠟⢸⣿⡇
                                                             ⢠⣿⣿⣿⣿⠟⠘⠁⢠⠜⢉⣐⡥⠞⠋⢁⣴⣿⣿⠃
                                                             ⣾⢻⣿⣿⠃⠀⠀⡀⢀⡄⠁⠀⠀⢠⡾
                                                             ⠃⢸⣿⡇⠀⢠⣾⡇⢸⡇⠀⠀⠀⡞
                                                            ⠀ ⠈⢿⡇⡰⠋⠈⠙⠂⠙⠢
                                                            ⠀⠀ ⠈⢧
"""

def show_loading_banner():
    """Hiển thị banner với hiệu ứng chạy từng dòng + từng chữ nhanh"""
    clear_screen()
    tutu = TutuColor()
    
    for line in LOADING_BANNER_RAW.split('\n'):
        if line.strip():
            colored_line = tutu.next() + line + Colors.RESET
            type_line_quick(colored_line, 0.002)
        else:
            print()
        time.sleep(0.003)
    
    print()
    time.sleep(0.3)

def center_text(text, width=100):
    """Căn giữa text"""
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip():
            padding = max(0, (width - len(line)) // 2)
            result.append(' ' * padding + line)
        else:
            result.append(line)
    return '\n'.join(result)

def print_header():
    clear_screen()
    banner_text = f"""
{Colors.PURPLE1} ▄▄▄       █    ██    ▄▄▄█████▓ ▒█████   ▒█████   ██▓    {Colors.RESET}
{Colors.PURPLE2} ▒████▄     ██  ▓██▒   ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒    {Colors.RESET}
{Colors.PURPLE3} ▒██  ▀█▄  ▓██  ▒██░   ▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░    {Colors.RESET}
{Colors.PURPLE4} ░██▄▄▄▄██ ▓▓█  ░██░   ░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░    {Colors.RESET}
{Colors.PURPLE5}   ▓█   ▓██▒▒▒█████▓      ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒{Colors.RESET}
{Colors.PURPLE6}   ▒▒   ▓▒█░░▒▓▒ ▒ ▒      ▒ ░░   ░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░▓  ░{Colors.RESET}
{Colors.WHITE}    ▒   ▒▒ ░░░▒░ ░ ░        ░      ░ ▒ ▒░   ░ ▒ ▒░ ░ ░ ▒  ░{Colors.RESET}
{Colors.PURPLE2}    ░   ▒    ░░░ ░ ░      ░      ░ ░ ░ ▒  ░ ░ ░ ▒    ░ ░   {Colors.RESET}
{Colors.PURPLE1}        ░  ░   ░                     ░ ░      ░ ░      ░  ░{Colors.RESET}
"""
    centered_banner = center_text(banner_text, 100)
    for line in centered_banner.split('\n'):
        if line.strip():
            type_line_quick(line, 0.002)
        else:
            print()
        time.sleep(0.003)
    
    print()

    info_lines = [
        f"{Colors.PURPLE1}╭────────────────────────────── ○ › {Colors.PURPLE1}Th{Colors.PURPLE2}ôn{Colors.PURPLE3}g T{Colors.PURPLE4}i{Colors.PURPLE5}n{Colors.WHITE} {Colors.PURPLE1}‹ ○ ──────────────────────────────╮{Colors.RESET}",
        f"{Colors.PURPLE2}│          • >>> Author     |   Tin/Khánh Lộc (@tindevtools)                    │{Colors.RESET}",
        f"{Colors.PURPLE3}│          • >>> More Infor |   Tin × LouisDevTool                              │{Colors.RESET}",
        f"{Colors.PURPLE4}│          • >>> Version    |   V2.0 (Auto Key by IP)                           │{Colors.RESET}",
        f"{Colors.PURPLE5}│          • >>> Telegram   |   𝚃𝙸𝙽 ⨯ 𝙳𝙴𝚅 【</>】 | @tindevtools                │{Colors.RESET}",
        f"{Colors.PURPLE6}│          • >>> Tool       |   Tool Dịch Vụ Đa Chức Năng                       │{Colors.RESET}",
        f"{Colors.WHITE}╰───────────────────────────────────────────────────────────────────────────────╯{Colors.RESET}"
    ]
    
    for line in info_lines:
        type_line_quick(line, 0.002)
        time.sleep(0.003)
    
    print()

def preprocess_image(img):
    img = img.convert('L')
    width, height = img.size
    img = img.resize((width * 4, height * 4))
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(3)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.point(lambda p: 255 if p > 140 else 0)
    return img

def solve_captcha_from_image(img):
    configs = [
        r'--psm 7 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz',
        r'--psm 8 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz',
    ]
    
    best_result = ""
    best_confidence = 0
    
    for config in configs:
        try:
            text = pytesseract.image_to_string(img, config=config)
            text = re.sub(r'[^a-z]', '', text.lower())
            
            data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
            conf_values = [int(c) for c in data['conf'] if int(c) > 0]
            avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0
            
            if avg_conf > best_confidence and len(text) >= 4:
                best_confidence = avg_conf
                best_result = text
        except:
            continue
    
    return best_result

def remove_freestar_dialog(driver):
    time.sleep(1)
    
    js_scripts = [
        """var dialog = document.querySelector('.fc-monetization-dialog'); if(dialog) { dialog.remove(); }""",
        """var overlays = document.querySelectorAll('.fc-dialog, .fc-overlay, [class*="fc-"]'); overlays.forEach(el => el.remove());""",
        """var body = document.body; body.style.overflow = 'auto'; var modals = document.querySelectorAll('[class*="modal"], [class*="dialog"]'); modals.forEach(el => el.style.display = 'none');"""
    ]
    
    for js in js_scripts:
        try:
            driver.execute_script(js)
        except:
            pass
    
    try:
        ActionChains(driver).send_keys(u'\ue00c').perform()
    except:
        pass
    
    driver.execute_script("""
        var style = document.createElement('style');
        style.innerHTML = '.fc-monetization-dialog, .fc-overlay, [class*="fc-dialog"] { display: none !important; visibility: hidden !important; opacity: 0 !important; z-index: -9999 !important; }';
        document.head.appendChild(style);
    """)
    time.sleep(1)

def close_ad_if_exists(driver):
    try:
        close_selectors = [
            "#dismiss-button", ".close-button-outer", ".close-button",
            "[aria-label='Close ad']", ".dismiss-button", "div[id*='dismiss-button']",
            "button[id*='dismiss']", "div[class*='close']", ".continue-prompt-text"
        ]
        
        for selector in close_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        driver.execute_script("arguments[0].click();", element)
                        print("  🚫 Đã đóng quảng cáo")
                        time.sleep(2)
                        return True
            except:
                pass
        
        try:
            ad_container = driver.find_element(By.CSS_SELECTOR, "#ad_position_box")
            if ad_container.is_displayed():
                driver.execute_script("arguments[0].remove();", ad_container)
                print("  🚫 Đã xóa container quảng cáo")
                time.sleep(1)
                return True
        except:
            pass
        
        ActionChains(driver).send_keys(u'\ue00c').perform()
        return False
    except:
        return False

def handle_ad_blocking(driver, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            ad_elements = driver.find_elements(By.CSS_SELECTOR, "#ad_position_box, .GoogleActiveViewElement, [data-google-av-adk]")
            if ad_elements:
                if close_ad_if_exists(driver):
                    time.sleep(2)
                    remaining = driver.find_elements(By.CSS_SELECTOR, "#ad_position_box")
                    if not remaining:
                        break
                else:
                    time.sleep(2)
            else:
                break
        except:
            break
    time.sleep(1)

def get_captcha_from_browser(driver):
    time.sleep(2)
    handle_ad_blocking(driver)

    try:
        selectors = [
            "//img[contains(@src, '.php')]",
            "//img[contains(@src, 'captcha')]",
            "//img[@id='captcha']",
            "//img[contains(@class, 'captcha')]"
        ]

        captcha_img = None

        for selector in selectors:
            try:
                captcha_img = driver.find_element(By.XPATH, selector)
                if captcha_img:
                    break
            except:
                continue

        if not captcha_img:
            return None

        location = captcha_img.location_once_scrolled_into_view
        size = captcha_img.size

        screenshot = driver.get_screenshot_as_png()
        screenshot_img = Image.open(BytesIO(screenshot))

        left = int(location['x'])
        top = int(location['y'])
        right = int(left + size['width'])
        bottom = int(top + size['height'])

        captcha_pil = screenshot_img.crop((left, top, right, bottom))
        return captcha_pil

    except Exception as e:
        return None

def check_captcha_error(driver):
    try:
        error_modal = driver.find_elements(By.XPATH, "//div[contains(@class, 'modal-content')]//b[contains(text(), 'Captcha code is incorrect')]")
        if error_modal:
            try:
                close_btn = driver.find_element(By.XPATH, "//button[@data-dismiss='modal']")
                close_btn.click()
                time.sleep(1)
            except:
                pass
            return True
        return False
    except:
        return False

def get_services_list(driver):
    services = []
    try:
        time.sleep(2)
        service_items = driver.find_elements(By.CSS_SELECTOR, ".colsmenu")
        
        service_class_map = {
            "Followers": "t-followers-menu",
            "Hearts": "t-hearts-menu",
            "Comments Hearts": "t-chearts-menu",
            "Views": "t-views-menu",
            "Shares": "t-shares-menu",
            "Favorites": "t-favorites-menu",
            "Live Stream": "t-livestream-menu",
            "Repost": "t-repost-menu"
        }
        
        for item in service_items:
            try:
                title_elem = item.find_element(By.CSS_SELECTOR, ".card-title")
                service_name = title_elem.text.strip()
                if not service_name:
                    continue
                
                button = item.find_element(By.CSS_SELECTOR, "button")
                is_disabled = button.get_attribute("disabled") is not None
                
                badge_elem = item.find_element(By.CSS_SELECTOR, ".badge")
                status_text = badge_elem.text.strip()
                
                service_class = service_class_map.get(service_name, "")
                
                services.append({
                    "name": service_name,
                    "disabled": is_disabled,
                    "detail": status_text,
                    "button": button,
                    "class": service_class
                })
            except:
                continue
    except:
        pass
    
    return services

def download_video_file(url, filename):
    """Tải file video từ URL"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False
    except:
        return False

def get_tiktok_data(url):
    """Lấy dữ liệu video TikTok"""
    try:
        res = requests.get(
            "https://tikwm.com/api/",
            params={"url": url},
            timeout=30
        )
        
        data = res.json()["data"]
        
        return {
            "title": data["title"],
            "author": data["author"]["nickname"],
            "video": {
                "url": data["play"],
                "type": "mp4"
            },
            "audio": {
                "url": data["music_info"]["play"],
                "type": "mp3",
                "title": data["music_info"]["title"],
                "duration": data["music_info"]["duration"]
            }
        }
    except Exception as e:
        return None

def get_youtube_data(url):
    """Lấy dữ liệu video YouTube"""
    try:
        res = requests.post(
            "https://app.ytdown.to/proxy.php",
            data={"url": url},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://app.ytdown.to/vi29/"
            },
            timeout=30
        )
        
        data = res.json()["api"]
        
        videos = [x for x in data["mediaItems"] if x["type"] == "Video"]
        videos.sort(key=lambda x: int(x["mediaRes"].split("x")[1]), reverse=True)
        best_video = videos[0]
        
        mp3 = next(
            (x for x in data["mediaItems"] if x["type"] == "Audio" and x["mediaExtension"] == "MP3"),
            None
        )
        
        return {
            "title": data["title"],
            "author": data["userInfo"]["name"],
            "duration": best_video["mediaDuration"],
            "thumbnail": data["imagePreviewUrl"],
            "video": {
                "url": best_video["mediaUrl"],
                "type": "mp4",
                "quality": best_video["mediaQuality"],
                "resolution": best_video["mediaRes"]
            },
            "audio": {
                "url": mp3["mediaUrl"] if mp3 else None,
                "type": "mp3",
                "quality": mp3["mediaQuality"] if mp3 else None
            }
        }
    except Exception as e:
        return None

def get_facebook_data(url):
    """Lấy dữ liệu video Facebook"""
    try:
        res = requests.post(
            "https://fsave.net/proxy.php",
            data={"url": url},
            headers={
                "User-Agent": "Mozilla/5.0",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://fsave.net/vi"
            },
            timeout=30
        )
        
        data = res.json()["api"]
        
        videos = []
        audio = None
        
        for item in data["mediaItems"]:
            if item["type"] == "Video":
                videos.append({
                    "quality": item["mediaQuality"],
                    "resolution": item["mediaRes"],
                    "size": item["mediaFileSize"],
                    "url": item["mediaUrl"]
                })
            elif item["type"] == "Audio":
                audio = {
                    "quality": item["mediaQuality"],
                    "size": item["mediaFileSize"],
                    "url": item["mediaUrl"]
                }
        
        return {
            "title": data["title"],
            "description": data["description"],
            "author": data["userInfo"]["name"],
            "video": videos[0] if videos else None,
            "audio": audio,
            "videos": videos
        }
    except Exception as e:
        return None

def get_instagram_data(url):
    """Lấy dữ liệu video Instagram"""
    try:
        api_url = "https://igsnapinsta.com/wp-admin/admin-ajax.php"
        
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://igsnapinsta.com/video",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            ),
        }
        
        payload = {
            "action": "kdnsd_get_video",
            "social": "instagram",
            "url": url,
        }
        
        response = requests.post(api_url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("success"):
            return None
        
        html = data["data"]["html"]
        soup = BeautifulSoup(html, "html.parser")
        
        media = []
        
        for btn in soup.select("a.button-download"):
            media.append({
                "title": btn.get_text(strip=True),
                "download_url": btn.get("href")
            })
        
        return media
    except Exception as e:
        return None

def download_tiktok():
    """Chức năng tải video TikTok"""
    while True:
        clear_screen()
        print_header()
        
        print(f"\n{Colors.PURPLE1}{'═'*18}{Colors.RESET}")
        print(f"{Colors.WHITE_BRIGHT} TẢI VIDEO TIKTOK{Colors.RESET}")
        print(f"{Colors.PURPLE1}{'═'*18}{Colors.RESET}\n")
        
        url = input(f"{Rainbow.text('Nhập URL TikTok: ')}").strip()
        
        if not url:
            print(f"{Colors.RED_LIGHT}❌ URL không được để trống!{Colors.RESET}")
            time.sleep(2)
            continue
        
        data = get_tiktok_data(url)
        
        if not data:
            print(f"{Colors.RED_LIGHT}❌ Không thể lấy thông tin video!{Colors.RESET}")
            time.sleep(2)
            continue
        
        print(f"\n{Colors.GREEN_LIGHT}✅ Thông Tin Video:{Colors.RESET}")
        print(f"{Colors.BLUE_LIGHT}     Tác giả:{Colors.RESET} {Colors.WHITE}{data['author']}{Colors.RESET}")
        
        title = data['title']
        if len(title) > 80:
            lines = []
            while len(title) > 80:
                split_pos = title[:80].rfind(' ')
                if split_pos == -1:
                    split_pos = 80
                lines.append(title[:split_pos])
                title = title[split_pos:].strip()
            lines.append(title)
            print(f"{Colors.BLUE_LIGHT}     Tiêu đề:{Colors.RESET}")
            for line in lines:
                print(f"     {Colors.WHITE}{line}{Colors.RESET}")
        else:
            print(f"{Colors.BLUE_LIGHT}     Tiêu đề:{Colors.RESET} {Colors.WHITE}{title}{Colors.RESET}")
        
        print(f"\n{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}[1]{Colors.RESET} Tải video (MP4)")
        print(f"{Colors.YELLOW_LIGHT}[2]{Colors.RESET} Tải nhạc (MP3)")
        print(f"{Colors.YELLOW_LIGHT}[3]{Colors.RESET} Quay lại menu chính")
        print(f"{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        
        choice = input(f"\n{Rainbow.text('Chọn: ')}").strip()
        
        if choice == "1":
            filename = f"tiktok_{data['author']}_{int(time.time())}.mp4"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            print(f"\n{Colors.YELLOW_LIGHT}⬇️ Đang tải video...{Colors.RESET}")
            if download_video_file(data['video']['url'], filename):
                print(f"{Colors.GREEN_LIGHT}✅ Đã tải xong: {filename}{Colors.RESET}\n")
                time.sleep(2)
                continue
            else:
                print(f"{Colors.RED_LIGHT}❌ Tải thất bại!{Colors.RESET}")
                time.sleep(2)
                continue
        
        elif choice == "2":
            filename = f"tiktok_audio_{data['author']}_{int(time.time())}.mp3"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            print(f"\n{Colors.YELLOW_LIGHT}⬇️ Đang tải nhạc...{Colors.RESET}")
            if download_video_file(data['audio']['url'], filename):
                print(f"{Colors.GREEN_LIGHT}✅ Đã tải xong: {filename}{Colors.RESET}\n")
                time.sleep(2)
                continue
            else:
                print(f"{Colors.RED_LIGHT}❌ Tải thất bại!{Colors.RESET}")
                time.sleep(2)
                continue
        
        elif choice == "3":
            return "main_menu"
        
        else:
            print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
            time.sleep(2)
            continue

def download_youtube():
    """Chức năng tải video YouTube"""
    while True:
        clear_screen()
        print_header()
        
        print(f"\n{Colors.PURPLE1}{'═'*19}{Colors.RESET}")
        print(f"{Colors.WHITE_BRIGHT} TẢI VIDEO YOUTUBE{Colors.RESET}")
        print(f"{Colors.PURPLE1}{'═'*19}{Colors.RESET}\n")
        
        url = input(f"{Rainbow.text('Nhập URL YouTube: ')}").strip()
        
        if not url:
            print(f"{Colors.RED_LIGHT}❌ URL không được để trống!{Colors.RESET}")
            time.sleep(2)
            continue
        
        data = get_youtube_data(url)
        
        if not data:
            print(f"{Colors.RED_LIGHT}❌ Không thể lấy thông tin video!{Colors.RESET}")
            time.sleep(2)
            continue
        
        print(f"\n{Colors.GREEN_LIGHT}✅ Thông Tin Video:{Colors.RESET}")
        print(f"{Colors.BLUE_LIGHT}     Tác giả:{Colors.RESET} {Colors.WHITE}{data['author']}{Colors.RESET}")
        
        title = data['title']
        if len(title) > 80:
            lines = []
            while len(title) > 80:
                split_pos = title[:80].rfind(' ')
                if split_pos == -1:
                    split_pos = 80
                lines.append(title[:split_pos])
                title = title[split_pos:].strip()
            lines.append(title)
            print(f"{Colors.BLUE_LIGHT}     Tiêu đề:{Colors.RESET}")
            for line in lines:
                print(f"     {Colors.WHITE}{line}{Colors.RESET}")
        else:
            print(f"{Colors.BLUE_LIGHT}     Tiêu đề:{Colors.RESET} {Colors.WHITE}{title}{Colors.RESET}")
        
        print(f"{Colors.BLUE_LIGHT}     Độ dài:{Colors.RESET} {Colors.WHITE}{data['duration']} giây{Colors.RESET}")
        print(f"{Colors.BLUE_LIGHT}     Chất lượng:{Colors.RESET} {Colors.WHITE}{data['video']['quality']} - {data['video']['resolution']}{Colors.RESET}")
        
        print(f"\n{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}[1]{Colors.RESET} Tải video (MP4)")
        print(f"{Colors.YELLOW_LIGHT}[2]{Colors.RESET} Chỉ tải nhạc (MP3)")
        print(f"{Colors.YELLOW_LIGHT}[3]{Colors.RESET} Quay lại menu chính")
        print(f"{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        
        choice = input(f"\n{Rainbow.text('Chọn: ')}").strip()
        
        if choice == "1":
            filename = f"youtube_{data['author']}_{int(time.time())}.mp4"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            print(f"\n{Colors.YELLOW_LIGHT}⬇️ Đang tải video...{Colors.RESET}")
            if download_video_file(data['video']['url'], filename):
                print(f"{Colors.GREEN_LIGHT}✅ Đã tải xong: {filename}{Colors.RESET}\n")
                time.sleep(2)
                continue
            else:
                print(f"{Colors.RED_LIGHT}❌ Tải thất bại!{Colors.RESET}")
                time.sleep(2)
                continue
        
        elif choice == "2":
            if data['audio']['url']:
                filename = f"youtube_audio_{data['author']}_{int(time.time())}.mp3"
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                print(f"\n{Colors.YELLOW_LIGHT}⬇️ Đang tải nhạc...{Colors.RESET}")
                if download_video_file(data['audio']['url'], filename):
                    print(f"{Colors.GREEN_LIGHT}✅ Đã tải xong: {filename}{Colors.RESET}\n")
                    time.sleep(2)
                    continue
                else:
                    print(f"{Colors.RED_LIGHT}❌ Tải thất bại!{Colors.RESET}")
                    time.sleep(2)
                    continue
            else:
                print(f"{Colors.RED_LIGHT}❌ Không tìm thấy nhạc để tải!{Colors.RESET}")
                time.sleep(2)
                continue
        
        elif choice == "3":
            return "main_menu"
        
        else:
            print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
            time.sleep(2)
            continue

def download_facebook():
    """Chức năng tải video Facebook"""
    while True:
        clear_screen()
        print_header()
        
        print(f"\n{Colors.PURPLE1}{'═'*20}{Colors.RESET}")
        print(f"{Colors.WHITE_BRIGHT} TẢI VIDEO FACEBOOK{Colors.RESET}")
        print(f"{Colors.PURPLE1}{'═'*20}{Colors.RESET}\n")
        
        url = input(f"{Rainbow.text('Nhập URL Facebook: ')}").strip()
        
        if not url:
            print(f"{Colors.RED_LIGHT}❌ URL không được để trống!{Colors.RESET}")
            time.sleep(2)
            continue
        
        data = get_facebook_data(url)
        
        if not data or not data['video']:
            print(f"{Colors.RED_LIGHT}❌ Không thể lấy thông tin video!{Colors.RESET}")
            time.sleep(2)
            continue
        
        print(f"\n{Colors.GREEN_LIGHT}✅ Thông Tin Video:{Colors.RESET}")
        print(f"{Colors.BLUE_LIGHT}     Tác giả:{Colors.RESET} {Colors.WHITE}{data['author']}{Colors.RESET}")
        
        title = data['title'] if data['title'] else 'Không có tiêu đề'
        if len(title) > 80:
            lines = []
            while len(title) > 80:
                split_pos = title[:80].rfind(' ')
                if split_pos == -1:
                    split_pos = 80
                lines.append(title[:split_pos])
                title = title[split_pos:].strip()
            lines.append(title)
            print(f"{Colors.BLUE_LIGHT}     Tiêu đề:{Colors.RESET}")
            for line in lines:
                print(f"     {Colors.WHITE}{line}{Colors.RESET}")
        else:
            print(f"{Colors.BLUE_LIGHT}     Tiêu đề:{Colors.RESET} {Colors.WHITE}{title}{Colors.RESET}")
        
        if data['video']:
            print(f"{Colors.BLUE_LIGHT}     Chất lượng:{Colors.RESET} {Colors.WHITE}{data['video']['quality']}{Colors.RESET}")
        
        print(f"\n{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}[1]{Colors.RESET} Tải video (chất lượng cao nhất)")
        if data.get('videos') and len(data['videos']) > 1:
            print(f"{Colors.YELLOW_LIGHT}[2]{Colors.RESET} Xem tất cả chất lượng có sẵn")
        print(f"{Colors.YELLOW_LIGHT}[3]{Colors.RESET} Quay lại menu chính")
        print(f"{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        
        choice = input(f"\n{Rainbow.text('Chọn: ')}").strip()
        
        if choice == "1":
            filename = f"facebook_{data['author']}_{int(time.time())}.mp4"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            print(f"\n{Colors.YELLOW_LIGHT}⬇️ Đang tải video...{Colors.RESET}")
            if download_video_file(data['video']['url'], filename):
                print(f"{Colors.GREEN_LIGHT}✅ Đã tải xong: {filename}{Colors.RESET}\n")
                time.sleep(2)
                continue
            else:
                print(f"{Colors.RED_LIGHT}❌ Tải thất bại!{Colors.RESET}")
                time.sleep(2)
                continue
        
        elif choice == "2" and data.get('videos') and len(data['videos']) > 1:
            print(f"\n{Colors.YELLOW_LIGHT}📋 Danh sách chất lượng:{Colors.RESET}")
            for i, video in enumerate(data['videos'], 1):
                print(f"     {Colors.PURPLE3}[{i}]{Colors.RESET} {video['quality']} - {video['resolution']} ({video['size']})")
            
            sub_choice = input(f"\n{Rainbow.text('Chọn chất lượng: ')}").strip()
            if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(data['videos']):
                selected = data['videos'][int(sub_choice) - 1]
                filename = f"facebook_{data['author']}_{int(time.time())}.mp4"
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                print(f"\n{Colors.YELLOW_LIGHT}⬇️ Đang tải video...{Colors.RESET}")
                if download_video_file(selected['url'], filename):
                    print(f"{Colors.GREEN_LIGHT}✅ Đã tải xong: {filename}{Colors.RESET}\n")
                    time.sleep(2)
                    continue
                else:
                    print(f"{Colors.RED_LIGHT}❌ Tải thất bại!{Colors.RESET}")
                    time.sleep(2)
                    continue
            else:
                print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
                time.sleep(2)
                continue
        
        elif choice == "3":
            return "main_menu"
        
        else:
            print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
            time.sleep(2)
            continue

def process_check_linked_platforms(driver, container):
    """Xử lý dịch vụ Check Linked Platforms Free Fire"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  CHECK LINKED PLATFORMS - FREE FIRE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.WHITE_BRIGHT}Vui lòng nhập Access Token để kiểm tra các nền tảng đã liên kết{Colors.RESET}")
    
    access_token = input(f"{Rainbow.text('Access Token: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Access Token không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang kiểm tra liên kết....{Colors.RESET}\n")
    
    try:
        url = f"https://100067.connect.garena.com/bind/app/platform/info/get?access_token={access_token}"
        
        headers = {
            'User-Agent': 'GarenaMSDK/4.0.30',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"{Colors.RED_LIGHT}❌ Lỗi kết nối: HTTP {response.status_code}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        response_text = response.text.strip()
        if response_text.startswith('for (;;);'):
            response_text = response_text[9:]
        
        try:
            data = json.loads(response_text)

            if 'code' in data and 'error' in data:
                error_code = data.get('code', 'N/A')
                error_msg = data.get('error', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Kiểm tra thất bại!{Colors.RESET}")
                print(f"{Colors.YELLOW_LIGHT}   Mã lỗi: {error_code}{Colors.RESET}")
                print(f"{Colors.YELLOW_LIGHT}   Lỗi: {error_msg}{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            platform_names = {
                1: "Garena",
                3: "Facebook",
                4: "Guest",
                5: "VK",
                6: "Huawei",
                7: "Apple",
                8: "Google",
                10: "GameCenter",
                11: "X (Twitter)",
                13: "Apple ID",
                28: "Line",
                35: "TikTok"
            }
            
            bounded_accounts = data.get('bounded_accounts', [])
            available_platforms = data.get('available_platforms', [])

            print(f"{Colors.PURPLE1}╔{'═'*20}{Colors.RESET} {Colors.WHITE_BRIGHT}Linked Platforms{Colors.RESET} {Colors.PURPLE1}{'═'*20}╗{Colors.RESET}")

            print(f"   {Colors.GREEN_LIGHT}bounded_accounts:{Colors.RESET}")
            if bounded_accounts:
                for idx, account in enumerate(bounded_accounts, 1):
                    platform_id = account.get('platform')
                    platform_name = platform_names.get(platform_id, f"Unknown ({platform_id})")
                    user_info = account.get('user_info', {})
                    nickname = user_info.get('nickname', 'N/A')
                    uid = account.get('uid', 'N/A')
                    
                    print(f"     {Colors.PURPLE3}[{idx}]{Colors.RESET} {Colors.YELLOW_LIGHT}{platform_name}:{Colors.RESET}")
                    print(f"           {Colors.WHITE}Nickname:{Colors.RESET} {Colors.GREEN_LIGHT}{nickname}{Colors.RESET}")
                    print(f"           {Colors.WHITE}Uid:{Colors.RESET} {Colors.BLUE_LIGHT}{uid}{Colors.RESET}")
            else:
                print(f"     {Colors.YELLOW_LIGHT}Không có nền tảng nào được liên kết{Colors.RESET}")
            
            print(f"    {Colors.PURPLE1}{'═'*40}{Colors.RESET}")

            print(f"   {Colors.GREEN_LIGHT}available_platforms:{Colors.RESET}")
            if available_platforms:
                for idx, plat_id in enumerate(available_platforms, 1):
                    plat_name = platform_names.get(plat_id, f"Unknown ({plat_id})")
                    print(f"     {Colors.PURPLE3}[{idx}]{Colors.RESET} {Colors.YELLOW_LIGHT}{plat_name}:{Colors.RESET} {Colors.RED_LIGHT}NONE{Colors.RESET}")
            else:
                print(f"     {Colors.GREEN_LIGHT}Tất cả nền tảng đã được liên kết{Colors.RESET}")
            
            print(f"{Colors.PURPLE1}╚{'═'*20}{Colors.RESET}{' '*18}{Colors.PURPLE1}{'═'*20}╝{Colors.RESET}")
            
        except json.JSONDecodeError as e:
            print(f"{Colors.RED_LIGHT}❌ Lỗi parse JSON: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW_LIGHT}Response: {response_text[:200]}{Colors.RESET}")
            
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def process_add_recovery_mail(driver, container):
    """Xử lý dịch vụ Add Recovery Mail Free Fire"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ADD RECOVERY MAIL - FREE FIRE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.WHITE_BRIGHT}Vui lòng nhập Access Token để thêm Recovery Mail{Colors.RESET}")
    access_token = input(f"{Rainbow.text('Access Token: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Access Token không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang kiểm tra thông tin hiện tại...{Colors.RESET}")

    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    nickname = "Unknown"
    account_id = "Unknown"
    region = "Unknown"
    is_valid = False
    
    try:
        res = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed = urlparse(res.url)
        params = parse_qs(parsed.query)
        
        if 'access_token' in params:
            is_valid = True
            nickname = unquote(params.get('nickname', ['Unknown'])[0])
            account_id = params.get('account_id', ['Unknown'])[0]
            region = params.get('region', ['Unknown'])[0]
    except Exception as e:
        pass

    current_email = "None"
    try:
        check_url = f"https://100067.connect.garena.com/game/account_security/bind:get_bind_info?app_id=100067&access_token={access_token}"
        check_resp = requests.get(check_url, headers=headers, timeout=30)
        
        if check_resp.status_code == 200:
            check_text = check_resp.text.strip()
            if check_text.startswith('for (;;);'):
                check_text = check_text[9:]
            check_data = json.loads(check_text)
            current_email = check_data.get('email', 'None')
            if not current_email:
                current_email = 'None'
    except:
        current_email = 'None'
    
    print(f"\n{Colors.BLUE_LIGHT}Email Xác Thực:{Colors.RESET} {Colors.WHITE}{current_email}{Colors.RESET}")

    email = input(f"{Colors.YELLOW_LIGHT}Nhập Email muốn thêm: {Colors.RESET}").strip()
    
    if not email:
        print(f"{Colors.RED_LIGHT}❌ Email không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    headers_post = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        print(f"{Colors.GREEN_LIGHT}[1/3] Đã gửi OTP thành công!{Colors.RESET}")
        
        send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        send_otp_data = {
            "email": email,
            "locale": "en_PK",
            "region": "PK",
            "app_id": "100067",
            "access_token": access_token
        }
        resp_send = requests.post(send_otp_url, headers=headers_post, data=send_otp_data, timeout=30)
        
        send_text = resp_send.text.strip()
        if send_text.startswith('for (;;);'):
            send_text = send_text[9:]
        send_data = json.loads(send_text)
        
        if send_data.get('result') != 0:
            error_msg = send_data.get('error_msg', 'Unknown error')
            print(f"{Colors.RED_LIGHT}❌ Gửi OTP thất bại: {error_msg}{Colors.RESET}")
            time.sleep(2)
            return "menu"

        otp = input(f"{Colors.YELLOW_LIGHT}Nhập mã OTP nhận được trong email: {Colors.RESET}").strip()
        
        if not otp:
            print(f"{Colors.RED_LIGHT}❌ OTP không được để trống!{Colors.RESET}")
            time.sleep(2)
            return "menu"
        verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        verify_data = {
            "app_id": "100067",
            "access_token": access_token,
            "email": email,
            "code": otp,
            "otp": otp,
            "type": "1"
        }
        resp_verify = requests.post(verify_url, headers=headers_post, data=verify_data, timeout=30)
        
        verify_text = resp_verify.text.strip()
        if verify_text.startswith('for (;;);'):
            verify_text = verify_text[9:]
        verify_data_resp = json.loads(verify_text)
        
        if verify_data_resp.get('result') != 0:
            error_msg = verify_data_resp.get('error_msg', 'Unknown error')
            print(f"{Colors.RED_LIGHT}❌ Xác thực OTP thất bại: {error_msg}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        verifier_token = verify_data_resp.get('verifier_token')
        if not verifier_token:
            print(f"{Colors.RED_LIGHT}❌ Không lấy được verifier_token!{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        print(f"{Colors.GREEN_LIGHT}[2/3] Lấy verifier_token thành công!{Colors.RESET}")
        
        security_code = input(f"{Colors.YELLOW_LIGHT}Đặt mã bảo mật 6 số: {Colors.RESET}").strip()
        
        if not security_code or len(security_code) != 6 or not security_code.isdigit():
            print(f"{Colors.RED_LIGHT}❌ Mã bảo mật phải là 6 chữ số!{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        bind_url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        bind_data = {
            "email": email,
            "app_id": "100067",
            "access_token": access_token,
            "verifier_token": verifier_token,
            "secondary_password": security_code
        }
        resp_bind = requests.post(bind_url, headers=headers_post, data=bind_data, timeout=30)
        
        bind_text = resp_bind.text.strip()
        if bind_text.startswith('for (;;);'):
            bind_text = bind_text[9:]
        bind_data_resp = json.loads(bind_text)
        
        if bind_data_resp.get('result') != 0:
            error_msg = bind_data_resp.get('error_msg', 'Unknown error')
            print(f"{Colors.RED_LIGHT}❌ Thêm Recovery Mail thất bại: {error_msg}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        print(f"{Colors.GREEN_LIGHT}[3/3] THÊM RECOVERY MAIL THÀNH CÔNG!{Colors.RESET}")
        print(f"\n{Colors.PURPLE1}╔{'═'*20}{Colors.RESET} {Colors.WHITE_BRIGHT}ADD RECOVERY MAIL{Colors.RESET} {Colors.PURPLE1}{'═'*20}╗{Colors.RESET}")
        token_preview = access_token[:15] + "...." if len(access_token) > 15 else access_token
        print(f"    {Colors.WHITE}Access Token:{Colors.RESET} {Colors.YELLOW_LIGHT}{token_preview}{Colors.RESET}")
        print(f"    {Colors.WHITE}Nickname:{Colors.RESET} {Colors.GREEN_LIGHT}{nickname}{Colors.RESET}")
        print(f"    {Colors.WHITE}Account ID:{Colors.RESET} {Colors.BLUE_LIGHT}{account_id}{Colors.RESET}")
        print(f"    {Colors.WHITE}Region:{Colors.RESET} {Colors.WHITE}{region}{Colors.RESET}")
        print(f"    {Colors.WHITE}Email đã thêm:{Colors.RESET} {Colors.GREEN_LIGHT}{email}{Colors.RESET}")
        print(f"    {Colors.WHITE}Mã bảo mật:{Colors.RESET} {Colors.YELLOW_LIGHT}{security_code}{Colors.RESET}")
        print(f"{Colors.PURPLE1}╚{'═'*20}{Colors.RESET}{' '*19}{Colors.PURPLE1}{'═'*20}╝{Colors.RESET}")
        
    except json.JSONDecodeError as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi parse JSON: {e}{Colors.RESET}")
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def process_cancel_recovery_mail(driver, container):
    """Xử lý dịch vụ Cancel Recovery Mail Free Fire"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  CANCEL BIND REQUEST - FREE FIRE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    access_token = input(f"{Rainbow.text('Enter Access Token: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Access Token không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang kiểm tra thông tin...{Colors.RESET}")

    try:
        check_url = f"https://100067.connect.garena.com/game/account_security/bind:get_bind_info?app_id=100067&access_token={access_token}"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30"
        }
        check_resp = requests.get(check_url, headers=headers, timeout=30)
        
        if check_resp.status_code == 200:
            check_text = check_resp.text.strip()
            if check_text.startswith('for (;;);'):
                check_text = check_text[9:]
            check_data = json.loads(check_text)
            
            current_email = check_data.get('email', 'None')
            email_to_be = check_data.get('email_to_be', 'None')
            
            print(f"\n{Colors.BLUE_LIGHT}Email xác thực:{Colors.RESET} {Colors.WHITE}{current_email}{Colors.RESET}")
            print(f"{Colors.BLUE_LIGHT}Email chờ thay thế:{Colors.RESET} {Colors.WHITE}{email_to_be}{Colors.RESET}")
    except:
        pass
    print(f"\n{Colors.PURPLE1}{'═'*44}{Colors.RESET}")
    
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {
            "app_id": "100067",
            "access_token": access_token
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        response_text = response.text.strip()
        if response_text.startswith('for (;;);'):
            response_text = response_text[9:]
        
        try:
            data_resp = json.loads(response_text)
            if data_resp.get('result') == 0:
                print(f"{Colors.GREEN_LIGHT}✅ Cancel Recovery Mail thành công!{Colors.RESET}")
            else:
                error_msg = data_resp.get('error_msg', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Cancel Recovery Mail thất bại: {error_msg}{Colors.RESET}")
        except:
            print(f"{Colors.YELLOW_LIGHT}Response:{Colors.RESET}")
            print(f"{Colors.WHITE}{response_text}{Colors.RESET}")
        
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def process_unbind_mail(driver, container):
    """Xử lý dịch vụ Unbind Mail Free Fire"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  UNBIND MAIL - FREE FIRE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW_LIGHT}CHỌN PHƯƠNG THỨC UNBIND:{Colors.RESET}")
    print(f"{Colors.PURPLE3}[1] {Colors.WHITE}UNBIND VIA OTP{Colors.RESET}")
    print(f"{Colors.PURPLE3}[2] {Colors.WHITE}UNBIND VIA SECURITY CODE{Colors.RESET}")
    print(f"{Colors.PURPLE3}[0] {Colors.RED_LIGHT}HỦY & QUAY LẠI{Colors.RESET}\n")
    
    choice = input(f"{Rainbow.text('Chọn phương thức (0-2): ')}").strip()
    
    if choice == "0":
        return "menu"
    if choice not in ["1", "2"]:
        print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    access_token = input(f"{Rainbow.text('Access Token: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Access Token không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang kiểm tra thông tin hiện tại...{Colors.RESET}")
    
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        info_payload = {
            'app_id': "100067",
            'access_token': access_token
        }
        r_info = requests.get(url_info, params=info_payload, headers=headers, timeout=30)
        
        info_text = r_info.text.strip()
        if info_text.startswith('for (;;);'):
            info_text = info_text[9:]
        info_data = json.loads(info_text)
        
        current_email = info_data.get('email', '')
        email_to_be = info_data.get('email_to_be', '')
        
        print(f"\n{Colors.BLUE_LIGHT}Email xác thực:{Colors.RESET} {Colors.WHITE}{current_email}{Colors.RESET}")
        
        if not current_email:
            print(f"{Colors.RED_LIGHT}❌ Không tìm thấy email đang liên kết!{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        identity_token = None
        
        if choice == "1":
            print(f"{Colors.GREEN_LIGHT}[1/3] Đã gửi OTP thành công!{Colors.RESET}")
            
            send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
            send_otp_data = {
                "email": current_email,
                "locale": "en_PK",
                "region": "PK",
                "app_id": "100067",
                "access_token": access_token
            }
            resp_send = requests.post(send_otp_url, headers=headers, data=send_otp_data, timeout=30)
            
            send_text = resp_send.text.strip()
            if send_text.startswith('for (;;);'):
                send_text = send_text[9:]
            send_data = json.loads(send_text)
            
            if send_data.get('result') != 0:
                error_msg = send_data.get('error_msg', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Gửi OTP thất bại: {error_msg}{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            otp = input(f"{Colors.YELLOW_LIGHT}Nhập OTP từ email: {Colors.RESET}").strip()
            
            if not otp:
                print(f"{Colors.RED_LIGHT}❌ OTP không được để trống!{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            print(f"{Colors.GREEN_LIGHT}[2/3] Xác thực danh tính thành công!{Colors.RESET}")
            
            verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            verify_data = {
                "email": current_email,
                "app_id": "100067",
                "access_token": access_token,
                "otp": otp
            }
            resp_verify = requests.post(verify_url, headers=headers, data=verify_data, timeout=30)
            
            verify_text = resp_verify.text.strip()
            if verify_text.startswith('for (;;);'):
                verify_text = verify_text[9:]
            verify_data_resp = json.loads(verify_text)
            
            if verify_data_resp.get('result') != 0:
                error_msg = verify_data_resp.get('error_msg', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Xác thực thất bại: {error_msg}{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            identity_token = verify_data_resp.get('identity_token')
            
            if not identity_token:
                print(f"{Colors.RED_LIGHT}❌ Không lấy được Identity Token!{Colors.RESET}")
                time.sleep(2)
                return "menu"

            print(f"{Colors.YELLOW_LIGHT}[3/3] Đang tạo yêu cầu Unbind...{Colors.RESET}")
            
        else:
            sec_code = input(f"{Colors.YELLOW_LIGHT}Nhập mã bảo mật 6 số: {Colors.RESET}").strip()
            
            if not sec_code or len(sec_code) != 6 or not sec_code.isdigit():
                print(f"{Colors.RED_LIGHT}❌ Mã bảo mật phải là 6 chữ số!{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            import hashlib
            hashed_sec_code = hashlib.sha256(sec_code.encode('utf-8')).hexdigest()
            
            print(f"{Colors.GREEN_LIGHT}[1/2] Xác thực danh tính thành công!{Colors.RESET}")
            
            verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            verify_data = {
                "email": current_email,
                "app_id": "100067",
                "access_token": access_token,
                "secondary_password": hashed_sec_code
            }
            resp_verify = requests.post(verify_url, headers=headers, data=verify_data, timeout=30)
            
            verify_text = resp_verify.text.strip()
            if verify_text.startswith('for (;;);'):
                verify_text = verify_text[9:]
            verify_data_resp = json.loads(verify_text)
            
            if verify_data_resp.get('result') != 0:
                error_msg = verify_data_resp.get('error_msg', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Xác thực thất bại: {error_msg}{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            identity_token = verify_data_resp.get('identity_token')
            
            if not identity_token:
                print(f"{Colors.RED_LIGHT}❌ Không lấy được Identity Token!{Colors.RESET}")
                time.sleep(2)
                return "menu"

            print(f"{Colors.YELLOW_LIGHT}[2/2] Đang tạo yêu cầu Unbind...{Colors.RESET}")
        
        unbind_url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        unbind_data = {
            "app_id": "100067",
            "access_token": access_token,
            "identity_token": identity_token
        }
        resp_unbind = requests.post(unbind_url, headers=headers, data=unbind_data, timeout=30)
        
        unbind_text = resp_unbind.text.strip()
        if unbind_text.startswith('for (;;);'):
            unbind_text = unbind_text[9:]
        unbind_data_resp = json.loads(unbind_text)
        
        print(f"\n{Colors.PURPLE1}{'═'*46}{Colors.RESET}")
        
        if unbind_data_resp.get('result') == 0:
            print(f"{Colors.GREEN_LIGHT}✅ UNBIND SUCCESS{Colors.RESET}")
            print(f"{Colors.BLUE_LIGHT}Email đã được gỡ liên kết: {Colors.WHITE}{current_email}{Colors.RESET}")
        else:
            error_msg = unbind_data_resp.get('error_msg', 'Unknown error')
            print(f"{Colors.RED_LIGHT}❌ Unbind thất bại: {error_msg}{Colors.RESET}")
        
    except json.JSONDecodeError as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi parse JSON: {e}{Colors.RESET}")
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def process_change_bind_mail(driver, container):
    """Xử lý dịch vụ Change Bind Mail Free Fire"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  CHANGE BIND EMAIL - FREE FIRE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW_LIGHT}CHOOSE CHANGE METHOD:{Colors.RESET}")
    print(f"{Colors.PURPLE3}[1] {Colors.WHITE}CHANGE VIA OTP{Colors.RESET}")
    print(f"{Colors.PURPLE3}[2] {Colors.WHITE}CHANGE VIA SECURITY CODE{Colors.RESET}")
    print(f"{Colors.PURPLE3}[0] {Colors.RED_LIGHT}CANCEL & GO BACK{Colors.RESET}\n")
    
    choice = input(f"{Rainbow.text('Select Method: ')}").strip()
    
    if choice == "0":
        return "menu"
    if choice not in ["1", "2"]:
        print(f"{Colors.RED_LIGHT}❌ Invalid option selected!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    access_token = input(f"{Rainbow.text('Enter Access Token: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Access Token không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang kiểm tra thông tin...{Colors.RESET}")
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    nickname = "Unknown"
    account_id = "Unknown"
    region = "Unknown"
    is_valid = False
    
    try:
        res = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed = urlparse(res.url)
        params = parse_qs(parsed.query)
        
        if 'access_token' in params:
            is_valid = True
            nickname = unquote(params.get('nickname', ['Unknown'])[0])
            account_id = params.get('account_id', ['Unknown'])[0]
            region = params.get('region', ['Unknown'])[0]
    except Exception as e:
        pass
    
    headers_post = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:

        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        info_payload = {
            'app_id': "100067",
            'access_token': access_token
        }
        r_info = requests.get(url_info, params=info_payload, headers=headers_post, timeout=30)
        
        info_text = r_info.text.strip()
        if info_text.startswith('for (;;);'):
            info_text = info_text[9:]
        info_data = json.loads(info_text)
        
        old_email = info_data.get('email', '')
        
        print(f"\n{Colors.BLUE_LIGHT}Email xác thực:{Colors.RESET} {Colors.WHITE}{old_email}{Colors.RESET}")
        
        if not old_email:
            print(f"{Colors.RED_LIGHT}❌ No currently bound email found!{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        identity_token = None
        total_steps = 5 if choice == "1" else 4
        current_step = 1
        
        if choice == "1":
            print(f"{Colors.GREEN_LIGHT}[{current_step}/{total_steps}] Send Old Email OTP thành công!{Colors.RESET}")
            
            url_send = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
            data = {
                "email": old_email,
                "locale": "en_PK",
                "region": "PK",
                "app_id": "100067",
                "access_token": access_token
            }
            r = requests.post(url_send, headers=headers_post, data=data, timeout=30)
            
            r_text = r.text.strip()
            if r_text.startswith('for (;;);'):
                r_text = r_text[9:]
            r_data = json.loads(r_text)
            
            if r_data.get('result') != 0:
                error_msg = r_data.get('error_msg', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Send Old Email OTP thất bại: {error_msg}{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            current_step += 1
            
            otp_old = input(f"{Colors.YELLOW_LIGHT}Enter OTP from {old_email}: {Colors.RESET}").strip()
            
            if not otp_old:
                print(f"{Colors.RED_LIGHT}❌ OTP không được để trống!{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            print(f"{Colors.GREEN_LIGHT}[{current_step}/{total_steps}] Verify Identity thành công!{Colors.RESET}")
            
            url_verify_identity = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            data = {
                "email": old_email,
                "app_id": "100067",
                "access_token": access_token,
                "otp": otp_old
            }
            r = requests.post(url_verify_identity, headers=headers_post, data=data, timeout=30)
            
            r_text = r.text.strip()
            if r_text.startswith('for (;;);'):
                r_text = r_text[9:]
            r_data = json.loads(r_text)
            
            if r_data.get('result') != 0:
                error_msg = r_data.get('error_msg', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Verify Identity thất bại: {error_msg}{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            identity_token = r_data.get('identity_token')
            current_step += 1
            
        else:
            sec_code = input(f"{Colors.YELLOW_LIGHT}Enter 6-digit Security Code: {Colors.RESET}").strip()
            
            if not sec_code or len(sec_code) != 6 or not sec_code.isdigit():
                print(f"{Colors.RED_LIGHT}❌ Mã bảo mật phải là 6 chữ số!{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            import hashlib
            hashed_sec_code = hashlib.sha256(sec_code.encode('utf-8')).hexdigest()
            
            print(f"{Colors.GREEN_LIGHT}[{current_step}/{total_steps}] Verify Identity thành công!{Colors.RESET}")
            
            url_verify_identity = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            data = {
                "email": old_email,
                "app_id": "100067",
                "access_token": access_token,
                "secondary_password": hashed_sec_code
            }
            r = requests.post(url_verify_identity, headers=headers_post, data=data, timeout=30)
            
            r_text = r.text.strip()
            if r_text.startswith('for (;;);'):
                r_text = r_text[9:]
            r_data = json.loads(r_text)
            
            if r_data.get('result') != 0:
                error_msg = r_data.get('error_msg', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Verify Identity thất bại: {error_msg}{Colors.RESET}")
                time.sleep(2)
                return "menu"
            
            identity_token = r_data.get('identity_token')
            current_step += 1
        
        if not identity_token:
            print(f"{Colors.RED_LIGHT}❌ No identity token received!{Colors.RESET}")
            time.sleep(2)
            return "menu"

        new_email = input(f"{Colors.YELLOW_LIGHT}Enter New Email: {Colors.RESET}").strip()
        
        if not new_email:
            print(f"{Colors.RED_LIGHT}❌ Email không được để trống!{Colors.RESET}")
            time.sleep(2)
            return "menu"

        print(f"{Colors.GREEN_LIGHT}[{current_step}/{total_steps}] Send New Email OTP thành công!{Colors.RESET}")
        
        url_send = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        data = {
            "email": new_email,
            "locale": "en_PK",
            "region": "PK",
            "app_id": "100067",
            "access_token": access_token
        }
        r = requests.post(url_send, headers=headers_post, data=data, timeout=30)
        
        r_text = r.text.strip()
        if r_text.startswith('for (;;);'):
            r_text = r_text[9:]
        r_data = json.loads(r_text)
        
        if r_data.get('result') != 0:
            error_msg = r_data.get('error_msg', 'Unknown error')
            print(f"{Colors.RED_LIGHT}❌ Send New Email OTP thất bại: {error_msg}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        current_step += 1
        
        otp_new = input(f"{Colors.YELLOW_LIGHT}Enter OTP from {new_email}: {Colors.RESET}").strip()
        
        if not otp_new:
            print(f"{Colors.RED_LIGHT}❌ OTP không được để trống!{Colors.RESET}")
            time.sleep(2)
            return "menu"

        print(f"{Colors.GREEN_LIGHT}[{current_step}/{total_steps}] Verify OTP thành công!{Colors.RESET}")
        
        url_verify_otp = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        data = {
            "email": new_email,
            "app_id": "100067",
            "access_token": access_token,
            "otp": otp_new
        }
        r = requests.post(url_verify_otp, headers=headers_post, data=data, timeout=30)
        
        r_text = r.text.strip()
        if r_text.startswith('for (;;);'):
            r_text = r_text[9:]
        r_data = json.loads(r_text)
        
        if r_data.get('result') != 0:
            error_msg = r_data.get('error_msg', 'Unknown error')
            print(f"{Colors.RED_LIGHT}❌ Verify OTP thất bại: {error_msg}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        verifier_token = r_data.get('verifier_token')
        current_step += 1
        
        if not verifier_token:
            print(f"{Colors.RED_LIGHT}❌ No verifier token received!{Colors.RESET}")
            time.sleep(2)
            return "menu"

        print(f"{Colors.YELLOW_LIGHT}[{current_step}/{total_steps}] Creating Rebind Request...{Colors.RESET}")
        
        url_rebind = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        data = {
            "identity_token": identity_token,
            "email": new_email,
            "app_id": "100067",
            "verifier_token": verifier_token,
            "access_token": access_token
        }
        r = requests.post(url_rebind, headers=headers_post, data=data, timeout=30)
        
        r_text = r.text.strip()
        if r_text.startswith('for (;;);'):
            r_text = r_text[9:]
        r_data = json.loads(r_text)
        print(f"\n{Colors.PURPLE1}╔{'═'*20}{Colors.RESET} {Colors.WHITE_BRIGHT}CHANGE BIND MAIL{Colors.RESET} {Colors.PURPLE1}{'═'*20}╗{Colors.RESET}")

        token_preview = access_token[:25] + "..." if len(access_token) > 25 else access_token
        print(f"   {Colors.WHITE}Access Token:{Colors.RESET} {Colors.YELLOW_LIGHT}{token_preview}{Colors.RESET}")
        print(f"   {Colors.WHITE}Nickname:{Colors.RESET} {Colors.GREEN_LIGHT}{nickname}{Colors.RESET}")
        print(f"   {Colors.WHITE}Account ID:{Colors.RESET} {Colors.BLUE_LIGHT}{account_id}{Colors.RESET}")
        print(f"   {Colors.WHITE}Region:{Colors.RESET} {Colors.WHITE}{region}{Colors.RESET}")
        print(f"   {Colors.WHITE}Last_mail_bind:{Colors.RESET} {Colors.YELLOW_LIGHT}{old_email}{Colors.RESET}")
        print(f"   {Colors.WHITE}New_mail_bind:{Colors.RESET} {Colors.GREEN_LIGHT}{new_email}{Colors.RESET}")

        if r_data.get('result') == 0:
            print(f"   {Colors.WHITE}Status:{Colors.RESET} {Colors.GREEN_LIGHT}SUCCESS{Colors.RESET}")
        else:
            error_msg = r_data.get('error_msg', 'Unknown error')
            print(f"   {Colors.WHITE}Status:{Colors.RESET} {Colors.RED_LIGHT}FAILED - {error_msg}{Colors.RESET}")
        
        print(f"{Colors.PURPLE1}╚{'═'*20}{Colors.RESET}{' '*18}{Colors.PURPLE1}{'═'*20}╝{Colors.RESET}")
        
    except json.JSONDecodeError as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi parse JSON: {e}{Colors.RESET}")
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def process_revoke_access_token(driver, container):
    """Xử lý dịch vụ Revoke Access Token Free Fire"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  REVOKE ACCESS TOKEN - FREE FIRE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    access_token = input(f"{Rainbow.text('Enter Access Token to Revoke: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Token cannot be empty!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    nickname = "Unknown"
    account_id = "Unknown"
    region = "Unknown"
    is_valid = False
    
    try:
        res = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed = urlparse(res.url)
        params = parse_qs(parsed.query)
        
        if 'access_token' in params:
            is_valid = True
            nickname = unquote(params.get('nickname', ['Unknown'])[0])
            account_id = params.get('account_id', ['Unknown'])[0]
            region = params.get('region', ['Unknown'])[0]
    except Exception as e:
        pass
    
    if not is_valid:
        print(f"{Colors.RED_LIGHT}❌ Token is already invalid, expired, or revoked!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"{Colors.GREEN_LIGHT}✅ Token is Valid!{Colors.RESET}")
    
    refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
    
    try:
        logout_res = requests.get(logout_url, headers=headers, timeout=15)
        
        if logout_res.status_code == 200 and "error" not in logout_res.text:
            print(f"\n{Colors.GREEN_LIGHT}●{'═' * 19} {Colors.WHITE_BRIGHT}REVOKED{Colors.RESET} {Colors.GREEN_LIGHT}{'═' * 20}●{Colors.RESET}")
            print(f" {Colors.BLUE_LIGHT}Nickname    :{Colors.RESET} {Colors.WHITE}{nickname}{Colors.RESET}")
            print(f" {Colors.BLUE_LIGHT}Account ID  :{Colors.RESET} {Colors.WHITE}{account_id}{Colors.RESET}")
            print(f" {Colors.BLUE_LIGHT}Region      :{Colors.RESET} {Colors.WHITE}{region}{Colors.RESET}")
            print(f" {Colors.BLUE_LIGHT}Status      :{Colors.RESET} {Colors.GREEN_LIGHT}Successfully Logged Out & Revoked{Colors.RESET}")
            print(f"{Colors.GREEN_LIGHT}●{'═' * 48}●{Colors.RESET}\n")
        else:
            print(f"{Colors.RED_LIGHT}❌ Failed to revoke token! Server responded with an error.{Colors.RESET}")
            
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Error while revoking token: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"
def process_eat_access_token(driver, container):
    """Xử lý dịch vụ Eat to Access Token Free Fire"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  EAT TO ACCESS TOKEN - FREE FIRE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    user_input = input(f"{Rainbow.text('Enter EAT Token OR Full EAT URL: ')}").strip()
    
    if not user_input:
        print(f"{Colors.RED_LIGHT}❌ Input cannot be empty!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    eat_token = None

    if "http" in user_input or "?" in user_input:
        parsed_url = urlparse(user_input)
        query_params = parse_qs(parsed_url.query)
        if 'eat' in query_params:
            eat_token = query_params['eat'][0]
    else:
        eat_token = user_input.strip()
    
    if not eat_token:
        print(f"{Colors.RED_LIGHT}❌ Could not find an EAT token in your input.{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
    }
    
    try:
        response = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed_final = urlparse(response.url)
        final_params = parse_qs(parsed_final.query)
        
        if 'access_token' in final_params:
            access_token = final_params['access_token'][0]
            account_id = final_params.get('account_id', ['Unknown'])[0]
            nickname = final_params.get('nickname', ['Unknown'])[0]
            region = final_params.get('region', ['Unknown'])[0]
            
            print(f"\n{Colors.GREEN_LIGHT}●{'═' * 19} {Colors.WHITE_BRIGHT}SUCCESS{Colors.RESET} {Colors.GREEN_LIGHT}{'═' * 20}●{Colors.RESET}")
            print(f" {Colors.BLUE_LIGHT}Nickname    :{Colors.RESET} {Colors.WHITE}{unquote(nickname)}{Colors.RESET}")
            print(f" {Colors.BLUE_LIGHT}Account ID  :{Colors.RESET} {Colors.WHITE}{account_id}{Colors.RESET}")
            print(f" {Colors.BLUE_LIGHT}Region      :{Colors.RESET} {Colors.WHITE}{region}{Colors.RESET}")
            print(f" {Colors.BLUE_LIGHT}Access Token:{Colors.RESET}")
            print(f" {Colors.YELLOW_LIGHT}{access_token}{Colors.RESET}")
            print(f"{Colors.GREEN_LIGHT}●{'═' * 48}●{Colors.RESET}\n")
            
        else:
            print(f"{Colors.RED_LIGHT}❌ Access token not found. The token might be expired or invalid.{Colors.RESET}")
            
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Failed to generate access token: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def process_band_account_7days(driver, container):
    """Xử lý dịch vụ Band Account 7Days Free Fire [VIP]"""
    clear_screen()
    print_header()
    
    print(f"{Colors.YELLOW_LIGHT}⚠️  LƯU Ý: Dịch vụ này chỉ dành cho VIP!{Colors.RESET}")
    print(f"{Colors.YELLOW_LIGHT}⚠️  Sẽ band tài khoản trong 7 ngày.{Colors.RESET}\n")
    
    access_token = input(f"{Rainbow.text('Access Token: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Access Token không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    can_use, remaining, max_limit, message = check_band_limit(access_token, "Ban7days_FF")
    
    if not can_use:
        print(f"{Colors.RED_LIGHT}❌ {message}{Colors.RESET}")
        time.sleep(3)
        return "menu"

    print(f"\n{Colors.YELLOW_LIGHT}Đang lấy thông tin tài khoản...{Colors.RESET}")
    
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    nickname = "Unknown"
    account_id = "Unknown"
    region = "Unknown"
    is_valid = False
    
    try:
        res = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed = urlparse(res.url)
        params = parse_qs(parsed.query)
        
        if 'access_token' in params:
            is_valid = True
            nickname = unquote(params.get('nickname', ['Unknown'])[0])
            account_id = params.get('account_id', ['Unknown'])[0]
            region = params.get('region', ['Unknown'])[0]
    except Exception as e:
        pass
    
    if not is_valid:
        print(f"{Colors.RED_LIGHT}❌ Token không hợp lệ hoặc đã hết hạn!{Colors.RESET}")
        time.sleep(2)
        return "menu"

    print(f"\n{Colors.RED_LIGHT}⚠️  Bạn có chắc chắn muốn band tài khoản này trong 7 ngày?{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}💡Lần sử dụng còn lại: {remaining}/{max_limit}{Colors.RESET}")
    confirm = input(f"{Rainbow.text('Nhập YES để xác nhận: ')}").strip().upper()
    
    if confirm != "YES":
        print(f"{Colors.YELLOW_LIGHT}Đã hủy thao tác!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang khoá tài khoản...{Colors.RESET}\n")
    
    try:
        url = f"https://ban7-day-a78m.vercel.app/ban7/token?access_token={access_token}"
        
        headers_band = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers_band, timeout=30)
        
        if response.status_code != 200:
            print(f"{Colors.RED_LIGHT}❌ Lỗi kết nối: HTTP {response.status_code}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        response_text = response.text.strip()
        
        try:
            data = json.loads(response_text)

            if data.get('success') == True:
                account_data = data.get('data', {})
                
                band_nickname = account_data.get('nickname', nickname)
                band_account_id = account_data.get('account_id', account_id)
                band_region = account_data.get('region', region)
                status = account_data.get('status', 'SUSPENDED')
                version = account_data.get('version', 'Unknown')
                message = data.get('message', 'Hoàn tất khoá tài khoản!')
                update_success, update_msg = update_band_count(access_token, "Ban7days_FF")
                print(f"\n{Colors.PURPLE1}╔{'═'*20}{Colors.RESET} {Colors.WHITE_BRIGHT}BANNED ACCOUNT{Colors.RESET} {Colors.PURPLE1}{'═'*20}╗{Colors.RESET}")
                print(f"  {Colors.WHITE}Nickname:{Colors.RESET} {Colors.YELLOW_LIGHT}{band_nickname}{Colors.RESET}")
                print(f"  {Colors.WHITE}Account ID:{Colors.RESET} {Colors.WHITE}{band_account_id}{Colors.RESET}")
                print(f"  {Colors.WHITE}Region:{Colors.RESET} {Colors.WHITE}{band_region}{Colors.RESET}")
                token_preview = access_token[:25] + "..." if len(access_token) > 25 else access_token
                print(f"  {Colors.WHITE}Access Token:{Colors.RESET} {Colors.YELLOW_LIGHT}{token_preview}{Colors.RESET}")
                print(f"  {Colors.WHITE}Type:{Colors.RESET} {Colors.ORANGE2}Band 7 days{Colors.RESET}")
                print(f"  {Colors.WHITE}Status:{Colors.RESET} {Colors.RED_LIGHT}{status}{Colors.RESET}")
                print(f"  {Colors.WHITE}Version:{Colors.RESET} {Colors.WHITE}{version}{Colors.RESET}")
                print(f"  {Colors.WHITE}Message:{Colors.RESET} {Colors.GREEN_LIGHT}{message}{Colors.RESET}")
                new_remaining = remaining - 1
                print(f"  {Colors.WHITE}Còn lại:{Colors.RESET} {Colors.BLUE_LIGHT}{new_remaining}/{max_limit} lần{Colors.RESET}")
                
                print(f"{Colors.PURPLE1}╚{'═'*20}{Colors.RESET}{' '*16}{Colors.PURPLE1}{'═'*20}╝{Colors.RESET}")
                
            else:
                error_msg = data.get('message', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Band account thất bại: {error_msg}{Colors.RESET}")
                
        except json.JSONDecodeError:
            print(f"{Colors.RED_LIGHT}❌ Lỗi parse JSON!{Colors.RESET}")
            print(f"{Colors.YELLOW_LIGHT}Response: {response_text[:200]}{Colors.RESET}")
            
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def process_band_account_permanent(driver, container):
    """Xử lý dịch vụ Band Account Permanent Free Fire [VIP BUY]"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  BAND ACCOUNT PERMANENT - FREE FIRE [VIP BUY]{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW_LIGHT}⚠️ LƯU Ý: Dịch vụ này chỉ dành cho VIP BUY!{Colors.RESET}")
    print(f"{Colors.RED_LIGHT}⚠️ Sẽ band vĩnh viễn tài khoản! KHÔNG THỂ HOÀN TÁC!{Colors.RESET}\n")
    
    access_token = input(f"{Rainbow.text('Access Token: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Access Token không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    can_use, remaining, max_limit, message = check_band_limit(access_token, "Bandvv_FF")
    
    if not can_use:
        print(f"{Colors.RED_LIGHT}❌ {message}{Colors.RESET}")
        time.sleep(3)
        return "menu"
    print(f"\n{Colors.YELLOW_LIGHT}Đang lấy thông tin tài khoản...{Colors.RESET}")
    
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    nickname = "Unknown"
    account_id = "Unknown"
    region = "Unknown"
    is_valid = False
    
    try:
        res = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed = urlparse(res.url)
        params = parse_qs(parsed.query)
        
        if 'access_token' in params:
            is_valid = True
            nickname = unquote(params.get('nickname', ['Unknown'])[0])
            account_id = params.get('account_id', ['Unknown'])[0]
            region = params.get('region', ['Unknown'])[0]
    except Exception as e:
        pass
    
    if not is_valid:
        print(f"{Colors.RED_LIGHT}❌ Token không hợp lệ hoặc đã hết hạn!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"{Colors.GREEN_LIGHT}✅ Token hợp lệ!{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Nickname:{Colors.RESET} {Colors.WHITE}{nickname}{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Account ID:{Colors.RESET} {Colors.WHITE}{account_id}{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Region:{Colors.RESET} {Colors.WHITE}{region}{Colors.RESET}")
    print(f"\n{Colors.RED_LIGHT}⚠️  BẠN CÓ CHẮC CHẮN MUỐN BAND VĨNH VIỄN TÀI KHOẢN NÀY?{Colors.RESET}")
    print(f"{Colors.RED_LIGHT}⚠️  HÀNH ĐỘNG NÀY KHÔNG THỂ HOÀN TÁC!{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}💡  Lần sử dụng còn lại: {remaining}/{max_limit}{Colors.RESET}")
    confirm = input(f"{Rainbow.text('Nhập YES để xác nhận: ')}").strip().upper()
    
    if confirm != "YES":
        print(f"{Colors.YELLOW_LIGHT}Đã hủy thao tác!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang khoá vĩnh viễn tài khoản...{Colors.RESET}\n")
    
    try:

        url = f"https://band-vv-jupp.vercel.app/ban?access_token={access_token}"
        
        headers_band = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers_band, timeout=30)
        
        if response.status_code != 200:
            print(f"{Colors.RED_LIGHT}❌ Lỗi kết nối: HTTP {response.status_code}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        response_text = response.text.strip()
        
        try:
            data = json.loads(response_text)

            if data.get('success') == True:
                band_account_id = data.get('account_id', account_id)
                guild_id = data.get('guild_id')
                login_token = data.get('login_token', 'Unknown')
                open_id = data.get('open_id', 'Unknown')
                server = data.get('server', region)

                if guild_id is None:
                    guild_id = 'None'
                
                update_success, update_msg = update_band_count(access_token, "Bandvv_FF")
                print(f"\n{Colors.PURPLE1}╔{'═'*20}{Colors.RESET} {Colors.WHITE_BRIGHT}BANNED ACCOUNT{Colors.RESET} {Colors.PURPLE1}{'═'*20}╗{Colors.RESET}")
                print(f"  {Colors.WHITE}Nickname:{Colors.RESET} {Colors.YELLOW_LIGHT}{nickname}{Colors.RESET}")
                print(f"  {Colors.WHITE}Account ID:{Colors.RESET} {Colors.WHITE}{band_account_id}{Colors.RESET}")
                print(f"  {Colors.WHITE}Region:{Colors.RESET} {Colors.WHITE}{server}{Colors.RESET}")
                token_preview = access_token[:25] + "..." if len(access_token) > 25 else access_token
                print(f"  {Colors.WHITE}Access Token:{Colors.RESET} {Colors.YELLOW_LIGHT}{token_preview}{Colors.RESET}")
                print(f"  {Colors.WHITE}Type:{Colors.RESET} {Colors.RED_LIGHT}Band Permanent{Colors.RESET}")

                print(f"  {Colors.WHITE}Status:{Colors.RESET} {Colors.RED_LIGHT}SUSPENDED{Colors.RESET}")

                version = "OB54"
                print(f"  {Colors.WHITE}Version:{Colors.RESET} {Colors.WHITE}{version}{Colors.RESET}")

                message = "Hoàn tất khoá tài khoản vĩnh viễn!"
                print(f"  {Colors.WHITE}Message:{Colors.RESET} {Colors.GREEN_LIGHT}{message}{Colors.RESET}")

                new_remaining = remaining - 1
                print(f"  {Colors.WHITE}Còn lại:{Colors.RESET} {Colors.BLUE_LIGHT}{new_remaining}/{max_limit} lần{Colors.RESET}")
                
                print(f"{Colors.PURPLE1}╚{'═'*20}{Colors.RESET}{' '*16}{Colors.PURPLE1}{'═'*20}╝{Colors.RESET}")
                
            else:
                error_msg = data.get('message', 'Unknown error')
                print(f"{Colors.RED_LIGHT}❌ Band permanent thất bại: {error_msg}{Colors.RESET}")
                
        except json.JSONDecodeError:
            print(f"{Colors.RED_LIGHT}❌ Lỗi parse JSON!{Colors.RESET}")
            print(f"{Colors.YELLOW_LIGHT}Response: {response_text[:200]}{Colors.RESET}")
            
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

current_used_key = None

def get_current_key():
    """Lấy key hiện tại"""
    global current_used_key
    return current_used_key

def set_current_key(key):
    """Set key hiện tại"""
    global current_used_key
    current_used_key = key
def process_enc_python_simple(driver, container):
    """Xử lý dịch vụ Enc Python Simple - Lấy code từ encsimple.py"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ENC PYTHON SIMPLE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    if not os.path.exists('encsimple.py'):
        print(f"{Colors.RED_LIGHT}❌ Không tìm thấy encsimple.py!{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}💡 Vui lòng đặt file encsimple.py trong cùng thư mục{Colors.RESET}")
        time.sleep(3)
        return "menu"
    
    try:
        with open('encsimple.py', 'r', encoding='utf-8') as f:
            enc_code = f.read()
        namespace = {}
        import sys, os, zlib, base64, marshal
        exec(enc_code, namespace)
        if 'MainMenu' in namespace:
            namespace['MainMenu']()
        else:
            for key, value in namespace.items():
                if callable(value) and key.startswith('main'):
                    value()
                    break
        
        print(f"\n{Colors.GREEN_LIGHT}✅ Hoàn thành mã hóa!{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"


def process_enc_pymeo(driver, container):
    """Xử lý dịch vụ Enc Pymeo - Lấy code từ pymeomeoenc.py"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ENC PYMEO - PYMEOMEO OBF{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    if not os.path.exists('pymeomeoenc.py'):
        print(f"{Colors.RED_LIGHT}❌ Không tìm thấy pymeomeoenc.py!{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}💡 Vui lòng đặt file pymeomeoenc.py trong cùng thư mục{Colors.RESET}")
        time.sleep(3)
        return "menu"
    
    try:
        with open('pymeomeoenc.py', 'r', encoding='utf-8') as f:
            enc_code = f.read()
        namespace = {}
        import sys, os, random, zlib, base64, marshal, bz2, ast

        exec(enc_code, namespace)
        if 'main' in namespace:
            namespace['main']()
        elif 'Main' in namespace:
            namespace['Main']()
        else:
            for key, value in namespace.items():
                if callable(value) and not key.startswith('_'):
                    value()
                    break
        
        print(f"\n{Colors.GREEN_LIGHT}✅ Hoàn thành mã hóa!{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"


def process_enc_obsidian(driver, container):
    """Xử lý dịch vụ Enc Obsidian - Lấy code từ obsidian.py"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ENC OBSIDIAN - OBSIDIAN OBFUSCATOR{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    if not os.path.exists('obsidian.py'):
        print(f"{Colors.RED_LIGHT}❌ Không tìm thấy obsidian.py!{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}💡 Vui lòng đặt file obsidian.py trong cùng thư mục{Colors.RESET}")
        time.sleep(3)
        return "menu"
    
    try:
        with open('obsidian.py', 'r', encoding='utf-8') as f:
            enc_code = f.read()
        namespace = {}
        import sys, os, random, zlib, base64, marshal, bz2, lzma, ast, hashlib
        
        exec(enc_code, namespace)
        
        if 'main' in namespace:
            namespace['main']()
        elif 'Main' in namespace:
            namespace['Main']()
        else:
            for key, value in namespace.items():
                if callable(value) and not key.startswith('_'):
                    value()
                    break
        
        print(f"\n{Colors.GREEN_LIGHT}✅ Hoàn thành mã hóa!{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"


def process_enc_pyhydra(driver, container):
    """Xử lý dịch vụ Enc Pyhydra - Lấy code từ pyhydra.py"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ENC PYHYDRA - PYHYDRA OBFUSCATOR{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")

    if not os.path.exists('pyhydra.py'):
        print(f"{Colors.RED_LIGHT}❌ Không tìm thấy pyhydra.py!{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}💡 Vui lòng đặt file pyhydra.py trong cùng thư mục{Colors.RESET}")
        time.sleep(3)
        return "menu"
    
    try:
        with open('pyhydra.py', 'r', encoding='utf-8') as f:
            enc_code = f.read()
        namespace = {}
        import sys, os, random, zlib, base64, marshal, hashlib
        exec(enc_code, namespace)
        if 'main' in namespace:
            namespace['main']()
        elif 'Main' in namespace:
            namespace['Main']()
        else:
            for key, value in namespace.items():
                if callable(value) and not key.startswith('_'):
                    value()
                    break
        
        print(f"\n{Colors.GREEN_LIGHT}✅ Hoàn thành mã hóa!{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def check_band_limit(access_token, band_type):
    """
    Kiểm tra giới hạn sử dụng band
    band_type: "Ban7days_FF" hoặc "Bandvv_FF"
    Trả về: (can_use, remaining, max_limit, message)
    """
    try:
        current_key = get_current_key()
        if not current_key:
            ip = get_ip()
            current_key = find_key_by_ip(ip)
            if current_key:
                set_current_key(current_key)
            else:
                return False, 0, 0, "Không tìm thấy key! Vui lòng đăng nhập lại."

        url = f"{FIREBASE_URL}/keys/{current_key}.json"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code != 200:
            return False, 0, 0, "Không thể kết nối đến server!"
        
        key_data = resp.json()
        
        if not key_data:
            return False, 0, 0, "Key không tồn tại!"

        band_data = key_data.get(band_type, {})
        current = band_data.get('current', 0)
        max_limit = band_data.get('max', 0)
        
        if current >= max_limit:
            return False, 0, max_limit, f"Đã sử dụng hết {max_limit} lần!"
        
        remaining = max_limit - current
        return True, remaining, max_limit, f"Còn {remaining}/{max_limit} lần sử dụng"
        
    except Exception as e:
        return False, 0, 0, f"Lỗi: {str(e)}"


def update_band_count(access_token, band_type):
    """
    Cập nhật số lần sử dụng band
    band_type: "Ban7days_FF" hoặc "Bandvv_FF"
    """
    try:
        current_key = get_current_key()
        if not current_key:
            ip = get_ip()
            current_key = find_key_by_ip(ip)
            if current_key:
                set_current_key(current_key)
            else:
                return False, "Không tìm thấy key!"
        
        url = f"{FIREBASE_URL}/keys/{current_key}/{band_type}.json"

        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            current_data = resp.json()
            if current_data:
                current = current_data.get('current', 0)
            else:
                current = 0
        else:
            current = 0
        
        new_current = current + 1
        update_data = {
            'current': new_current
        }
        
        resp = requests.patch(url, json=update_data, timeout=10)
        
        if resp.status_code == 200:
            return True, f"Đã sử dụng {new_current} lần"
        else:
            return False, "Cập nhật thất bại!"
            
    except Exception as e:
        return False, f"Lỗi: {str(e)}"


def download_instagram():
    """Chức năng tải video Instagram"""
    while True:
        clear_screen()
        print_header()
        
        print(f"\n{Colors.PURPLE1}{'═'*20}{Colors.RESET}")
        print(f"{Colors.WHITE_BRIGHT} TẢI VIDEO INSTAGRAM{Colors.RESET}")
        print(f"{Colors.PURPLE1}{'═'*20}{Colors.RESET}\n")
        
        url = input(f"{Rainbow.text('Nhập URL Instagram: ')}").strip()
        
        if not url:
            print(f"{Colors.RED_LIGHT}❌ URL không được để trống!{Colors.RESET}")
            time.sleep(2)
            continue
        
        data = get_instagram_data(url)
        
        if not data:
            print(f"{Colors.RED_LIGHT}❌ Không thể lấy thông tin video!{Colors.RESET}")
            time.sleep(2)
            continue
        
        print(f"\n{Colors.GREEN_LIGHT}✅ Tìm thấy {len(data)} media!{Colors.RESET}")
        
        print(f"\n{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        for i, media in enumerate(data, 1):
            print(f"{Colors.YELLOW_LIGHT}[{i}]{Colors.RESET} {media['title']}")
        print(f"{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}[{len(data)+1}]{Colors.RESET} Quay lại menu chính")
        print(f"{Colors.PURPLE2}{'─'*40}{Colors.RESET}")
        
        choice = input(f"\n{Rainbow.text('Chọn media (1-{}): ').format(len(data)+1)}").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(data):
            selected = data[int(choice) - 1]
            filename = f"instagram_{int(time.time())}.mp4"
            
            print(f"\n{Colors.YELLOW_LIGHT}⬇️ Đang tải...{Colors.RESET}")
            if download_video_file(selected['download_url'], filename):
                print(f"{Colors.GREEN_LIGHT}✅ Đã tải xong: {filename}{Colors.RESET}\n")
                time.sleep(2)
                continue
            else:
                print(f"{Colors.RED_LIGHT}❌ Tải thất bại!{Colors.RESET}")
                time.sleep(2)
                continue
        
        elif choice.isdigit() and int(choice) == len(data) + 1:
            return "main_menu"
        
        else:
            print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
            time.sleep(2)
            continue

def process_facebook_regpp5(driver, container):
    """Xử lý dịch vụ RegPP5 Facebook - KHÔNG dùng Selenium"""
    clear_screen()
    print_header()
    
    cookie = input(f"{Rainbow.text('Nhập Cookie: ')}").strip()
    
    if not cookie:
        print(f"{Colors.RED_LIGHT}❌ Cookie không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    if 'c_user' not in cookie or 'xs' not in cookie:
        print(f"{Colors.RED_LIGHT}❌ Cookie không hợp lệ! Cần có c_user và xs.{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    name_input = input(f"{Rainbow.text('Tên trang: ')}").strip()
    if not name_input:
        name_input = "Aurora"
    
    random_suffix = str(random.randint(0, 1000000000000000))
    name = name_input + random_suffix
    
    bio = input(f"{Rainbow.text('Mô tả (bio): ')}").strip()
    if not bio:
        bio = "Created by Aurora Tool"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang tạo Page Profile...{Colors.RESET}")
    
    try:
        reg = REGPRO5(cookie)
        
        if not reg.login():
            print(f"{Colors.RED_LIGHT}Đăng nhập thất bại! Cookie không hợp lệ hoặc đã hết hạn.{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        success, result = reg.REG(bio, name)
        
        if success:
            print(f"\n{Colors.GREEN_LIGHT}✅ Tạo trang thành công!{Colors.RESET}")
            print(f"{Colors.BLUE_LIGHT}ID trang: {Colors.WHITE}{result}{Colors.RESET}")
            print(f"{Colors.BLUE_LIGHT}Tên trang: {Colors.WHITE}{name}{Colors.RESET}")
        else:
            print(f"\n{Colors.RED_LIGHT}❌ Tạo trang thất bại: {result}{Colors.RESET}")
        
        time.sleep(3)
        return "menu"
        
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {e}{Colors.RESET}")
        time.sleep(3)
        return "menu"

def process_facebook_buff_share(driver, container):
    """Xử lý dịch vụ Buff Share Facebook - KHÔNG dùng Selenium"""
    global buffshare_success_count, buffshare_fail_count
    
    clear_screen()
    print_header()
    
    print(f"{Colors.YELLOW_LIGHT}Nhập link Facebook (post/reel/video...):{Colors.RESET}")
    page_url = input(f"{Rainbow.text('Link: ')}").strip()
    
    if not page_url:
        print(f"{Colors.RED_LIGHT}❌ Link không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    cookie = input(f"{Rainbow.text('Cookie Facebook: ')}").strip()
    
    if not cookie:
        print(f"{Colors.RED_LIGHT}❌ Cookie không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    if 'c_user' not in cookie or 'xs' not in cookie:
        print(f"{Colors.RED_LIGHT}❌ Cookie không hợp lệ! Cần có c_user và xs.{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.PURPLE1}{'═'*50}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}CHỌN CHẾ ĐỘ SHARE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*50}{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}[1]{Colors.RESET} Private")
    print(f"{Colors.BLUE_LIGHT}[2]{Colors.RESET} Public")
    
    mode_choice = input(f"\n{Rainbow.text('Chọn chế độ (1 hoặc 2): ')}").strip()
    
    if mode_choice == '2':
        share_mode = 'public'
        mode_text = 'PUBLIC'
    else:
        share_mode = 'private'
        mode_text = 'PRIVATE'
    
    total_share = input(f"{Rainbow.text('Số lần share: ')}").strip()
    if not total_share.isdigit() or int(total_share) <= 0:
        print(f"{Colors.RED_LIGHT}❌ Số lượng không hợp lệ!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    total_share = int(total_share)
    num_threads = 5

    post_id = BuffShareTool.get_post_id_from_url(page_url, cookie)
    
    if not post_id:
        print(f"{Colors.RED_LIGHT}❌ Không thể lấy Post ID! Kiểm tra lại link hoặc cookie.{Colors.RESET}")
        time.sleep(3)
        return "menu"
    
    print(f"{Colors.GREEN_LIGHT}Post ID: {Colors.WHITE}{post_id}{Colors.RESET}")
    
    token_data = BuffShareTool.get_token_from_cookie(cookie)
    
    if not token_data:
        print(f"{Colors.RED_LIGHT}❌ Cookie không hợp lệ hoặc đã hết hạn!{Colors.RESET}")
        time.sleep(3)
        return "menu"
    
    print(f"{Colors.GREEN_LIGHT}Lấy token thành công!{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Chế độ share: {Colors.WHITE}{mode_text}{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Tổng số share: {Colors.WHITE}{total_share}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}{'='*50}{Colors.RESET}")

    
    buffshare_success_count = 0
    buffshare_fail_count = 0
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(1, total_share + 1):
            future = executor.submit(buffshare_worker, token_data, post_id, i, share_mode)
            futures.append(future)
            if i < total_share:
                time.sleep(0.05)
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                with buffshare_print_lock:
                    print(f"{Colors.RED_LIGHT}[!] Lỗi: {str(e)[:50]}{Colors.RESET}")
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{Colors.PURPLE1}{'═'*50}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}KẾT QUẢ BUFF SHARE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*50}{Colors.RESET}")
    print(f"{Colors.GREEN_LIGHT}Thành công: {buffshare_success_count}{Colors.RESET}")
    print(f"{Colors.RED_LIGHT}Thất bại: {buffshare_fail_count}{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Chế độ share: {Colors.WHITE}{mode_text}{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Tỷ lệ thành công: {Colors.WHITE}{buffshare_success_count/total_share*100:.1f}%{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}⏱Thời gian: {Colors.WHITE}{elapsed_time:.1f}s{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Tốc độ: {Colors.WHITE}{total_share/elapsed_time:.1f} share/s{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*50}{Colors.RESET}")
    
    time.sleep(4)
    return "menu"

def process_facebook_up_avatar(driver, container):
    """Xử lý dịch vụ Up Avatar Facebook - GIỮ NGUYÊN CODE GỐC"""
    clear_screen()
    print_header()
    
    cookie_input = input(f"{Rainbow.text('Nhập cookie 1 dòng: ')}").strip()
    
    if not cookie_input:
        print(f"{Colors.RED_LIGHT}❌ Cookie không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    cookies = cookie_str_to_dict(cookie_input)
    USER_ID = cookies.get("c_user")
    
    if not USER_ID:
        print(f"{Colors.RED_LIGHT}❌ Cookie không có c_user{Colors.RESET}")
        time.sleep(2)
        return "menu"

    fb_dtsg = get_fb_dtsg(cookie_input)
    lsd = get_lsd(cookie_input)
    
    if not fb_dtsg or not lsd:
        print(f"{Colors.RED_LIGHT}❌ Cookie die hoặc checkpoint{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"{Colors.YELLOW_LIGHT}Đang lấy token...{Colors.RESET}")

    fb_dtsg = get_fb_dtsg(cookie_input)
    if not fb_dtsg:
        fb_dtsg = get_fb_dtsg_v2(cookie_input)
    
    lsd = get_lsd(cookie_input)
    
    if not fb_dtsg or not lsd:
        print(f"{Colors.RED_LIGHT}❌ Cookie die hoặc checkpoint{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}DEBUG: fb_dtsg={fb_dtsg}, lsd={lsd}{Colors.RESET}")
        time.sleep(5)
        return "menu"
    
    filename = "anh.png"
    if not os.path.exists(filename):
        print(f"{Colors.RED_LIGHT}❌ Không tìm thấy file {filename}{Colors.RESET}")
        print(f"{Colors.YELLOW_LIGHT}Vui lòng đặt file ảnh tên 'anh.png' trong cùng thư mục{Colors.RESET}")
        time.sleep(3)
        return "menu"
    
    subname = mimetypes.guess_type(filename)[0]
    if not subname:
        subname = "image/png"
    
    headers = {
        'accept': '*/*',
        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'origin': 'https://www.facebook.com',
        'priority': 'u=1, i',
        'referer': 'https://www.facebook.com/profile.php?id=' + USER_ID,
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="149.0.7827.155", "Chromium";v="149.0.7827.155", "Not)A;Brand";v="24.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"19.0.0"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'x-asbd-id': '359341',
        'x-fb-lsd': lsd,
    }
    
    print(f"{Colors.YELLOW_LIGHT}Đang upload ảnh...{Colors.RESET}")
    
    try:
        params = {
            'photo_source': '57',
            'profile_id': USER_ID,
            'av': USER_ID,
            '__a': '1',
            'dpr': '1',
            'fb_dtsg': fb_dtsg,
            'jazoest': '25725',
            'lsd': lsd,
        }
        
        files = {
            'file': (filename, open(filename, "rb"), subname),
        }
        
        response = requests.post(
            'https://www.facebook.com/profile/picture/upload/',
            params=params,
            cookies=cookies,
            headers=headers,
            files=files,
        )
        
        r = response.text.replace("for (;;);", "")
        json_ = json.loads(r)
        img_id = json_['payload']['fbid']
        
        print(f"{Colors.GREEN_LIGHT}Upload ảnh thành công! ID: {img_id}{Colors.RESET}")
        
        print(f"{Colors.YELLOW_LIGHT}Đang cập nhật avatar...{Colors.RESET}")
        
        variables = {
            "input": {
                "attribution_id_v2": "ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,1782006756159,767181,190055527696468,,",
                "caption": "",
                "existing_photo_id": img_id,
                "expiration_time": None,
                "profile_id": USER_ID,
                "profile_pic_method": "EXISTING",
                "profile_pic_source": "TIMELINE",
                "scaled_crop_rect": {
                    "height": 1,
                    "width": 0.99073,
                    "x": 0.00464,
                    "y": 0
                },
                "skip_cropping": True,
                "actor_id": USER_ID,
                "client_mutation_id": "1"
            },
            "isPage": False,
            "isProfile": True,
            "scale": 1,
            "__relay_internal__pv__ProfileGeminiIsCoinFlipEnabledrelayprovider": False
        }
        
        data = {
            'av': USER_ID,
            'fb_dtsg': fb_dtsg,
            'jazoest': '25673',
            'lsd': lsd,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'ProfileCometProfilePictureSetMutation',
            'server_timestamps': 'true',
            'variables': json.dumps(variables),
            'doc_id': '26996880216606251',
        }
        
        headers_mutation = {
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.facebook.com',
            'referer': 'https://www.facebook.com/',
            'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        }
        
        response2 = requests.post(
            'https://www.facebook.com/api/graphql/',
            cookies=cookies,
            headers=headers_mutation,
            data=data
        )
        
        if response2.status_code == 200:
            print(f"{Colors.GREEN_LIGHT}✅ Đổi avatar thành công!{Colors.RESET}")
        else:
            print(f"{Colors.RED_LIGHT}❌ Đổi avatar thất bại! Status: {response2.status_code}{Colors.RESET}")
        
        time.sleep(3)
        return "menu"
        
    except FileNotFoundError:
        print(f"{Colors.RED_LIGHT}❌ Không tìm thấy file {filename}{Colors.RESET}")
        time.sleep(3)
        return "menu"
    except KeyError as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không tìm thấy key {e} trong response{Colors.RESET}")
        time.sleep(3)
        return "menu"
    except json.JSONDecodeError as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi parse JSON: {e}{Colors.RESET}")
        time.sleep(3)
        return "menu"
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {e}{Colors.RESET}")
        time.sleep(3)
        return "menu"
def run_enc_script(script_name):
    """Chạy file script mã hóa"""
    if not os.path.exists(script_name):
        print(f"{Colors.RED_LIGHT}❌ Không tìm thấy file: {script_name}{Colors.RESET}")
        return False
    
    try:
        subprocess.run([sys.executable, script_name], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi khi chạy {script_name}: {e}{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {e}{Colors.RESET}")
        return False


def process_enc_python_simple(driver, container):
    """Xử lý dịch vụ Enc Python Simple"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ENC PYTHON SIMPLE{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW_LIGHT}📌 Đang chạy encsimple.py...{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}💡 Tool mã hóa đơn giản với marshal + zlib + base64{Colors.RESET}\n")
    
    if run_enc_script("encsimple.py"):
        print(f"\n{Colors.GREEN_LIGHT}✅ Hoàn thành mã hóa!{Colors.RESET}")
    else:
        print(f"\n{Colors.RED_LIGHT}❌ Mã hóa thất bại!{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"


def process_enc_pymeo(driver, container):
    """Xử lý dịch vụ Enc Pymeo"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ENC PYMEO - PYMEOMEO OBF{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW_LIGHT}📌 Đang chạy pymeomeoenc.py...{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}💡 Tool mã hóa Pymeo - Premium Obfuscator{Colors.RESET}\n")
    
    if run_enc_script("pymeomeoenc.py"):
        print(f"\n{Colors.GREEN_LIGHT}✅ Hoàn thành mã hóa!{Colors.RESET}")
    else:
        print(f"\n{Colors.RED_LIGHT}❌ Mã hóa thất bại!{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"


def process_enc_obsidian(driver, container):
    """Xử lý dịch vụ Enc Obsidian"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ENC OBSIDIAN - OBSIDIAN OBFUSCATOR{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW_LIGHT}📌 Đang chạy obsidian.py...{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}💡 Tool mã hóa Obsidian - Premium Obfuscator{Colors.RESET}\n")
    
    if run_enc_script("obsidian.py"):
        print(f"\n{Colors.GREEN_LIGHT}✅ Hoàn thành mã hóa!{Colors.RESET}")
    else:
        print(f"\n{Colors.RED_LIGHT}❌ Mã hóa thất bại!{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"


def process_enc_pyhydra(driver, container):
    """Xử lý dịch vụ Enc Pyhydra"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*40}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}  ENC PYHYDRA - PYHYDRA OBFUSCATOR{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*40}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW_LIGHT}📌 Đang chạy pyhydra.py...{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}💡 Tool mã hóa Pyhydra - Premium Obfuscator{Colors.RESET}\n")
    
    if run_enc_script("pyhydra.py"):
        print(f"\n{Colors.GREEN_LIGHT}✅ Hoàn thành mã hóa!{Colors.RESET}")
    else:
        print(f"\n{Colors.RED_LIGHT}❌ Mã hóa thất bại!{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def cookie_str_to_dict(cookie_str: str):
    """Chuyển cookie string thành dict"""
    cookies = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k] = v
    return cookies

def get_fb_dtsg(cookie_str):
    """Lấy fb_dtsg từ Facebook - GIỮ NGUYÊN NHƯ CODE GỐC"""
    headers = {
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0",
        "accept": "text/html"
    }
    
    try:
        r = requests.get("https://www.facebook.com/", headers=headers, timeout=30)
        html = r.text
        
        patterns = [
            r'name="fb_dtsg" value="([^"]+)"',
            r'"DTSGInitialData".*?"token":"([^"]+)"'
        ]
        
        for p in patterns:
            m = re.search(p, html)
            if m:
                return m.group(1)
        return None
    except:
        return None

def get_lsd(cookie_str):
    """Lấy lsd từ Facebook - GIỮ NGUYÊN NHƯ CODE GỐC"""
    try:
        r = requests.get("https://www.facebook.com/", headers={"cookie": cookie_str}, timeout=30)
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"', r.text)
        return m.group(1) if m else None
    except:
        return None

def process_facebook_buff_follow(driver, container):
    """Xử lý dịch vụ Buff Follow Facebook - GIỮ NGUYÊN CODE GỐC"""
    global list_page
    
    clear_screen()
    print_header()
    
    print(f"\n{Colors.PURPLE1}{'═'*50}{Colors.RESET}")
    print(f"{Colors.WHITE_BRIGHT}📱 BUFF FOLLOW FACEBOOK{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*50}{Colors.RESET}\n")
    
    cookies_list = []
    dem_ck = 1
    
    print(f"{Colors.YELLOW_LIGHT}Nhập cookie (Enter để dừng):{Colors.RESET}")
    while True:
        cookie = input(f"{Colors.BLUE_LIGHT}[{dem_ck}] {Colors.WHITE}Cookie: {Colors.RESET}").strip()
        if cookie == '' and dem_ck >= 2:
            break
        elif cookie == '':
            print(f"{Colors.RED_LIGHT}❌ Cần ít nhất 1 cookie!{Colors.RESET}")
            continue
        if 'c_user=' not in cookie:
            print(f"{Colors.RED_LIGHT}❌ Cookie không hợp lệ! Cần có c_user.{Colors.RESET}")
            continue
        
        f = KsxKoji()
        if f.__Get_ThongTin__(cookie):
            if f.__Get_Page__(cookie):
                print(f"{Colors.GREEN_LIGHT}✅ {f.name} - Có {f.dem} Page PR5{Colors.RESET}")
                cookies_list.append(cookie)
                dem_ck += 1
            else:
                print(f"{Colors.RED_LIGHT}❌ Không lấy được Page PR5{Colors.RESET}")
        else:
            print(f"{Colors.RED_LIGHT}❌ Cookie die!{Colors.RESET}")
    
    if not cookies_list:
        print(f"{Colors.RED_LIGHT}❌ Không có cookie hợp lệ!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.PURPLE1}{'═'*50}{Colors.RESET}")
    target_uid = input(f"{Rainbow.text('Nhập UID Profile muốn Follow: ')}").strip()
    if not target_uid or not target_uid.isdigit():
        print(f"{Colors.RED_LIGHT}❌ UID không hợp lệ!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    so_luong = input(f"{Rainbow.text('Nhập số lượng Follow: ')}").strip()
    if not so_luong.isdigit() or int(so_luong) <= 0:
        print(f"{Colors.RED_LIGHT}❌ Số lượng không hợp lệ!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    so_luong = int(so_luong)
    
    delay = input(f"{Rainbow.text('Nhập delay (giây, tối thiểu 5): ')}").strip()
    if not delay.isdigit() or int(delay) < 5:
        delay = 10
    else:
        delay = int(delay)
    
    print(f"\n{Colors.YELLOW_LIGHT}Bắt đầu Buff Follow...{Colors.RESET}")
    print(f"{Colors.BLUE_LIGHT}Target: {target_uid} | Số lượng: {so_luong} | Delay: {delay}s{Colors.RESET}")
    print(f"{Colors.PURPLE1}{'═'*50}{Colors.RESET}\n")
    
    f = KsxKoji()
    dem = 0
    dem_ck = 0
    total_cookies = len(cookies_list)
    
    while dem < so_luong:
        try:
            cookie = cookies_list[dem_ck % total_cookies]
            
            if not f.__Get_ThongTin__(cookie):
                dem_ck += 1
                continue
            
            list_page.clear()
            if not f.__Get_Page__(cookie):
                dem_ck += 1
                continue
            
            if not list_page:
                dem_ck += 1
                continue
            
            print(f"{Colors.GREEN_LIGHT}📱 Đang dùng: {f.name} - Có {len(list_page)} Page PR5{Colors.RESET}")
            
            for page_id in list_page:
                if dem >= so_luong:
                    break
                
                result = f.__Follow__(cookie, page_id, target_uid)
                dem += 1
                
                if result == True:
                    print(f"{Colors.GREEN_LIGHT}✅ [{dem}/{so_luong}] Follow thành công từ Page {page_id}{Colors.RESET}")
                elif result == 'block':
                    print(f"{Colors.RED_LIGHT}❌ Page {page_id} bị block, bỏ qua{Colors.RESET}")
                    continue
                else:
                    print(f"{Colors.RED_LIGHT}❌ [{dem}/{so_luong}] Follow thất bại từ Page {page_id}{Colors.RESET}")
                
                if dem < so_luong:
                    time.sleep(delay)
            
            dem_ck += 1
            
        except Exception as e:
            print(f"{Colors.RED_LIGHT}❌ Lỗi: {e}{Colors.RESET}")
            dem_ck += 1
            time.sleep(2)
    
    print(f"\n{Colors.GREEN_LIGHT}{'═'*50}{Colors.RESET}")
    print(f"{Colors.GREEN_LIGHT}✅ HOÀN THÀNH! Đã Follow {dem} lần{Colors.RESET}")
    print(f"{Colors.GREEN_LIGHT}{'═'*50}{Colors.RESET}")
    time.sleep(3)
    return "menu"

def process_comments_hearts_service(driver, container):
    clear_screen()
    banner_text = f"""
{Colors.PURPLE1}  ▄▄▄       █    ██    ▄▄▄█████▓ ▒█████   ▒█████   ██▓    {Colors.RESET}
{Colors.PURPLE2} ▒████▄     ██  ▓██▒   ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒    {Colors.RESET}
{Colors.PURPLE3} ▒██  ▀█▄  ▓██  ▒██░   ▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░    {Colors.RESET}
{Colors.PURPLE4} ░██▄▄▄▄██ ▓▓█  ░██░   ░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░    {Colors.RESET}
{Colors.PURPLE5}  ▓█   ▓██▒▒▒█████▓      ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒{Colors.RESET}
{Colors.PURPLE6}  ▒▒   ▓▒█░░▒▓▒ ▒ ▒      ▒ ░░   ░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░▓  ░{Colors.RESET}
{Colors.WHITE}    ▒   ▒▒ ░░░▒░ ░ ░        ░      ░ ▒ ▒░   ░ ▒ ▒░ ░ ░ ▒  ░{Colors.RESET}
{Colors.PURPLE2}    ░   ▒    ░░░ ░ ░      ░      ░ ░ ░ ▒  ░ ░ ░ ▒    ░ ░   {Colors.RESET}
{Colors.PURPLE1}        ░  ░   ░                     ░ ░      ░ ░      ░  ░{Colors.RESET}
"""
    for line in banner_text.split('\n'):
        if line.strip():
            type_line_quick(line, 0.002)
        else:
            print()
        time.sleep(0.003)
    
    print()
    info_lines = [
        f"{Colors.PURPLE1}╭────────────────────────────── ○ › {Colors.PURPLE1}Th{Colors.PURPLE2}ôn{Colors.PURPLE3}g T{Colors.PURPLE4}i{Colors.PURPLE5}n{Colors.WHITE} {Colors.PURPLE1}‹ ○ ──────────────────────────────╮{Colors.RESET}",
        f"{Colors.PURPLE2}│          • >>> Author     |   Tin/Khánh Lộc (@tindevtools)                    │{Colors.RESET}",
        f"{Colors.PURPLE3}│          • >>> More Infor |   Tin × LouisDevTool                              │{Colors.RESET}",
        f"{Colors.PURPLE4}│          • >>> Version    |   V2.0 (Auto Key by IP)                           │{Colors.RESET}",
        f"{Colors.PURPLE5}│          • >>> Telegram   |   𝚃𝙸𝙽 ⨯ 𝙳𝙴𝚅 【</>】 | @tindevtools                │{Colors.RESET}",
        f"{Colors.PURPLE6}│          • >>> Tool       |   Tool Dịch Vụ Đa Chức Năng                       │{Colors.RESET}",
        f"{Colors.WHITE}╰───────────────────────────────────────────────────────────────────────────────╯{Colors.RESET}"
    ]
    
    for line in info_lines:
        type_line_quick(line, 0.002)
        time.sleep(0.003)
    
    print()
    time.sleep(1)
    url = input(f"\n{Colors.PURPLE1}Nh{Colors.PURPLE2}ập{Colors.PURPLE3} U{Colors.PURPLE4}RL{Colors.PURPLE5} Ti{Colors.PURPLE6}kT{Colors.WHITE}ok:{Colors.RESET} ").strip()
    
    if not url.startswith("https://www.tiktok.com/") and not url.startswith("https://vm.tiktok.com/"):
        print(f"{Colors.RED_LIGHT}❌ URL không hợp lệ!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    target_username = input(f"\n{Colors.WHITE_BRIGHT}Username :{Colors.RESET} ").strip()
    if target_username.startswith("@"):
        target_username = target_username[1:]
    
    if not target_username:
        print(f"{Colors.RED_LIGHT}❌ Username không hợp lệ!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    print(f"\n{Colors.WHITE_BRIGHT}{'═'*70}{Colors.RESET}")
    
    try:
        input_field = container.find_element(By.CSS_SELECTOR, "input.form-control[type='search']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
        time.sleep(0.5)
        input_field.clear()
        input_field.send_keys(url)
        time.sleep(0.5)
        click_search(container, driver)
    except Exception as e:
        time.sleep(2)
        return "menu"

    wbutton_found = False
    try:
        wbutton = container.find_element(By.CSS_SELECTOR, "button.wbutton")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wbutton)
        time.sleep(0.5)
        wbutton.click()
        wbutton_found = True
        time.sleep(5)
        handle_ad_blocking(driver)
    except:
        pass

    if not wbutton_found:
        if not wait_for_ready(container, driver):
            print(f"{Colors.RED_LIGHT}❌ Hết thời gian chờ{Colors.RESET}")
            return "menu"

        click_search(container, driver)
        time.sleep(3)
        handle_ad_blocking(driver)

        try:
            wbutton = container.find_element(By.CSS_SELECTOR, "button.wbutton")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wbutton)
            time.sleep(0.5)
            wbutton.click()
            wbutton_found = True
            time.sleep(5)
            handle_ad_blocking(driver)
        except Exception as e:
            print(f"{Colors.RED_LIGHT}❌ Không tìm thấy nút buff sau khi chờ{Colors.RESET}")
            return "menu"
    
    if not wbutton_found:
        return "menu"

    time.sleep(3)
    handle_ad_blocking(driver)

    found = False
    current_page = 1
    
    while True:
        comment_forms = container.find_elements(By.XPATH, ".//form[@class='w1a']")
        
        for form in comment_forms:
            try:
                username_elem = form.find_element(By.XPATH, ".//div[@class='font-weight-bold d-inline-flex kadi-rengi']")
                username = username_elem.text.strip().replace("@", "")
                
                if username.lower() == target_username.lower():
                    submit_btn = form.find_element(By.XPATH, ".//button[@type='submit']")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                    time.sleep(0.5)
                    submit_btn.click()
                    found = True
                    break
            except:
                continue
        
        if found:
            break

        try:
            next_btn = container.find_element(By.XPATH, "//button[contains(@class, 'fa-chevron-right')]")
            if next_btn.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                time.sleep(0.5)
                next_btn.click()
                current_page += 1
                time.sleep(5)
                handle_ad_blocking(driver)
            else:
                print(f"{Colors.RED_LIGHT}❌ Không tìm thấy username '{target_username}' trong danh sách{Colors.RESET}")
                return "menu"
        except:
            print(f"{Colors.RED_LIGHT}❌ Không tìm thấy username '{target_username}' trong danh sách{Colors.RESET}")
            return "menu"

    wait_for_sending_complete(container, driver)
    
    success_elem = container.find_elements(By.XPATH, ".//span[contains(text(), 'successfully sent')]")
    sent_text = ""
    if success_elem:
        sent_text = success_elem[0].text
    else:
        sent_text = "Comment hearts successfully sent"
    
    video_uid = extract_uid_from_url(url)
    current_time = time.strftime("%H:%M")
    
    if video_uid:
        print(f"{Colors.WHITE}[1] [{current_time}] {Colors.GREEN_LIGHT}[SUCCESS] {Colors.WHITE}UID: {Colors.ORANGE2}{video_uid}{Colors.WHITE}   |   {Colors.GREEN_LIGHT}{sent_text}{Colors.RESET}")
    else:
        print(f"{Colors.WHITE}[1] [{current_time}] {Colors.GREEN_LIGHT}[SUCCESS] {Colors.WHITE}Comments Hearts   |   {Colors.GREEN_LIGHT}{sent_text}{Colors.RESET}")

    stt = 2
    
    while True:
        if not wait_for_ready(container, driver):
            continue

        click_search(container, driver)
        time.sleep(3)
        handle_ad_blocking(driver)

        try:
            wbutton = container.find_element(By.CSS_SELECTOR, "button.wbutton")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wbutton)
            time.sleep(0.5)
            wbutton.click()
            time.sleep(5)
            handle_ad_blocking(driver)
        except:
            print(f"{Colors.RED_LIGHT}❌ Không tìm thấy nút buff{Colors.RESET}")
            break

        time.sleep(3)
        comment_forms = container.find_elements(By.XPATH, ".//form[@class='w1a']")
        found = False
        
        for form in comment_forms:
            try:
                username_elem = form.find_element(By.XPATH, ".//div[@class='font-weight-bold d-inline-flex kadi-rengi']")
                username = username_elem.text.strip().replace("@", "")
                
                if username.lower() == target_username.lower():
                    submit_btn = form.find_element(By.XPATH, ".//button[@type='submit']")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                    time.sleep(0.5)
                    submit_btn.click()
                    found = True
                    break
            except:
                continue
        
        if not found:
            print(f"{Colors.RED_LIGHT}❌ Không tìm thấy lại username '{target_username}'{Colors.RESET}")
            break
        
        current_time = time.strftime("%H:%M")
        wait_for_sending_complete(container, driver)
        
        success_elem = container.find_elements(By.XPATH, ".//span[contains(text(), 'successfully sent')]")
        
        if video_uid:
            print(f"{Colors.WHITE}[{stt}] [{current_time}] {Colors.GREEN_LIGHT}[SUCCESS] {Colors.WHITE}UID: {Colors.ORANGE2}{video_uid}{Colors.WHITE}   |   {Colors.GREEN_LIGHT}{sent_text}{Colors.RESET}")
        else:
            print(f"{Colors.WHITE}[{stt}] [{current_time}] {Colors.GREEN_LIGHT}[SUCCESS] {Colors.WHITE}Comments Hearts   |   {Colors.GREEN_LIGHT}{sent_text}{Colors.RESET}")
        
        stt += 1
        time.sleep(2)

def process_views_service(driver, container):
    return process_generic_service(driver, container, "Views", "button.wbutton")

def process_hearts_service(driver, container):
    return process_generic_service(driver, container, "Hearts", "button.wbutton")

def process_shares_service(driver, container):
    return process_generic_service(driver, container, "Shares", "button.wbutton")

def process_favorites_service(driver, container):
    return process_generic_service(driver, container, "Favorites", "button.wbutton")

def process_live_stream_service(driver, container):
    return process_generic_service(driver, container, "Live Stream", "button.wbutton")

def process_repost_service(driver, container):
    return process_generic_service(driver, container, "Repost", "button.wbutton")

def process_followers_service(driver, container):
    return process_generic_service(driver, container, "Followers", "button.wbutton")

def process_generic_service(driver, container, service_name, button_selector="button.wbutton"):
    clear_screen()
    banner_text = f"""
{Colors.PURPLE1}  ▄▄▄       █    ██    ▄▄▄█████▓ ▒█████   ▒█████   ██▓    {Colors.RESET}
{Colors.PURPLE2} ▒████▄     ██  ▓██▒   ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒    {Colors.RESET}
{Colors.PURPLE3} ▒██  ▀█▄  ▓██  ▒██░   ▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░    {Colors.RESET}
{Colors.PURPLE4} ░██▄▄▄▄██ ▓▓█  ░██░   ░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░    {Colors.RESET}
{Colors.PURPLE5}  ▓█   ▓██▒▒▒█████▓      ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒{Colors.RESET}
{Colors.PURPLE6}  ▒▒   ▓▒█░░▒▓▒ ▒ ▒      ▒ ░░   ░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░▓  ░{Colors.RESET}
{Colors.WHITE}    ▒   ▒▒ ░░░▒░ ░ ░        ░      ░ ▒ ▒░   ░ ▒ ▒░ ░ ░ ▒  ░{Colors.RESET}
{Colors.PURPLE2}    ░   ▒    ░░░ ░ ░      ░      ░ ░ ░ ▒  ░ ░ ░ ▒    ░ ░   {Colors.RESET}
{Colors.PURPLE1}        ░  ░   ░                     ░ ░      ░ ░      ░  ░{Colors.RESET}
"""
    for line in banner_text.split('\n'):
        if line.strip():
            type_line_quick(line, 0.002)
        else:
            print()
        time.sleep(0.003)
    
    print()

    info_lines = [
        f"{Colors.PURPLE1}╭────────────────────────────── ○ › {Colors.PURPLE1}Th{Colors.PURPLE2}ôn{Colors.PURPLE3}g T{Colors.PURPLE4}i{Colors.PURPLE5}n{Colors.WHITE} {Colors.PURPLE1}‹ ○ ──────────────────────────────╮{Colors.RESET}",
        f"{Colors.PURPLE2}│          • >>> Author     |   Tin/Khánh Lộc (@tindevtools)                    │{Colors.RESET}",
        f"{Colors.PURPLE3}│          • >>> More Infor |   Tin × LouisDevTool                              │{Colors.RESET}",
        f"{Colors.PURPLE4}│          • >>> Version    |   V2.0 (Auto Key by IP)                           │{Colors.RESET}",
        f"{Colors.PURPLE5}│          • >>> Telegram   |   𝚃𝙸𝙽 ⨯ 𝙳𝙴𝚅 【</>】 | @tindevtools                │{Colors.RESET}",
        f"{Colors.PURPLE6}│          • >>> Tool       |   Tool Dịch Vụ Đa Chức Năng                       │{Colors.RESET}",
        f"{Colors.WHITE}╰───────────────────────────────────────────────────────────────────────────────╯{Colors.RESET}"
    ]
    
    for line in info_lines:
        type_line_quick(line, 0.002)
        time.sleep(0.003)
    
    print()
    time.sleep(1)

    url = input(f"\n{Colors.PURPLE1}Nh{Colors.PURPLE2}ập{Colors.PURPLE3} U{Colors.PURPLE4}RL{Colors.PURPLE5} Ti{Colors.PURPLE6}kT{Colors.WHITE}ok:{Colors.RESET} ").strip()

    if not url.startswith("https://www.tiktok.com/") and not url.startswith("https://vm.tiktok.com/"):
        print(f"{Colors.RED_LIGHT}❌ URL không hợp lệ!{Colors.RESET}")
        time.sleep(2)
        return "menu"

    video_uid = extract_uid_from_url(url)
    if not video_uid:
        print(f"{Colors.YELLOW_LIGHT}⚠️ Không thể lấy UID từ link, vui lòng nhập UID thủ công:{Colors.RESET}")
        video_uid = input(f"{Colors.WHITE_BRIGHT}UID: {Colors.RESET}").strip()

    print(f"\n{Colors.WHITE_BRIGHT}{'═'*70}{Colors.RESET}")
    
    try:
        input_field = container.find_element(By.CSS_SELECTOR, "input.form-control[type='search']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
        time.sleep(0.5)
        input_field.clear()
        input_field.send_keys(url)
        time.sleep(0.5)
        click_search(container, driver)
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {e}{Colors.RESET}")
        time.sleep(2)
        return "menu"

    wbutton_found = False
    try:
        wbutton = container.find_element(By.CSS_SELECTOR, button_selector)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wbutton)
        time.sleep(0.5)
        wbutton.click()
        wbutton_found = True
        time.sleep(5)
        handle_ad_blocking(driver)
    except:
        pass
    
    if not wbutton_found:
        if not wait_for_ready(container, driver):
            print(f"{Colors.RED_LIGHT}❌ Hết thời gian chờ{Colors.RESET}")
            return "menu"

        click_search(container, driver)
        time.sleep(3)
        handle_ad_blocking(driver)

        try:
            wbutton = container.find_element(By.CSS_SELECTOR, button_selector)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wbutton)
            time.sleep(0.5)
            wbutton.click()
            wbutton_found = True
            time.sleep(5)
            handle_ad_blocking(driver)
        except Exception as e:
            print(f"{Colors.RED_LIGHT}❌ Không tìm thấy nút buff sau khi chờ{Colors.RESET}")
            return "menu"
    
    if not wbutton_found:
        return "menu"

    buff_count = 0
    stt = 1
    
    while True:
        if not wait_for_ready(container, driver):
            continue
        
        click_search(container, driver)

        action_btn = None
        for attempt in range(10):
            action_buttons = container.find_elements(By.CSS_SELECTOR, button_selector)
            if action_buttons:
                action_btn = action_buttons[0]
                break
            time.sleep(2)
        
        if not action_btn:
            continue
        
        action_text = action_btn.text.strip()
        current_count = extract_number_from_text(action_text)
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_btn)
        time.sleep(0.5)
        action_btn.click()
        buff_count += 1

        current_time = time.strftime("%H:%M")

        wait_for_sending_complete(container, driver)
        
        time.sleep(2)
        handle_ad_blocking(driver)

        success_elem = None
        success_selectors = [
            ".//span[contains(text(), 'Successfully')]",
            ".//span[contains(text(), 'successfully sent')]",
            ".//span[contains(text(), 'hearts sent')]",
            ".//span[contains(text(), 'views sent')]"
        ]
        
        for selector in success_selectors:
            try:
                success_elem = container.find_element(By.XPATH, selector)
                if success_elem:
                    break
            except:
                pass

        action_buttons_after = container.find_elements(By.CSS_SELECTOR, button_selector)
        if action_buttons_after:
            action_text_after = action_buttons_after[0].text.strip()
            new_count = extract_number_from_text(action_text_after)
        else:
            new_count = current_count
        
        if success_elem:
            sent_text = success_elem.text
            if "Favorites" in service_name:
                status_color = Colors.YELLOW_LIGHT
            elif "Hearts" in service_name:
                status_color = Colors.RED_LIGHT
            elif "Views" in service_name:
                status_color = Colors.GREEN_LIGHT
            elif "Shares" in service_name:
                status_color = Colors.BLUE_LIGHT
            else:
                status_color = Colors.GREEN_LIGHT
    
            if video_uid:
                print(f"{Colors.WHITE}[{stt}] [{current_time}] {Colors.GREEN_LIGHT}[SUCCESS] {Colors.WHITE}UID: {Colors.ORANGE2}{video_uid}{Colors.WHITE}   |   {status_color}{sent_text}{Colors.RESET}")
            else:
                if new_count:
                    print(f"{Colors.WHITE}[{stt}] [{current_time}] {Colors.GREEN_LIGHT}[SUCCESS] {Colors.WHITE}{service_name}: {Colors.ORANGE2}{new_count}{Colors.WHITE}   |   {status_color}{sent_text}{Colors.RESET}")
                else:
                    print(f"{Colors.WHITE}[{stt}] [{current_time}] {Colors.GREEN_LIGHT}[SUCCESS] {Colors.WHITE}{service_name}: {Colors.ORANGE2}?{Colors.WHITE}   |   {status_color}{sent_text}{Colors.RESET}")
        
        stt += 1
        time.sleep(2)

def click_search(container, driver):
    try:
        search_btn = container.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
        time.sleep(1)
        search_btn.click()
        time.sleep(5)
        handle_ad_blocking(driver)
        return True
    except:
        return False

def wait_for_ready(container, driver):
    timeout = 300
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            handle_ad_blocking(driver)
            
            countdown_elem = None
            try:
                countdown_elem = container.find_element(By.CSS_SELECTOR, ".views-countdown")
            except:
                try:
                    countdown_elem = container.find_element(By.CSS_SELECTOR, "#login-countdown")
                except:
                    try:
                        countdown_elem = driver.find_element(By.CSS_SELECTOR, ".views-countdown")
                    except:
                        try:
                            countdown_elem = driver.find_element(By.XPATH, "//span[contains(text(), 'Please wait')]")
                        except:
                            pass
            
            if countdown_elem:
                text = countdown_elem.text
                if "READY" in text:
                    return True
            time.sleep(1)
        except:
            time.sleep(1)
    
    return False

def wait_for_sending_complete(container, driver):
    while True:
        try:
            handle_ad_blocking(driver)
            
            sending_elem = container.find_elements(By.XPATH, ".//span[contains(text(), 'hearts are sending')]")
            if not sending_elem:
                success_elem = container.find_elements(By.XPATH, ".//span[contains(text(), 'successfully sent')]")
                if success_elem:
                    return True
                countdown_elem = container.find_elements(By.CSS_SELECTOR, ".views-countdown")
                if countdown_elem:
                    return True
            time.sleep(2)
        except:
            time.sleep(2)

def extract_uid_from_url(url):
    """Trích xuất UID video từ URL TikTok"""
    match = re.search(r'/(?:video|photo)/(\d+)', url)
    if match:
        return match.group(1)
    if "vt.tiktok.com" in url:
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            final_url = response.url
            match = re.search(r'/(?:video|photo)/(\d+)', final_url)
            if match:
                return match.group(1)
        except:
            pass
        try:
            api_url = "https://api.like3s.vn/api/tools/find-uid"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json"
            }
            response = requests.post(api_url, json={"url": url}, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "uid" in data:
                    return data["uid"]
        except:
            pass
    
    return None

def extract_number_from_text(text):
    match = re.search(r'([\d,]+)', text)
    if match:
        return match.group(1).replace(',', '')
    return None

def process_check_recovery_mail(driver, container):
    """Xử lý dịch vụ Check Recovery Mail Free Fire"""
    clear_screen()
    print_header()
    
    print(f"{Colors.WHITE_BRIGHT}Vui lòng nhập Access Token để kiểm tra Recovery Mail{Colors.RESET}")
    
    access_token = input(f"{Rainbow.text('Access Token: ')}").strip()
    
    if not access_token:
        print(f"{Colors.RED_LIGHT}❌ Access Token không được để trống!{Colors.RESET}")
        time.sleep(2)
        return "menu"
    
    print(f"\n{Colors.YELLOW_LIGHT}Đang kiểm tra thông tin...{Colors.RESET}\n")
    
    try:
        url = f"https://100067.connect.garena.com/game/account_security/bind:get_bind_info?app_id=100067&access_token={access_token}"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"{Colors.RED_LIGHT}❌ Lỗi kết nối: HTTP {response.status_code}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        
        data = response.json()
        if data.get('result') != 0:
            error_msg = data.get('error_msg', 'Unknown error')
            print(f"{Colors.RED_LIGHT}❌ Lỗi từ API: {error_msg}{Colors.RESET}")
            time.sleep(2)
            return "menu"
        email_to_be = data.get('email_to_be', 'Chưa có')
        email = data.get('email', 'Chưa có')
        mobile = data.get('mobile', 'Chưa có')
        mobile_to_be = data.get('mobile_to_be', 'Chưa có')
        countdown = data.get('request_exec_countdown', 0)
        if countdown > 0:
            days = countdown // 86400
            hours = (countdown % 86400) // 3600
            minutes = (countdown % 3600) // 60
            seconds = countdown % 60
            time_str = f"{days} ngày {hours} giờ {minutes} phút {seconds} giây"
        else:
            time_str = "0 giây"
        print(f"{Colors.PURPLE1}{'═'*27}{Colors.RESET}")
        print(f"{Colors.WHITE_BRIGHT}  THÔNG TIN RECOVERY MAIL{Colors.RESET}")
        print(f"{Colors.PURPLE1}{'═'*27}{Colors.RESET}")
        print(f"{Colors.PURPLE2}┌{'─'*58}┐{Colors.RESET}")
        print(f"{Colors.PURPLE3}  {Colors.WHITE}Mail xác thực:{Colors.RESET} {Colors.GREEN_LIGHT}{email:<47}{Colors.RESET}{Colors.PURPLE3}{Colors.RESET}")
        print(f"{Colors.PURPLE4}  {Colors.WHITE}Mail chờ:{Colors.RESET} {Colors.GREEN_LIGHT}{email_to_be:<42}{Colors.RESET}{Colors.PURPLE4}{Colors.RESET}")
        if mobile and mobile != 'Chưa có':
            print(f"{Colors.PURPLE5}  {Colors.WHITE}📱 SĐT chờ:{Colors.RESET} {Colors.GREEN_LIGHT}{mobile:<47}{Colors.RESET}{Colors.PURPLE5}{Colors.RESET}")
        if mobile_to_be and mobile_to_be != 'Chưa có':
            print(f"{Colors.PURPLE6}  {Colors.WHITE}📱 SĐT xác thực:{Colors.RESET} {Colors.GREEN_LIGHT}{mobile_to_be:<42}{Colors.RESET}{Colors.PURPLE6}{Colors.RESET}")
        if countdown > 0:
            print(f"{Colors.WHITE}  {Colors.ORANGE2}⏱ Thời gian còn lại:{Colors.RESET} {Colors.YELLOW_LIGHT}{time_str:<38}{Colors.RESET}{Colors.WHITE}{Colors.RESET}")
        else:
            print(f"{Colors.WHITE}   {Colors.ORANGE2}⏱ Trạng thái:{Colors.RESET} {Colors.GREEN_LIGHT}Đã sẵn sàng{' ':<45}{Colors.RESET}{Colors.WHITE}{Colors.RESET}")
        
        print(f"{Colors.PURPLE1}└{'─'*58}┘{Colors.RESET}")
        print(f"\n{Colors.BLUE_LIGHT}💡 Ghi chú:{Colors.RESET}")
        print(f"  • Mail chờ: {Colors.GREEN_LIGHT}Email đang được liên kết{Colors.RESET}")
        print(f"  • Mail xác thực: {Colors.GREEN_LIGHT}Email sẽ được thay thế{Colors.RESET}")
        if countdown > 0:
            print(f"  • {Colors.YELLOW_LIGHT}⚠️ Cần chờ {time_str} để thay đổi mail tiếp theo{Colors.RESET}")
        else:
            print(f"  • {Colors.GREEN_LIGHT}✅ Có thể thay đổi mail ngay{Colors.RESET}")
        
        print(f"\n{Colors.PURPLE1}{'═'*60}{Colors.RESET}")
        
    except requests.exceptions.Timeout:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Kết nối đến server quá lâu!{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Không thể kết nối đến server!{Colors.RESET}")
    except json.JSONDecodeError:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: Dữ liệu trả về không hợp lệ!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {str(e)}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW_LIGHT}Nhấn Enter để quay lại menu...{Colors.RESET}")
    input()
    return "menu"

def process_service(driver, service_name, service_class):
    if service_class == "regpp5" or service_name == "RegPP5":
        return process_facebook_regpp5(driver, None)
    
    if service_class in ["buffshare", "upavatar", "bufffollow"]:
        service_handlers = {
            "buffshare": process_facebook_buff_share,
            "upavatar": process_facebook_up_avatar,
            "bufffollow": process_facebook_buff_follow
        }
        handler = service_handlers.get(service_class)
        if handler:
            return handler(driver, None)
    
    if service_class:
        try:
            container = driver.find_element(By.CSS_SELECTOR, f".{service_class}")
        except:
            containers = driver.find_elements(By.CSS_SELECTOR, ".card-ortlax")
            container = None
            for c in containers:
                try:
                    title = c.find_element(By.CSS_SELECTOR, ".card-title")
                    if title.text.strip() == service_name:
                        container = c
                        break
                except:
                    continue
            if not container:
                print(f"❌ Không tìm thấy container cho dịch vụ {service_name}")
                time.sleep(2)
                return "menu"
    else:
        containers = driver.find_elements(By.CSS_SELECTOR, ".card-ortlax")
        container = None
        for c in containers:
            try:
                title = c.find_element(By.CSS_SELECTOR, ".card-title")
                if title.text.strip() == service_name:
                    container = c
                    break
            except:
                continue
        if not container:
            print(f"❌ Không tìm thấy container cho dịch vụ {service_name}")
            time.sleep(2)
            return "menu"
    
    clear_screen()
    print("╔" + "="*70 + "╗")
    print(f"║  📱 DỊCH VỤ: {service_name:<59}║")
    print("╚" + "="*70 + "╝")
    
    service_handlers = {
        "Views": process_views_service,
        "Hearts": process_hearts_service,
        "Comments Hearts": process_comments_hearts_service,
        "Shares": process_shares_service,
        "Favorites": process_favorites_service,
        "Live Stream": process_live_stream_service,
        "Repost": process_repost_service,
        "Followers": process_followers_service,
    }
    
    handler = service_handlers.get(service_name)
    if handler:
        return handler(driver, container)
    else:
        print(f"❌ Chưa hỗ trợ dịch vụ {service_name}")
        time.sleep(2)
        return "menu"

def check_main_menu(driver):
    try:
        menu_buttons = driver.find_elements(By.CSS_SELECTOR, ".t-followers-button, .t-hearts-button, .t-views-button")
        return len(menu_buttons) > 0
    except:
        return False

def reload_page(driver):
    driver.refresh()
    time.sleep(5)
    remove_freestar_dialog(driver)
    handle_ad_blocking(driver)

def display_services_menu(driver):
    clear_screen()
    print_header()
    
    services = get_services_list(driver)
    
    if not services:
        print("⚠️ Không tìm thấy menu dịch vụ")
        print("💡 Đang thử tải lại trang...")
        driver.refresh()
        time.sleep(5)
        services = get_services_list(driver)
        
        if not services:
            print("❌ Vẫn không tìm thấy dịch vụ. Vui lòng kiểm tra kết nối.")
            return False, []

    RED = '\033[91m'
    GREEN = '\033[92m'
    RESET = '\033[0m'
    GOLD_PINK = '\033[38;2;255;255;220m'
    YELLOW = '\033[38;2;255;230;100m'
    GREEN_STATUS = Colors.GREEN_LIGHT
    RED_STATUS = Colors.RED_LIGHT 

    BORDER1 = Colors.PURPLE6
    BORDER2 = Colors.PURPLE5
    BORDER3 = Colors.PURPLE4
    BORDER4 = Colors.PURPLE3
    BORDER5 = Colors.PURPLE2
    BORDER6 = Colors.PURPLE1

    NAME_WIDTH = 20
    menu_text = f"{GOLD_PINK}○ › Tik Tok ‹ ○{Colors.RESET}"
    print(f"{BORDER6}╔{'═'*15}{Colors.RESET}{' '*5}{menu_text}{Colors.RESET}{' '*5}{BORDER6}{'═'*15}╗{Colors.RESET}")
    first = services[0]
    idx = 1
    name_display = first['name']
    detail_display = first['detail']
    if "soon" in detail_display.lower():
        detail_display = f"{RED_STATUS}soon will be update{RESET}"
    elif "hour" in detail_display.lower():
        detail_display = f"{GREEN_STATUS}{detail_display}{RESET}"
    print(f"{BORDER5} {Colors.RESET}   {Colors.PURPLE1}[{idx}]{Colors.RESET} {YELLOW}{name_display:<{NAME_WIDTH}}│    {GREEN_STATUS}{detail_display:<31} {BORDER5} {Colors.RESET}")
    second = services[1]
    idx = 2
    name_display = second['name']
    detail_display = second['detail']
    if "soon" in detail_display.lower():
        detail_display = f"{RED_STATUS}soon will be update{Colors.RESET}"
    elif "hour" in detail_display.lower():
        detail_display = f"{GREEN_STATUS}{detail_display}{Colors.RESET}"
    print(f"{BORDER4} {Colors.RESET}   {Colors.PURPLE2}[{idx}]{Colors.RESET} {YELLOW}{name_display:<{NAME_WIDTH-1}} │    {GREEN_STATUS}{detail_display:<31} {BORDER4} {Colors.RESET}")
    for idx, service in enumerate(services[2:-2], 3):
        name_display = service['name']
        detail_display = service['detail']
        
        if "soon" in detail_display.lower():
            detail_display = f"{RED_STATUS}soon will be update{RESET}"
        elif "hour" in detail_display.lower():
            detail_display = f"{GREEN_STATUS}{detail_display}{RESET}"
        
        print(f"    {Colors.PURPLE3}[{idx}]{Colors.RESET} {YELLOW}{name_display:<{NAME_WIDTH-1}} │    {GREEN_STATUS}{detail_display}")
    seventh = services[-2]
    idx = len(services) - 1
    name_display = seventh['name']
    detail_display = seventh['detail']
    if "soon" in detail_display.lower():
        detail_display = f"{RED_STATUS}soon will be update{RESET}"
    elif "hour" in detail_display.lower():
        detail_display = f"{GREEN_STATUS}{detail_display}{RESET}"
    print(f"{BORDER3} {Colors.RESET}   {Colors.PURPLE5}[{idx}]{Colors.RESET} {YELLOW}{name_display:<{NAME_WIDTH-1}} │    {GREEN_STATUS}{detail_display:<31} {BORDER2} {Colors.RESET}")
    last = services[-1]
    idx = len(services)
    name_display = last['name']
    detail_display = last['detail']
    if "soon" in detail_display.lower():
        detail_display = f"{RED_STATUS}soon will be update{RESET}"
    elif "hour" in detail_display.lower():
        detail_display = f"{GREEN_STATUS}{detail_display}{RESET}"
    print(f"{BORDER2} {Colors.RESET}   {Colors.PURPLE6}[{idx}]{Colors.RESET} {YELLOW}{name_display:<{NAME_WIDTH}}│    {GREEN_STATUS}{detail_display:<31} {BORDER1} {Colors.RESET}")
    print(f"{BORDER1}╚{'═'*15}{Colors.RESET}{' '*25}{BORDER1}{'═'*15}╝{Colors.RESET}")
    print(f"\n{Colors.PURPLE1}╔{'═'*14}{Colors.RESET}{' '*5}{GOLD_PINK}○ › Face book ‹ ○{Colors.RESET}{' '*5}{Colors.PURPLE1}{'═'*14}╗{Colors.RESET}")
    print(f"    {BORDER5}[9]{Colors.RESET} {YELLOW}Reg Page Profile{' ':<3} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER4}[10]{Colors.RESET} {YELLOW}Buff Share{' ':<8} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER3}[11]{Colors.RESET} {YELLOW}Up Avatar{' ':<9} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER2}[12]{Colors.RESET} {YELLOW}Buff Follow{' ':<7} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"{BORDER1}╚{'═'*14}{Colors.RESET}{' '*27}{BORDER1}{'═'*14}╝{Colors.RESET}")
    print(f"\n{Colors.PURPLE1}╔{'═'*14}{Colors.RESET}{' '*5}{GOLD_PINK}○ › Tải Video ‹ ○{Colors.RESET}{' '*5}{Colors.PURPLE1}{'═'*14}╗{Colors.RESET}")
    print(f"    {BORDER5}[13]{Colors.RESET} {YELLOW}TikTok{' ':<12} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER4}[14]{Colors.RESET} {YELLOW}YouTube{' ':<11} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER3}[15]{Colors.RESET} {YELLOW}Facebook{' ':<10} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER2}[16]{Colors.RESET} {YELLOW}Instagram{' ':9} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"{BORDER1}╚{'═'*14}{Colors.RESET}{' '*27}{BORDER1}{'═'*14}╝{Colors.RESET}")
    print(f"\n{Colors.PURPLE1}╔{'═'*14}{Colors.RESET}{' '*5}{GOLD_PINK}○ › ENC PYTHON ‹ ○{Colors.RESET}{' '*5}{Colors.PURPLE1}{'═'*14}╗{Colors.RESET}")
    print(f"    {BORDER5}[17]{Colors.RESET} {YELLOW}Enc Python Simple{' ':<1} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER4}[18]{Colors.RESET} {YELLOW}Enc Pymeo{' ':<9} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER3}[19]{Colors.RESET} {YELLOW}Enc Obsidian{' ':<6} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER2}[20]{Colors.RESET} {YELLOW}Enc Pyhydra{' ':<7} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"{BORDER1}╚{'═'*14}{Colors.RESET}{' '*27}{BORDER1}{'═'*14}╝{Colors.RESET}")
    print(f"\n{Colors.PURPLE1}╔{'═'*20}{Colors.RESET}{' '*5}{GOLD_PINK}○ › Free Fire ‹ ○{Colors.RESET}{' '*5}{Colors.PURPLE1}{'═'*20}╗{Colors.RESET}")
    print(f"    {BORDER5}[21]{Colors.RESET} {YELLOW}Check Recovery Mail{' ':<14} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER5}[22]{Colors.RESET} {YELLOW}Check Linked Platforms{' ':11} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER5}[23]{Colors.RESET} {YELLOW}Add Recovery Mail{' ':<16} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER4}[24]{Colors.RESET} {YELLOW}Cancel Recovery Mail{' ':<13} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER4}[25]{Colors.RESET} {YELLOW}Unbind Mail{' ':<22} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER4}[26]{Colors.RESET} {YELLOW}Change Bind Mail{' ':<17} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER3}[27]{Colors.RESET} {YELLOW}Revoke Access Token{' ':<14} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER3}[28]{Colors.RESET} {YELLOW}Eat to Access Token{' ':<14} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER3}[29]{Colors.RESET} {YELLOW}Band Account 7Days [VIP]{' ':<9} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"    {BORDER2}[30]{Colors.RESET} {YELLOW}Band Account Permanent [PREMIUM]{' ':<1} │    {GREEN_STATUS}Updated & Working{Colors.RESET}")
    print(f"{BORDER1}╚{'═'*20}{Colors.RESET}{' '*27}{BORDER1}{'═'*20}╝{Colors.RESET}")
    
    return True, services


def select_service(services):
    while True:
        try:
            choice = input(f"\n{Rainbow.text('Nhập số dịch vụ: ')}").strip()

            if choice in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                choice_num = int(choice)
                if choice_num <= len(services):
                    selected = services[choice_num - 1]
                    if selected['disabled']:
                        print(f"{Colors.RED_LIGHT}❌ Dịch vụ '{selected['name']}' đang cập nhật!{Colors.RESET}")
                        continue
                    return selected
                else:
                    print(f"{Colors.RED_LIGHT}❌ Không tìm thấy dịch vụ!{Colors.RESET}")
                    continue

            if choice in ["9", "10", "11", "12"]:
                facebook_services = {
                    "9": {"name": "RegPP5", "class": "regpp5"},
                    "10": {"name": "Buff Share", "class": "buffshare"},
                    "11": {"name": "Up Avatar", "class": "upavatar"},
                    "12": {"name": "Buff Follow", "class": "bufffollow"}
                }
                selected = facebook_services.get(choice)
                if selected:
                    service_obj = {
                        "name": selected["name"],
                        "disabled": False,
                        "class": selected["class"]
                    }
                    return service_obj
                else:
                    print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
                    continue

            if choice == "13":
                result = download_tiktok()
                if result == "main_menu":
                    return None
                continue
            elif choice == "14":
                result = download_youtube()
                if result == "main_menu":
                    return None
                continue
            elif choice == "15":
                result = download_facebook()
                if result == "main_menu":
                    return None
                continue
            elif choice == "16":
                result = download_instagram()
                if result == "main_menu":
                    return None
                continue

            if choice in ["17", "18", "19", "20"]:
                enc_services = {
                    "17": {"name": "Enc Python Simple", "class": "enc_simple"},
                    "18": {"name": "Enc Pymeo", "class": "enc_pymeo"},
                    "19": {"name": "Enc Obsidian", "class": "enc_obsidian"},
                    "20": {"name": "Enc Pyhydra", "class": "enc_pyhydra"}
                }
                selected = enc_services.get(choice)
                if selected:
                    service_obj = {
                        "name": selected["name"],
                        "disabled": False,
                        "class": selected["class"]
                    }
                    return service_obj
                else:
                    print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
                    continue

            if choice in ["21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]:
                freefire_services = {
                    "21": {"name": "Check Recovery Mail", "class": "check_recovery_mail"},
                    "22": {"name": "Check Linked Platforms", "class": "check_linked_platforms"},
                    "23": {"name": "Add Recovery Mail", "class": "add_recovery_mail"},
                    "24": {"name": "Cancel Recovery Mail", "class": "cancel_recovery_mail"},
                    "25": {"name": "Unbind Mail", "class": "unbind_mail"},
                    "26": {"name": "Change Bind Mail", "class": "change_bind_mail"},
                    "27": {"name": "Revoke Access Token", "class": "revoke_access_token"},
                    "28": {"name": "Eat to Access Token", "class": "eat_access_token"},
                    "29": {"name": "Band Account 7Days [VIP]", "class": "band_account_7days"},
                    "30": {"name": "Band Account Permanent [PREMIUM]", "class": "band_account_permanent"}
                }
                selected = freefire_services.get(choice)
                if selected:
                    service_obj = {
                        "name": selected["name"],
                        "disabled": False,
                        "class": selected["class"]
                    }
                    return service_obj
                else:
                    print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
                    continue
            
            if not choice.isdigit():
                print(f"{Colors.RED_LIGHT}❌ Vui lòng nhập số!{Colors.RESET}")
                continue
            
            choice_num = int(choice)
            if choice_num < 1 or choice_num > len(services) + 3:
                print(f"{Colors.RED_LIGHT}❌ Chỉ có 30 dịch vụ! Vui lòng chọn từ 1-30{Colors.RESET}")
                continue
            
            selected = services[choice_num - 1]
            
            if selected['disabled']:
                print(f"{Colors.RED_LIGHT}❌ Dịch vụ '{selected['name']}' đang cập nhật! Vui lòng chọn dịch vụ khác.{Colors.RESET}")
                continue
            
            return selected
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.WHITE_BRIGHT}Thoát chương trình...{Colors.RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"{Colors.RED_LIGHT}❌ Lỗi: {e}{Colors.RESET}")

def run_tool():
    global driver_instance, popup_killer_running
    driver = None
    
    clear_screen()
    show_loading_banner()
    show_loading_animation()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gcm')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--log-level=3')
    options.add_argument('--silent')
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2,
    }
    options.add_experimental_option("prefs", prefs)
    chrome_service = Service()
    chrome_service.creation_flags = subprocess.CREATE_NO_WINDOW
    try:
        driver = webdriver.Chrome(service=chrome_service, options=options)
        driver_instance = driver
        start_popup_killer(driver)
    except Exception as e:
        print(f"❌ Không thể khởi tạo ChromeDriver: {e}")
        return
    
    attempt = 1
    max_attempts = 50
    success = False
    
    while attempt <= max_attempts and not success and not is_shutting_down:
        if attempt == 1:
            driver.get("https://zefoy.com/")
            time.sleep(5)
            remove_freestar_dialog(driver)
            handle_ad_blocking(driver)
        else:
            reload_page(driver)
        
        if is_shutting_down:
            break
            
        img_captcha = get_captcha_from_browser(driver)
        if not img_captcha:
            attempt += 1
            continue
        
        img_processed = preprocess_image(img_captcha)
        captcha_result = solve_captcha_from_image(img_processed)
        
        if not captcha_result:
            attempt += 1
            continue
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        captcha_input = None
        try:
            captcha_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control[placeholder='Enter the word']"))
            )
        except:
            try:
                captcha_input = driver.find_element(By.ID, "captchatoken")
            except:
                try:
                    captcha_input = driver.find_element(By.XPATH, "//input[@type='search']")
                except:
                    pass
        
        if not captcha_input:
            attempt += 1
            continue
        
        captcha_input.clear()
        captcha_input.send_keys(captcha_result)
        time.sleep(1)
        
        submit_btn = None
        try:
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        except:
            try:
                submit_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'submit-captcha')]")
            except:
                pass
        
        if submit_btn:
            try:
                submit_btn.click()
            except:
                driver.execute_script("""
                    document.getElementById('ad_position_box')?.remove();
                    document.querySelectorAll('#dismiss-button, .close-button-outer, .close-button').forEach(btn => btn.click());
                """)
                time.sleep(0.5)
                try:
                    submit_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", submit_btn)
        else:
            captcha_input.submit()
        
        time.sleep(5)
        handle_ad_blocking(driver)
        
        if check_main_menu(driver):
            success = True
            break
        else:
            if check_captcha_error(driver):
                attempt += 1
                continue
            else:
                attempt += 1
                continue
    
    if success and not is_shutting_down:
        clear_screen()
        while not is_shutting_down:
            try:
                menu_ok, services = display_services_menu(driver)
                
                if not menu_ok:
                    print("⚠️ Không thể tải menu, thử lại...")
                    time.sleep(3)
                    driver.refresh()
                    time.sleep(5)
                    continue
                
                selected_service = select_service(services)
                
                if selected_service is None:
                    print("\nThoát chương trình...")
                    break
                enc_services = {
                    "enc_simple": process_enc_python_simple,
                    "enc_pymeo": process_enc_pymeo,
                    "enc_obsidian": process_enc_obsidian,
                    "enc_pyhydra": process_enc_pyhydra
                }
                
                if selected_service['class'] in enc_services:
                    handler = enc_services[selected_service['class']]
                    if handler:
                        result = handler(driver, None)
                        if result == "quit":
                            print("\nThoát chương trình...")
                            break
                        elif result == "menu":
                            continue
                    else:
                        print(f"\n{Colors.YELLOW_LIGHT}🔄 Đang xử lý dịch vụ: {selected_service['name']}{Colors.RESET}")
                        print(f"{Colors.RED_LIGHT}❌ Dịch vụ đang được phát triển!{Colors.RESET}")
                        time.sleep(3)
                        continue

                freefire_services = {
                    "check_recovery_mail": process_check_recovery_mail,
                    "check_linked_platforms": process_check_linked_platforms,
                    "add_recovery_mail": process_add_recovery_mail,
                    "cancel_recovery_mail": process_cancel_recovery_mail,
                    "unbind_mail": process_unbind_mail,
                    "change_bind_mail": process_change_bind_mail,
                    "revoke_access_token": process_revoke_access_token,
                    "eat_access_token": process_eat_access_token,
                    "band_account_7days": process_band_account_7days,
                    "band_account_permanent": process_band_account_permanent
                }
                
                if selected_service['class'] in freefire_services:
                    handler = freefire_services[selected_service['class']]
                    if handler:
                        result = handler(driver, None)
                        if result == "quit":
                            print("\nThoát chương trình...")
                            break
                        elif result == "menu":
                            continue
                    else:
                        print(f"\n{Colors.YELLOW_LIGHT}🔄 Đang xử lý dịch vụ: {selected_service['name']}{Colors.RESET}")
                        print(f"{Colors.RED_LIGHT}❌ Dịch vụ đang được phát triển!{Colors.RESET}")
                        time.sleep(3)
                        continue
                
                facebook_services = ["regpp5", "buffshare", "upavatar", "bufffollow"]
                if selected_service['class'] in facebook_services:
                    result = process_service(driver, selected_service['name'], selected_service['class'])
                    if result == "quit":
                        print("\nThoát chương trình...")
                        break
                    elif result == "menu":
                        continue
                else:
                    if click_service_button(driver, selected_service):
                        result = process_service(driver, selected_service['name'], selected_service['class'])
                        
                        if result == "quit":
                            print("\nThoát chương trình...")
                            break
                        elif result == "menu":
                            continue
                    else:
                        print("❌ Không thể click vào dịch vụ, thử lại...")
                        time.sleep(2)
                        continue
            except KeyboardInterrupt:
                signal_handler(None, None)
                break
            except Exception as e:
                if not is_shutting_down:
                    print(f"❌ Lỗi: {e}")
                    time.sleep(2)
                continue
    elif not success and not is_shutting_down:
        clear_screen()
        print("="*58)
        print("❌ THẤT BẠI")
        print("="*58)
        print(f"\n❌ Không thể đăng nhập sau {max_attempts} lần thử")
        time.sleep(5)
    
    popup_killer_running = False
    if driver:
        try:
            driver.quit()
        except:
            pass
    clear_screen()
    print(" HẸN GẶP LẠI!")

def click_service_button(driver, service):
    try:
        handle_ad_blocking(driver)
        service['button'].click()
        time.sleep(3)
        handle_ad_blocking(driver)
        return True
    except Exception as e:
        print(f"❌ Lỗi khi click: {e}")
        return False

def main():
    global driver_instance, popup_killer_running
    
    while True:
        clear_screen()
        show_loading_banner()
        print_info_table()
        
        print(f"\n{Rainbow.text('[+] Nhập số [1] Vào Tool')}")
        print(f"{Rainbow.text('[+] Nhập số [0] Thoát Tool')}")
        print()
        
        choice = input(f"{Rainbow.text('Nhập lựa chọn: ')}").strip()
        
        if choice == "1":
            if key_auth_screen():
                run_tool()
            else:
                print(f"{Colors.RED_LIGHT}❌ Xác thực thất bại!{Colors.RESET}")
                time.sleep(2)
                continue
                
        elif choice == "0":
            print(f"\n{Colors.GREEN_LIGHT}HẸN GẶP LẠI!{Colors.RESET}")
            time.sleep(1)
            clear_screen()
            print(f"{Colors.YELLOW_LIGHT}Tool đã thoát!{Colors.RESET}")
            sys.exit(0)
        else:
            print(f"{Colors.RED_LIGHT}❌ Lựa chọn không hợp lệ!{Colors.RESET}")
            time.sleep(2)
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colors.YELLOW_LIGHT}ĐANG TẮT BẰNG PHÍM TẮT!{Colors.RESET}")
        os._exit(0)
    except SystemExit:
        os.system('cls' if os.name == 'nt' else 'clear')
        os._exit(0)
    except Exception as e:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colors.RED_LIGHT}❌ Lỗi: {e}{Colors.RESET}")
        os._exit(1)
