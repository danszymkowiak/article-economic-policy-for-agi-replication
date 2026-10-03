from llm_panel.bootstrap.env import load_dotenv


def test_loads_plain_quoted_and_exported_values_and_skips_comments(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "# comment\n\nA=1\nB='two words'\nC=\"3\"\nexport D=4\nE = 5 \nnot a pair\n", "utf-8"
    )
    environ: dict = {}
    names = load_dotenv(path, environ)
    assert environ == {"A": "1", "B": "two words", "C": "3", "D": "4", "E": "5"}
    assert names == ["A", "B", "C", "D", "E"]


def test_does_not_override_existing_environment(tmp_path):
    path = tmp_path / ".env"
    path.write_text("A=from_file\nB=new\n", "utf-8")
    environ = {"A": "from_env"}
    assert load_dotenv(path, environ) == ["B"]
    assert environ == {"A": "from_env", "B": "new"}


def test_missing_file_is_a_noop(tmp_path):
    environ: dict = {}
    assert load_dotenv(tmp_path / ".env", environ) == []
    assert environ == {}
