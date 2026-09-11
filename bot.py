#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok Share Bot V11 - PRO Edition
أداة قوية لزيادة مشاركات تيكتوك
"""

import os
import re
import time
import random
import hashlib
import requests
import asyncio
import logging
import json
import concurrent.futures
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توكن البوت
BOT_TOKEN = os.getenv("BOT_TOKEN", "8525297145:AAEn1YFZVuUHa5vF2Tp__SSFkqeJQYC0A3g")

# تعطيل تحذيرات SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Thread pool للطلبات المتوازية
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)


class Gorgon:
    """توليد توقيعات X-Gorgon و X-Khronos"""
    
    def __init__(self, params: str, data: str, cookies: str, unix: int):
        self.unix = unix
        self.params = params
        self.data = data
        self.cookies = cookies
    
    def hash(self, data: str) -> str:
        try:
            return hashlib.md5(data.encode()).hexdigest()
        except:
            return hashlib.md5(data).hexdigest()
    
    def get_base_string(self) -> str:
        base_str = self.hash(self.params)
        base_str = base_str + self.hash(self.data) if self.data else base_str + '0' * 32
        base_str = base_str + self.hash(self.cookies) if self.cookies else base_str + '0' * 32
        return base_str
    
    def get_value(self) -> dict:
        base_str = self.get_base_string()
        return self.encrypt(base_str)
    
    def encrypt(self, data: str) -> dict:
        unix = self.unix
        length = 20
        key = [223, 119, 185, 64, 185, 155, 132, 131, 209, 185, 
               203, 209, 247, 194, 185, 133, 195, 208, 251, 195]
        
        param_list = []
        for i in range(0, 12, 4):
            temp = data[8 * i:8 * (i + 1)]
            for j in range(4):
                H = int(temp[j * 2:(j + 1) * 2], 16)
                param_list.append(H)
        
        param_list.extend([0, 6, 11, 28])
        H = int(hex(unix), 16)
        param_list.append((H & 4278190080) >> 24)
        param_list.append((H & 16711680) >> 16)
        param_list.append((H & 65280) >> 8)
        param_list.append((H & 255) >> 0)
        
        eor_result_list = []
        for (A, B) in zip(param_list, key):
            eor_result_list.append(A ^ B)
        
        for i in range(length):
            C = self.reverse(eor_result_list[i])
            D = eor_result_list[(i + 1) % length]
            E = C ^ D
            F = self.rbit_algorithm(E)
            H = (F ^ 4294967295 ^ length) & 255
            eor_result_list[i] = H
        
        result = ''
        for param in eor_result_list:
            result += self.hex_string(param)
        
        return {
            'X-Gorgon': '0404b0d30000' + result,
            'X-Khronos': str(unix)
        }
    
    def rbit_algorithm(self, num):
        result = ''
        tmp_string = bin(num)[2:]
        while len(tmp_string) < 8:
            tmp_string = '0' + tmp_string
        for i in range(0, 8):
            result = result + tmp_string[7 - i]
        return int(result, 2)
    
    def hex_string(self, num):
        tmp_string = hex(num)[2:]
        if len(tmp_string) < 2:
            tmp_string = '0' + tmp_string
        return tmp_string
    
    def reverse(self, num):
        tmp_string = self.hex_string(num)
        return int(tmp_string[1:] + tmp_string[:1], 16)


class ProxyManager:
    """مدير البروكسيات المتقدم"""
    
    def __init__(self):
        self.proxies = []
        self.failed_proxies = []
        self.proxy_stats = {}
    
    def add_proxy(self, proxy_str: str) -> tuple:
        proxy_str = proxy_str.strip()
        parts = proxy_str.split(':')
        
        if len(parts) >= 4:
            proxy = {
                'ip': parts[0],
                'port': parts[1],
                'user': parts[2],
                'pass': ':'.join(parts[3:]),
            }
        elif len(parts) == 2:
            proxy = {
                'ip': parts[0],
                'port': parts[1],
                'user': None,
                'pass': None,
            }
        else:
            return (False, "❌ صيغة خاطئة!\n\nاستخدم: `IP:PORT:USER:PASS`")
        
        key = f"{proxy['ip']}:{proxy['port']}"
        for p in self.proxies:
            if f"{p['ip']}:{p['port']}" == key:
                return (False, "⚠️ البروكسي موجود مسبقاً!")
        
        self.proxies.append(proxy)
        self.proxy_stats[key] = {'success': 0, 'fail': 0}
        return (True, f"✅ تمت الإضافة!\n\n🌐 `{key}`\n📦 المجموع: {len(self.proxies)}")
    
    def get_proxy_url(self, proxy: dict) -> dict:
        if proxy['user'] and proxy['pass']:
            url = f"http://{proxy['user']}:{proxy['pass']}@{proxy['ip']}:{proxy['port']}"
        else:
            url = f"http://{proxy['ip']}:{proxy['port']}"
        return {'http': url, 'https': url}
    
    def get_random_proxy(self) -> tuple:
        if self.proxies:
            proxy = random.choice(self.proxies)
            return (proxy, self.get_proxy_url(proxy))
        return (None, None)
    
    def mark_success(self, proxy):
        if proxy:
            key = f"{proxy['ip']}:{proxy['port']}"
            if key in self.proxy_stats:
                self.proxy_stats[key]['success'] += 1
    
    def mark_fail(self, proxy):
        if proxy:
            key = f"{proxy['ip']}:{proxy['port']}"
            if key in self.proxy_stats:
                self.proxy_stats[key]['fail'] += 1
                # حذف البروكسي إذا فشل أكثر من 10 مرات متتالية
                if self.proxy_stats[key]['fail'] > 10 and self.proxy_stats[key]['success'] == 0:
                    self.proxies = [p for p in self.proxies if f"{p['ip']}:{p['port']}" != key]
                    self.failed_proxies.append(key)
    
    def get_count(self):
        return len(self.proxies)
    
    def get_stats(self):
        return f"✅ شغالة: {len(self.proxies)} | ❌ فشلت: {len(self.failed_proxies)}"
    
    def clear_all(self):
        self.proxies = []
        self.failed_proxies = []
        self.proxy_stats = {}


class SessionManager:
    """مدير الحسابات المتقدم"""
    
    def __init__(self):
        # الحسابات الافتراضية
        self.accounts = [
            {"session_id": "89845b2e5b6b8fd1211a3311a9111d28", "user_id": "313287288795504640", "username": "agus_plantabaja", "active": True},
            {"session_id": "f435bff62869a47e51ca7c262ef961f6", "user_id": "7459087661242139656", "username": "aqngfsnt0ef", "active": True},
            {"session_id": "fcfe941923f72b043aa530477631a7da", "user_id": "6891382117931336709", "username": "lpzsx.fds", "active": True},
            {"session_id": "7fc6af6ad17ce30d4266d43e23205ebc", "user_id": "7250647321838175238", "username": "xxxzeww3", "active": True},
            {"session_id": "e3ac9ab8886c0e031ca3e0724227740e", "user_id": "7163634145918436357", "username": "تقئ", "active": True},
        ]
        self.account_index = 0
        self.account_stats = {acc['username']: {'success': 0, 'fail': 0} for acc in self.accounts}
    
    def add_account(self, session_id: str, username: str = None, user_id: str = None):
        if not username:
            username = f"user_{len(self.accounts) + 1}"
        if not user_id:
            user_id = "0"
        
        # التحقق من عدم التكرار
        for acc in self.accounts:
            if acc['session_id'] == session_id:
                return (False, "⚠️ الحساب موجود مسبقاً!")
        
        self.accounts.append({
            "session_id": session_id,
            "user_id": user_id,
            "username": username,
            "active": True
        })
        self.account_stats[username] = {'success': 0, 'fail': 0}
        return (True, f"✅ تمت إضافة الحساب!\n\n👤 `{username}`\n📦 المجموع: {len(self.accounts)}")
    
    def get_next_account(self):
        active_accounts = [acc for acc in self.accounts if acc['active']]
        if not active_accounts:
            return None
        
        account = active_accounts[self.account_index % len(active_accounts)]
        self.account_index += 1
        return account
    
    def get_all_active(self):
        return [acc for acc in self.accounts if acc['active']]
    
    def mark_success(self, username):
        if username in self.account_stats:
            self.account_stats[username]['success'] += 1
    
    def mark_fail(self, username):
        if username in self.account_stats:
            self.account_stats[username]['fail'] += 1
            # تعطيل الحساب إذا فشل أكثر من 20 مرة متتالية
            if self.account_stats[username]['fail'] > 20 and self.account_stats[username]['success'] == 0:
                for acc in self.accounts:
                    if acc['username'] == username:
                        acc['active'] = False
                        break
    
    def get_count(self):
        return len([acc for acc in self.accounts if acc['active']])
    
    def get_stats(self):
        text = "📊 *حالة الحسابات:*\n\n"
        for acc in self.accounts:
            stats = self.account_stats.get(acc['username'], {'success': 0, 'fail': 0})
            status = "✅" if acc['active'] else "❌"
            text += f"{status} `{acc['username']}` - ✓{stats['success']} ✗{stats['fail']}\n"
        return text


class TikTokEngine:
    """محرك المشاركات القوي"""
    
    def __init__(self, proxy_manager: ProxyManager, session_manager: SessionManager):
        self.proxy_manager = proxy_manager
        self.session_manager = session_manager
        
        # أجهزة متنوعة
        self.devices = [
            {"model": "SM-S908E", "brand": "samsung", "os": "13", "dpi": "480", "resolution": "1440*3200"},
            {"model": "SM-G998B", "brand": "samsung", "os": "13", "dpi": "420", "resolution": "1440*3200"},
            {"model": "SM-S918B", "brand": "samsung", "os": "14", "dpi": "480", "resolution": "1440*3088"},
            {"model": "Pixel 7 Pro", "brand": "google", "os": "14", "dpi": "512", "resolution": "1440*3120"},
            {"model": "Pixel 8 Pro", "brand": "google", "os": "14", "dpi": "480", "resolution": "1344*2992"},
            {"model": "2201116SG", "brand": "xiaomi", "os": "13", "dpi": "440", "resolution": "1220*2712"},
            {"model": "23127PN0CC", "brand": "xiaomi", "os": "14", "dpi": "480", "resolution": "1440*3200"},
            {"model": "CPH2449", "brand": "oppo", "os": "13", "dpi": "480", "resolution": "1080*2400"},
            {"model": "V2227A", "brand": "vivo", "os": "13", "dpi": "480", "resolution": "1080*2400"},
            {"model": "LE2121", "brand": "oneplus", "os": "13", "dpi": "480", "resolution": "1440*3216"},
        ]
        
        # نقاط نهاية API
        self.endpoints = [
            "https://api16-normal-c-useast1a.tiktokv.com",
            "https://api16-normal-c-useast2a.tiktokv.com",
            "https://api22-normal-c-useast2a.tiktokv.com",
            "https://api19-normal-c-useast1a.tiktokv.com",
            "https://api16-va.tiktokv.com",
        ]
        
        # إصدارات التطبيق
        self.app_versions = [
            {"version": "350103", "manifest": "2023501030"},
            {"version": "340205", "manifest": "2023402050"},
            {"version": "330106", "manifest": "2023301060"},
            {"version": "320305", "manifest": "2023203050"},
        ]
    
    def extract_video_id(self, url: str) -> str:
        match = re.findall(r'(\d{18,19})', url)
        if match:
            return match[0]
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36'}
            response = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
            match = re.findall(r'(\d{18,19})', response.url)
            if match:
                return match[0]
        except:
            pass
        
        return None
    
    def send_share(self, video_id: str, account: dict = None, proxy_info: tuple = None) -> dict:
        """إرسال مشاركة واحدة"""
        
        if not account:
            account = self.session_manager.get_next_account()
        if not account:
            return {"success": False, "account": "N/A", "error": "No active accounts"}
        
        proxy_obj, proxy_url = proxy_info if proxy_info else (None, None)
        if not proxy_url:
            proxy_obj, proxy_url = self.proxy_manager.get_random_proxy()
        
        try:
            device = random.choice(self.devices)
            endpoint = random.choice(self.endpoints)
            app_ver = random.choice(self.app_versions)
            
            device_id = ''.join([str(random.randint(0, 9)) for _ in range(19)])
            iid = ''.join([str(random.randint(0, 9)) for _ in range(19)])
            openudid = ''.join(random.choices('0123456789abcdef', k=16))
            uuid = ''.join(random.choices('0123456789abcdef', k=32))
            ts = int(time.time())
            
            params = (
                f"device_id={device_id}"
                f"&iid={iid}"
                f"&device_type={device['model']}"
                f"&device_brand={device['brand']}"
                f"&os_version={device['os']}"
                f"&openudid={openudid}"
                f"&uuid={uuid}"
                f"&app_name=musical_ly"
                f"&version_code={app_ver['version']}"
                f"&manifest_version_code={app_ver['manifest']}"
                f"&device_platform=android"
                f"&resolution={device['resolution']}"
                f"&dpi={device['dpi']}"
                f"&aid=1233"
                f"&ts={ts}"
                f"&_rticket={ts*1000}"
                f"&channel=googleplay"
                f"&ac=wifi"
                f"&sys_region=US"
                f"&app_language=en"
                f"&language=en"
                f"&timezone_name=America/New_York"
                f"&timezone_offset=-18000"
                f"&carrier_region=US"
            )
            
            payload = f"item_id={video_id}&share_delta=1"
            cookie = f"sessionid={account['session_id']}"
            
            sig = Gorgon(params=params, data=payload, cookies=cookie, unix=ts).get_value()
            x_ss_stub = hashlib.md5(payload.encode()).hexdigest().upper()
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'User-Agent': f'com.zhiliaoapp.musically/{app_ver["manifest"]} (Linux; U; Android {device["os"]}; en_US; {device["model"]}; Build/TP1A.220624.014; Cronet/TTNetVersion:b4d74d15 2023-04-21 QuicVersion:0144d358 2023-03-10)',
                'X-Gorgon': sig['X-Gorgon'],
                'X-Khronos': sig['X-Khronos'],
                'X-SS-Stub': x_ss_stub,
                'X-Tt-Token': account['session_id'],
                'Cookie': cookie,
                'Accept-Encoding': 'gzip, deflate',
                'X-SS-REQ-TICKET': str(ts * 1000),
                'sdk-version': '2',
                'passport-sdk-version': '19',
            }
            
            response = requests.post(
                f"{endpoint}/aweme/v1/aweme/stats/?{params}",
                data=payload,
                headers=headers,
                proxies=proxy_url,
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    status_code = data.get('status_code', -1)
                    
                    if status_code == 0 or 'log_pb' in data:
                        self.session_manager.mark_success(account['username'])
                        self.proxy_manager.mark_success(proxy_obj)
                        return {"success": True, "account": account['username'], "error": None}
                    else:
                        self.session_manager.mark_fail(account['username'])
                        return {"success": False, "account": account['username'], "error": f"Code: {status_code}"}
                except:
                    self.session_manager.mark_success(account['username'])
                    return {"success": True, "account": account['username'], "error": None}
            else:
                return {"success": False, "account": account['username'], "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.ProxyError:
            self.proxy_manager.mark_fail(proxy_obj)
            return {"success": False, "account": account['username'], "error": "Proxy Error"}
        except requests.exceptions.Timeout:
            return {"success": False, "account": account['username'], "error": "Timeout"}
        except Exception as e:
            return {"success": False, "account": account['username'], "error": str(e)[:30]}


# إنشاء المدراء
proxy_manager = ProxyManager()
session_manager = SessionManager()
engine = TikTokEngine(proxy_manager, session_manager)

# تخزين جلسات المستخدمين
user_sessions = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    welcome_text = """
🚀 *TikTok Share Bot V11 PRO*

