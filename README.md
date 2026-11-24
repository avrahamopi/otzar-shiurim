# אוצר שיעורי הישיבות

## מבנה
- `data/yeshivot.json` – 62 ישיבות ההסדר מרשימת האיגוד (hesder.org.il), עם אזור וראשי ישיבה.
- `data/channels.json` – מקור השיעורים לכל ישיבה (ערוץ יוטיוב, אתר). כאן מוסיפים ישיבה חדשה.
- `data/shiurim.json` – כל השיעורים (נוצר אוטומטית).
- `ingest/ingest.py` – מושך שיעורים חדשים מפיד ה-RSS של כל ערוץ ומתייג אותם.
- `ingest/tagger.py` – תיוג אוטומטי של רב ונושא לפי הכותרת.
- `ingest/build_site.py` – בונה את `dist/index.html` מהנתונים.

## הרצה
```
python3 ingest/ingest.py        # משיכת שיעורים חדשים (צריך אינטרנט רגיל)
python3 ingest/build_site.py    # בניית האתר
```
אופציונלי: `YT_API_KEY=...` כדי להוסיף אורך שיעור לשיעורים חדשים.

להרצה אוטומטית כל כמה שעות: GitHub Actions עם cron, ופרסום `dist/` ל-GitHub Pages / Netlify.

## פידי פודקאסט
```
python3 ingest/build_feeds.py   # כותב dist/feeds/*.xml + cover.jpg + index.json
```
סדר הרצה מלא: `ingest.py` → `build_feeds.py` → `build_site.py`, ואז להעלות את `dist/`.

לפני רישום: למלא ב-`data/feeds_config.json` את `site_url` (הכתובת האמיתית), שם ומייל.
רישום חד-פעמי: Apple Podcasts Connect (podcastsconnect.apple.com) ו-Spotify for Creators — מגישים את כתובת `/feeds/all.xml` (ואפשר גם פידי נושא).

## מקורות שמע
- `wordpress` בקובץ channels.json — אתר ישיבה על WordPress עם API (למשל שדרות: sderot.org, סוג `lessons`).
- `podcast` — פיד RSS או מזהה Apple Podcasts.
- `youtube` — לווידאו בלבד.

## העלאה לאוויר בחינם (GitHub Pages)
1. יוצרים מאגר ב-GitHub ומעלים אליו את תיקיית הפרויקט.
2. Settings → Pages → Source: Deploy from a branch → `gh-pages`.
3. (רשות) Settings → Secrets → `YT_API_KEY` כדי לקבל אורך לשיעורי יוטיוב.
4. Actions → update-site → Run workflow. מעכשיו הוא רץ לבד כל 4 שעות.
האתר יעלה בכתובת `https://<שם-משתמש>.github.io/<שם-המאגר>/`, והפידים ב-`/feeds/all.xml`.
