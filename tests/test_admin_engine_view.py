from typing import Any, cast

import pytest
from markupsafe import Markup
from mock import AsyncMock, MagicMock
from starlette.datastructures import URL

from app.controllers.admin.models import EngineProjection
from app.controllers.admin.views import EngineView
from app.controllers.admin.views.base import AdminModelView, PrettyJSONField
from app.controllers.admin.views.mixins import SyncProjectionsMixin
from app.dto.projections import StartSyncAllProjectionsCmd
from app.infra.common.correlation import RequestContext, with_request_context


def test_engine_view_uses_shared_admin_components():
    assert issubclass(EngineView, SyncProjectionsMixin)
    assert issubclass(EngineView, AdminModelView)
    assert EngineView.form_overrides["config"] is PrettyJSONField


def test_engine_view_formats_config_as_escaped_markup():
    model = EngineProjection(config={"value": "</div>"})

    formatted = EngineView.format_config(model, "config")

    assert isinstance(formatted, Markup)
    assert "</div>" not in str(formatted).removeprefix('<div style="white-space: pre-wrap;">').removesuffix("</div>")
    assert "&lt;/div&gt;" in formatted


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
