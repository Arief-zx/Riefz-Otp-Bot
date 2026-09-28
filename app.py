import os
import asyncio
import re
import requests
import json
import html
import time
import shutil
from datetime import datetime
from collections import defaultdict
from typing import Optional, List, Dict, Any

import phonenumbers
from phonenumbers import geocoder
from dotenv import load_dotenv

from telegram import (
    Bot,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CopyTextButton,
)
from telegram.constants import ParseMode
from telegram.error import RetryAfter, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ==================== LOAD .ENV ====================
load_dotenv()

# ==================== KONFIGURASI ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_GROUP_ID = int(os.getenv("DEFAULT_GROUP_ID", "-1003784272912"))
STATS_CHANNEL_ID = int(os.getenv("STATS_CHANNEL_ID", "-1003238142301"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "zxiety")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
DELETE_DELAY = int(os.getenv("DELETE_DELAY", "120"))
RELOAD_INTERVAL = int(os.getenv("RELOAD_INTERVAL", "10"))
BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", "86400"))
STATS_RESET_INTERVAL = int(os.getenv("STATS_RESET_INTERVAL", "600"))
MAX_SEEN_OTPS = int(os.getenv("MAX_SEEN_OTPS", "10000"))

API_SOURCES = [url.strip() for url in os.getenv("API_SOURCES", "").split(",") if url.strip()]

# ==================== EMOJI CONFIGURATION ====================
EMOJI_IDS = {
    "play_button": "6329978317592075530",
    "key_icon": "5296369303661067030",
    "methods_icon": "5224607267797606837",
    "channel_icon": "5458603043203327669",
    "panel_icon": "5424972470023104089",
    "mask_icon": "6010179433598559269",
    "message_icon": "6215476864597625864",
}

# ==================== COUNTRY CODES ====================
COUNTRY_CODES = {
    "INDONESIA": "ID", "MALAYSIA": "MY", "SINGAPORE": "SG", "THAILAND": "TH",
    "VIETNAM": "VN", "PHILIPPINES": "PH", "MYANMAR": "MM", "CAMBODIA": "KH",
    "LAOS": "LA", "BRUNEI": "BN", "TIMOR LESTE": "TL", "CHINA": "CN",
    "JAPAN": "JP", "SOUTH KOREA": "KR", "KOREA": "KR", "INDIA": "IN",
    "PAKISTAN": "PK", "BANGLADESH": "BD", "NEPAL": "NP", "SRI LANKA": "LK",
    "AFGHANISTAN": "AF", "IRAN": "IR", "IRAQ": "IQ", "SAUDI ARABIA": "SA",
    "YEMEN": "YE", "OMAN": "OM", "UNITED ARAB EMIRATES": "AE", "UAE": "AE",
    "QATAR": "QA", "KUWAIT": "KW", "BAHRAIN": "BH", "JORDAN": "JO",
    "LEBANON": "LB", "SYRIA": "SY", "ISRAEL": "IL", "TURKEY": "TR",
    "AZERBAIJAN": "AZ", "GEORGIA": "GE", "ARMENIA": "AM", "KAZAKHSTAN": "KZ",
    "UZBEKISTAN": "UZ", "TURKMENISTAN": "TM", "KYRGYZSTAN": "KG",
    "TAJIKISTAN": "TJ", "MONGOLIA": "MN", "TAIWAN": "TW", "HONG KONG": "HK",
    "MACAO": "MO", "MALDIVES": "MV", "BHUTAN": "BT",
    "UNITED STATES": "US", "USA": "US", "CANADA": "CA", "MEXICO": "MX",
    "GUATEMALA": "GT", "BELIZE": "BZ", "EL SALVADOR": "SV", "HONDURAS": "HN",
    "NICARAGUA": "NI", "COSTA RICA": "CR", "PANAMA": "PA", "CUBA": "CU",
    "JAMAICA": "JM", "HAITI": "HT", "DOMINICAN REPUBLIC": "DO",
    "PUERTO RICO": "PR", "TRINIDAD AND TOBAGO": "TT", "BARBADOS": "BB",
    "BAHAMAS": "BS", "GRENADA": "GD", "SAINT LUCIA": "LC",
    "SAINT VINCENT": "VC", "ANTIGUA AND BARBUDA": "AG",
    "SAINT KITTS AND NEVIS": "KN", "DOMINICA": "DM",
    "BERMUDA": "BM", "CAYMAN ISLANDS": "KY", "TURKS AND CAICOS": "TC",
    "BRITISH VIRGIN ISLANDS": "VG", "US VIRGIN ISLANDS": "VI",
    "ANGUILLA": "AI", "MONTSERRAT": "MS",
    "BRAZIL": "BR", "ARGENTINA": "AR", "CHILE": "CL", "PERU": "PE",
    "COLOMBIA": "CO", "VENEZUELA": "VE", "ECUADOR": "EC", "BOLIVIA": "BO",
    "PARAGUAY": "PY", "URUGUAY": "UY", "GUYANA": "GY", "SURINAME": "SR",
    "FRENCH GUIANA": "GF", "FALKLAND ISLANDS": "FK",
    "UNITED KINGDOM": "GB", "UK": "GB", "GERMANY": "DE", "FRANCE": "FR",
    "ITALY": "IT", "SPAIN": "ES", "PORTUGAL": "PT", "NETHERLANDS": "NL",
    "BELGIUM": "BE", "SWITZERLAND": "CH", "AUSTRIA": "AT", "SWEDEN": "SE",
    "NORWAY": "NO", "DENMARK": "DK", "FINLAND": "FI", "ICELAND": "IS",
    "IRELAND": "IE", "POLAND": "PL", "CZECH REPUBLIC": "CZ", "SLOVAKIA": "SK",
    "HUNGARY": "HU", "ROMANIA": "RO", "BULGARIA": "BG", "GREECE": "GR",
    "ALBANIA": "AL", "SERBIA": "RS", "CROATIA": "HR", "SLOVENIA": "SI",
    "BOSNIA": "BA", "MONTENEGRO": "ME", "NORTH MACEDONIA": "MK",
    "LITHUANIA": "LT", "LATVIA": "LV", "ESTONIA": "EE", "BELARUS": "BY",
    "UKRAINE": "UA", "MOLDOVA": "MD", "RUSSIA": "RU", "LUXEMBOURG": "LU",
    "MALTA": "MT", "CYPRUS": "CY", "MONACO": "MC", "LIECHTENSTEIN": "LI",
    "SAN MARINO": "SM", "VATICAN CITY": "VA", "ANDORRA": "AD",
    "GIBRALTAR": "GI", "FAROE ISLANDS": "FO", "GREENLAND": "GL",
    "ALAND ISLANDS": "AX", "JERSEY": "JE", "GUERNSEY": "GG", "ISLE OF MAN": "IM",
    "SOUTH AFRICA": "ZA", "NIGERIA": "NG", "EGYPT": "EG", "KENYA": "KE",
    "TANZANIA": "TZ", "GHANA": "GH", "CÔTE D'IVOIRE": "CI", "CAMEROON": "CM",
    "SENEGAL": "SN", "MALI": "ML", "BURKINA FASO": "BF", "NIGER": "NE",
    "CHAD": "TD", "SUDAN": "SD", "SOUTH SUDAN": "SS", "ERITREA": "ER",
    "DJIBOUTI": "DJ", "SOMALIA": "SO", "ETHIOPIA": "ET", "UGANDA": "UG",
    "RWANDA": "RW", "BURUNDI": "BI", "ZAMBIA": "ZM", "ZIMBABWE": "ZW",
    "MALAWI": "MW", "MOZAMBIQUE": "MZ", "ANGOLA": "AO", "NAMIBIA": "NA",
    "BOTSWANA": "BW", "LESOTHO": "LS", "ESWATINI": "SZ", "MADAGASCAR": "MG",
    "MAURITIUS": "MU", "SEYCHELLES": "SC", "COMOROS": "KM", "CAPE VERDE": "CV",
    "SAO TOME": "ST", "EQUATORIAL GUINEA": "GQ", "GABON": "GA",
    "CONGO": "CG", "DR CONGO": "CD", "CENTRAL AFRICAN REPUBLIC": "CF",
    "BENIN": "BJ", "TOGO": "TG", "GUINEA": "GN", "GUINEA BISSAU": "GW",
    "LIBERIA": "LR", "SIERRA LEONE": "SL", "MAURITANIA": "MR",
    "ALGERIA": "DZ", "TUNISIA": "TN", "LIBYA": "LY", "MOROCCO": "MA",
    "WESTERN SAHARA": "EH", "SAINT HELENA": "SH", "MAYOTTE": "YT",
    "REUNION": "RE", "MARTINIQUE": "MQ", "GUADELOUPE": "GP",
    "AUSTRALIA": "AU", "NEW ZEALAND": "NZ", "PAPUA NEW GUINEA": "PG",
    "FIJI": "FJ", "SOLOMON ISLANDS": "SB", "VANUATU": "VU", "SAMOA": "WS",
    "TONGA": "TO", "KIRIBATI": "KI", "TUVALU": "TV", "NAURU": "NR",
    "PALAU": "PW", "MICRONESIA": "FM", "MARSHALL ISLANDS": "MH",
    "COOK ISLANDS": "CK", "NIUE": "NU", "TOKELAU": "TK",
    "FRENCH POLYNESIA": "PF", "NEW CALEDONIA": "NC", "GUAM": "GU",
    "AMERICAN SAMOA": "AS", "NORTHERN MARIANA ISLANDS": "MP",
    "PITCAIRN ISLANDS": "PN", "WALLIS AND FUTUNA": "WF",
    "CURACAO": "CW", "ARUBA": "AW", "SINT MAARTEN": "SX",
    "BONAIRE": "BQ", "SAINT MARTIN": "MF", "SAINT BARTHELEMY": "BL",
    "UNKNOWN": "UN", "GLOBAL": "GL"
}

# ==================== GLOBAL VARIABLES ====================
FLAGS: Dict[str, str] = {}
SERVICES: Dict[str, str] = {}
GROUP_CONFIG: Dict[str, Any] = {}
STATS_DATA: Dict[str, Any] = {
    "countries": defaultdict(int),
    "services": defaultdict(int),
    "total_otp": 0,
    "last_reset": None
}
LAST_RELOAD_TIME: float = 0
last_backup_time: float = 0
last_stats_sent_time: float = 0
bot: Bot = None

# ==================== DATA LOADING FUNCTIONS ====================
def load_flags() -> Dict[str, str]:
    global FLAGS
    flags = {}
    folder = "data"
    
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"[!] Folder '{folder}' dibuat, isi dengan file flags")
        return flags
    
    print(f"[i] Memeriksa folder '{folder}'...")
    for filename in os.listdir(folder):
        if filename.lower().endswith(".json") and filename.lower() not in ["services.json", "stats.json"]:
            filepath = os.path.join(folder, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        formatted_data = {str(k).upper().strip(): v for k, v in data.items()}
                        flags.update(formatted_data)
                        print(f"   └─ [✓] {filename}: Berhasil memuat {len(formatted_data)} bendera.")
                    else:
                        print(f"   └─ [⚠️] {filename}: Dilewati karena format isinya bukan {{}}")
            except Exception as e:
                print(f"   └─ [❌] {filename}: Gagal membaca file. Error: {e}")
    
    return flags

def load_services() -> Dict[str, str]:
    filepath = "data/services.json"
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[❌] Gagal memuat services.json: {e}")
    return {}

def load_group_config() -> Dict[str, Any]:
    filepath = "data/groups.json"
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[❌] Gagal memuat groups.json: {e}")
    return {}

def save_group_config(config: Dict[str, Any]) -> bool:
    filepath = "data/groups.json"
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"[❌] Gagal menyimpan groups.json: {e}")
        return False

