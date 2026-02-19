"""Tests for remaining integrations: GitHub, Gmail, Notion, Scraper, ImageGen."""

from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

class TestGitHubClient:

    @patch("goliath.integrations.github.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.GITHUB_TOKEN = ""
        mock_config.GITHUB_OWNER = ""

        from goliath.integrations.github import GitHubClient
        with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
            GitHubClient()

    @patch("goliath.integrations.github.config")
    def test_init_sets_auth_header(self, mock_config):
        mock_config.GITHUB_TOKEN = "ghp_test123"
        mock_config.GITHUB_OWNER = "testuser"

        from goliath.integrations.github import GitHubClient
        client = GitHubClient()
        assert "Bearer ghp_test123" in client.session.headers["Authorization"]
        assert client.owner == "testuser"

    @patch("goliath.integrations.github.config")
    def test_list_repos(self, mock_config):
        mock_config.GITHUB_TOKEN = "ghp_test"
        mock_config.GITHUB_OWNER = "testuser"

        from goliath.integrations.github import GitHubClient
        client = GitHubClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"name": "repo1"}, {"name": "repo2"}]
        client.session.get = MagicMock(return_value=mock_resp)

        repos = client.list_repos()
        assert len(repos) == 2
        url = client.session.get.call_args[0][0]
        assert "/users/testuser/repos" in url

    @patch("goliath.integrations.github.config")
    def test_create_issue(self, mock_config):
        mock_config.GITHUB_TOKEN = "ghp_test"
        mock_config.GITHUB_OWNER = ""

        from goliath.integrations.github import GitHubClient
        client = GitHubClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"number": 42, "title": "Bug"}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.create_issue("owner/repo", title="Bug", body="It broke", labels=["bug"])
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["title"] == "Bug"
        assert payload["labels"] == ["bug"]

    @patch("goliath.integrations.github.config")
    def test_create_repo(self, mock_config):
        mock_config.GITHUB_TOKEN = "ghp_test"
        mock_config.GITHUB_OWNER = ""

        from goliath.integrations.github import GitHubClient
        client = GitHubClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "new-repo", "private": True}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.create_repo("new-repo", description="Test", private=True)
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["private"] is True

    @patch("goliath.integrations.github.config")
    def test_trigger_workflow(self, mock_config):
        mock_config.GITHUB_TOKEN = "ghp_test"
        mock_config.GITHUB_OWNER = ""

        from goliath.integrations.github import GitHubClient
        client = GitHubClient()

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        client.session.post = MagicMock(return_value=mock_resp)

        client.trigger_workflow("owner/repo", "build.yml", ref="main")
        url = client.session.post.call_args[0][0]
        assert "actions/workflows/build.yml/dispatches" in url


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------

class TestGmailClient:

    @patch("goliath.integrations.gmail.config")
    def test_missing_address_raises(self, mock_config):
        mock_config.GMAIL_ADDRESS = ""
        mock_config.GMAIL_APP_PASSWORD = "pass"

        from goliath.integrations.gmail import GmailClient
        with pytest.raises(RuntimeError, match="GMAIL_ADDRESS"):
            GmailClient()

    @patch("goliath.integrations.gmail.config")
    def test_missing_password_raises(self, mock_config):
        mock_config.GMAIL_ADDRESS = "user@gmail.com"
        mock_config.GMAIL_APP_PASSWORD = ""

        from goliath.integrations.gmail import GmailClient
        with pytest.raises(RuntimeError, match="GMAIL_APP_PASSWORD"):
            GmailClient()

    @patch("goliath.integrations.gmail.smtplib")
    @patch("goliath.integrations.gmail.config")
    def test_send_plain_text(self, mock_config, mock_smtplib):
        mock_config.GMAIL_ADDRESS = "sender@gmail.com"
        mock_config.GMAIL_APP_PASSWORD = "app-pass"

        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtplib.SMTP.return_value.__exit__ = MagicMock(return_value=False)

        from goliath.integrations.gmail import GmailClient
        client = GmailClient()
        client.send(to="recipient@example.com", subject="Test", body="Hello")

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@gmail.com", "app-pass")
        mock_server.sendmail.assert_called_once()
        call_args = mock_server.sendmail.call_args[0]
        assert call_args[0] == "sender@gmail.com"
        assert "recipient@example.com" in call_args[1]

    @patch("goliath.integrations.gmail.config")
    def test_attachment_not_found(self, mock_config):
        mock_config.GMAIL_ADDRESS = "sender@gmail.com"
        mock_config.GMAIL_APP_PASSWORD = "app-pass"

        from goliath.integrations.gmail import GmailClient
        client = GmailClient()
        with pytest.raises(FileNotFoundError):
            client.send(
                to="r@example.com",
                subject="Test",
                body="Hello",
                attachments=["/nonexistent/file.pdf"],
            )

    @patch("goliath.integrations.gmail.smtplib")
    @patch("goliath.integrations.gmail.config")
    def test_send_multiple_recipients(self, mock_config, mock_smtplib):
        mock_config.GMAIL_ADDRESS = "sender@gmail.com"
        mock_config.GMAIL_APP_PASSWORD = "app-pass"

        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtplib.SMTP.return_value.__exit__ = MagicMock(return_value=False)

        from goliath.integrations.gmail import GmailClient
        client = GmailClient()
        client.send(
            to=["a@example.com", "b@example.com"],
            subject="Test",
            body="Hello",
            cc="c@example.com",
        )

        recipients = mock_server.sendmail.call_args[0][1]
        assert "a@example.com" in recipients
        assert "b@example.com" in recipients
        assert "c@example.com" in recipients


# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------

class TestNotionClient:

    @patch("goliath.integrations.notion.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.NOTION_API_KEY = ""

        from goliath.integrations.notion import NotionClient
        with pytest.raises(RuntimeError, match="NOTION_API_KEY"):
            NotionClient()

    @patch("goliath.integrations.notion.config")
    def test_init_sets_headers(self, mock_config):
        mock_config.NOTION_API_KEY = "ntn_test123"

        from goliath.integrations.notion import NotionClient
        client = NotionClient()
        assert "Bearer ntn_test123" in client.session.headers["Authorization"]
        assert client.session.headers["Notion-Version"] == "2022-06-28"

    @patch("goliath.integrations.notion.config")
    def test_search(self, mock_config):
        mock_config.NOTION_API_KEY = "ntn_test"

        from goliath.integrations.notion import NotionClient
        client = NotionClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"id": "page_1"}]}
        client.session.post = MagicMock(return_value=mock_resp)

        results = client.search("project plan", filter_type="page")
        assert len(results) == 1
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["query"] == "project plan"
        assert payload["filter"]["value"] == "page"

    @patch("goliath.integrations.notion.config")
    def test_create_page_requires_parent(self, mock_config):
        mock_config.NOTION_API_KEY = "ntn_test"

        from goliath.integrations.notion import NotionClient
        client = NotionClient()
        with pytest.raises(ValueError, match="parent_database_id or parent_page_id"):
            client.create_page(properties={"Name": {"title": []}})

    @patch("goliath.integrations.notion.config")
    def test_create_page_in_database(self, mock_config):
        mock_config.NOTION_API_KEY = "ntn_test"

        from goliath.integrations.notion import NotionClient
        client = NotionClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "page_2"}
        client.session.post = MagicMock(return_value=mock_resp)

        props = {"Name": {"title": [{"text": {"content": "Task"}}]}}
        result = client.create_page(properties=props, parent_database_id="db_1")

        payload = client.session.post.call_args.kwargs["json"]
        assert payload["parent"]["database_id"] == "db_1"

    @patch("goliath.integrations.notion.config")
    def test_query_database(self, mock_config):
        mock_config.NOTION_API_KEY = "ntn_test"

        from goliath.integrations.notion import NotionClient
        client = NotionClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"id": "row_1"}]}
        client.session.post = MagicMock(return_value=mock_resp)

        results = client.query_database(
            "db_1",
            filter={"property": "Status", "select": {"equals": "Done"}},
        )
        assert len(results) == 1

    @patch("goliath.integrations.notion.config")
    def test_append_blocks(self, mock_config):
        mock_config.NOTION_API_KEY = "ntn_test"

        from goliath.integrations.notion import NotionClient
        client = NotionClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"id": "block_1"}]}
        client.session.patch = MagicMock(return_value=mock_resp)

        blocks = [{"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hi"}}]}}]
        client.append_blocks("page_1", children=blocks)

        url = client.session.patch.call_args[0][0]
        assert "blocks/page_1/children" in url

    @patch("goliath.integrations.notion.config")
    def test_delete_block(self, mock_config):
        mock_config.NOTION_API_KEY = "ntn_test"

        from goliath.integrations.notion import NotionClient
        client = NotionClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "block_1", "archived": True}
        client.session.delete = MagicMock(return_value=mock_resp)

        result = client.delete_block("block_1")
        assert result["archived"] is True


# ---------------------------------------------------------------------------
# Web Scraper
# ---------------------------------------------------------------------------

