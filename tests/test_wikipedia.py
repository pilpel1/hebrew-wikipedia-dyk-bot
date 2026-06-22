from wiki_didyouknow_bot.wikipedia import parse_did_you_know_html


def test_parse_did_you_know_html_extracts_text_and_image():
    html = """
    <section>
      <h2><a href="/wiki/ויקיפדיה:הידעת%3F">הידעת</a></h2>
      <img alt="הידעת?" src="//upload.wikimedia.org/icon.png" />
      <figure>
        <img alt="דוגמה" src="//upload.wikimedia.org/example.jpg" />
        <figcaption>כיתוב תמונה שלא צריך להופיע בטקסט</figcaption>
      </figure>
      <p>ב<a href="/wiki/ארץ_האש">ארץ האש</a> יש אתר הקרוי על שם ה<a href="/wiki/קונקיסטדור">קונקיסטדור</a>.</p>
      <p>הוא העניק ל<a href="/wiki/רכס_הרים">רכס</a><a href="/wiki/גבעה">גבעות</a> שם מיוחד.</p>
      <p>עוד משפט קצר.</p>
      <div style="clear: left; float: left;"><a href="/wiki/ויקיפדיה:הידעת%3F">לקטעי "הידעת?" נוספים</a></div>
    </section>
    """

    item = parse_did_you_know_html(html)

    assert item.image_url == "https://upload.wikimedia.org/example.jpg"
    assert item.source_url == "https://he.wikipedia.org/wiki/ויקיפדיה:הידעת%3F"
    assert "בארץ האש" in item.text
    assert "הקונקיסטדור" in item.text
    assert "לרכס גבעות" in item.text
    assert "עוד משפט קצר" in item.text
    assert "כיתוב תמונה" not in item.text
    assert "לקטעי" not in item.text
    assert '<a href="https://he.wikipedia.org/wiki/ארץ_האש">ארץ האש</a>' in item.html_text
    assert 'ה<a href="https://he.wikipedia.org/wiki/קונקיסטדור">קונקיסטדור</a>' in item.html_text
    assert '<a href="https://he.wikipedia.org/wiki/רכס_הרים">רכס</a> <a href="https://he.wikipedia.org/wiki/גבעה">גבעות</a>' in item.html_text