def load_stats() -> bool:
    global STATS_DATA
    filepath = "data/stats.json"
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "countries" in data:
                    data["countries"] = defaultdict(int, data["countries"])
                if "services" in data:
                    data["services"] = defaultdict(int, data["services"])
                STATS_DATA = data
                return True
        except Exception as e:
            print(f"[❌] Gagal memuat stats.json: {e}")
    return False

def save_stats() -> bool:
    global STATS_DATA
    filepath = "data/stats.json"
    try:
        data = {
            "countries": dict(STATS_DATA["countries"]),
            "services": dict(STATS_DATA["services"]),
            "total_otp": STATS_DATA["total_otp"],
            "last_reset": STATS_DATA["last_reset"]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"[❌] Gagal menyimpan stats.json: {e}")
        return False

def reload_data() -> bool:
    global FLAGS, SERVICES, GROUP_CONFIG, LAST_RELOAD_TIME
    current_time = time.time()
    
    if current_time - LAST_RELOAD_TIME < RELOAD_INTERVAL:
        return False
    
    try:
        new_flags = load_flags()
        new_services = load_services()
        new_groups = load_group_config()
        
        FLAGS = new_flags
        SERVICES = new_services
        GROUP_CONFIG = new_groups
        LAST_RELOAD_TIME = current_time
        print(f"[🔄] Data reloaded at {datetime.now().strftime('%H:%M:%S')}")
        print(f"   └─ Flags: {len(FLAGS)} | Services: {len(SERVICES)} | Groups: {len(GROUP_CONFIG.get('groups', []))}")
        return True
    except Exception as e:
        print(f"[❌] Error reloading data: {e}")
        return False