📌 *الاستخدام:*
أرسل رابط فيديو → اضغط تشغيل

📋 *الأوامر:*
/start - القائمة الرئيسية
/stop - إيقاف المشاركات
/status - حالة الحسابات
/addproxy - إضافة بروكسي
/addsession - إضافة حساب
/proxies - قائمة البروكسيات
/speed - تغيير السرعة
/parallel - تفعيل/تعطيل التوازي

⚡ *الميزات:*
• طلبات متوازية (2-3 في نفس الوقت)
• 10 أنواع أجهزة مختلفة
• 5 سيرفرات API
• 4 إصدارات تطبيق
• إدارة بروكسيات ذكية
• إدارة حسابات متقدمة

👥 الحسابات: """ + str(session_manager.get_count()) + """
🌐 البروكسيات: """ + str(proxy_manager.get_count()) + """

✅ أرسل رابط الفيديو للبدء!
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions and user_sessions[user_id].get('running'):
        user_sessions[user_id]['running'] = False
        await update.message.reply_text("⏹ *تم الإيقاف!*", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ لا توجد مشاركات قيد التشغيل.", parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = session_manager.get_stats()
    stats += f"\n🌐 {proxy_manager.get_stats()}"
    await update.message.reply_text(stats, parse_mode='Markdown')


async def addproxy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        proxy_str = ' '.join(context.args)
        success, msg = proxy_manager.add_proxy(proxy_str)
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "📝 *إضافة بروكسي:*\n\n`/addproxy IP:PORT:USER:PASS`",
            parse_mode='Markdown'
        )


