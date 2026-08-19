import hashlib
from pathlib import Path
from typing import Any, cast

import pytest
from markupsafe import Markup
from mock import AsyncMock, MagicMock
from starlette.datastructures import URL

from app.controllers.admin.models import EngineProjection
from app.controllers.admin.views import EngineView
from app.controllers.admin.views.base import AdminModelView, LargeTextAreaWidget, PrettyJSONField
from app.controllers.admin.views.mixins import SyncProjectionsMixin
from app.dto.projections import StartSyncAllProjectionsCmd
from app.infra.common.correlation import RequestContext, with_request_context


def test_engine_view_uses_shared_admin_components():
    assert issubclass(EngineView, SyncProjectionsMixin)
    assert issubclass(EngineView, AdminModelView)
    assert EngineView.form_overrides["config"] is PrettyJSONField
    assert EngineView.create_template == "admin/create.html"
    assert EngineView.details_template == "admin/details.html"
    assert EngineView.edit_template == "admin/edit.html"


def test_json_editor_uses_code_friendly_textarea():
    field = MagicMock()
    field.id = "config"
    field.name = "config"
    field.flags = MagicMock()
    field._value.return_value = "{}"

    rendered = LargeTextAreaWidget()(field)

    assert 'data-json-editor="true"' in rendered
    assert 'spellcheck="false"' in rendered
    assert "ui-monospace" in rendered
    assert "min-height: 32rem" in rendered


def test_json_editor_assets_are_self_hosted():
    admin_dir = Path(__file__).parents[1] / "app/controllers/admin"
    editor_script = (admin_dir / "statics/json-editor.js").read_text()
    script_template = (admin_dir / "templates/admin/json-editor-scripts.html").read_text()

    assert "CodeMirror.fromTextArea" in editor_script
    assert 'mode: { name: "javascript", json: true }' in editor_script
    assert 'button("Format"' in editor_script
    assert 'button("Minify"' in editor_script
    assert 'addEventListener("submit"' in editor_script
    assert "https://" not in script_template
    assert "codemirror/lib/codemirror.js" in script_template


def test_vendored_codemirror_files_match_manifest():
    codemirror_dir = Path(__file__).parents[1] / "app/controllers/admin/statics/codemirror"

    for entry in (codemirror_dir / "SHA256SUMS").read_text().splitlines():
        expected_hash, relative_path = entry.split("  ", maxsplit=1)
        actual_hash = hashlib.sha256((codemirror_dir / relative_path).read_bytes()).hexdigest()

        assert actual_hash == expected_hash, f"CodeMirror asset changed: {relative_path}"


def test_json_viewer_uses_editor_surface_styles():
    admin_dir = Path(__file__).parents[1] / "app/controllers/admin"
    details_template = (admin_dir / "templates/admin/details.html").read_text()
    editor_styles = (admin_dir / "statics/json-editor.css").read_text()

    assert "json-editor.css" in details_template
    assert ".json-viewer-surface" in editor_styles
    assert "background: #fff" in editor_styles
    assert ".json-viewer-surface td.code pre" in editor_styles
    assert "color: #000" in editor_styles
    assert "white-space: nowrap" in editor_styles
    assert "width: 1%" in editor_styles


def test_engine_view_formats_config_as_escaped_markup():
    model = EngineProjection(config={"enabled": True, "value": "</textarea><script>alert(1)</script>"})

    formatted = EngineView.format_config(model, "config")

    assert isinstance(formatted, Markup)
    assert "data-json-viewer" in formatted
    assert "data-json-copy" in formatted
    assert "data-json-wrap" in formatted
    assert 'class="json-viewer-surface"' in formatted
    assert '<td class="linenos">' in formatted
    assert "2 keys" in formatted
    assert "color:" in formatted
    assert 'style="background: #f0f0f0"' not in formatted
    assert "</textarea><script>" not in formatted
    assert "&lt;/textarea&gt;&lt;script&gt;" in formatted


@pytest.mark.asyncio
async def test_sync_action_starts_projection_sync_and_redirects_to_list():
    view = EngineView()
    start_projection_sync = AsyncMock()
    cast(Any, view).start_projection_sync = start_projection_sync
    request = MagicMock()
    request.url_for.return_value = URL("http://testserver/admin/engine/list")

    with with_request_context(RequestContext(request_id="request-id")):
        response = await view.start_syncing_all_projections(request)

    start_projection_sync.assert_awaited_once_with(StartSyncAllProjectionsCmd(correlation_id="request-id"))
    request.url_for.assert_called_once_with("admin:list", identity="engine-projection")
    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/admin/engine/list"