# ==================== HELPER FUNCTIONS ====================
def is_premium_emoji(emoji: str) -> bool:
    return isinstance(emoji, str) and emoji.isdigit() and len(emoji) >= 10

def format_emoji_html(emoji: str, default: str = "📱") -> str:
    if is_premium_emoji(emoji):
        return f'<tg-emoji emoji-id="{emoji}">{default}</tg-emoji>'
    else:
        return emoji if emoji else default

def get_app_emoji(service_name: str) -> str:
    service_name = str(service_name).lower().strip()
    
    for key, emoji in SERVICES.items():
        if not key.startswith("custom_"):
            if key.lower() == service_name:
                return emoji
    
    for key, emoji in SERVICES.items():
        if not key.startswith("custom_"):
            if key.lower() in service_name or service_name in key.lower():
                return emoji
    
    return "📱"

def get_flag(country_name: str) -> str:
    country_key = country_name.upper().strip()
    flag = FLAGS.get(country_key, "")
    if flag:
        return flag
    return "🏳️"

def get_flag_html(country_name: str) -> str:
    flag = get_flag(country_name)
    return format_emoji_html(flag, "🏳️")

def get_app_emoji_html(service_name: str) -> str:
    emoji = get_app_emoji(service_name)
    return format_emoji_html(emoji, "📱")

