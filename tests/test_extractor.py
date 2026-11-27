from extractor import html_to_markdown
from notifier import check_and_send_alert
from schemas import ProductData


def test_html_to_markdown_strips_scripts():
    sample_html = """
    <html>
      <head><script>console.log("tracking");</script></head>
      <body>
        <h1>INNELO Resistance Bands Set</h1>
        <p>Price: $21.99</p>
        <p>5-level stackable exercise bands with door anchor.</p>
      </body>
    </html>
    """
    md = html_to_markdown(sample_html)
    assert "INNELO Resistance Bands Set" in md
    assert "$21.99" in md
    assert "console.log" not in md


def test_alert_not_triggered_above_target():
    product = ProductData(
        url="https://example.com/item",
        title="Resistance Bands",
        price=29.99,
        currency="USD",
        in_stock=True,
    )
    assert check_and_send_alert(product, target_price=25.00) is False
