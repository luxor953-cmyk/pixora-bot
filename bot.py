import os
import time
import io
import base64
import json
import threading
import html
import re
import requests
import hmac
import hashlib
from urllib.parse import urlencode
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    ALGIERS_TZ = ZoneInfo("Africa/Algiers")
except Exception:
    ALGIERS_TZ = None

def algiers_now_str():
    try:
        if ALGIERS_TZ:
            return datetime.now(ALGIERS_TZ).strftime("%d %b %Y, %H:%M")
        return datetime.now().strftime("%d %b %Y, %H:%M")
    except Exception:
        return time.strftime("%d %b %Y, %H:%M")

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, BotCommand
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571"))
BINANCE_ID = os.environ.get("BINANCE_ID", "957483337").strip()
SUPPORT_WHATSAPP = os.environ.get("SUPPORT_WHATSAPP", "https://wa.me/213555668244").strip()
RESELLER_KEY = os.environ.get("RESELLER_KEY", "").strip()
VENTEBOT_API_URL = os.environ.get("VENTEBOT_API_URL", "https://web-production-1c7b1.up.railway.app/api/reseller").strip().rstrip("/")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "").strip()
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "").strip()
ORDERS_FILE = os.environ.get("ORDERS_FILE", "orders.json")
SUBSCRIBERS_FILE = os.environ.get("SUBSCRIBERS_FILE", "subscribers.json")
SNAPSHOT_FILE = os.environ.get("SNAPSHOT_FILE", "products_snapshot.json")
IMAGE_IDS_FILE = os.environ.get("IMAGE_IDS_FILE", "image_ids.json")
NOTIFY_FILE = os.environ.get("NOTIFY_FILE", "notify_requests.json")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

USER_SELECTED_PRODUCT = {}
USER_WAITING_FOR_SEARCH = {}
ADMIN_WAITING_IMAGE = {}
USER_LANGUAGES = {}
USER_PROCESSING = set()
_PRODUCTS_CACHE = {"data": {}, "time": 0}
CACHE_TTL = 60

LANG_TEXTS = {
    "ar": {"welcome": "🔥 أهلاً بك في متجر Pixora Store الرقمي!\n\nاختر القسم أو المنتج المطلوب:", "search": "🔍 بحث عن منتج", "orders": "📜 مشترياتي", "deposit": "💳 شحن الرصيد / الدفع", "support": "🛠 الدعم الفني", "api": "🔑 خدمات API", "lang": "🌐 اللغة / Language", "admin": "🛠 لوحة تحكم الإدارة", "no_products": "⚠ لا توجد منتجات متاحة حالياً...", "sold_out": "نفد"},
    "en": {"welcome": "🔥 Welcome to Pixora Store Digital!\n\nChoose a category or product:", "search": "🔍 Search Product", "orders": "📜 My Orders", "deposit": "💳 Top up / Payment", "support": "🛠 Support", "api": "🔑 API Services", "lang": "🌐 Language", "admin": "🛠 Admin Panel", "no_products": "⚠ No products available right now...", "sold_out": "Sold out"},
    "fr": {"welcome": "🔥 Bienvenue sur Pixora Store Numérique !\n\nChoisissez une catégorie ou un produit :", "search": "🔍 Rechercher", "orders": "📜 Mes Commandes", "deposit": "💳 Recharger / Paiement", "support": "🛠 Support", "api": "🔑 Services API", "lang": "🌐 Langue", "admin": "🛠 Panneau Admin", "no_products": "⚠ Aucun produit disponible...", "sold_out": "Épuisé"}
}
BANNED_KEYWORDS = ["spotify","anghami","netflix","shahid","disney","apple music","iptv","movie","film","music","osn","watchit","prime video","اغاني","موسيقى","أفلام","مسلسلات","سينما"]
FAMILY_NAMES = {"chatgpt":"🤖 ChatGPT","claude":"🧠 Claude","google":"✨ Google","capcut":"🎬 CapCut","canva":"🎨 Canva","zoom":"📹 Zoom","elevenlabs":"🎙 ElevenLabs","gamma":"📊 Gamma","lovable":"💻 Lovable","microsoft":"🪟 Microsoft","miro":"📌 Miro","notion":"📝 Notion","quizlet":"📚 Quizlet","railway":"⚙ Railway","wordwall":"🎮 Wordwall","api_services":"🔑 API","vpn":"🔒 VPN","tests":"🧪 Test"}
BRAND_ICONS = {"claude":"🧠","chatgpt":"🤖","openai":"🤖","gemini":"✨","google":"🔵","grok":"✖","perplexity":"🔍","manus":"🤖","gamma":"📊","muse":"🎵","canva":"🎨","capcut":"🎬","figma":"🎨","framer":"🖼","leonardo":"🎨","runway":"🎬","heygen":"🎥","kling":"🎬","higgsfield":"🎬","descript":"🎙","picsart":"🎨","openart":"🎨","gumloop":"🔄","suno":"🎵","notion":"📝","n8n":"⚡","airtable":"📊","miro":"📌","wordwall":"🎮","quizlet":"📚","readwise":"📚","granola":"📓","linear":"📐","autodesk":"📐","jetbrains":"🧑💻","cursor":"💻","replit":"💻","codex":"💻","bolt":"⚡","lovable":"💻","supercut":"✂","pangram":"✍","quillbot":"✍","text":"📝","langsmith":"🔗","supabase":"🗄","resend":"📧","factory":"🏭","arize":"📊","posthog":"📊","fin":"💰","jam":"🎵","coursera":"🎓","udemy":"🎓","edx":"🎓","duolingo":"🦉","spotify":"🎵","youtube":"▶","hbo":"🎬","crunchyroll":"🍥","apple":"🍎","gmail":"📧","outlook":"📧","nordvpn":"🔒","expressvpn":"🔒","surfshark":"🦈","hma":"🔒","avast":"🛡","sentry":"🛡","proton":"🔒","vpn":"🔒","microsoft":"🪟","office":"📄","adobe":"🎨","stripe":"💳","mercury":"🏦","railway":"🚂","linkedin":"💼","trading":"📈","zoom":"📹","discord":"💬","intercom":"💬","joinsecret":"🔐","scribd":"📚","amazon":"📦","osn":"📺","king":"👑","mobbin":"📱","wisp":"🌊","warp":"🚀","waking":"⏰","bide":"🔍","ploy":"📦","super":"⭐","eleven":"🎙","elevenlabs":"🎙","magic":"✨","api":"🔑","test":"🧪","chat":"💬"}

def get_brand_icon(name):
    n=(name or "").lower()
    for k,v in BRAND_ICONS.items():
        if k in n: return v
    return "📦"
def get_product_icon(info):
    icon=get_brand_icon(info.get("name",""))
    if icon!="📦": return icon
    return get_brand_icon((info.get("family") or ""))

def family_sort_key(fam):
    raw=FAMILY_NAMES.get(fam,fam)
    clean=re.sub(r"[^A-Za-z\u0600-\u06FF0-9 ]","",raw).strip().lower()
    if not clean: clean=str(fam).lower()
    return (1 if fam=="tests" else 0, clean)

FAMILY_IMAGES = {}
FAMILY_IMAGES_B64 = {}
def get_family_image_bytes(family):
    b64=FAMILY_IMAGES_B64.get(family)
    if not b64: return None
    try: return io.BytesIO(base64.b64decode(b64))
    except Exception as e:
        print("B64 DECODE ERROR",family,e); return None
PRODUCT_IMAGES = {}