def get_emoji_id(name: str) -> str:
    return EMOJI_IDS.get(name, "")

def get_country_code(country_name: str) -> str:
    return COUNTRY_CODES.get(country_name.upper(), country_name[:2].upper())

def get_country_info(phone_number: str) -> tuple:
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number
    try:
        parsed = phonenumbers.parse(phone_number)
        country_name = geocoder.country_name_for_number(parsed, "en") or "Unknown"
        flag = get_flag(country_name)
        iso = get_country_code(country_name)
        return country_name, flag, iso
    except:
        return "Unknown", get_flag("UNKNOWN"), "UN"

def extract_otp(msg: str) -> Optional[str]:
    otp_match = re.search(r'\d{3}[-\s]?\d{3,4}|\d{4,8}', msg)
    return otp_match.group(0) if otp_match else None

def mask_number(num: str, emoji_id: Optional[str] = None) -> str:
    num = str(num).replace('+', '')
    if len(num) <= 6:
        return num
    
    prefix = num[:5]
    suffix = num[-3:]

    if emoji_id:
        masked_str = f'<tg-emoji emoji-id="{emoji_id}">❌</tg-emoji>'
    else:
        masked_str = "x"

    return prefix + masked_str + suffix

def update_stats(service: str, country_name: str) -> None:
    global STATS_DATA
    STATS_DATA["countries"][country_name] += 1
    STATS_DATA["services"][service] += 1
    STATS_DATA["total_otp"] += 1
    STATS_DATA["last_reset"] = datetime.now().isoformat()
    save_stats()

def fetch_otp_from_api(url: str) -> List:
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if isinstance(data, list):
            return data
        
        if "aaData" in data:
            records = data.get("aaData", [])
            result = []
            for r in records:
                if len(r) >= 5 and isinstance(r[0], str) and ":" in r[0]:
                    result.append([r[3], r[2], r[4]])
            return result
        
        return []
        
    except Exception as e:
        print(f"⚠️ Error fetching from {url}: {e}")
        return []

