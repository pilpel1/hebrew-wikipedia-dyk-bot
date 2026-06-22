# Hebrew Wikipedia Did You Know Bot

בוט טלגרם קטן ששולח פעם ביום לערוץ את קטע ה"הידעת" היומי מתוך ויקיפדיה העברית, כולל תמונה כאשר קיימת.

## למה ערוץ קודם?

הגרסה הנוכחית בנויה בעיקר לבוט שמפרסם לערוץ. זו הבחירה הפשוטה והנקייה לפרויקט פתוח: אין צורך לשמור משתמשים, לנהל הסרות, או להחזיק מסד נתונים.

כן קיימות פקודות פרטיות אופציונליות:

- `/start`
- `/today`

אפשר לכבות אותן עם:

```env
ENABLE_PRIVATE_COMMANDS=false
```

אם בעתיד תרצה שכל משתמש יוכל להירשם ישירות לבוט, כדאי להוסיף שכבת persistence קטנה עם SQLite, פקודת `/subscribe`, פקודת `/unsubscribe`, ומדיניות פרטיות קצרה.

## דרישות

- Python 3.11 ומעלה
- Bot token מ-BotFather
- ערוץ טלגרם שבו הבוט מוגדר כאדמין עם הרשאת פרסום

## התקנה

```bash
cd /mnt/c/pyth/projects/hebrew-wikipedia-dyk-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

ב-Windows PowerShell:

```powershell
cd C:\pyth\projects\hebrew-wikipedia-dyk-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

הפרויקט מיועד לרוץ בלינוקס. פקודות PowerShell כאן הן רק לנוחות אם עובדים רגע מ-Windows.

## הגדרות

ערוך את `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:your-token
TELEGRAM_CHANNEL_ID=@your_channel_username
DAILY_SEND_TIME=09:00
TIMEZONE=Asia/Jerusalem
ENABLE_PRIVATE_COMMANDS=true
USER_AGENT=hebrew-wikipedia-dyk-bot/0.1
```

הערות:

- `TELEGRAM_CHANNEL_ID` יכול להיות username כמו `@my_channel`, או chat id מספרי.
- `DAILY_SEND_TIME` הוא בפורמט 24 שעות `HH:MM`.
- `.env` חסום ב-`.gitignore`, ולכן סודות לא אמורים להיכנס לגיטהאב.
- הקובץ הציבורי שמעלים לגיטהאב הוא `.env.example`.
- שם הקובץ המקובל הוא `requirements.txt`.

## הרצה

```bash
python -m wiki_didyouknow_bot
```

הבוט עובד ב-polling כדי לשמור על פרויקט פשוט. זה שימושי להרצה מקומית או על שרת משלך.

לפרויקט הזה הדרך המומלצת לפרודקשן היא GitHub Actions: לא מריצים תהליך קבוע, אלא workflow יומי שמפעיל `--send-once`.

בדיקה בלי לשלוח לטלגרם:

```bash
python -m wiki_didyouknow_bot --preview
```

שליחה חד-פעמית לערוץ שהוגדר:

```bash
python -m wiki_didyouknow_bot --send-once
```

## הרצה דרך GitHub Actions

הקובץ `.github/workflows/daily-did-you-know.yml` מריץ את הבוט פעם ביום:

1. מתקין Python.
2. מתקין dependencies.
3. מריץ tests.
4. מפעיל `python -m wiki_didyouknow_bot --send-once`.

צריך להגדיר ב-GitHub repository:

- Secret בשם `TELEGRAM_BOT_TOKEN`
- Secret בשם `TELEGRAM_CHANNEL_ID`
- Variable אופציונלי בשם `DAILY_SEND_TIME`, למשל `09:00`
- Variable אופציונלי בשם `TIMEZONE`, למשל `Asia/Jerusalem`
- Variable אופציונלי בשם `USER_AGENT`

ה-cron של GitHub Actions עובד לפי UTC. כדי להתמודד עם שעון קיץ/חורף בישראל, ה-workflow רץ ב-`06:00 UTC` וגם ב-`07:00 UTC`, אבל שולח רק אם השעה המקומית תואמת ל-`DAILY_SEND_TIME`.

אם רוצים שעה אחרת, בדרך כלל מספיק לשנות את ה-variable `DAILY_SEND_TIME`. אם זו שעה שלא מתאימה ל-`06:00` או `07:00 UTC`, צריך לעדכן גם את שורות ה-cron:

```yaml
- cron: "0 6 * * *"
- cron: "0 7 * * *"
```

אפשר גם להריץ ידנית דרך הטאב `Actions` בזכות `workflow_dispatch`.

## בדיקות

```bash
pytest
```

## מבנה הפרויקט

```text
hebrew-wikipedia-dyk-bot/
├── wiki_didyouknow_bot/
│   ├── __main__.py
│   ├── config.py
│   ├── telegram_bot.py
│   └── wikipedia.py
├── tests/
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## רישיון

MIT