def get_product_image(info):
    pid=str(info.get("id","")); fam=info.get("family"); name=(info.get("name") or "").lower()
    if "wispr" in name or "flow" in name: return "https://logo.clearbit.com/wisprflow.ai"
    if "chatgpt" in name or "openai" in name: return "https://logo.clearbit.com/openai.com"
    if "claude" in name: return "https://logo.clearbit.com/anthropic.com"
    if "gemini" in name or "google" in name: return "https://logo.clearbit.com/google.com"
    if pid in PRODUCT_IMAGES and PRODUCT_IMAGES[pid]: return PRODUCT_IMAGES[pid]
    if info.get("image") and str(info.get("image")).startswith("http"): return info["image"]
    if fam and fam in FAMILY_IMAGES: return FAMILY_IMAGES[fam]
    return ""

def user_lang(chat_id): return USER_LANGUAGES.get(chat_id,"ar")
def safe_html(v): return html.escape(str(v),quote=False)
def is_allowed_product(name,description=""):
    text=f"{name} {description}".lower()
    return not any(w in text for w in BANNED_KEYWORDS)
def get_product_family(name):
    n=str(name).lower()
    rules=[(("test","api test"),"tests"),(("chatgpt","gpt","openai"),"chatgpt"),(("claude",),"claude"),(("gemini","google","gmail"),"google"),(("capcut",),"capcut"),(("canva",),"canva"),(("zoom",),"zoom"),(("elevenlabs",),"elevenlabs"),(("gamma",),"gamma"),(("lovable",),"lovable"),(("microsoft",),"microsoft"),(("miro",),"miro"),(("notion",),"notion"),(("quizlet",),"quizlet"),(("railway",),"railway"),(("wordwall",),"wordwall"),(("api",),"api_services"),(("vpn","hma","surfshark","expressvpn"),"vpn")]
    for words,family in rules:
        if any(w in n for w in words): return family
    return None

def load_orders():
    if not os.path.exists(ORDERS_FILE): return {}
    try:
        with open(ORDERS_FILE,"r",encoding="utf-8") as f:
            d=json.load(f); return d if isinstance(d,dict) else {}
    except Exception as e: print("ORDERS READ",e); return {}
def save_orders(data):
    try:
        tmp=ORDERS_FILE+".tmp"
        with open(tmp,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
        os.replace(tmp,ORDERS_FILE)
    except Exception as e: print("ORDERS SAVE",e)
def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE): return []
    try:
        with open(SUBSCRIBERS_FILE,"r",encoding="utf-8") as f:
            d=json.load(f); return d if isinstance(d,list) else []
    except Exception: return []
def save_subscribers(s):
    try:
        with open(SUBSCRIBERS_FILE,"w",encoding="utf-8") as f: json.dump(list(set(s)),f,ensure_ascii=False)
    except Exception as e: print(e)
def add_subscriber(cid):
    s=load_subscribers()
    if cid not in s: s.append(cid); save_subscribers(s)
def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE): return {}
    try:
        with open(SNAPSHOT_FILE,"r",encoding="utf-8") as f:
            d=json.load(f); return d if isinstance(d,dict) else {}
    except Exception: return {}
def save_snapshot(s):
    try:
        with open(SNAPSHOT_FILE,"w",encoding="utf-8") as f: json.dump(s,f,ensure_ascii=False,indent=2)
    except Exception as e: print(e)
def load_notify_requests():
    if not os.path.exists(NOTIFY_FILE): return {}
    try:
        with open(NOTIFY_FILE,"r",encoding="utf-8") as f:
            d=json.load(f); return d if isinstance(d,dict) else {}
    except Exception: return {}