# ==================== TELEGRAM HANDLERS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *OTP Forwarder Bot*\n\n"
        "Bot ini akan meneruskan OTP dari berbagai sumber ke grup.\n\n"
        "📌 *Commands:*\n"
        "/start - Show this message\n"
        "/addgroup - Add current group to receive OTPs (FREE)\n"
        "/listgroups - List all active groups\n"
        "/stats - Show current statistics\n\n"
        "*Owner Commands:*\n"
        "/removegroup - Remove current group\n"
        "/addidemoji <service> <emoji> <id> - Add emoji for service\n"
        "/removeemoji <service> - Remove emoji for service\n"
        "/listemoji - List all custom emojis\n"
        "/reload - Manually reload data",
        parse_mode=ParseMode.MARKDOWN
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global STATS_DATA
    
    total_otp = STATS_DATA["total_otp"]
    top_countries = sorted(STATS_DATA["countries"].items(), key=lambda x: x[1], reverse=True)[:10]
    
    message = "📊 <b>STATISTIK OTP</b>\n"
    message += "═══════════════════\n"
    message += f"📱 Total OTP: {total_otp}\n\n"
    
    if top_countries:
        message += "🌍 <b>TOP 10 Countries:</b>\n"
        message += "─────────────────\n"
        for i, (country, count) in enumerate(top_countries, 1):
            flag_html = get_flag_html(country)
            bar = "█" * min(count, 15)
            message += f"{i}. {flag_html} {country}: {count} {bar}\n"
    else:
        message += "🌍 Belum ada data country\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

async def add_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user = update.effective_user
    
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Command ini hanya bisa digunakan di grup!")
        return
    
    reload_data()
    
    if "groups" not in GROUP_CONFIG:
        GROUP_CONFIG["groups"] = []
    
    if chat_id in GROUP_CONFIG["groups"]:
        await update.message.reply_text("ℹ️ Grup ini sudah terdaftar.")
        return
    
    GROUP_CONFIG["groups"].append(chat_id)
    if save_group_config(GROUP_CONFIG):
        await update.message.reply_text(f"✅ Grup berhasil ditambahkan!")
        inviter_username = user.username if user else None
        await invite_owner_to_group(context.bot, chat_id, inviter_username)
        reload_data()
    else:
        await update.message.reply_text("❌ Gagal menyimpan konfigurasi.")

async def remove_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if OWNER_ID and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Command ini hanya untuk owner bot!")
        return
    
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Command ini hanya bisa digunakan di grup!")
        return
    
    reload_data()
    
    if "groups" not in GROUP_CONFIG or chat_id not in GROUP_CONFIG["groups"]:
        await update.message.reply_text("ℹ️ Grup ini tidak terdaftar.")
        return
    
    GROUP_CONFIG["groups"].remove(chat_id)
    if save_group_config(GROUP_CONFIG):
        await update.message.reply_text(f"✅ Grup berhasil dihapus!")
        reload_data()
    else:
        await update.message.reply_text("❌ Gagal menyimpan konfigurasi.")

async def list_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reload_data()
    groups = GROUP_CONFIG.get("groups", [])
    
    if not groups:
        await update.message.reply_text("📋 Tidak ada grup yang terdaftar.")
        return
    
    message = "📋 *Daftar Grup Aktif:*\n\n"
    for i, group_id in enumerate(groups, 1):
        message += f"{i}. `{group_id}`\n"
    
    message += f"\nTotal: {len(groups)} grup"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def add_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if OWNER_ID and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Command ini hanya untuk owner bot!")
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "❌ *Format salah!*\n\n"
            "Gunakan: `/addidemoji <service_name> <emoji> <id>`\n\n"
            "Contoh: `/addidemoji Paypal 📱 62827252628281`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    service_name = args[0]
    emoji = args[1]
    emoji_id = args[2]
    
    if not emoji_id.isdigit():
        await update.message.reply_text("❌ ID harus berupa angka!")
        return
    
    service_key = service_name.lower().strip()
    SERVICES[service_key] = emoji_id
    
    try:
        with open("data/services.json", "w", encoding="utf-8") as f:
            json.dump(SERVICES, f, indent=4)
        
        reload_data()
        
        await update.message.reply_text(
            f"✅ *Emoji berhasil ditambahkan!*\n\n"
            f"📱 Service: {service_name}\n"
            f"🎨 Emoji: {emoji}\n"
            f"🆔 ID: `{emoji_id}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal menyimpan: {e}")

