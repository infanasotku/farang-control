import json
from typing import Any

from markupsafe import Markup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

_FORMATTER = HtmlFormatter(
    linenos="table",
    nobackground=True,
    noclasses=True,
    style="friendly",
    wrapcode=True,
)

_VIEWER = Markup(
    """
    <details class="json-viewer" data-json-viewer open>
      <summary class="json-viewer-summary">
        <strong>JSON</strong>
        <span class="text-muted"> · {summary} · {size}</span>
      </summary>
      <div class="json-viewer-toolbar">
        <button type="button" class="btn btn-sm" data-json-copy
          onclick="event.preventDefault(); const b=this; const v=b.closest('[data-json-viewer]').querySelector('[data-json-source]').value; navigator.clipboard.writeText(v).then(() => {{ const t=b.textContent; b.textContent='Copied'; setTimeout(() => b.textContent=t, 1200); }});">
          Copy
        </button>
        <button type="button" class="btn btn-sm" data-json-wrap
          onclick="event.preventDefault(); const p=this.closest('[data-json-viewer]').querySelector('td.code pre'); p.style.whiteSpace=p.style.whiteSpace==='pre-wrap'?'pre':'pre-wrap';">
          Toggle wrap
        </button>
      </div>
      <div class="json-viewer-surface">
        {highlighted}
      </div>
      <textarea data-json-source hidden>{source}</textarea>
    </details>
    """
)


def render_json(value: Any) -> Markup:
    source = json.dumps(value, ensure_ascii=False, indent=2)
    highlighted = Markup(highlight(source, JsonLexer(), _FORMATTER))

    if isinstance(value, dict):
        summary = f"{len(value)} keys"
    elif isinstance(value, list):
        summary = f"{len(value)} items"
    else:
        summary = type(value).__name__

    size = _format_size(len(source.encode()))
    return _VIEWER.format(
        highlighted=highlighted,
        size=size,
        source=source,
        summary=summary,
    )


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    return f"{size / 1024:.1f} KiB"