def save_notify_requests(d):
    try:
        with open(NOTIFY_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
    except Exception as e: print(e)
def add_notify_request(pid,cid):
    d=load_notify_requests(); lst=d.get(str(pid),[])
    if cid not in lst: lst.append(cid); d[str(pid)]=lst; save_notify_requests(d); return True
    return False
def load_image_ids():
    if not os.path.exists(IMAGE_IDS_FILE): return {}
    try:
        with open(IMAGE_IDS_FILE,"r",encoding="utf-8") as f:
            d=json.load(f); return d if isinstance(d,dict) else {}
    except Exception: return {}
def save_image_ids(d):
    try:
        with open(IMAGE_IDS_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
    except Exception as e: print(e)
def get_stored_image_id(fam=None,product_key=None):
    d=load_image_ids()
    if product_key and f"product:{product_key}" in d: return d[f"product:{product_key}"]
    if fam and f"family:{fam}" in d: return d[f"family:{fam}"]
    return None

def check_and_notify_changes():
    try: products=fetch_supplier_products(force_refresh=True)
    except Exception as e: print("NOTIFY CHECK",e); return
    if not products: return
    old=load_snapshot()
    if not old:
        save_snapshot({k:{"name":v["name"],"price":v["price"],"stock":v["stock"]} for k,v in products.items()}); return
    reqs=load_notify_requests()
    if not reqs:
        save_snapshot({k:{"name":v["name"],"price":v["price"],"stock":v["stock"]} for k,v in products.items()}); return
    for key,info in products.items():
        prev=old.get(key)
        if not prev: continue
        if int(prev.get("stock",0))==0 and int(info["stock"])>0:
            wanters=reqs.get(str(key),[])
            if wanters:
                mk=InlineKeyboardMarkup().add(InlineKeyboardButton(f"🛒 شراء - ${info['price']}",callback_data="buy_"+key))
                for cid in wanters:
                    try: bot.send_message(cid,f"🔔 المنتج متوفر الآن\n\n🏷 {safe_html(info['name'])}\n🟢 الكمية المتوفرة: <b>{info['stock']}</b> | 💰 السعر: <b>${info['price']}</b>",reply_markup=mk,parse_mode="HTML")
                    except Exception as e: print(e)
                reqs.pop(str(key),None); save_notify_requests(reqs)
    save_snapshot({k:{"name":v["name"],"price":v["price"],"stock":v["stock"]} for k,v in products.items()})
def start_notify_watcher():
    def loop():
        time.sleep(30)
        while True:
            try: check_and_notify_changes()
            except Exception as e: print("WATCHER",e)
            time.sleep(600)
    threading.Thread(target=loop,daemon=True).start()

def send_photo_smart(chat_id,fam,info,caption,markup):
    fid=get_stored_image_id(fam=fam,product_key=str(info.get("id","")) if info else None)
    if fid:
        try: bot.send_photo(chat_id,fid,caption=caption,reply_markup=markup,parse_mode="HTML"); return True
        except Exception as e: print("FILE_ID",e)
    if fam and fam in FAMILY_IMAGES_B64:
        try:
            b=get_family_image_bytes(fam)
            if b: b.name=f"{fam}.jpg"; bot.send_photo(chat_id,b,caption=caption,reply_markup=markup,parse_mode="HTML"); return True
        except Exception as e: print("B64",e)
    url=FAMILY_IMAGES.get(fam) if fam else None
    if url:
        try: bot.send_photo(chat_id,url,caption=caption,reply_markup=markup,parse_mode="HTML"); return True
        except Exception as e: print("URL",e)
    bot.send_message(chat_id,caption,reply_markup=markup,parse_mode="HTML"); return False

def supplier_headers(): return {"X-Reseller-Key": RESELLER_KEY}
def extract_image_url(item):
    for key in ["image_url","image","photo","thumbnail","cover","img","picture","poster","banner"]:
        v=item.get(key)
        if isinstance(v,str) and v.strip().startswith("http"): return v.strip()
        if isinstance(v,dict):
            for sub in ["url","src","link","href"]:
                if isinstance(v.get(sub),str) and v.get(sub,"").startswith("http"): return v[sub].strip()
    for key in ["images","photos","gallery"]:
        v=item.get(key)
        if isinstance(v,list) and v:
            first=v[0]
            if isinstance(first,str) and first.startswith("http"): return first.strip()
            if isinstance(first,dict):
                for sub in ["url","src"]:
                    if isinstance(first.get(sub),str) and first.get(sub,"").startswith("http"): return first[sub].strip()
    for v in item.values():
        if isinstance(v,str) and v.startswith("http") and any(v.lower().split("?")[0].endswith(ext) for ext in [".jpg",".jpeg",".png",".webp"]): return v.strip()
    return ""

# ===== وصف المورد: مفيش إيموجي خالص - الإيموجي يتبدل بشرطة - =====
def _clean_desc_line(s):
    import re as _re
    # 1. شيل إيموجي تليجرام المخصص
    s = _re.sub(r'<tg-emoji[^>]*>.*?</tg-emoji>', '', s, flags=_re.DOTALL)
    s = _re.sub(r'<tg-emoji[^>]*/?>', '', s)
    s = s.replace('<tg-emoji>', '').replace('</tg-emoji>', '')
    # 2. شيل أي تاج HTML
    s = _re.sub(r'<[^>]+>', '', s)
    s = _re.sub(r'emoji-id="[^"]*"', '', s)
    s = _re.sub(r'emoji-id=\S+', '', s)
    # 3. أي إيموجي أو رمز في أول السطر أو في نصه يتبدل بشرطة -
    # ⏳ ✅ ⚠ 🔹 • 🛡 🚫 وكل الإيموجي
    s = _re.sub(r'[\U00010000-\U0010ffff\u2600-\u27BF\u2700-\u27BF\uFE0F\u200D]+', ' - ', s)
    for ch in ['✅','✔','✓','⚠','🚨','⏳','👤','🛡','📩','📦','🔔','💰','🏷','📝','🔑','🔹','🔸','•','●','▪','▫','➤','▶','»','«','★','☆','⚡','🔥','💎','📌','📋','🚫']:
        s = s.replace(ch, ' - ')
    s = _re.sub(r'\s+', ' ', s)
    # نظف الشرطات الزيادة في الأول والآخر، وسيب شرطة واحدة في الأول لو السطر كان فيه إيموجي
    s = s.strip()
    s = _re.sub(r'^(-\s*)+', '', s)  # هنضيف الشرطة بنفسنا بعدين بشكل موحد
    s = s.strip(' :;•. ')
    s = _re.sub(r'\s+', ' ', s)
    return s.strip()

def get_product_system(info):
    text=f"{info.get('name','')} {info.get('description','')}".lower()
    duration=""
    if "12 month" in text or "12 شهر" in text or "سنة" in text or "year" in text or "سنوي" in text: duration="12 Months"
    elif "6 month" in text or "6 شهور" in text or "6 أشهر" in text: duration="6 Months"
    elif "3 month" in text or "3 شهور" in text or "3 أشهر" in text: duration="3 Months"
    elif "month" in text or "شهر" in text or "30 يوم" in text: duration="1 Month"
    elif "week" in text or "أسبوع" in text: duration="1 Week"
    elif "day" in text or "يوم" in text: duration="1 Day"
    elif "lifetime" in text or "مدى الحياة" in text: duration="Lifetime"
    kind=""
    if "private" in text or "خاص" in text or "شخصي" in text: kind="Private"
    elif "shared" in text or "مشترك" in text: kind="Shared"
    parts=[p for p in [duration,kind] if p]
    return " - ".join(parts) if parts else "Subscription"

def format_supplier_description(info):
    """وصف المورد كما هو، لكن من غير أي إيموجي.
    أي إيموجي يتبدل بشرطة - . لا يغير السعر ولا المدة."""
    raw=(info.get("description") or "").strip()
    name=(info.get("name") or "").strip()
    lines=[]
    for l in raw.splitlines():
        s=_clean_desc_line(l)
        if not s: continue
        low=s.lower()
        if "http" in low or "telegram" in low or "whatsapp" in low or "t.me" in low: continue
        if len(s) < 3: continue
        lines.append(s)
    # شيل التكرار + اسم المنتج لو اتكرر + عناوين مقطوعة لوحدها
    seen=set(); uniq=[]
    for l in lines:
        k=l.lower()
        if k in seen: continue
        if k == name.lower(): continue
        if k in ["first 1 hour","first 72 hours","warranty policy","important","features","fraud prevention"]: continue
        seen.add(k); uniq.append(l)
    lines=uniq[:16]
    if len(lines) >= 3:
        # كل سطر يبدأ بشرطة - ، من غير أي إيموجي ومن غير ترقيم
        out=[f"- {l}" for l in lines]
        return "\n".join(out)
    # لو المورد لم يرسل وصفا مفصلا، ابن وصفا مختصرا بشرطة - فقط
    system=get_product_system(info)
    duration=system.split(" - ")[0] if system else "Subscription"
    nl=name.lower()
    if "gmail" in nl: acct="Gmail Account"
    elif "shared" in nl or "مشترك" in nl: acct="Shared Account"
    elif "private" in nl or "خاص" in nl: acct="Private Account"
    else: acct="Gmail Account"
    base=name
    return (
        f"{base}\n\n"
        f"- Duration: {duration}\n"
        f"- Account Type: {acct}\n"
        f"- Warranty: 3 Days (72 Hours)\n"
        f"- Delivery: Email + Password + 2FA\n"
        f"- Pre-activated {base} subscription\n"
        f"- Full access to {base} features\n"
        f"- Ready to use account\n"
        f"- Password and 2FA can be changed\n\n"
        f"- WARRANTY POLICY\n"
        f"- First 1 Hour: Warranty covers incorrect passwords and invalid 2FA codes\n"
        f"- First 72 Hours: Free replacement if account is deleted or deactivated\n\n"
        f"- IMPORTANT - AFTER PURCHASE\n"
        f"- Change your password immediately\n"
        f"- Update your 2FA authentication\n"
        f"- Change the email to your personal email if available\n"
        f"- Secure your account as soon as you receive it\n\n"
        f"- FRAUD PREVENTION\n"
        f"- False claims regarding incorrect passwords or 2FA after changing account credentials will not be accepted\n"
        f"- Fraudulent buyers may be permanently banned from our store"
    )

def fetch_supplier_products(force_refresh=False):
    now=time.time()
    if not force_refresh and _PRODUCTS_CACHE["data"] and (now-_PRODUCTS_CACHE["time"]<CACHE_TTL): return _PRODUCTS_CACHE["data"]
    if not RESELLER_KEY:
        print("CONFIG ERROR: RESELLER_KEY empty"); return _PRODUCTS_CACHE["data"] or {}
    try:
        r=requests.get(f"{VENTEBOT_API_URL}/products",headers=supplier_headers(),timeout=20)
        if r.status_code!=200:
            print("SUPPLIER ERROR",r.status_code,r.text[:1000]); return _PRODUCTS_CACHE["data"] or {}
        payload=r.json()
        if isinstance(payload,list): items=payload
        elif isinstance(payload,dict):
            items=payload.get("products") or payload.get("data") or payload.get("items") or []
            if isinstance(items,dict): items=items.get("products") or items.get("items") or []
        else: items=[]
        result={}
        for item in items:
            if not isinstance(item,dict): continue
            name=item.get("name") or item.get("title") or "منتج رقمي"
            desc=item.get("description") or item.get("desc") or ""
            if not is_allowed_product(name,desc): continue
            pid=str(item.get("id") or item.get("code") or "").strip()
            if not pid: continue
            try:
                cost=float(item.get("price_usd") or item.get("price") or item.get("cost") or 0)
                fam_tmp=get_product_family(str(name).strip())
                if fam_tmp=="tests": price=round(cost,2)
                else: price=round(cost+0.80,2)
                _nl=str(name).lower()
                _is_gemini= (("gemini" in _nl or "جيميناي" in _nl or "جيميني" in _nl) and ("plus" in _nl or "بلص" in _nl or "بلس" in _nl) and ("6" in _nl) and ("month" in _nl or "شهر" in _nl or "اشهر" in _nl or "أشهر" in _nl))
                if _is_gemini and fam_tmp!="tests": price=round(cost+0.5,2)
            except (TypeError,ValueError): price=0.0
            result[pid]={"id":pid,"name":str(name).strip(),"price":price,"stock":int(item.get("stock") or item.get("quantity") or 0),"description":str(desc or "اشتراك رقمي."),"image":extract_image_url(item),"family":get_product_family(name)}
        _PRODUCTS_CACHE["data"]=result; _PRODUCTS_CACHE["time"]=now; return result
    except Exception as e:
        print("FETCH EXCEPTION",repr(e)); return _PRODUCTS_CACHE["data"] or {}

def api_get(path):
    if not RESELLER_KEY: return None
    try:
        res=requests.get(f"{VENTEBOT_API_URL}{path}",headers=supplier_headers(),timeout=15)
        return res.json() if res.status_code==200 else None
    except Exception as e: print("SUPPLIER GET",path,repr(e)); return None
def api_get_my_wallet(): return api_get("/me")
def api_get_wallet_transactions(): return api_get("/wallet/transactions")
def api_get_deposit_methods(): return api_get("/wallet/deposit-methods")
def log_response_structure(v,depth=0):
    if depth>6: return "..."
    if isinstance(v,dict): return {str(k):log_response_structure(x,depth+1) for k,x in v.items()}
    if isinstance(v,list): return [log_response_structure(v[0],depth+1)] if v else []
    return type(v).__name__

DELIVERY_KEYS=["account_data","credentials","credential","delivery","login","account","key","code","license","serial","username","email","password","content","details","product_data","delivery_data","info","data","account_info","access","activation","pin","token"]
IGNORE_KEYS={"id","product_id","order_id","status","price","quantity","created_at","updated_at","idempotency_key","request_status","user_id","reseller_id"}
def _format_value(v):
    if isinstance(v,dict):
        parts=[]
        for kk,vv in v.items():
            if str(kk).lower() in IGNORE_KEYS: continue
            if vv is None or vv=="": continue
            parts.append(f"{kk}: {vv}")
        return "\n".join(parts) if parts else None
    if isinstance(v,list):
        parts=[_format_value(x) for x in v]; parts=[p for p in parts if p]; return "\n".join(parts) if parts else None
    if isinstance(v,str):
        v=v.strip(); return v if len(v)>=2 else None
    if isinstance(v,(int,float)): return str(v)
    return None
def _find_credentials(obj,depth=0):
    if depth>5: return None
    if isinstance(obj,dict):
        for k in DELIVERY_KEYS:
            if k in obj and obj[k] not in (None,"",{},[]):
                f=_format_value(obj[k])
                if f and len(f)>=3 and f.lower() not in ("completed","success","paid"): return f
        for k,v in obj.items():
            if str(k).lower() in IGNORE_KEYS: continue
            if str(k).lower() in ("name","title","description","desc"): continue
            r=_find_credentials(v,depth+1)
            if r: return r
        return None
    if isinstance(obj,list):
        for v in obj:
            r=_find_credentials(v,depth+1)
            if r: return r
        return None
    return None
def extract_delivery_data(response_data):
    if not isinstance(response_data,dict): return None
    order=response_data.get("order")
    if not isinstance(order,dict): order=response_data
    items=order.get("items") or order.get("data") or []
    if isinstance(items,dict): items=[items]
    creds=[]
    if isinstance(items,list):
        for it in items:
            if not isinstance(it,dict): continue
            f=_find_credentials(it)
            if f and f not in creds: creds.append(f)
    if not creds:
        f=_find_credentials(order)
        if f: creds.append(f)
    if not creds:
        f=_find_credentials(response_data)
        if f: creds.append(f)
    if not creds: return None
    if len(creds)==1: return creds[0]
    return "\n\n".join(f"بيانات المنتج {i}:\n{v}" for i,v in enumerate(creds,start=1))

def supplier_order_status(order_id):
    r=requests.get(f"{VENTEBOT_API_URL}/orders/{order_id}",headers=supplier_headers(),timeout=20)
    try: d=r.json()
    except Exception: d={}
    return r.status_code,d
def lookup_supplier_order(key):
    r=requests.get(f"{VENTEBOT_API_URL}/orders/lookup",headers=supplier_headers(),params={"idempotency_key":key,"limit":20,"offset":0},timeout=20)
    try: d=r.json()
    except Exception: d={}
    return r.status_code,d
def purchase_order_from_supplier(product_id,payment_reference):
    if not RESELLER_KEY: return {"success":False,"error":"RESELLER_KEY غير مضبوط."}
    pv=int(product_id) if str(product_id).isdigit() else product_id
    key=f"pixora_{payment_reference}_{product_id}"[:120]
    headers={"X-Reseller-Key":RESELLER_KEY,"Content-Type":"application/json","Accept":"application/json"}
    payload={"product_id":pv,"quantity":1,"idempotency_key":key}
    data={}; order=None; order_id=None
    try:
        resp=requests.post(f"{VENTEBOT_API_URL}/orders",json=payload,headers=headers,timeout=30)
        print("SUPPLIER CREATE STATUS:",resp.status_code)
        try: data=resp.json()
        except Exception: data={}
        print("SUPPLIER CREATE STRUCTURE:",json.dumps(log_response_structure(data),ensure_ascii=False))
        try: print("SUPPLIER CREATE RAW PREVIEW:",str(data)[:2000])
        except Exception: pass
        if isinstance(data,dict):
            order=data.get("order")
            if isinstance(order,dict): order_id=order.get("id")
            elif isinstance(data.get("data"),dict): order=data.get("data"); order_id=order.get("id")
    except requests.RequestException as e: print("SUPPLIER CREATE EXC",repr(e))
    if not isinstance(order,dict) or not order_id:
        try:
            ls,ld=lookup_supplier_order(key); print("LOOKUP",ls)
            results=ld.get("results",[]) if isinstance(ld,dict) else []
            for res in results if isinstance(results,list) else []:
                if not isinstance(res,dict): continue
                if res.get("idempotency_key")!=key: continue
                rs=str(res.get("request_status","")).lower()
                cand=res.get("order")
                if isinstance(cand,dict): order=cand; order_id=cand.get("id")
                if rs=="failed_no_charge": return {"success":False,"error":"المورد أكد أن الطلب فشل دون خصم رصيد (failed_no_charge).","idempotency_key":key}
                break
        except requests.RequestException as e: print("LOOKUP EXC",repr(e))
    status=str(order.get("status","")).upper() if isinstance(order,dict) else ""
    if status not in ("COMPLETED","DELIVERED","SUCCESS","DONE","FULFILLED","PAID","READY") and order_id:
        for _ in range(10):
            time.sleep(5)
            try:
                hs,pd=supplier_order_status(order_id); print("POLL",hs)
                cand=None
                if isinstance(pd,dict): cand=pd.get("order") or pd.get("data")
                if isinstance(cand,dict): order=cand; status=str(order.get("status","")).upper()
                print("STATE",status or "UNKNOWN")
                if status in ("COMPLETED","DELIVERED","SUCCESS","DONE","FULFILLED","PAID","READY"): break
                if extract_delivery_data({"order":order}): break
            except requests.RequestException as e: print("POLL EXC",repr(e))
    if order_id and not extract_delivery_data({"order":order}):
        try:
            _,fd=supplier_order_status(order_id); fo=None
            if isinstance(fd,dict): fo=fd.get("order") or fd.get("data")
            if isinstance(fo,dict):
                merged=dict(order); merged.update(fo)
                if fo.get("items"): merged["items"]=fo["items"]
                order=merged; status=str(order.get("status","")).upper(); print("FINAL FETCH",status)
        except Exception as e: print("FINAL FETCH EXC",repr(e))
    delivery_preview=extract_delivery_data({"order":order}) if isinstance(order,dict) else None
    if (status in ("COMPLETED","DELIVERED","SUCCESS","DONE","FULFILLED","PAID","READY") or delivery_preview) and isinstance(order,dict):
        return {"success":True,"data":{"success":True,"order":order},"idempotency_key":key,"order_id":order.get("id")}
    return {"success":False,"error":f"المورد لم يؤكد حالة COMPLETED. لم تتم إعادة الشراء لتجنب الخصم المكرر. الحالة الحالية: {status or 'غير معروفة'}.","idempotency_key":key,"order_id":order_id}

def verify_binance_transaction(order_id,expected_amount):
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY: return {"success":False,"error":"مفاتيح Binance API غير مضبوطة على Render."}
    try:
        ts=int(time.time()*1000); qs=urlencode({"timestamp":ts,"limit":50}); sig=hmac.new(BINANCE_SECRET_KEY.encode(),qs.encode(),hashlib.sha256).hexdigest()
        url=f"https://api.binance.com/sapi/v1/pay/transactions?{qs}&signature={sig}"
        resp=requests.get(url,headers={"X-MBX-APIKEY":BINANCE_API_KEY},timeout=15)
        if resp.status_code!=200: return {"success":False,"error":f"Binance HTTP {resp.status_code}: {resp.text[:500]}"}
        txs=resp.json().get("data",[])
        for tx in txs:
            if str(tx.get("orderId"))==str(order_id) or str(tx.get("transactionId"))==str(order_id):
                actual=float(tx.get("amount",0))
                if actual>=float(expected_amount): return {"success":True}
                return {"success":False,"error":f"المبلغ المستلم ${actual} أقل من السعر ${expected_amount}."}
        return {"success":False,"error":"رقم العملية غير موجود ضمن آخر المعاملات."}
    except Exception as e: return {"success":False,"error":str(e)}
def notify_admin(text):
    if not bot: return
    try: bot.send_message(ADMIN_ID,text,parse_mode="HTML")
    except Exception as e: print("ADMIN NOTIF",repr(e))

def get_main_menu_markup(chat_id,is_admin=False):
    t=LANG_TEXTS.get(user_lang(chat_id),LANG_TEXTS["ar"]); mk=InlineKeyboardMarkup(); products=fetch_supplier_products()
    if not products: mk.add(InlineKeyboardButton(t["no_products"],callback_data="main_menu")); return mk
    fams=set(); singles=[]
    for k,info in products.items():
        if info["family"]: fams.add(info["family"])
        else: singles.append((k,info))
    others=sorted([x for x in fams if x!="tests"],key=lambda x: family_sort_key(x))
    for i in range(0,len(others),3):
        chunk=others[i:i+3]; btns=[]
        for fam in chunk:
            full=FAMILY_NAMES.get(fam,f"📁 {fam.upper()}")
            has=any(v["family"]==fam and v["stock"]>0 for v in products.values())
            dot="🟩" if has else "🟥"
            btns.append(InlineKeyboardButton(f"{dot} {full}",callback_data="fam_"+fam))
        mk.row(*btns)
    if "tests" in fams: mk.row(InlineKeyboardButton(FAMILY_NAMES.get("tests","🧪 Test"),callback_data="fam_tests"))
    singles_sorted=sorted(singles,key=lambda x: x[1]["name"].lower())
    for i in range(0,len(singles_sorted),2):
        chunk=singles_sorted[i:i+2]; btns=[]
        for k,info in chunk:
            ic=get_product_icon(info)
            if info["stock"]>0: btns.append(InlineKeyboardButton(f"🟩 {ic} {info['name']} · ${info['price']}",callback_data="buy_"+k))
            else: btns.append(InlineKeyboardButton(f"🟥 {ic} {info['name']} · غير متوفر",callback_data="buy_"+k))
        mk.row(*btns)
    mk.row(InlineKeyboardButton(t["search"],callback_data="search_product"),InlineKeyboardButton(t["orders"],callback_data="my_orders"))
    mk.row(InlineKeyboardButton(t["deposit"],callback_data="payment_methods"),InlineKeyboardButton(t["support"],url=SUPPORT_WHATSAPP))
    mk.row(InlineKeyboardButton(t["api"],callback_data="show_apis"),InlineKeyboardButton(t["lang"],callback_data="menu_lang"))
    if is_admin: mk.row(InlineKeyboardButton(t["admin"],callback_data="admin_panel"))
    return mk
def get_admin_markup():
    mk=InlineKeyboardMarkup()
    mk.row(InlineKeyboardButton("💰 فحص الرصيد",callback_data="adm_balance"),InlineKeyboardButton("💳 طرق الإيداع",callback_data="adm_deposits"))
    mk.row(InlineKeyboardButton("📊 سجل المعاملات",callback_data="adm_transactions"),InlineKeyboardButton("🔙 القائمة الرئيسية",callback_data="main_menu"))
    return mk

def send_product_card(chat_id,info,markup,reply_to_msg_id=None):
    # وصف المورد منظم بنفس قالب صورة المورد
    desc_text=format_supplier_description(info)
    msg=(f"🏷 <b>{safe_html(info['name'])}</b>\n"
         f"💰 السعر: <b>${info['price']}</b> | التوفر: <b>{info['stock']}</b>\n\n"
         f"تفاصيل المنتج:\n{safe_html(desc_text)}")
    if send_photo_smart(chat_id,info.get("family"),info,msg,markup): return True
    image=get_product_image(info)
    if image and image.startswith("http"):
        try: bot.send_photo(chat_id,image,caption=msg,reply_markup=markup,parse_mode="HTML"); return True
        except Exception as e:
            print("IMAGE SEND",repr(e))
            try: bot.send_photo(chat_id,image,caption=msg,reply_markup=markup); return True
            except Exception as e2: print("IMAGE RETRY",repr(e2))
    bot.send_message(chat_id,msg,reply_markup=markup,parse_mode="HTML"); return False

def send_home(chat_id):
    bot.send_message(chat_id,LANG_TEXTS[user_lang(chat_id)]["welcome"],reply_markup=get_main_menu_markup(chat_id,chat_id==ADMIN_ID))

if bot:
    try: bot.set_my_commands([BotCommand("start","تشغيل المتجر 🚀"),BotCommand("products","تصفح المنتجات 🛍"),BotCommand("my_orders","مشترياتي 📜"),BotCommand("language","اللغة / Language 🌐")])
    except Exception as e: print("COMMANDS",repr(e))
    @bot.message_handler(commands=["start","products"])
    def send_welcome(message):
        cid=message.chat.id; add_subscriber(cid); USER_WAITING_FOR_SEARCH.pop(cid,None); USER_SELECTED_PRODUCT.pop(cid,None)
        try:
            m=bot.send_message(cid,"🔄",reply_markup=ReplyKeyboardRemove()); bot.delete_message(cid,m.message_id)
        except Exception: pass
        send_home(cid)
    @bot.message_handler(commands=["my_orders"])
    def cmd_my_orders(message):
        cid=message.chat.id; orders=load_orders().get(str(cid),[])
        if not orders: body="📜 لا توجد طلبات سابقة."
        else:
            rows=[]
            for o in orders[-30:]: rows.append(f"📦 <b>{safe_html(o.get('product','منتج'))}</b>\n🔑 <code>{safe_html(o.get('item',''))}</code>\n🕒 {safe_html(o.get('time',''))}\n──────────────")
            body="📜 سجل مشترياتي السابقة:\n\n"+"\n".join(rows)
        bot.send_message(cid,body,reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu")),parse_mode="HTML")
    @bot.message_handler(commands=["language"])
    def cmd_language(message):
        mk=InlineKeyboardMarkup().add(InlineKeyboardButton("🇸🇦 العربية",callback_data="lang_ar"),InlineKeyboardButton("🇬🇧 English",callback_data="lang_en"),InlineKeyboardButton("🇫🇷 Français",callback_data="lang_fr"))
        bot.send_message(message.chat.id,"🌐 اختر اللغة:",reply_markup=mk)
    @bot.message_handler(commands=["setimage"])
    def cmd_setimage(message):
        if message.chat.id!=ADMIN_ID: return
        mk=InlineKeyboardMarkup()
        for fam,name in sorted(FAMILY_NAMES.items(),key=lambda x: family_sort_key(x[0])): mk.add(InlineKeyboardButton(f"🖼 {name}",callback_data="setimg_"+fam))
        bot.send_message(message.chat.id,"🖼 <b>اختر العائلة اللي عايز تغير صورتها، وبعدين ابعت الصورة:</b>",reply_markup=mk,parse_mode="HTML")
    @bot.message_handler(commands=["chatgpt_desc"])
    def cmd_chatgpt_desc(message):
        if message.chat.id!=ADMIN_ID: return
        products=fetch_supplier_products(force_refresh=True); text="📋 وصف ChatGPT الخام من المورد:\n\n"
        for k,info in products.items():
            if info.get("family")!="chatgpt": continue
            text+=f"— {info['name']}\nID: {k}\nالوصف: {info['description']}\n\n"
            if len(text)>3500: bot.send_message(message.chat.id,text); text=""
        if text.strip(): bot.send_message(message.chat.id,text)
    @bot.message_handler(content_types=["photo"])
    def handle_admin_photo(message):
        cid=message.chat.id
        if cid!=ADMIN_ID or cid not in ADMIN_WAITING_IMAGE: return
        fam=ADMIN_WAITING_IMAGE.pop(cid)
        try:
            fid=message.photo[-1].file_id; d=load_image_ids(); d[f"family:{fam}"]=fid; save_image_ids(d)
            bot.send_message(cid,f"✅ تم حفظ صورة <b>{FAMILY_NAMES.get(fam,fam)}</b> بنجاح!",parse_mode="HTML")
        except Exception as e: bot.send_message(cid,f"❌ خطأ: {e}")
    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        try: _handle_query_inner(call)
        except Exception as e:
            print("CALLBACK ERROR",repr(e))
            try: bot.send_message(call.message.chat.id,"حدث خطأ مؤقت. يرجى المحاولة مرة أخرى.")
            except Exception: pass
        return
    def _handle_query_inner(call):
        cid=call.message.chat.id
        try: add_subscriber(cid)
        except Exception: pass
        msg_id=call.message.message_id; data=call.data or ""; is_admin=cid==ADMIN_ID; products=fetch_supplier_products()
        if data.startswith("lang_"):
            lang=data.replace("lang_","")
            if lang not in LANG_TEXTS: lang="ar"
            USER_LANGUAGES[cid]=lang; bot.answer_callback_query(call.id,"✅")
            try: bot.edit_message_text(LANG_TEXTS[lang]["welcome"],cid,msg_id,reply_markup=get_main_menu_markup(cid,is_admin))
            except Exception: send_home(cid)
        elif data.startswith("setimg_"):
            if not is_admin: return
            fam=data[7:]; ADMIN_WAITING_IMAGE[cid]=fam; bot.answer_callback_query(call.id); bot.send_message(cid,f"📸 ابعت دلوقتي صورة <b>{FAMILY_NAMES.get(fam,fam)}</b> (ابعتها كصورة مش كملف):",parse_mode="HTML"); return
        elif data.startswith("fam_"):
            fam=data[4:]; bot.answer_callback_query(call.id)
            try: bot.delete_message(cid,msg_id)
            except Exception: pass
            mk=InlineKeyboardMarkup(); found=[(k,v) for k,v in products.items() if v["family"]==fam]; found_sorted=sorted(found,key=lambda x: x[1]["name"].lower())
            for k,info in found_sorted:
                system=get_product_system(info); ic=get_product_icon(info)
                if info["stock"]>0: mk.add(InlineKeyboardButton(f"🟩 {ic} {info['name']} | {system} | ${info['price']} 🟩",callback_data="buy_"+k))
                else: mk.add(InlineKeyboardButton(f"🟥 {ic} {info['name']} | {system} | غير متوفر 🟥",callback_data="buy_"+k))
            mk.add(InlineKeyboardButton("🔙 القائمة الرئيسية",callback_data="main_menu"))
            fid=get_stored_image_id(fam=fam); sent=False; caption=f"📁 <b>{safe_html(FAMILY_NAMES.get(fam,fam))}</b>"
            if fid:
                try: bot.send_photo(cid,fid,caption=caption,reply_markup=mk,parse_mode="HTML"); sent=True
                except Exception as e: print("FAMILY PHOTO",repr(e))
            if not sent and fam in FAMILY_IMAGES_B64:
                try:
                    b=get_family_image_bytes(fam)
                    if b: b.name=f"{fam}.jpg"; bot.send_photo(cid,b,caption=caption,reply_markup=mk,parse_mode="HTML"); sent=True
                except Exception as e: print("FAMILY B64",repr(e))
            if not sent: bot.send_message(cid,caption,reply_markup=mk,parse_mode="HTML")
        elif data=="menu_lang":
            bot.answer_callback_query(call.id); mk=InlineKeyboardMarkup().add(InlineKeyboardButton("🇸🇦 العربية",callback_data="lang_ar"),InlineKeyboardButton("🇬🇧 English",callback_data="lang_en"),InlineKeyboardButton("🇫🇷 Français",callback_data="lang_fr"),InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu")); bot.edit_message_text("🌐 اختر اللغة:",cid,msg_id,reply_markup=mk)
        elif data=="show_apis":
            bot.answer_callback_query(call.id); mk=InlineKeyboardMarkup()
            for k,info in products.items():
                if "api" in info["name"].lower() and info["stock"]>0: mk.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}",callback_data="buy_"+k))
            mk.add(InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu")); bot.edit_message_text("🔑 <b>خدمات API المتاحة:</b>",cid,msg_id,reply_markup=mk,parse_mode="HTML")
        elif data=="admin_panel" and is_admin:
            bot.answer_callback_query(call.id); bot.edit_message_text("🛠 <b>لوحة تحكم الإدارة:</b>",cid,msg_id,reply_markup=get_admin_markup(),parse_mode="HTML")
        elif data in ("adm_balance","adm_deposits","adm_transactions") and is_admin:
            bot.answer_callback_query(call.id)
            if data=="adm_balance": res=api_get_my_wallet(); title="💰 الرصيد"
            elif data=="adm_deposits": res=api_get_deposit_methods(); title="💳 طرق الإيداع"
            else: res=api_get_wallet_transactions(); title="📊 سجل المعاملات"
            body=safe_html(json.dumps(res,ensure_ascii=False,indent=2)[:3000]) if res else "تعذر جلب البيانات."
            bot.send_message(cid,f"{title}\n<pre>{body}</pre>",reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع",callback_data="admin_panel")),parse_mode="HTML")
        elif data=="search_product":
            bot.answer_callback_query(call.id); USER_WAITING_FOR_SEARCH[cid]=True; bot.edit_message_text("🔍 أرسل اسم المنتج للبحث:",cid,msg_id,reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 إلغاء",callback_data="main_menu")))
        elif data=="payment_methods":
            bot.answer_callback_query(call.id); pay_info=f"💳 <b>شحن الرصيد / الدفع:</b>\n\n- Binance ID: <code>{safe_html(BINANCE_ID)}</code>"; bot.edit_message_text(pay_info,cid,msg_id,reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu")),parse_mode="HTML")
        elif data.startswith("sold_out_"):
            _k=data[len("sold_out_"):]; _info=products.get(_k); bot.answer_callback_query(call.id)
            if _info and _info["stock"]<=0:
                _m=InlineKeyboardMarkup().add(InlineKeyboardButton("🔔 تنبيه عند توفر المنتج",callback_data="notify_"+_k)); _m.add(InlineKeyboardButton("🔙 رجوع",callback_data="main_menu"))
                try: bot.delete_message(cid,msg_id)
                except Exception: pass
                send_product_card(cid,_info,_m)
            else: bot.send_message(cid,"❌ المنتج غير متوفر حالياً.")
        elif data.startswith("buy_"):
            k=data[4:]; info=products.get(k); bot.answer_callback_query(call.id)
            if not info: bot.send_message(cid,"تعذر العثور على المنتج. يرجى تحديث القائمة والمحاولة مرة أخرى."); return
            if info["stock"]<=0:
                ms=InlineKeyboardMarkup().add(InlineKeyboardButton("🔔 تنبيه عند توفر المنتج",callback_data="notify_"+k)); ms.add(InlineKeyboardButton("🔙 رجوع",callback_data="main_menu"))
                try: bot.delete_message(cid,msg_id)
                except Exception: pass
                send_product_card(cid,info,ms); return
            if info["price"]<=0 and info.get("family")!="tests":
                bot.send_message(cid,"⚠ هذا المنتج غير مفعّل. يرجى التواصل مع الدعم."); notify_admin(f"⚠ محاولة شراء منتج سعره صفر: {safe_html(info['name'])} (ID: {safe_html(k)})"); return
            USER_SELECTED_PRODUCT[cid]=k
            if info.get("family")=="tests" and info["price"]<=0: mk=InlineKeyboardMarkup().add(InlineKeyboardButton("🧪 تجربة مجانية",callback_data="pay_"+k))
            else: mk=InlineKeyboardMarkup().add(InlineKeyboardButton("🪙 إتمام الدفع",callback_data="pay_"+k))
            mk.row(InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu"))
            try: bot.delete_message(cid,msg_id)
            except Exception: pass
            send_product_card(cid,info,mk)
        elif data.startswith("notify_"):
            k=data[7:]; info=products.get(k); bot.answer_callback_query(call.id)
            if not info: bot.send_message(cid,"تعذر العثور على المنتج. يرجى تحديث القائمة والمحاولة مرة أخرى."); return
            added=add_notify_request(k,cid)
            if added: bot.send_message(cid,f"✅ تم تسجيل طلب التنبيه بنجاح.\nسيتم إشعارك عند توفر المنتج: <b>{safe_html(info['name'])}</b>.",parse_mode="HTML")
            else: bot.send_message(cid,"ℹ طلب التنبيه مسجّل مسبقاً لهذا المنتج.",parse_mode="HTML")
            return
        elif data.startswith("pay_"):
            k=data[4:]; info=products.get(k); bot.answer_callback_query(call.id)
            if not info: bot.send_message(cid,"تعذر تحديد المنتج. يرجى المحاولة مرة أخرى."); return
            if info.get("family")=="tests" and info["price"]<=0:
                bot.send_message(cid,"🧪 جارٍ التجهيز..."); result=purchase_order_from_supplier(k,f"free_test_{cid}_{int(time.time())}")
                if not result["success"]: bot.send_message(cid,f"❌ فشل طلب التجربة: {safe_html(result.get('error',''))}"); return
                delivery=extract_delivery_data(result["data"])
                if not delivery: bot.send_message(cid,"⚠ لم تصل بيانات التسليم. تم إشعار الإدارة."); notify_admin(f"⚠ طلب تيست مجاني بدون بيانات: {safe_html(info['name'])} - زبون {cid}"); return
                orders=load_orders(); orders.setdefault(str(cid),[]).append({"product":info["name"],"item":delivery,"reference":"FREE_TEST","status":"delivered","time":time.strftime("%Y-%m-%d %H:%M:%S")}); save_orders(orders)
                bot.send_message(cid,f"🎉 <b>تجربة مجانية - تم التسليم!</b>\n\n📦 <b>{safe_html(info['name'])}</b>\n🔑 <b>بيانات المنتج:</b>\n<pre>{safe_html(delivery[:3500])}</pre>",parse_mode="HTML",reply_markup=get_main_menu_markup(cid,is_admin)); USER_SELECTED_PRODUCT.pop(cid,None); return
            if info["price"]<=0: bot.send_message(cid,"تعذر تحديد المنتج. يرجى المحاولة مرة أخرى."); return
            USER_SELECTED_PRODUCT[cid]=k; pay_msg=(f"🪙 إتمام الدفع\n\n📦 المنتج: <b>{safe_html(info['name'])}</b>\n💰 المبلغ: <b>${info['price']} USDT</b>\n\nقم بالتحويل إلى Binance ID: <code>{safe_html(BINANCE_ID)}</code>\n\nثم أرسل رقم العملية (Order ID) هنا في المحادثة.")
            pm=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu"))
            try: bot.delete_message(cid,msg_id)
            except Exception: pass
            try: bot.send_message(cid,pay_msg,reply_markup=pm,parse_mode="HTML")
            except Exception as e: print("PAY MSG",repr(e)); bot.send_message(cid,pay_msg,reply_markup=pm)
        elif data=="my_orders":
            bot.answer_callback_query(call.id); orders=load_orders().get(str(cid),[])
            if not orders: body="📜 لا توجد طلبات."
            else: body="📜 سجل مشترياتي:\n"+"\n".join(f"📦 {safe_html(o.get('product','منتج'))}\n🔑 <code>{safe_html(o.get('item',''))}</code>" for o in orders[-30:])
            try: bot.edit_message_text(body,cid,msg_id,reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu")),parse_mode="HTML")
            except Exception:
                try: bot.delete_message(cid,msg_id)
                except Exception: pass
                bot.send_message(cid,body,reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu")),parse_mode="HTML")
        elif data=="main_menu":
            bot.answer_callback_query(call.id); USER_SELECTED_PRODUCT.pop(cid,None); USER_WAITING_FOR_SEARCH.pop(cid,None)
            try: bot.delete_message(cid,msg_id)
            except Exception: pass
            send_home(cid)
    @bot.message_handler(content_types=["text","photo"])
    def handle_incoming(message):
        cid=message.chat.id
        if message.text and message.text.startswith("/"): return
        _txt=(message.text or "").strip(); _is_pay=cid in USER_SELECTED_PRODUCT and cid not in USER_PROCESSING; _looks=bool(re.match(r"^[A-Za-z0-9_-]{8,}$",_txt))
        if USER_WAITING_FOR_SEARCH.get(cid) or (not _is_pay and not _looks and len(_txt)>=2):
            USER_WAITING_FOR_SEARCH.pop(cid,None); query=_txt.lower()
            if not query or len(query)<2: bot.send_message(cid,"أرسل كلمة للبحث، حرفين على الأقل."); return
            products=fetch_supplier_products()
            def _norm(s): return re.sub(r"[^a-z0-9\u0600-\u06FF]","",(s or "").lower())
            def _score(name,q):
                n=_norm(name); qq=_norm(q)
                if not n or not qq: return 0
                if qq in n: return 100
                it=iter(n)
                if all(ch in it for ch in qq): return 85
                common=len(set(n)&set(qq)); return int(common/max(len(set(qq)),1)*70)
            scored=[]
            for k,info in products.items():
                best=max(_score(info["name"],query),_score(info.get("description",""),query))
                if best>=50: scored.append((best,k,info))
            scored.sort(key=lambda x: (-x[0],x[2]["name"].lower())); mk=InlineKeyboardMarkup(); found=len(scored)
            for _,k,info in scored:
                system=get_product_system(info); ic=get_product_icon(info)
                if info["stock"]>0: mk.add(InlineKeyboardButton(f"🟩 {ic} {info['name']} | {system} | ${info['price']} 🟩",callback_data="buy_"+k))
                else: mk.add(InlineKeyboardButton(f"🟥 {ic} {info['name']} | {system} | غير متوفر 🟥",callback_data="buy_"+k))
            mk.row(InlineKeyboardButton("🏠 القائمة الرئيسية",callback_data="main_menu"))
            if found: bot.send_message(cid,f"🔍 نتائج البحث عن: <b>{safe_html(_txt)}</b>\nعدد النتائج: <b>{found}</b>",reply_markup=mk,parse_mode="HTML")
            else: bot.send_message(cid,f"❌ لا توجد نتائج لـ: <b>{safe_html(_txt)}</b>",reply_markup=mk,parse_mode="HTML")
            return
        if cid not in USER_SELECTED_PRODUCT: bot.send_message(cid,"⚠ يرجى اختيار المنتج أولاً من القائمة.",reply_markup=get_main_menu_markup(cid,cid==ADMIN_ID)); return
        if cid in USER_PROCESSING: bot.send_message(cid,"⏳ طلبك قيد المعالجة، انتظر قليلاً."); return
        ref=(message.text or "").strip()
        if not re.match(r"^[A-Za-z0-9_-]{8,}$",ref): bot.send_message(cid,"❌ رقم العملية غير صالح. يجب أن يكون 8 خانات على الأقل (حروف وأرقام)."); return
        USER_PROCESSING.add(cid)
        try:
            pk=USER_SELECTED_PRODUCT.get(cid); products=fetch_supplier_products(); info=products.get(pk)
            if not info: bot.send_message(cid,"تعذر العثور على المنتج. تواصل مع الدعم قبل إعادة الدفع."); return
            bot.send_message(cid,"⏳ جاري فحص عملية الدفع عبر Binance...")
            pay=verify_binance_transaction(ref,info["price"])
            if not pay["success"]: bot.send_message(cid,f"❌ <b>فشل التحقق:</b>\n{safe_html(pay['error'])}",parse_mode="HTML"); return
            bot.send_message(cid,"✅ تم تأكيد الدفع. جارٍ إرسال الطلب إلى المورد...")
            result=purchase_order_from_supplier(pk,ref)
            if not result["success"]:
                notify_admin(f"🚨 <b>دفع مؤكد لكن طلب المورد فشل</b>\nالزبون: <code>{cid}</code>\nالمنتج: {safe_html(info['name'])}\nمرجع الدفع: <code>{safe_html(ref)}</code>\nالخطأ: <code>{safe_html(result.get('error','غير معروف')[:700])}</code>")
                bot.send_message(cid,"✅ تم تأكيد الدفع، لكن المورد لم يؤكد إتمام الطلب. تم إشعار الإدارة، لا ترسل دفعة ثانية."); USER_SELECTED_PRODUCT.pop(cid,None); return
            delivery=extract_delivery_data(result["data"])
            if not delivery:
                notify_admin(f"⚠ <b>الدفع وطلب المورد تم قبولهما، لكن لم أستطع استخراج بيانات التسليم.</b>\nالزبون: <code>{cid}</code>\nالمنتج: {safe_html(info['name'])}\nمرجع الدفع: <code>{safe_html(ref)}</code>\nOrder ID المورد: <code>{result.get('order_id')}</code>")
                bot.send_message(cid,"✅ تم تأكيد الدفع وإرسال الطلب للمورد، لكن بيانات المنتج لم تصلنا بصيغة مفهومة. تم إشعار الإدارة لمتابعة التسليم. لا تدفع مرة أخرى.")
                orders=load_orders(); orders.setdefault(str(cid),[]).append({"product":info["name"],"item":"قيد المتابعة مع المورد - لم تصل بيانات التسليم بعد","reference":ref,"status":"pending_delivery","time":time.strftime("%Y-%m-%d %H:%M:%S")}); save_orders(orders); USER_SELECTED_PRODUCT.pop(cid,None); return
            orders=load_orders(); orders.setdefault(str(cid),[]).append({"product":info["name"],"item":delivery,"reference":ref,"status":"delivered","time":time.strftime("%Y-%m-%d %H:%M:%S")}); save_orders(orders)
            oid=str(result.get('order_id') or ref or "—")
            dm=(f"🎉 <b>تم تأكيد الدفع والتسليم بنجاح!</b>\n\n📦 طلب رقم: <b>#{safe_html(oid)}</b>\n📦 <b>{safe_html(info['name'])}</b>\n🔢 مرجع الدفع: <code>{safe_html(ref)}</code>\n📅 التاريخ: <b>{algiers_now_str()}</b> (توقيت الجزائر)\n🔑 <b>بيانات المنتج:</b>\n<pre>{safe_html(delivery[:3500])}</pre>\n\nاحتفظ برقم الطلب للرجوع إليه عند وجود أي مشكلة.")
            bot.send_message(cid,dm,parse_mode="HTML",reply_markup=get_main_menu_markup(cid,cid==ADMIN_ID)); USER_SELECTED_PRODUCT.pop(cid,None)
        except Exception as e:
            print("PAYMENT HANDLER",repr(e)); notify_admin(f"🚨 خطأ غير متوقع أثناء معالجة طلب:\nالزبون: <code>{cid}</code>\n<code>{safe_html(str(e)[:700])}</code>"); bot.send_message(cid,"حدث خطأ أثناء معالجة الطلب. تم إشعار الإدارة. لا تعاود الدفع قبل التواصل مع الدعم.")
        finally: USER_PROCESSING.discard(cid)

app=Flask(__name__)
@app.route("/")
def health_check(): return "Pixora Store Active!",200
@app.route("/health")
def health(): return {"status":"ok"},200
def keep_alive():
    while True:
        time.sleep(300); url=os.environ.get("RENDER_EXTERNAL_URL","").strip()
        if url:
            try: requests.get(url,timeout=10)
            except Exception: pass
if __name__=="__main__":
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN غير موجود في Environment Variables على Render.")
    if bot:
        try: bot.remove_webhook()
        except Exception as e: print("REMOVE WEBHOOK",repr(e))
    threading.Thread(target=keep_alive,daemon=True).start()
    try: start_notify_watcher()
    except Exception as e: print("WATCHER START",repr(e))
    threading.Thread(target=lambda: app.run(host="0.0.0.0",port=int(os.environ.get("PORT","10000")),use_reloader=False),daemon=True).start()
    while True:
        try: bot.infinity_polling(skip_pending=True,timeout=60,long_polling_timeout=60)
        except Exception as e: print("BOT POLLING",repr(e)); time.sleep(5)