async def remove_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if OWNER_ID and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Command ini hanya untuk owner bot!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "❌ *Format salah!*\n\n"
            "Gunakan: `/removeemoji <service_name>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    service_name = args[0].lower().strip()
    
    if service_name not in SERVICES:
        await update.message.reply_text(f"❌ Service `{service_name}` tidak ditemukan!", parse_mode=ParseMode.MARKDOWN)
        return
    
    del SERVICES[service_name]
    
    try:
        with open("data/services.json", "w", encoding="utf-8") as f:
            json.dump(SERVICES, f, indent=4)
        
        reload_data()
        
        await update.message.reply_text(
            f"✅ *Emoji berhasil dihapus!*\n\n"
            f"📱 Service: {service_name}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal menyimpan: {e}")

async def list_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if OWNER_ID and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Command ini hanya untuk owner bot!")
        return
    
    reload_data()
    
    custom_emojis = {k: v for k, v in SERVICES.items() if not k.startswith("custom_")}
    
    if not custom_emojis:
        await update.message.reply_text("📋 Belum ada custom emoji yang ditambahkan.")
        return
    
    message = "📋 *Daftar Custom Emoji:*\n"
    message += "═══════════════════\n\n"
    for i, (service, emoji_id) in enumerate(custom_emojis.items(), 1):
        message += f"{i}. *{service.title()}*\n"
        message += f"   🆔 ID: `{emoji_id}`\n\n"
    
    message += f"Total: {len(custom_emojis)} service"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if OWNER_ID and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Command ini hanya untuk owner bot!")
        return
    
    global LAST_RELOAD_TIME
    LAST_RELOAD_TIME = 0
    reload_data()
    
    await update.message.reply_text(
        f"✅ *Data berhasil direload!*\n\n"
        f"📊 Flags: {len(FLAGS)}\n"
        f"📱 Services: {len(SERVICES)}\n"
        f"👥 Groups: {len(GROUP_CONFIG.get('groups', []))}",
        parse_mode=ParseMode.MARKDOWN
    )

async def invite_owner_to_group(bot: Bot, chat_id: int, inviter_username: Optional[str] = None) -> bool:
    if not OWNER_ID:
        print("⚠️ OWNER_ID not set")
        return False
    
    try:
        chat = await bot.get_chat(chat_id)
        chat_title = chat.title or "Unknown Group"
        
        notification = (
            f"🔔 *Grup Baru Ditambahkan!*\n\n"
            f"📌 *Nama Grup:* {chat_title}\n"
            f"🆔 *ID Grup:* `{chat_id}`\n"
            f"👤 *Ditambahkan oleh:* @{inviter_username or 'Unknown'}\n\n"
            f"Bot akan mengirimkan OTP ke grup ini."
        )
        
        await bot.send_message(
            chat_id=OWNER_ID,
            text=notification,
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            if OWNER_USERNAME:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"👋 @{OWNER_USERNAME} telah diundang ke grup ini!\n\n✅ Grup ini sekarang akan menerima OTP."
                )
        except Exception as e:
            print(f"⚠️ Gagal mengundang owner ke grup: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gagal mengundang owner: {e}")
        return False

# ==================== AUTO FUNCTIONS ====================
async def auto_delete_message(bot: Bot, chat_id: int, message_id: int, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"🗑️ Auto deleted message ID {message_id} after {delay} seconds.")
    except Exception as e:
        print(f"⚠️ Gagal menghapus pesan ID {message_id}: {e}")

async def create_backup() -> None:
    global last_backup_time
    current_time = time.time()
    
    if current_time - last_backup_time < BACKUP_INTERVAL:
        return
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = os.path.join(backup_dir, f"backup_{timestamp}")
    os.makedirs(backup_folder, exist_ok=True)
    
    data_files = ["services.json", "groups.json", "stats.json"]
    data_dir = "data"
    
    for file in data_files:
        src = os.path.join(data_dir, file)
        if os.path.exists(src):
            dst = os.path.join(backup_folder, file)
            shutil.copy2(src, dst)
    
    last_backup_time = current_time
    print(f"💾 Backup created: {backup_folder}")
    
    backups = sorted([d for d in os.listdir(backup_dir) if d.startswith("backup_")])
    while len(backups) > 7:
        old_backup = os.path.join(backup_dir, backups[0])
        shutil.rmtree(old_backup)
        backups.pop(0)