class TestWebScraper:

    def test_url_scheme_validation(self):
        from goliath.integrations.scraper import _validate_url

        _validate_url("https://example.com")  # should not raise
        _validate_url("http://example.com")  # should not raise

        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            _validate_url("file:///etc/passwd")

        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            _validate_url("ftp://example.com/file")

    @patch("goliath.integrations.scraper._validate_url")
    def test_fetch_calls_validate(self, mock_validate):
        from goliath.integrations.scraper import WebScraper

        scraper = WebScraper()
        mock_resp = MagicMock()
        mock_resp.text = "<html><body><h1>Hello</h1></body></html>"
        mock_resp.status_code = 200
        scraper.session.get = MagicMock(return_value=mock_resp)

        scraper.fetch("https://example.com")
        mock_validate.assert_called_once_with("https://example.com")

    @patch("goliath.integrations.scraper._validate_url")
    def test_get_text(self, mock_validate):
        from goliath.integrations.scraper import WebScraper

        scraper = WebScraper()
        mock_resp = MagicMock()
        mock_resp.text = "<html><body><p>Hello World</p><script>bad</script></body></html>"
        scraper.session.get = MagicMock(return_value=mock_resp)

        text = scraper.get_text("https://example.com")
        assert "Hello World" in text
        assert "bad" not in text

    @patch("goliath.integrations.scraper._validate_url")
    def test_get_links(self, mock_validate):
        from goliath.integrations.scraper import WebScraper

        scraper = WebScraper()
        mock_resp = MagicMock()
        mock_resp.text = '<html><body><a href="/about">About</a><a href="https://external.com">Ext</a></body></html>'
        scraper.session.get = MagicMock(return_value=mock_resp)

        links = scraper.get_links("https://example.com")
        assert len(links) == 2
        assert links[0]["text"] == "About"
        assert links[1]["href"] == "https://external.com"

    @patch("goliath.integrations.scraper._validate_url")
    def test_extract(self, mock_validate):
        from goliath.integrations.scraper import WebScraper

        scraper = WebScraper()
        mock_resp = MagicMock()
        mock_resp.text = '<html><body><h1>Title</h1><p class="intro">Intro text</p></body></html>'
        scraper.session.get = MagicMock(return_value=mock_resp)

        result = scraper.extract("https://example.com", {"headings": "h1", "intros": ".intro"})
        assert result["headings"] == ["Title"]
        assert result["intros"] == ["Intro text"]


# ---------------------------------------------------------------------------
# Image Generation
# ---------------------------------------------------------------------------

class TestImageGenClient:

    @patch("goliath.integrations.imagegen.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.OPENAI_API_KEY = ""

        from goliath.integrations.imagegen import ImageGenClient
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            ImageGenClient()

    @patch("goliath.integrations.imagegen.OpenAI")
    @patch("goliath.integrations.imagegen.config")
    def test_generate(self, mock_config, mock_openai_cls):
        mock_config.OPENAI_API_KEY = "sk-test"
        mock_config.IMAGEGEN_DEFAULT_MODEL = "dall-e-3"

        mock_img = MagicMock()
        mock_img.url = "https://oai.com/img.png"
        mock_img.revised_prompt = "A beautiful sunset"
        mock_client = MagicMock()
        mock_client.images.generate.return_value = MagicMock(data=[mock_img])
        mock_openai_cls.return_value = mock_client

        from goliath.integrations.imagegen import ImageGenClient
        client = ImageGenClient()
        result = client.generate("sunset")

        assert result["url"] == "https://oai.com/img.png"
        assert result["revised_prompt"] == "A beautiful sunset"
        mock_client.images.generate.assert_called_once()

    @patch("goliath.integrations.imagegen.OpenAI")
    @patch("goliath.integrations.imagegen.config")
    def test_generate_multiple(self, mock_config, mock_openai_cls):
        mock_config.OPENAI_API_KEY = "sk-test"
        mock_config.IMAGEGEN_DEFAULT_MODEL = "dall-e-2"

        imgs = []
        for i in range(3):
            m = MagicMock()
            m.url = f"https://oai.com/img{i}.png"
            m.revised_prompt = None
            imgs.append(m)
        mock_client = MagicMock()
        mock_client.images.generate.return_value = MagicMock(data=imgs)
        mock_openai_cls.return_value = mock_client

        from goliath.integrations.imagegen import ImageGenClient
        client = ImageGenClient()
        results = client.generate("art", n=3, model="dall-e-2")

        assert isinstance(results, list)
        assert len(results) == 3

    @patch("goliath.integrations.imagegen.OpenAI")
    @patch("goliath.integrations.imagegen.config")
    def test_edit_file_not_found(self, mock_config, mock_openai_cls):
        mock_config.OPENAI_API_KEY = "sk-test"
        mock_config.IMAGEGEN_DEFAULT_MODEL = "dall-e-3"
        mock_openai_cls.return_value = MagicMock()

        from goliath.integrations.imagegen import ImageGenClient
        client = ImageGenClient()
        with pytest.raises(FileNotFoundError, match="Image not found"):
            client.edit(image="/nonexistent/img.png", prompt="add rainbow")

    @patch("goliath.integrations.imagegen.OpenAI")
    @patch("goliath.integrations.imagegen.config")
    def test_variation_file_not_found(self, mock_config, mock_openai_cls):
        mock_config.OPENAI_API_KEY = "sk-test"
        mock_config.IMAGEGEN_DEFAULT_MODEL = "dall-e-3"
        mock_openai_cls.return_value = MagicMock()

        from goliath.integrations.imagegen import ImageGenClient
        client = ImageGenClient()
        with pytest.raises(FileNotFoundError, match="Image not found"):
            client.variation(image="/nonexistent/img.png")