async def addsession_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        session_id = context.args[0]
        username = context.args[1] if len(context.args) > 1 else None
        success, msg = session_manager.add_account(session_id, username)
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "📝 *إضافة حساب:*\n\n`/addsession SESSION_ID [USERNAME]`",
            parse_mode='Markdown'
        )


async def proxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"📊 *البروكسيات:*\n\n{proxy_manager.get_stats()}"
    await update.message.reply_text(text, parse_mode='Markdown')


async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    if context.args:
        try:
            delay = float(context.args[0])
            if delay < 1:
                delay = 1
            elif delay > 10:
                delay = 10
            user_sessions[user_id]['delay'] = delay
            await update.message.reply_text(f"⏱ *تم تغيير التأخير إلى {delay} ثانية*", parse_mode='Markdown')
        except:
            await update.message.reply_text("❌ أدخل رقم صحيح (1-10)", parse_mode='Markdown')
    else:
        current = user_sessions[user_id].get('delay', 3)
        await update.message.reply_text(
            f"⏱ *التأخير الحالي:* {current} ثانية\n\n"
            f"للتغيير: `/speed 2`",
            parse_mode='Markdown'
        )


async def parallel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    current = user_sessions[user_id].get('parallel', 2)
    
    if context.args:
        try:
            parallel = int(context.args[0])
            if parallel < 1:
                parallel = 1
            elif parallel > 5:
                parallel = 5
            user_sessions[user_id]['parallel'] = parallel
            await update.message.reply_text(f"🚀 *تم تغيير التوازي إلى {parallel} طلبات*", parse_mode='Markdown')
        except:
            await update.message.reply_text("❌ أدخل رقم صحيح (1-5)", parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"🚀 *التوازي الحالي:* {current} طلبات\n\n"
            f"للتغيير: `/parallel 3`",
            parse_mode='Markdown'
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if 'tiktok.com' in text or 'tiktok' in text.lower():
        video_id = engine.extract_video_id(text)
        
        if not video_id:
            await update.message.reply_text("❌ *لم يتم العثور على الفيديو!*", parse_mode='Markdown')
            return
        
        if user_id in user_sessions:
            user_sessions[user_id]['running'] = False
            await asyncio.sleep(0.5)
        
        user_sessions[user_id] = {
            'video_id': video_id,
            'running': False,
            'success': 0,
            'fails': 0,
            'total': 0,
            'delay': user_sessions.get(user_id, {}).get('delay', 3),
            'parallel': user_sessions.get(user_id, {}).get('parallel', 2),
        }
        
        keyboard = [[
            InlineKeyboardButton("🚀 تشغيل", callback_data=f"start_{video_id}"),
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel")
        ]]
        
        await update.message.reply_text(
            f"🎬 *الفيديو جاهز!*\n\n"
            f"📌 ID: `{video_id}`\n"
            f"👥 الحسابات: {session_manager.get_count()}\n"
            f"🌐 البروكسيات: {proxy_manager.get_count()}\n"
            f"⏱ التأخير: {user_sessions[user_id]['delay']}s\n"
            f"🚀 التوازي: {user_sessions[user_id]['parallel']}\n\n"
            f"اضغط *تشغيل* للبدء:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "cancel":
        if user_id in user_sessions:
            user_sessions[user_id]['running'] = False
        await query.edit_message_text("❌ *تم الإلغاء.*", parse_mode='Markdown')
        return
    
    if data == "stop_shares":
        if user_id in user_sessions:
            user_sessions[user_id]['running'] = False
        return
    
    if data.startswith("start_"):
        video_id = data.replace("start_", "")
        
        if user_id not in user_sessions:
            await query.edit_message_text("❌ *انتهت الجلسة! أرسل الرابط مرة أخرى.*", parse_mode='Markdown')
            return
        
        user_sessions[user_id]['running'] = True
        user_sessions[user_id]['success'] = 0
        user_sessions[user_id]['fails'] = 0
        user_sessions[user_id]['total'] = 0
        user_sessions[user_id]['video_id'] = video_id
        
        keyboard = [[InlineKeyboardButton("⏹ إيقاف", callback_data="stop_shares")]]
        
        await query.edit_message_text(
            f"🚀 *جاري الإرسال...*\n\n"
            f"📌 `{video_id}`\n"
            f"✅ نجاح: 0\n"
            f"❌ فشل: 0\n"
            f"📊 المجموع: 0",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        asyncio.create_task(share_loop_pro(user_id, video_id, query.message))


async def share_loop_pro(user_id: int, video_id: str, message):
    """حلقة إرسال المشاركات المتوازية"""
    
    last_update = time.time()
    consecutive_fails = 0
    loop = asyncio.get_event_loop()
    
    logger.info(f"Starting PRO share loop for user {user_id}, video {video_id}")
    
    while user_id in user_sessions and user_sessions[user_id].get('running', False):
        try:
            session = user_sessions.get(user_id)
            if not session:
                break
            
            parallel_count = session.get('parallel', 2)
            delay = session.get('delay', 3)
            
            # إرسال طلبات متوازية
            tasks = []
            for _ in range(parallel_count):
                tasks.append(
                    loop.run_in_executor(
                        executor,
                        engine.send_share,
                        video_id,
                        None,
                        None
                    )
                )
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    session['fails'] += 1
                    consecutive_fails += 1
                elif isinstance(result, dict):
                    session['total'] += 1
                    if result.get('success'):
                        session['success'] += 1
                        consecutive_fails = 0
                    else:
                        session['fails'] += 1
                        consecutive_fails += 1
            
            # إيقاف إذا فشل كثيراً
            if consecutive_fails >= 100:
                session['running'] = False
                break
            
            # تحديث الرسالة
            current_time = time.time()
            if current_time - last_update >= 1:
                last_update = current_time
                
                rate = (session['success'] / session['total'] * 100) if session['total'] > 0 else 0
                speed = session['total'] / max(1, (current_time - session.get('start_time', current_time)))
                
                if 'start_time' not in session:
                    session['start_time'] = current_time
                
                status_text = (
                    f"🚀 *جاري الإرسال...*\n\n"
                    f"📌 `{video_id}`\n"
                    f"✅ نجاح: {session['success']}\n"
                    f"❌ فشل: {session['fails']}\n"
                    f"📊 المجموع: {session['total']}\n"
                    f"📈 النسبة: {rate:.1f}%\n"
                    f"⚡ السرعة: {speed:.1f}/ث\n"
                    f"🌐 بروكسي: {proxy_manager.get_count()}\n\n"
                    f"⏱ {datetime.now().strftime('%H:%M:%S')}"
                )
                
                keyboard = [[InlineKeyboardButton("⏹ إيقاف", callback_data="stop_shares")]]
                
                try:
                    await message.edit_text(
                        status_text,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except:
                    pass
            
            await asyncio.sleep(delay)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Loop error: {e}")
            await asyncio.sleep(1)
    
    # رسالة النهاية
    session = user_sessions.get(user_id)
    if session:
        rate = (session['success'] / session['total'] * 100) if session['total'] > 0 else 0
        
        final_text = (
            f"⏹ *تم الإيقاف!*\n\n"
            f"📌 `{video_id}`\n"
            f"✅ نجاح: {session['success']}\n"
            f"❌ فشل: {session['fails']}\n"
            f"📊 المجموع: {session['total']}\n"
            f"📈 النسبة: {rate:.1f}%"
        )
        
        try:
            await message.edit_text(final_text, parse_mode='Markdown')
        except:
            pass


def main():
    logger.info("Starting TikTok Share Bot V11 PRO...")
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("addproxy", addproxy_command))
    application.add_handler(CommandHandler("addsession", addsession_command))
    application.add_handler(CommandHandler("proxies", proxies_command))
    application.add_handler(CommandHandler("speed", speed_command))
    application.add_handler(CommandHandler("parallel", parallel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Bot V11 PRO started!")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