async def send_top_stats_to_channel(bot: Bot) -> None:
    global STATS_DATA, last_stats_sent_time
    
    current_time = time.time()
    
    if current_time - last_stats_sent_time < STATS_RESET_INTERVAL:
        return
    
    if STATS_DATA["total_otp"] == 0:
        last_stats_sent_time = current_time
        return
    
    top_countries = sorted(STATS_DATA["countries"].items(), key=lambda x: x[1], reverse=True)[:10]
    
    message = "📊 <b>TOP 10 COUNTRY OTP STATISTICS</b>\n"
    message += "═══════════════════════\n"
    message += f"📅 Periode: 10 Menit Terakhir\n"
    message += f"📱 Total OTP: {STATS_DATA['total_otp']}\n\n"
    
    message += "🌍 <b>TOP 10 COUNTRIES:</b>\n"
    message += "───────────────────\n"
    if top_countries:
        for i, (country, count) in enumerate(top_countries, 1):
            flag_html = get_flag_html(country)
            bar = "█" * min(count, 20)
            message += f"{i}. {flag_html} {country}: {count} OTP {bar}\n"
    else:
        message += "Belum ada data\n"
    
    STATS_DATA["countries"] = defaultdict(int)
    STATS_DATA["services"] = defaultdict(int)
    STATS_DATA["total_otp"] = 0
    STATS_DATA["last_reset"] = datetime.now().isoformat()
    save_stats()
    last_stats_sent_time = current_time
    
    try:
        await bot.send_message(
            chat_id=STATS_CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.HTML
        )
        print(f"📊 Top 10 stats sent to channel at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ Failed to send stats to channel: {e}")

async def send_to_group(bot: Bot, entry: List) -> bool:
    service = entry[0]
    num = entry[1]
    msg = entry[2]
    
    country_name, flag, iso = get_country_info(num)
    app_emoji = get_app_emoji(service)
    
    update_stats(service, country_name)
    
    mask_emoji_id = get_emoji_id('mask_icon')
    msg_emoji_id = get_emoji_id('message_icon')
    key_emoji_id = get_emoji_id('key_icon')

    masked = mask_number(num, emoji_id=mask_emoji_id)
    
    otp = extract_otp(msg)
    if not otp:
        return False
    
    safe_msg = html.escape(msg)
    
    rich_html_text = (
        f"<details>\n"
        f"<summary><b>{flag} #{iso} {app_emoji} {masked}</b></summary>"
        f'<blockquote><tg-emoji emoji-id="{msg_emoji_id}">💬</tg-emoji> <b>SMS :</b>\n'
        f"  <blockquote><code>{safe_msg}</code></blockquote>\n"
        f"</blockquote>\n"
        f"</details>"
    )

    row1_buttons = []
    if CopyTextButton is not None:
        row1_buttons.append({
            "text": f"{otp}", 
            "copy_text": {"text": otp}, 
            "icon_custom_emoji_id": key_emoji_id,
            "style": "primary"
        })
    else:
        row1_buttons.append({
            "text": f"{otp}", 
            "callback_data": f"{otp}",
            "style": "primary"
        })

    row2 = [
        {"text": "Get Number", "url": "https://t.me/riefzallotp", "icon_custom_emoji_id": "5406756500108501710", "style": "danger"}
    ]
    
    reply_markup = {"inline_keyboard": [row1_buttons, row2]}

    success_count = 0
    groups_to_send = [DEFAULT_GROUP_ID]
    
    reload_data()
    
    for group_id in GROUP_CONFIG.get("groups", []):
        if group_id not in groups_to_send:
            groups_to_send.append(group_id)
    
    for chat_id in groups_to_send:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage"
            
            payload = {
                "chat_id": chat_id,
                "rich_message": {
                    "html": rich_html_text
                },
                "reply_markup": reply_markup,
                "disable_web_page_preview": True
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, timeout=10))
            result = response.json()
            
            if result.get("ok"):
                sent_msg_id = result["result"]["message_id"]
                print(f"✅ Sent OTP for {num} - {service} - {otp} to chat {chat_id}")
                asyncio.create_task(auto_delete_message(bot, chat_id, sent_msg_id, DELETE_DELAY))
                success_count += 1
            else:
                print(f"⚠️ Telegram API Error for chat {chat_id}: {result.get('description')}")
        except Exception as e:
            print(f"❌ Failed to send to chat {chat_id}: {e}")
    
    return success_count > 0

