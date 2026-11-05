import os
import sqlite3
import json
import threading
import urllib.request
from datetime import date, timedelta

import arabic_reshaper
from bidi.algorithm import get_display

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Line

# مسیر فونت: فایل Vazirmatn-Regular.ttf باید در پوشه fonts کنار این فایل باشد.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "Vazirmatn-Regular.ttf")
APP_FONT = FONT_PATH if os.path.isfile(FONT_PATH) else "C:/Windows/Fonts/tahoma.ttf"

Window.size = (430, 850)
Window.clearcolor = (0.88, 0.95, 0.92, 1)

GREEN = (0.04, 0.53, 0.42, 1)
DARK_GREEN = (0.02, 0.39, 0.32, 1)
MINT = (0.88, 0.95, 0.92, 1)
WHITE = (1, 1, 1, 1)
CARD = (0.95, 0.97, 0.97, 1)
TEXT = (0.18, 0.22, 0.23, 1)
MUTED = (0.48, 0.53, 0.53, 1)
RED = (0.75, 0.22, 0.25, 1)
YELLOW = (0.95, 0.72, 0.12, 1)

# احادیث کوتاه؛ هر تاریخ یک حدیث متفاوت از این فهرست نمایش می‌دهد.
DAILY_HADITHS = [
    ("ارزش هر کار به نیت آن است.", "صحیح بخاری، حدیث ۱"),
    ("یا سخن نیک بگو یا سکوت کن.", "صحیح بخاری، حدیث ۶۰۱۸"),
    ("محبوب‌ترین کارها نزد خدا، پایدارترین آن‌هاست؛ هرچند اندک باشد.", "صحیح بخاری، حدیث ۶۴۶۴"),
    ("هر کس گرفتاری مؤمنی را برطرف کند، خدا گرفتاری او را برطرف می‌کند.", "صحیح مسلم، حدیث ۲۶۹۹"),
    ("صدقه از مال نمی‌کاهد.", "صحیح مسلم، حدیث ۲۵۸۸"),
    ("هیچ‌یک از شما ایمان کامل ندارد تا آنچه برای خود دوست دارد، برای برادرش نیز دوست بدارد.", "صحیح بخاری، حدیث ۱۳"),
    ("نیرومند کسی نیست که دیگران را زمین می‌زند؛ نیرومند کسی است که هنگام خشم خود را نگه می‌دارد.", "صحیح بخاری، حدیث ۶۱۱۴"),
    ("هر جا هستی، از خدا پروا کن و پس از بدی، نیکی کن تا آن را پاک سازد.", "جامع ترمذی، حدیث ۱۹۸۷"),
]


def fa(value):
    """اتصال حروف و تنظیم جهت نوشته فارسی برای Label و Button."""
    value = str(value or "")
    try:
        return get_display(arabic_reshaper.reshape(value))
    except Exception:
        return value


def digits(value):
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def jalali_date(gdate):
    try:
        import jdatetime
        jd = jdatetime.date.fromgregorian(date=gdate)
        return f"{digits(jd.day)} {jd.strftime('%B')} {digits(jd.year)}"
    except ImportError:
        return digits(gdate.strftime("%Y-%m-%d"))



PERSIAN_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]
WEEKDAY_NAMES = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه",
                 "جمعه", "شنبه", "یکشنبه"]

