from wiki_didyouknow_bot.wikipedia import parse_did_you_know_html


def test_parse_did_you_know_html_extracts_text_and_image():
    html = """
    <section>
      <h2>הידעת</h2>
      <img alt="הידעת?" src="//upload.wikimedia.org/icon.png" />
      <img alt="דוגמה" src="//upload.wikimedia.org/example.jpg" />
      <p>טקסט מסקרן על העולם.</p>
      <p>עוד משפט קצר.</p>
    </section>
    """

    item = parse_did_you_know_html(html)

    assert item.image_url == "https://upload.wikimedia.org/example.jpg"
    assert "טקסט מסקרן" in item.text
    assert "עוד משפט קצר" in item.text