# ==================== AUTO RELOAD BACKGROUND TASK ====================
async def auto_reload_and_backup_task() -> None:
    while True:
        await asyncio.sleep(RELOAD_INTERVAL)
        reload_data()
        await create_backup()
        await send_top_stats_to_channel(bot)

# ==================== MAIN FUNCTION ====================
async def main() -> None:
    global bot
    
    # Initial data load
    FLAGS = load_flags()
    SERVICES = load_services()
    GROUP_CONFIG = load_group_config()
    load_stats()
    
    print(f"[✓] Total Loaded: {len(FLAGS)} flags")
    print(f"[✓] Total Loaded: {len(SERVICES)} services")
    print(f"[✓] Active Groups: {len(GROUP_CONFIG.get('groups', []))}")
    print(f"[✓] Stats loaded: {STATS_DATA['total_otp']} OTPs recorded")
    
    # Initialize bot
    bot = Bot(token=BOT_TOKEN)
    
    # Build application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("addgroup", add_group_command))
    application.add_handler(CommandHandler("removegroup", remove_group_command))
    application.add_handler(CommandHandler("listgroups", list_groups_command))
    application.add_handler(CommandHandler("addidemoji", add_emoji_command))
    application.add_handler(CommandHandler("removeemoji", remove_emoji_command))
    application.add_handler(CommandHandler("listemoji", list_emoji_command))
    application.add_handler(CommandHandler("reload", reload_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Start bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Start background tasks
    asyncio.create_task(auto_reload_and_backup_task())
    
    print(f"🚀 Starting Multi-API OTP Forwarder Bot...")
    print(f"📊 Active API sources: {len(API_SOURCES)}")
    print(f"👥 Active Groups: {len(GROUP_CONFIG.get('groups', []))}")
    print(f"🔄 Auto-reload active (every {RELOAD_INTERVAL} seconds)")
    print(f"💾 Auto-backup active (every 24 hours)")
    
    # Load existing OTPs
    seen_otps = set()
    for url in API_SOURCES:
        try:
            entries = fetch_otp_from_api(url)
            for entry in entries:
                if len(entry) >= 3:
                    uid = f"{entry[0]}_{entry[1]}_{entry[2]}"
                    seen_otps.add(uid)
        except:
            pass
    print(f"📦 Initialized with {len(seen_otps)} existing OTPs.")
    
    # Main polling loop
    while True:
        for url in API_SOURCES:
            try:
                entries = fetch_otp_from_api(url)
                for entry in reversed(entries):
                    if len(entry) < 3:
                        continue
                    uid = f"{entry[0]}_{entry[1]}_{entry[2]}"
                    if uid not in seen_otps:
                        seen_otps.add(uid)
                        await send_to_group(bot, entry)
                        await asyncio.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Error: {e}")
        
        if len(seen_otps) > MAX_SEEN_OTPS:
            seen_otps = set(list(seen_otps)[-MAX_SEEN_OTPS//2:])
        
        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    print("="*50)
    print("OTP FORWARDER BOT WITH STATISTICS")
    print("="*50)
    print("\n💡 COMMANDS:")
    print("  ✅ /addgroup - Add group (FREE)")
    print("  🔒 /removegroup - Remove group (OWNER ONLY)")
    print("  📋 /listgroups - List all active groups")
    print("  📊 /stats - Show current statistics")
    print("  🔒 /addidemoji - Add emoji for service (Owner only)")
    print("  🔒 /removeemoji - Remove emoji (Owner only)")
    print("  🔒 /listemoji - List custom emojis (Owner only)")
    print("  🔒 /reload - Reload data (Owner only)")
    print("\n" + "="*50)
    print("="*50)
    
    asyncio.run(main())
