# -*- coding: utf-8 -*-
"""
💌 Date Invitation App
------------------------------------------------------------
یک اپلیکیشن استریم‌لیت دو مرحله‌ای:

۱) پسر وارد سایت می‌شود، اطلاعات تماس (تلگرام یا شماره) و زمان‌های
   پیشنهادی‌اش برای دیت را وارد می‌کند و یک لینک اختصاصی می‌سازد.
2) او همان لینک را برای دختر ارسال می‌کند (از هر طریقی که خودش
   دوست دارد: تلگرام، واتساپ، پیامک و ...).
۳) دختر با کلیک روی لینک وارد یک صفحه‌ی رمانتیک می‌شود، به سوال
   «با من میای دیت؟» با Yes/No جواب می‌دهد (دکمه‌ی No فرار می‌کند
   و بعد از چند بار کلیک ناپدید می‌شود!)، بعد زمان، مکان و یک
   پیشنهاد اختیاری را انتخاب می‌کند.
4) در پایان همه‌چیز در یک جدول خلاصه می‌شود و دختر می‌تواند با یک
   کلیک، خلاصه را از طریق تلگرام یا پیامک برای پسر بفرستد.

اجرا:
    pip install -r requirements.txt
    streamlit run app.py
"""

import json
import random
import urllib.parse
import uuid
from datetime import datetime, date, time as dtime
from pathlib import Path

import streamlit as st
import jdatetime

# ----------------------------------------------------------------------------
# Config & constants
# ----------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "matches.json"

# آدرس دیپلوی‌شده‌ی اپ — برای ساختن لینک کامل قابل‌ارسال
BASE_URL = "https://our-date-pashmakiana.streamlit.app/"

st.set_page_config(
    page_title="A Special Invitation 💌",
    page_icon="💌",
    layout="centered",
)

WEEKDAYS_FA = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
MONTHS_FA = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

NO_BUTTON_MESSAGES = [
    "No 😏",
    "Are you sure? 🥺",
    "Really, really sure? 😢",
    "Let me ask again... 🤔",
    "C'mon, think about it 😅",
    "You might regret this 💔",
    "I'm not giving up 😤",
    "One more chance? 🌸",
    "Pretty pretty please? 🙏",
    "This is your last shot... 😌",
]

LOCATION_OPTIONS = [
    ("☕", "Cafe"),
    ("🍽️", "Restaurant"),
    ("🌳", "Park / Walk"),
    ("🎡", "Amusement Park"),
    ("🚗", "Drive Around"),
    ("🎬", "Movie Night"),
    ("🛍️", "Shopping"),
    ("✨", "Surprise Me"),
]

MAX_NO_CLICKS = 9  # after this many clicks, the No button vanishes 😈

# ----------------------------------------------------------------------------
# Tiny JSON "database"
# ----------------------------------------------------------------------------


