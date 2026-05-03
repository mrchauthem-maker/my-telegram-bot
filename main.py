# ========= ÉP IPV4 =========
import os
import socket
os.environ["HTTPX_DISABLE_IPV6"] = "1"
socket.has_ipv6 = False
socket.setdefaulttimeout(20)

# ========= IMPORT =========
import asyncio
import logging
import unicodedata
import html

import pandas as pd
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# ========= TẮT LOG =========
logging.basicConfig(level=logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# ========= CONFIG =========
TOKEN = os.environ.get("BOT_TOKEN")
MAX_LEN = 4000
MAX_RESULT = 20

USER_SITE_PERMISSION = {
    7959511599: ["ALL"],
    7581345665: ["ALL"],
    8388919379: ["ALL"],
    8263229136: ["ALL"],
    1548507253: ["ALL"],
    6696630002: ["ALL"],
    8173283864: ["HTP", "H06", "HBI"],
    8280034198: ["HBT", "HGV", "H12", "HHM"],
    5992478757: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    6895064295: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    8555662897: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    7290128987: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    6303778323: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    8350267633: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    6284936902: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    7962041849: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    1208997110: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    7717699936: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    5833733184: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    1040790896: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    8119908248: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    8560797428: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    8770716600: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
    8719653700: ["BDB", "BDD", "BDI", "BDP", "BDR", "BDT"],
}

# ========= HELPER =========
def safe(x):
    return html.escape(str(x)) if x else ""

def normalize_text(text):
    if not isinstance(text, str):
        text = str(text)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    return text.lower().strip()

# ========= LOAD DATA =========
def load_data():
    try:
        df = pd.read_excel("DATA.xlsx", sheet_name=0)
    except Exception as e:
        print("❌ Lỗi đọc DATA.xlsx:", e)
        return pd.DataFrame()

    df = df.fillna("")
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    df["search_blob"] = df.astype(str).apply(
        lambda x: " ".join(x), axis=1
    ).apply(normalize_text)

    print("✅ Loaded:", len(df), "rows")
    return df

DF = load_data()

# ========= CHECK PERMISSION =========
def check_site_permission(user_id, site_id):
    site_id = str(site_id).upper()
    allow = USER_SITE_PERMISSION.get(user_id)
    if not allow:
        return False
    if "ALL" in allow:
        return True
    return any(site_id.startswith(p) for p in allow)

# ========= FORMAT ROW =========
def format_row(row):
    lat = safe(row.get("lat"))
    lon = safe(row.get("long"))
    maps = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "N/A"

    return (
        f"<b>- Site ID:</b> {safe(row.get('site_id'))}\n"
        f"<b>- Site New:</b> {safe(row.get('site_moi'))}\n"
        f"<b>- Mã PTM:</b> {safe(row.get('m_ptm'))}\n"
        f"<b>- CSHT:</b> {safe(row.get('m_csht'))}\n"
        f"<b>- Xã/Phường:</b> {safe(row.get('p_x_moi'))}\n"
        f"<b>- Quản lý MBF:</b> {safe(row.get('nv_mbf_quan_ly'))}\n"
        f"<b>- Quản lý OS:</b> {safe(row.get('nv_os_quan_ly_tram'))}\n"
        f"<b>- ĐVT:</b> {safe(row.get('dai_vt'))}\n"
        f"<b>- Phân loại trạm:</b> {safe(row.get('plt'))}\n"
        f"<b>- Loại trạm:</b> {safe(row.get('loai_tram'))}\n"
        f"<b>- Địa chỉ:</b> {safe(row.get('dia_chi_moi'))}\n"
        f"<b>- Hình thức ĐT:</b> {safe(row.get('hinh_thuc_dau_tu'))}\n"
        f"<b>- Chung cột:</b> {safe(row.get('chung_cot_anten'))}\n"
        f"<b>- Ngày P/S:</b> {safe(row.get('ngay_phat_song'))}\n"
        f"<b>- Chủ CSHT:</b> {safe(row.get('chu_csht'))}\n"
        f"<b>- HẠ TẦNG:</b> {safe(row.get('ha_tang'))}\n"
        f"<b>- GPXD trạm:</b> {safe(row.get('gpxd'))}\n"
        f"<b>- Mã PE:</b> {safe(row.get('ma_pe'))}\n"
        f"<b>- MÁY PHÁT ĐIỆN:</b> {safe(row.get('mpd'))}\n"
        f"<b>- TRUYỀN DẪN:</b> {safe(row.get('tdd'))}\n"
        f"<b>- Trạm main:</b> {safe(row.get('tram_main'))}\n"
        f"<b>- Vùng phủ:</b> {safe(row.get('vung_phu'))}\n"
        f"<b>- Long:</b> {lon}\n"
        f"<b>- Lat:</b> {lat}\n"
        f"<b>- Maps:</b> {maps}\n"
        f"-----------------------------\n"
    )

# ========= SEND LONG =========
async def send_long(update, text):
    parts = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_LEN:
            parts.append(current)
            current = ""
        current += line + "\n"
    if current:
        parts.append(current)
    for part in parts:
        await update.message.reply_text(
            part,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

# ========= HANDLE MESSAGE =========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text_input = update.message.text
    print(f"👤 USER: {user_id} | MSG: {text_input}")

    if user_id not in USER_SITE_PERMISSION:
        await update.message.reply_text("❌ Bạn không có quyền")
        return

    keyword = normalize_text(text_input)
    result = DF[DF["search_blob"].str.contains(keyword, na=False)]
    print("🔍 MATCH:", len(result))

    if result.empty:
        await update.message.reply_text("❌ Không tìm thấy dữ liệu")
        return

    text = "<b>📡 THÔNG TIN TRẠM</b>\n\n"
    found = False
    count = 0

    for _, row in result.iterrows():
        if count >= MAX_RESULT:
            break
        site_id = row.get("site_id", "")
        if not check_site_permission(user_id, site_id):
            continue
        found = True
        text += format_row(row)
        count += 1

    if not found:
        await update.message.reply_text("⛔ Không có quyền xem")
        return

    await send_long(update, text)

# ========= FLASK + WEBHOOK =========
flask_app = Flask(__name__)

async def setup_application():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await application.initialize()
    return application

application = asyncio.get_event_loop().run_until_complete(setup_application())

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    update = Update.de_json(data, application.bot)
    asyncio.get_event_loop().run_until_complete(application.process_update(update))
    return "ok", 200

@flask_app.route("/")
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)