# تعطیلات رسمی و چند مناسبت ملی/مذهبی شاخص سال ۱۴۰۵؛
# فهرست کامل‌تر در صورت دسترسی به اینترنت از تقویم سالانه دریافت می‌شود.
FALLBACK_OCCASIONS_1405 = {
    "1405-01-01": ["آغاز نوروز", "عید سعید فطر"],
    "1405-01-02": ["عید نوروز", "تعطیل به مناسبت عید سعید فطر"],
    "1405-01-03": ["عید نوروز"],
    "1405-01-04": ["عید نوروز"],
    "1405-01-12": ["روز جمهوری اسلامی ایران"],
    "1405-01-13": ["روز طبیعت (سیزده‌به‌در)"],
    "1405-01-25": ["شهادت امام جعفر صادق (ع)"],
    "1405-01-29": ["روز ارتش جمهوری اسلامی ایران"],
    "1405-02-01": ["روز بزرگداشت سعدی"],
    "1405-02-10": ["روز ملی خلیج فارس"],
    "1405-02-12": ["روز معلم"],
    "1405-02-25": ["روز بزرگداشت فردوسی"],
    "1405-02-28": ["روز بزرگداشت خیام"],
    "1405-03-03": ["فتح خرمشهر؛ روز مقاومت، ایثار و پیروزی", "شهادت امام محمد باقر (ع)"],
    "1405-03-06": ["عید سعید قربان"],
    "1405-03-14": ["عید سعید غدیر خم", "رحلت امام خمینی (ره)"],
    "1405-03-15": ["قیام ۱۵ خرداد"],
    "1405-04-03": ["تاسوعای حسینی"],
    "1405-04-04": ["عاشورای حسینی"],
    "1405-05-13": ["اربعین حسینی"],
    "1405-05-21": ["رحلت پیامبر اکرم (ص)؛ شهادت امام حسن مجتبی (ع)"],
    "1405-05-22": ["شهادت امام رضا (ع)"],
    "1405-05-30": ["شهادت امام حسن عسکری (ع)"],
    "1405-06-08": ["میلاد پیامبر اکرم (ص) و امام جعفر صادق (ع)"],
    "1405-06-17": ["قیام ۱۷ شهریور"],
    "1405-06-31": ["آغاز هفته دفاع مقدس"],
    "1405-07-20": ["روز بزرگداشت حافظ"],
    "1405-08-13": ["روز دانش‌آموز"],
    "1405-08-14": ["روز فرهنگ عمومی"],
    "1405-08-22": ["شهادت حضرت فاطمه زهرا (س)"],
    "1405-09-05": ["روز بسیج مستضعفان"],
    "1405-09-16": ["روز دانشجو"],
    "1405-09-30": ["شب یلدا"],
    "1405-10-02": ["ولادت امام علی (ع) و روز پدر"],
    "1405-10-16": ["مبعث رسول اکرم (ص)"],
    "1405-11-04": ["ولادت حضرت قائم (عج)؛ نیمه شعبان"],
    "1405-11-22": ["پیروزی انقلاب اسلامی"],
    "1405-12-09": ["شهادت حضرت علی (ع)"],
    "1405-12-19": ["عید سعید فطر"],
    "1405-12-20": ["تعطیل به مناسبت عید سعید فطر"],
    "1405-12-29": ["روز ملی شدن صنعت نفت ایران"]
}


def jalali_day_number(gdate):
    try:
        import jdatetime
        return digits(jdatetime.date.fromgregorian(date=gdate).day)
    except ImportError:
        return digits(gdate.day)



def jalali_info(gdate):
    """Return Persian weekday and full Jalali date."""
    weekday = WEEKDAY_NAMES[gdate.weekday()]
    try:
        import jdatetime
        jd = jdatetime.date.fromgregorian(date=gdate)
        full_date = f"{digits(jd.day)} {PERSIAN_MONTHS[jd.month - 1]} {digits(jd.year)}"
        return weekday, full_date, f"{jd.year:04d}-{jd.month:02d}-{jd.day:02d}"
    except ImportError:
        # jdatetime is optional; Gregorian fallback remains usable.
        return weekday, digits(gdate.strftime("%d-%m-%Y")), ""



def rounded(widget, color, radius=14):
    with widget.canvas.before:
        Color(*color)
        shape = RoundedRectangle(pos=widget.pos, size=widget.size,
                                 radius=[dp(radius)])
    def update(_obj, *_):
        shape.pos = widget.pos
        shape.size = widget.size
    widget.bind(pos=update, size=update)