def load_db() -> dict:
    if DB_PATH.exists():
        try:
            return json.loads(DB_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def save_invite(invite_id: str, data: dict) -> None:
    db = load_db()
    db[invite_id] = data
    save_db(db)


def get_invite(invite_id: str) -> dict | None:
    db = load_db()
    return db.get(invite_id)


def save_answer(invite_id: str, answer: dict) -> None:
    db = load_db()
    if invite_id in db:
        db[invite_id]["answer"] = answer
        save_db(db)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def to_shamsi_str(dt: datetime) -> str:
    jd = jdatetime.datetime.fromgregorian(datetime=dt)
    weekday = WEEKDAYS_FA[jd.weekday()]
    month = MONTHS_FA[jd.month - 1]
    return f"{weekday} {jd.day} {month} {jd.year} - ساعت {jd.strftime('%H:%M')}"


def to_gregorian_display(dt: datetime) -> str:
    return dt.strftime("%A, %d %B %Y - %H:%M")


def build_telegram_link(username: str, text: str) -> str:
    username = username.strip().lstrip("@")
    return f"https://t.me/{username}?text={urllib.parse.quote(text)}"


def build_sms_link(phone: str, text: str) -> str:
    phone = phone.strip()
    return f"sms:{phone}?&body={urllib.parse.quote(text)}"


def inject_base_style() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top, #2b0f1f 0%, #1a0b14 60%, #0f0710 100%);
        }
        .love-card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 24px;
            padding: 2rem;
            backdrop-filter: blur(6px);
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .big-emoji { font-size: 3.2rem; }
        h1, h2, h3, p, span, label, div { color: #fbe9f0; }
        .summary-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        .summary-table td {
            padding: 10px 14px;
            border-bottom: 1px solid rgba(255,255,255,0.15);
        }
        .summary-table td:first-child {
            font-weight: 600;
            width: 40%;
            color: #ff9ebb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# PAGE: Boy — create invitation
# ----------------------------------------------------------------------------


def boy_setup_page():
    inject_base_style()
    st.markdown(
        """
        <div class="love-card">
            <div class="big-emoji">💌</div>
            <h1>ساخت دعوت‌نامه‌ی دیت</h1>
            <p>اطلاعاتت رو وارد کن، لینک اختصاصی بساز و برای اون یکی نفر بفرست.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "slots" not in st.session_state:
        st.session_state.slots = []  # list of datetime objects

    st.subheader("۱. اطلاعات تماس تو")
    boy_name = st.text_input("اسمت (اختیاری)")
    contact_type = st.radio(
        "بعد از جواب دادن، جواب از چه طریقی برات ارسال بشه؟",
        ["تلگرام", "پیامک (SMS)"],
        horizontal=True,
    )
    telegram_username = ""
    phone_number = ""
    if contact_type == "تلگرام":
        telegram_username = st.text_input("یوزرنیم تلگرامت (بدون @)", placeholder="mahdi_xx")
    else:
        phone_number = st.text_input("شماره موبایلت", placeholder="09xxxxxxxxx")

    girl_name = st.text_input("اسم طرف مقابل (اختیاری، برای شخصی‌سازی پیام)")

    st.divider()
    st.subheader("۲. زمان‌هایی که برای دیت آزادی")
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        slot_date = st.date_input("تاریخ", value=date.today(), key="slot_date_input")
    with c2:
        slot_time = st.time_input("ساعت", value=dtime(18, 0), key="slot_time_input")
    with c3:
        st.write("")
        st.write("")
        if st.button("➕ اضافه کن"):
            new_dt = datetime.combine(slot_date, slot_time)
            st.session_state.slots.append(new_dt)
            st.session_state.slots.sort()

    if st.session_state.slots:
        st.write("زمان‌های اضافه‌شده:")
        for i, dt in enumerate(st.session_state.slots):
            cc1, cc2 = st.columns([5, 1])
            with cc1:
                st.write(f"🕒 {to_gregorian_display(dt)}  ·  ({to_shamsi_str(dt)})")
            with cc2:
                if st.button("حذف", key=f"remove_{i}"):
                    st.session_state.slots.pop(i)
                    st.rerun()
    else:
        st.info("حداقل یک زمان اضافه کن.")

    st.divider()
    ready = bool(st.session_state.slots) and (
        (contact_type == "تلگرام" and telegram_username.strip())
        or (contact_type == "پیامک (SMS)" and phone_number.strip())
    )

    if st.button("💖 لینک دعوت‌نامه رو بساز", disabled=not ready, use_container_width=True):
        invite_id = uuid.uuid4().hex[:10]
        data = {
            "boy_name": boy_name.strip(),
            "girl_name": girl_name.strip(),
            "contact_type": "telegram" if contact_type == "تلگرام" else "sms",
            "telegram_username": telegram_username.strip(),
            "phone_number": phone_number.strip(),
            "slots": [dt.isoformat() for dt in st.session_state.slots],
            "created_at": datetime.now().isoformat(),
        }
        save_invite(invite_id, data)
        st.session_state.generated_id = invite_id
        st.session_state.slots = []

    if st.session_state.get("generated_id"):
        invite_id = st.session_state.generated_id
        full_link = f"{BASE_URL}?id={invite_id}"
        st.success("لینکت آماده‌ست! همین رو برای طرف مقابل بفرست 👇")
        st.code(full_link, language="text")
        st.link_button("🔗 خودت هم امتحانش کن", full_link, use_container_width=True)


# ----------------------------------------------------------------------------
# PAGE: Girl — the invitation flow
# ----------------------------------------------------------------------------


def girl_invite_page(invite_id: str, data: dict):
    inject_base_style()

    if "stage" not in st.session_state:
        st.session_state.stage = 0
    if "no_count" not in st.session_state:
        st.session_state.no_count = 0
    if "no_message" not in st.session_state:
        st.session_state.no_message = "No 😔"

    stage = st.session_state.stage
    girl_name = data.get("girl_name") or "you"

    if stage == 0:
        stage_yes_no(data, girl_name)
    elif stage == 1:
        stage_pick_time(data)
    elif stage == 2:
        stage_pick_location(data)
    elif stage == 3:
        stage_note(data)
    elif stage == 4:
        stage_summary(invite_id, data)


def stage_yes_no(data: dict, girl_name: str):
    st.markdown(
        f"""
        <div class="love-card">
            <div class="big-emoji">💘</div>
            <h1>Hey {girl_name}!</h1>
            <h3>I have a question for you...</h3>
            <h2>Will you go on a date with me? 🥹</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    yes_scale = min(1 + st.session_state.no_count * 0.18, 3.2)
    no_offset_x = random.randint(-140, 140)
    no_offset_y = random.randint(-15, 45)
    show_no_button = st.session_state.no_count < MAX_NO_CLICKS

    st.markdown(
        f"""
        <style>
        div.st-key-yes_btn button {{
            font-size: {16 * yes_scale:.0f}px !important;
            padding: {10 * yes_scale:.0f}px {26 * yes_scale:.0f}px !important;
            transition: all 0.25s ease;
            background: linear-gradient(135deg,#ff5e7e,#ff2e63) !important;
            color: white !important;
            border: none !important;
            border-radius: 50px !important;
            box-shadow: 0 4px 24px rgba(255,46,99,.55) !important;
        }}
        div.st-key-no_btn {{
            position: relative;
            left: {no_offset_x}px;
            top: {no_offset_y}px;
            transition: all 0.2s ease;
        }}
        div.st-key-no_btn button {{
            border-radius: 50px !important;
            opacity: 0.85;
            background: rgba(255,255,255,0.08) !important;
            color: #fbe9f0 !important;
            border: 1px solid rgba(255,255,255,0.25) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💖 YES!", key="yes_btn", use_container_width=True):
            st.session_state.stage = 1
            st.rerun()
    with col2:
        if show_no_button:
            if st.button(st.session_state.no_message, key="no_btn"):
                st.session_state.no_count += 1
                st.session_state.no_message = random.choice(NO_BUTTON_MESSAGES)
                st.rerun()
        else:
            st.markdown(
                "<p style='opacity:.7;'>😉 The No button ran away for good...</p>",
                unsafe_allow_html=True,
            )

    if st.session_state.no_count > 0 and show_no_button:
        st.caption(f"Nice try dodging it {st.session_state.no_count} time(s) 😄")


def stage_pick_time(data: dict):
    st.markdown(
        """
        <div class="love-card">
            <div class="big-emoji">🗓️</div>
            <h1>Pick a time that works 💫</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    slots = [datetime.fromisoformat(s) for s in data.get("slots", [])]
    options = [to_gregorian_display(s) for s in slots]

    if not options:
        st.error("No time slots were provided for this invitation.")
        return

    choice = st.radio("Available times:", options, key="time_choice")
    chosen_dt = slots[options.index(choice)]

    st.markdown(
        f"""
        <div style="text-align:center; margin-top:1rem; padding:1rem;
                    border-radius:16px; background:rgba(255,255,255,0.08);">
            <p style="margin:0;">📅 In Shamsi (تقویم شمسی):</p>
            <h3 style="margin:.3rem 0 0 0;">{to_shamsi_str(chosen_dt)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Next ➡️", use_container_width=True):
        st.session_state.chosen_dt = chosen_dt.isoformat()
        st.session_state.stage = 2
        st.rerun()


def stage_pick_location(data: dict):
    st.markdown(
        """
        <div class="love-card">
            <div class="big-emoji">📍</div>
            <h1>Where would you like to go? ✨</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    labels = [f"{emoji}  {name}" for emoji, name in LOCATION_OPTIONS]
    choice = st.radio("Pick a vibe:", labels, key="location_choice")
    chosen_name = LOCATION_OPTIONS[labels.index(choice)][1]

    if st.button("Next ➡️", use_container_width=True):
        st.session_state.chosen_location = chosen_name
        st.session_state.stage = 3
        st.rerun()


def stage_note(data: dict):
    st.markdown(
        """
        <div class="love-card">
            <div class="big-emoji">📝</div>
            <h1>Got a specific spot in mind?</h1>
            <p>Totally optional — leave it blank to skip 😊</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    note = st.text_input("e.g. \"That little cafe near the park 🌸\"", key="note_input")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Skip", use_container_width=True):
            st.session_state.chosen_note = ""
            st.session_state.stage = 4
            st.rerun()
    with col2:
        if st.button("Continue ➡️", use_container_width=True):
            st.session_state.chosen_note = note.strip()
            st.session_state.stage = 4
            st.rerun()


def stage_summary(invite_id: str, data: dict):
    st.balloons()
    chosen_dt = datetime.fromisoformat(st.session_state.chosen_dt)
    location = st.session_state.chosen_location
    note = st.session_state.get("chosen_note", "")

    answer = {
        "slot_gregorian_str": to_gregorian_display(chosen_dt),
        "shamsi_str": to_shamsi_str(chosen_dt),
        "location": location,
        "note": note,
    }
    save_answer(invite_id, answer)

    st.markdown(
        """
        <div class="love-card">
            <div class="big-emoji">🎉</div>
            <h1>It's a date!</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rows = [
        ("📅 Date (Shamsi)", answer["shamsi_str"]),
        ("🕒 Date (Gregorian)", answer["slot_gregorian_str"]),
        ("📍 Place", answer["location"]),
    ]
    if note:
        rows.append(("📝 Note", note))

    table_html = "<table class='summary-table'>" + "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows
    ) + "</table>"
    st.markdown(f"<div class='love-card'>{table_html}</div>", unsafe_allow_html=True)

    message_lines = [
        "💌 She said YES! 💖",
        f"{data.get('girl_name') or 'She'} agreed to go on a date with you!",
        "",
        f"📅 {answer['shamsi_str']}",
        f"🕒 {answer['slot_gregorian_str']}",
        f"📍 {answer['location']}",
    ]
    if note:
        message_lines.append(f"📝 Her note: {note}")
    message_lines += ["", "Don't keep her waiting! 🥰"]
    summary_text = "\n".join(message_lines)

    st.subheader("Send him the answer 💘")

    if data.get("contact_type") == "telegram" and data.get("telegram_username"):
        link = build_telegram_link(data["telegram_username"], summary_text)
        st.link_button("📨 Send via Telegram", link, use_container_width=True)
    elif data.get("contact_type") == "sms" and data.get("phone_number"):
        link = build_sms_link(data["phone_number"], summary_text)
        st.link_button("📱 Send via SMS", link, use_container_width=True)
    else:
        st.warning("No contact method was set up for this invitation.")

    with st.expander("Or copy the message manually"):
        st.code(summary_text, language="text")


# ----------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------


def main():
    invite_id = st.query_params.get("id")

    if invite_id:
        data = get_invite(invite_id)
        if data is None:
            inject_base_style()
            st.markdown(
                """
                <div class="love-card">
                    <div class="big-emoji">💔</div>
                    <h2>This invitation link is invalid or has expired.</h2>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return
        girl_invite_page(invite_id, data)
    else:
        boy_setup_page()


if __name__ == "__main__":
    main()
