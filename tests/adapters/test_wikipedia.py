from llm_panel.adapters.wikipedia import html_to_text

HTML = """
<div class="mw-parser-output">
<p>Intro text.<sup class="reference">[1]</sup></p>
<h2>Effects</h2>
<p>A 2012 study found a 7 percent rise.</p>
<table><tr><th>Year</th><th>Rate</th></tr><tr><td>2012</td><td>7</td></tr></table>
<style>.x{color:red}</style>
<div class="navbox"><p>Navigation junk</p></div>
<h2>References</h2>
<ol class="references"><li>Citation text</li></ol>
</div>
"""


def test_headings_and_paragraphs_kept_in_order():
    text = html_to_text(HTML)
    assert text.index("Intro text.") < text.index("Effects") < text.index("A 2012 study")


def test_reference_markers_style_and_navbox_dropped():
    text = html_to_text(HTML)
    assert "[1]" not in text
    assert "color:red" not in text
    assert "Navigation junk" not in text


def test_reference_section_dropped():
    text = html_to_text(HTML)
    assert "Citation text" not in text


def test_table_cells_kept():
    text = html_to_text(HTML)
    assert "Year" in text and "2012" in text


def test_deterministic():
    assert html_to_text(HTML) == html_to_text(HTML)
