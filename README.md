# Hebrew Wikipedia Did You Know Bot

בוט טלגרם קטן ששולח פעם ביום לערוץ את קטע ה"הידעת" היומי מתוך ויקיפדיה העברית, כולל תמונה כאשר קיימת.

כאשר קיימת תמונה, הבוט שולח אותה כהודעה נפרדת ואז שולח את הטקסט כהודעה נפרדת. הטקסט נשלח עם קישורי Telegram לחיצים לערכי ויקיפדיה. אם הטקסט הגלוי ארוך ממגבלת Telegram של `4096` תווים אחרי parsing, הוא מפוצל לכמה הודעות בלי לשבור מילים או קישורים באמצע.

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

הקובץ `.github/workflows/daily-did-you-know.yml` מריץ את הבוט:

1. מתקין Python.
2. מתקין dependencies.
3. מריץ tests.
4. מפעיל `python -m wiki_didyouknow_bot --send-once`.

ה-workflow מופעל על ידי `workflow_dispatch` בלבד, לא על ידי `schedule`. הסיבה: scheduled workflows של GitHub לא אמינים ויכולים להתעכב שעות או להידלג. לכן את התזמון המדויק עושה מתזמן חיצוני שקורא ל-GitHub API.

צריך להגדיר ב-GitHub repository:

- Secret בשם `TELEGRAM_BOT_TOKEN`
- Secret בשם `TELEGRAM_CHANNEL_ID`
- Variable אופציונלי בשם `USER_AGENT`

### תזמון יומי מדויק עם cron-job.org

1. צור Fine-grained Personal Access Token ב-GitHub:
   - `Settings` (של החשבון) → `Developer settings` → `Personal access tokens` → `Fine-grained tokens`
   - `Repository access`: רק `hebrew-wikipedia-dyk-bot`
   - `Permissions` → `Actions`: `Read and write`
   - שמור את הטוקן, הוא מוצג רק פעם אחת.

2. ב-[cron-job.org](https://cron-job.org) צור job חדש:
   - URL:
     ```text
     https://api.github.com/repos/pilpel1/hebrew-wikipedia-dyk-bot/actions/workflows/daily-did-you-know.yml/dispatches
     ```
   - Method: `POST`
   - Headers:
     ```text
     Accept: application/vnd.github+json
     Authorization: Bearer <הטוקן שלך>
     X-GitHub-Api-Version: 2022-11-28
     ```
   - Request body:
     ```json
     {"ref":"main"}
     ```
   - Schedule: `09:00`, timezone `Asia/Jerusalem` (cron-job.org מטפל בעצמו בשעון קיץ/חורף).

תגובה תקינה מ-GitHub היא `204 No Content`. אם מקבלים `401`/`403`, בדוק את הטוקן וההרשאות. אם מקבלים `404`, בדוק את שם ה-repo ושם קובץ ה-workflow.

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