class FaLabel(Label):
    def __init__(self, text="", **kwargs):
        kwargs.setdefault("font_name", APP_FONT)
        kwargs.setdefault("color", TEXT)
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("valign", "middle")
        super().__init__(text=fa(text), **kwargs)
        self.bind(size=self._fit)
    def _fit(self, *_):
        self.text_size = (self.width, self.height)


class FaButton(Button):
    def __init__(self, text="", **kwargs):
        kwargs.setdefault("font_name", APP_FONT)
        kwargs.setdefault("font_size", "13sp")
        kwargs.setdefault("color", WHITE)
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        super().__init__(text=fa(text), **kwargs)


class RightToLeftProgress(Widget):
    """نوار پیشرفت که از سمت راست به چپ پر می‌شود."""
    value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.88, 0.91, 0.90, 1)
            self.track = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(5)])
            Color(*GREEN)
            self.fill = RoundedRectangle(pos=self.pos, size=(0, self.height),
                                         radius=[dp(5)])
        self.bind(pos=self._update_bar, size=self._update_bar,
                  value=self._update_bar)
        self._update_bar()

    def _update_bar(self, *_):
        self.track.pos = self.pos
        self.track.size = self.size
        width = self.width * max(0, min(100, self.value)) / 100
        self.fill.pos = (self.right - width, self.y)
        self.fill.size = (width, self.height)


class PlannerRoot(BoxLayout):
    """با کشیدن انگشت از لبه راست به چپ، منوی کناری باز می‌شود."""
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._edge_start = None

    def on_touch_down(self, touch):
        if touch.x >= self.width - dp(35):
            self._edge_start = (touch.x, touch.y)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._edge_start:
            start_x, start_y = self._edge_start
            self._edge_start = None
            if start_x - touch.x > dp(75) and abs(start_y - touch.y) < dp(90):
                self.app.open_side_menu()
                return True
        return super().on_touch_up(touch)


class PlannerApp(App):
    def build(self):
        self.title = "برنامه‌یار"
        self.day = date.today()
        self.search_value = ""
        self.db = sqlite3.connect(os.path.join(self.user_data_dir, "planner.db"))
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT, section TEXT, task TEXT, done INTEGER DEFAULT 0
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS goals40 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER DEFAULT 0
            )
        """)
        self.db.commit()

        self.sections = [
            ("mind", "تخلیه ذهنی", 0),
            ("daily", "روتین‌های روزانه", 0),
            ("moral", "روتین‌های اخلاقی", 0),
            ("easy", "سه کار آسان", 3),
            ("important", "سه کار مهم و ضروری", 3),
            ("next", "سه کار بعدی", 3),
        ]
        self.defaults = {
            "daily": ["نماز صبح", "نماز ظهر و عصر", "نماز مغرب و عشا",
                      "قضای نماز مادر", "قرائت قرآن", "دعای عهد"],
            "moral": ["صداقت", "خوش‌رویی", "بخشش و صدقه"]
        }

        self.root_box = PlannerRoot(
            self, orientation="vertical",
            padding=[dp(10), dp(6), dp(10), dp(6)],
            spacing=dp(5)
        )
        rounded(self.root_box, WHITE, 20)
        self.make_header()
        self.make_hadith()
        self.make_occasions()
        self.make_week()
        self.make_progress()

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.cards = GridLayout(cols=1, spacing=dp(7),
                                padding=[0, dp(2), 0, dp(6)],
                                size_hint_y=None)
        self.cards.bind(minimum_height=self.cards.setter("height"))
        self.scroll.add_widget(self.cards)
        self.root_box.add_widget(self.scroll)
        self.make_bottom_nav()
        self.load_defaults()
        self.refresh()
        return self.root_box

    def make_header(self):
        row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        sun = FaLabel("☀", size_hint_x=None, width=dp(38),
                      font_size="25sp", color=YELLOW, halign="center")
        greetings = BoxLayout(orientation="vertical")
        greetings.add_widget(FaLabel("سلام، روزت بخیر", bold=True,
                                     font_size="16sp"))
        greetings.add_widget(FaLabel("برای یک روز پربار آماده‌ای؟",
                                     font_size="11sp", color=MUTED))
        avatar = BoxLayout(size_hint_x=None, width=dp(46), padding=dp(3))
        rounded(avatar, MINT, 12)
        avatar.add_widget(FaLabel("👤", font_size="22sp", halign="center"))
        row.add_widget(sun)
        row.add_widget(greetings)
        row.add_widget(avatar)
        self.root_box.add_widget(row)

    def make_hadith(self):
        """کارت حدیث روز؛ با تغییر تاریخ، حدیث متناسب با همان روز عوض می‌شود."""
        card = BoxLayout(orientation="vertical", padding=[dp(9), dp(3)],
                         spacing=dp(1), size_hint_y=None, height=dp(58))
        rounded(card, MINT, 13)
        title = FaLabel("حدیث امروز", bold=True, font_size="10sp",
                        color=DARK_GREEN, size_hint_y=None, height=dp(15))
        self.hadith_text = FaLabel("", font_size="10sp", color=TEXT)
        self.hadith_source = FaLabel("", font_size="8sp", color=MUTED,
                                     size_hint_y=None, height=dp(12))
        card.add_widget(title)
        card.add_widget(self.hadith_text)
        card.add_widget(self.hadith_source)
        self.root_box.add_widget(card)
        self.update_hadith()

    def update_hadith(self):
        index = self.day.toordinal() % len(DAILY_HADITHS)
        quote, source = DAILY_HADITHS[index]
        self.hadith_text.text = fa(quote)
        self.hadith_source.text = fa(source)

    def make_occasions(self):
        card = BoxLayout(orientation="vertical", padding=[dp(9), dp(3)],
                         spacing=dp(1), size_hint_y=None, height=dp(43))
        rounded(card, CARD, 12)
        title = FaLabel("مناسبت‌های امروز", bold=True, font_size="10sp",
                        color=DARK_GREEN, size_hint_y=None, height=dp(14))
        self.occasions_text = FaLabel("در حال بررسی مناسبت‌های امروز...",
                                      font_size="9sp", color=TEXT)
        card.add_widget(title)
        card.add_widget(self.occasions_text)
        self.root_box.add_widget(card)
        self.occasions = dict(FALLBACK_OCCASIONS_1405)
        self.update_occasions()
        self.load_calendar_data_async()

    def update_occasions(self):
        _weekday, _full, key = jalali_info(self.day)
        if not key:
            self.occasions_text.text = fa("برای نمایش مناسبت‌ها، بسته jdatetime را نصب کنید.")
            return
        items = self.occasions.get(key, [])
        if items:
            self.occasions_text.text = fa(" • ".join(items))
        else:
            self.occasions_text.text = fa("مناسبت ثبت‌شده‌ای برای امروز وجود ندارد.")

    def load_calendar_data_async(self):
        """Download official 1405 observances and holidays; app works offline too."""
        def worker():
            combined = {}
            urls = [
                "https://raw.githubusercontent.com/MiladJoodi/FarsiUI/main/calendar/years/1405/holidays.json",
                "https://raw.githubusercontent.com/MiladJoodi/FarsiUI/main/calendar/years/1405/events.json"
            ]
            try:
                for url in urls:
                    request = urllib.request.Request(
                        url, headers={"User-Agent": "Barnamehyar/1.0"})
                    with urllib.request.urlopen(request, timeout=4) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                    for item in payload.get("items", []):
                        key = item.get("date")
                        title = (item.get("title") or {}).get("fa")
                        if key and title:
                            combined.setdefault(key, []).append(title)
                if combined:
                    Clock.schedule_once(
                        lambda _dt: self.apply_calendar_data(combined), 0)
            except Exception:
                # Offline or unavailable source: keep the built-in 1405 list.
                pass
        threading.Thread(target=worker, daemon=True).start()

    def apply_calendar_data(self, data):
        self.occasions = data
        self.update_occasions()

    def make_search(self):
        self.search = TextInput(
            hint_text=fa("جست‌وجو در کارها و برنامه‌ها"),
            multiline=False, halign="right", font_name=APP_FONT,
            font_size="13sp", foreground_color=TEXT,
            hint_text_color=MUTED, cursor_color=GREEN,
            background_normal="", background_active="",
            background_color=CARD, padding=[dp(12), dp(12)],
            size_hint_y=None, height=dp(43))
        rounded(self.search, CARD, 12)
        self.search.bind(text=self.on_search)
        self.root_box.add_widget(self.search)

    def on_search(self, _obj, value):
        self.search_value = value.strip().casefold()
        self.refresh()

    def make_week(self):
        self.week = BoxLayout(size_hint_y=None, height=dp(57), spacing=dp(5))
        self.root_box.add_widget(self.week)
        self.update_week()

    def update_week(self):
        from kivy.uix.behaviors import ButtonBehavior
        self.week.clear_widgets()
        names = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه",
                 "جمعه", "شنبه", "یکشنبه"]
        start = self.day - timedelta(days=2)
        for i in range(5):
            d = start + timedelta(days=i)
            selected = d == self.day
            chip = BoxLayout(orientation="vertical", padding=dp(3))
            rounded(chip, GREEN if selected else CARD, 10)
            chip.add_widget(FaLabel(names[d.weekday()], font_size="9sp",
                                    color=WHITE if selected else MUTED,
                                    halign="center"))
            if selected:
                _weekday, full_date, _key = jalali_info(d)
                chip.add_widget(FaLabel(full_date, font_size="11sp",
                                        bold=True, color=WHITE,
                                        halign="center"))
            else:
                chip.add_widget(FaLabel(jalali_day_number(d), font_size="14sp",
                                        bold=True, color=TEXT,
                                        halign="center"))
            class DateButton(ButtonBehavior, BoxLayout):
                pass
            button = DateButton()
            button.add_widget(chip)
            button.bind(on_release=lambda _b, selected_day=d:
                        self.select_day(selected_day))
            self.week.add_widget(button)

    def select_day(self, d):
        self.day = d
        self.load_defaults()
        self.update_week()
        self.update_hadith()
        self.update_occasions()
        self.refresh()

    def make_progress(self):
        # نوار پیشرفت در ابتدای ردیف و متن درصد در کنار آن قرار می‌گیرد.
        row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(10),
                        padding=[dp(4), dp(2), dp(4), dp(2)])

        bar_box = BoxLayout(size_hint_x=.48, size_hint_y=None,
                            height=dp(10))
        self.progress = RightToLeftProgress(size_hint_y=None, height=dp(8),
                                            value=0)
        bar_box.add_widget(self.progress)

        info = BoxLayout(orientation="vertical")
        self.progress_label = FaLabel("پیشرفت امروز: ۰٪",
                                      font_size="12sp", color=MUTED,
                                      halign="right")
        info.add_widget(self.progress_label)

        row.add_widget(bar_box)
        row.add_widget(info)
        self.root_box.add_widget(row)

    def load_defaults(self):
        key = self.day.isoformat()
        for section, tasks in self.defaults.items():
            count = self.db.execute(
                "SELECT COUNT(*) FROM tasks WHERE day=? AND section=?",
                (key, section)).fetchone()[0]
            if count == 0:
                for task in tasks:
                    self.db.execute(
                        "INSERT INTO tasks(day,section,task,done) VALUES(?,?,?,0)",
                        (key, section, task))
        self.db.commit()

    def update_progress(self):
        total, done = self.db.execute("""
            SELECT COUNT(*), COALESCE(SUM(done),0) FROM tasks
            WHERE day=? AND TRIM(task)!=''
        """, (self.day.isoformat(),)).fetchone()
        percent = int(done * 100 / total) if total else 0
        self.progress.value = percent
        self.progress_label.text = fa(f"پیشرفت امروز: {digits(percent)}٪")

    def refresh(self):
        self.cards.clear_widgets()
        key = self.day.isoformat()
        for section, title, limit in self.sections:
            rows = self.db.execute("""
                SELECT id,task,done FROM tasks
                WHERE day=? AND section=? ORDER BY id
            """, (key, section)).fetchall()
            visible = [r for r in rows if self.search_value in r[1].casefold()]
            if self.search_value and not visible:
                continue

            card = BoxLayout(orientation="vertical", padding=dp(10),
                             spacing=dp(7), size_hint_y=None)
            rounded(card, CARD, 15)
            heading = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(5))
            heading.add_widget(FaLabel(title, bold=True, font_size="14sp",
                                       color=DARK_GREEN))
            add = FaButton("+ افزودن", size_hint_x=None, width=dp(82),
                           font_size="11sp", background_color=GREEN)
            add.bind(on_release=lambda _b, s=section, lim=limit:
                     self.add_task(s, lim))
            heading.add_widget(add)
            card.add_widget(heading)

            for task_id, task, done in visible:
                card.add_widget(self.task_row(task_id, task, done))

            card.height = dp(44) + dp(54) * len(visible)
            if not visible:
                card.height = dp(52)
            self.cards.add_widget(card)
        self.update_progress()

    def task_row(self, task_id, task, done):
        row = BoxLayout(size_hint_y=None, height=dp(49), spacing=dp(8),
                        padding=[dp(5), dp(3), dp(5), dp(3)])
        rounded(row, WHITE, 9)

        # مربع انجام کار در سمت راست؛ لنگر عمودی باعث می‌شود دقیقاً وسط سطر بماند.
        check_holder = AnchorLayout(
            size_hint=(None, 1), width=dp(20),
            anchor_x="center", anchor_y="center"
        )
        check = Button(
            text=fa("✓") if done else "",
            size_hint=(None, None), size=(dp(13), dp(13)),
            font_name=APP_FONT, font_size="11sp",
            color=WHITE,
            background_normal="", background_down="",
            background_color=GREEN if done else WHITE
        )

        # حاشیه طوسی مربع در حالت انجام‌نشده
        with check.canvas.after:
            Color(*(DARK_GREEN if done else MUTED))
            border = Line(
                rectangle=(check.x, check.y, check.width, check.height),
                width=1.2
            )

        def update_check_border(_obj, *_):
            border.rectangle = (check.x, check.y, check.width, check.height)

        check.bind(pos=update_check_border, size=update_check_border)
        check.bind(on_release=lambda _b, tid=task_id, value=not bool(done):
                   self.set_done(tid, value))
        check_holder.add_widget(check)

        # لمس متن کار، پنجره ویرایش را باز می‌کند؛ متن راست‌چین است.
        label = FaButton(
            task, background_color=(0, 0, 0, 0),
            color=MUTED if done else TEXT,
            font_size="12sp", halign="right", valign="middle",
            size_hint_x=1
        )
        label.bind(size=lambda obj, _value:
                   setattr(obj, "text_size", (obj.width, obj.height)))
        label.text_size = (label.width, label.height)
        label.bind(on_release=lambda _b, tid=task_id, old=task:
                   self.edit_task(tid, old))

        # ابتدا متن و سپس مربع اضافه می‌شود تا مربع در انتهای سمت راست قرار بگیرد.
        row.add_widget(label)
        row.add_widget(check_holder)
        return row

    def add_task(self, section, limit):
        key = self.day.isoformat()
        count = self.db.execute(
            "SELECT COUNT(*) FROM tasks WHERE day=? AND section=?",
            (key, section)).fetchone()[0]
        if limit and count >= limit:
            self.message("این بخش حداکثر سه کار دارد.")
            return
        self.db.execute(
            "INSERT INTO tasks(day,section,task,done) VALUES(?,?, '',0)",
            (key, section))
        self.db.commit()
        task_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        self.refresh()
        self.edit_task(task_id, "")

    def edit_task(self, task_id, old_text):
        field = TextInput(text=old_text, multiline=False, halign="right",
                          font_name=APP_FONT, font_size="14sp",
                          foreground_color=TEXT, cursor_color=GREEN,
                          background_normal="", background_active="",
                          background_color=CARD, padding=[dp(10), dp(12)])
        body = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(9))
        body.add_widget(field)
        buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        save = FaButton("ذخیره", background_color=GREEN)
        cancel = FaButton("انصراف", background_color=MUTED)
        buttons.add_widget(save)
        buttons.add_widget(cancel)
        body.add_widget(buttons)
        popup = Popup(title=fa("ویرایش کار"), content=body,
                      size_hint=(.88, None), height=dp(175),
                      title_font=APP_FONT)
        save.bind(on_release=lambda *_:
                  self.save_edit(task_id, field.text, popup))
        cancel.bind(on_release=popup.dismiss)
        popup.open()
        field.focus = True

    def save_edit(self, task_id, value, popup):
        self.db.execute("UPDATE tasks SET task=? WHERE id=?",
                        (value.strip(), task_id))
        self.db.commit()
        popup.dismiss()
        self.refresh()

    def set_done(self, task_id, value):
        self.db.execute("UPDATE tasks SET done=? WHERE id=?",
                        (int(value), task_id))
        self.db.commit()
        self.refresh()

    def delete_task(self, task_id):
        self.db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.db.commit()
        self.refresh()

    def message(self, message):
        popup = Popup(title=fa("برنامه‌یار"),
                      content=FaLabel(message, font_size="13sp"),
                      size_hint=(.82, .28), title_font=APP_FONT)
        popup.open()

    def open_side_menu(self):
        body = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        title = FaLabel("بخش‌های برنامه", bold=True, font_size="17sp",
                        color=DARK_GREEN, size_hint_y=None, height=dp(42))
        body.add_widget(title)
        chله = FaButton("چله | اهداف ۴۰ روزه", background_color=GREEN,
                        size_hint_y=None, height=dp(48))
        chله.bind(on_release=lambda *_: self.open_goals40())
        body.add_widget(chله)
        close = FaButton("بستن", background_color=MUTED,
                         size_hint_y=None, height=dp(42))
        body.add_widget(close)
        popup = Popup(title=fa("منوی کناری"), content=body,
                      size_hint=(.78, .48), title_font=APP_FONT)
        close.bind(on_release=popup.dismiss)
        chله.bind(on_release=lambda *_: (popup.dismiss(), self.open_goals40()))
        popup.open()

    def open_goals40(self):
        body = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        body.add_widget(FaLabel("اهداف ۴۰ روزه", bold=True, font_size="16sp",
                                color=DARK_GREEN, size_hint_y=None, height=dp(35)))

        self.goals_list = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.goals_list.bind(minimum_height=self.goals_list.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.goals_list)
        body.add_widget(scroll)

        field = TextInput(
            hint_text=fa("هدف جدید را بنویسید"), multiline=False,
            halign="right", font_name=APP_FONT, font_size="13sp",
            size_hint_y=None, height=dp(42),
            background_normal="", background_active="",
            background_color=CARD, foreground_color=TEXT
        )
        body.add_widget(field)
        actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(7))
        add = FaButton("افزودن هدف", background_color=GREEN)
        close = FaButton("بستن", background_color=MUTED)
        actions.add_widget(add)
        actions.add_widget(close)
        body.add_widget(actions)

        popup = Popup(title=fa("چله"), content=body,
                      size_hint=(.9, .78), title_font=APP_FONT)
        add.bind(on_release=lambda *_: self.add_goal40(field))
        close.bind(on_release=popup.dismiss)
        self.goals_popup = popup
        self.refresh_goals40()
        popup.open()

    def refresh_goals40(self):
        if not hasattr(self, "goals_list"):
            return
        self.goals_list.clear_widgets()
        rows = self.db.execute(
            "SELECT id,title,done FROM goals40 ORDER BY id"
        ).fetchall()
        if not rows:
            self.goals_list.add_widget(FaLabel(
                "هنوز هدفی ثبت نشده است.", color=MUTED, font_size="12sp",
                size_hint_y=None, height=dp(40)))
        for goal_id, title, done in rows:
            line = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            tick = Button(
                text=fa("✓") if done else "",
                size_hint_x=None, width=dp(30), font_name=APP_FONT,
                background_normal="", background_down="",
                background_color=GREEN if done else YELLOW,
                color=WHITE)
            tick.bind(on_release=lambda _b, gid=goal_id, val=not bool(done):
                      self.toggle_goal40(gid, val))
            name = FaButton(title, background_color=CARD,
                            color=MUTED if done else TEXT, font_size="12sp")
            name.bind(on_release=lambda _b, gid=goal_id, old=title:
                      self.edit_goal40(gid, old))
            remove = FaButton("حذف", size_hint_x=None, width=dp(48),
                              background_color=RED, font_size="10sp")
            remove.bind(on_release=lambda _b, gid=goal_id:
                        self.delete_goal40(gid))
            line.add_widget(tick)
            line.add_widget(name)
            line.add_widget(remove)
            self.goals_list.add_widget(line)

    def add_goal40(self, field):
        value = field.text.strip()
        if not value:
            return
        self.db.execute("INSERT INTO goals40(title,done) VALUES(?,0)", (value,))
        self.db.commit()
        field.text = ""
        self.refresh_goals40()

    def toggle_goal40(self, goal_id, value):
        self.db.execute("UPDATE goals40 SET done=? WHERE id=?",
                        (int(value), goal_id))
        self.db.commit()
        self.refresh_goals40()

    def edit_goal40(self, goal_id, old):
        field = TextInput(text=old, multiline=False, halign="right",
                          font_name=APP_FONT, font_size="13sp")
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        content.add_widget(field)
        save = FaButton("ذخیره", background_color=GREEN,
                        size_hint_y=None, height=dp(40))
        content.add_widget(save)
        popup = Popup(title=fa("ویرایش هدف"), content=content,
                      size_hint=(.85, .25), title_font=APP_FONT)
        save.bind(on_release=lambda *_: (
            self.db.execute("UPDATE goals40 SET title=? WHERE id=?",
                            (field.text.strip(), goal_id)),
            self.db.commit(), popup.dismiss(), self.refresh_goals40()
        ))
        popup.open()

    def delete_goal40(self, goal_id):
        self.db.execute("DELETE FROM goals40 WHERE id=?", (goal_id,))
        self.db.commit()
        self.refresh_goals40()

    def make_bottom_nav(self):
        nav = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(4),
                        padding=[dp(3), dp(2), dp(3), 0])
        rounded(nav, WHITE, 13)
        for symbol, title in [("⌂", "خانه"), ("▥", "آمار"),
                              ("▣", "برنامه"), ("⚙", "تنظیمات")]:
            button = FaButton(f"{symbol}  {title}", background_color=WHITE,
                              color=GREEN if title == "خانه" else MUTED,
                              font_size="11sp")
            button.bind(on_release=lambda _b, name=title: self.nav_action(name))
            nav.add_widget(button)
        self.root_box.add_widget(nav)

    def nav_action(self, name):
        if name == "خانه":
            self.search.text = ""
            self.refresh()
        elif name == "آمار":
            total, done = self.db.execute("""
                SELECT COUNT(*),COALESCE(SUM(done),0) FROM tasks
                WHERE day=? AND TRIM(task)!=''
            """, (self.day.isoformat(),)).fetchone()
            self.message(f"تعداد کارها: {digits(total)}\nانجام‌شده: {digits(done)}")
        elif name == "برنامه":
            self.change_day(1)
        else:
            self.message("بخش تنظیمات در نسخه بعدی تکمیل می‌شود.")

    def change_day(self, amount):
        self.day += timedelta(days=amount)
        self.load_defaults()
        self.update_week()
        self.update_hadith()
        self.update_occasions()
        self.refresh()

    def on_stop(self):
        try:
            self.db.close()
        except Exception:
            pass


if __name__ == "__main__":
    PlannerApp().run()
