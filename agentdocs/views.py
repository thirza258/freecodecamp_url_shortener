"""Serve generated agent-discovery documents."""

import mimetypes
from pathlib import Path

from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

DOCS_ROOT = (Path(__file__).resolve().parent / "docs").resolve()

_LINKSET = {"api-catalog"}
_TEXT = {".md": "text/markdown; charset=utf-8", ".txt": "text/plain; charset=utf-8"}


def _serve(relative):
    path = (DOCS_ROOT / relative).resolve()
    if DOCS_ROOT not in path.parents or not path.is_file():
        raise Http404("Agent document not found")
    if path.name in _LINKSET:
        content_type = "application/linkset+json; charset=utf-8"
    elif path.suffix in _TEXT:
        content_type = _TEXT[path.suffix]
    elif path.suffix == ".json" or path.parent.name == ".well-known":
        content_type = "application/json; charset=utf-8"
    else:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    response = HttpResponse(path.read_bytes(), content_type=content_type)
    response["Access-Control-Allow-Origin"] = "*"
    return response


@require_GET
def well_known(request, doc_path):
    return _serve(f".well-known/{doc_path}")


@require_GET
def auth_md(request):
    return _serve("auth.md")


@require_GET
def llms_txt(request):
    return _serve("llms.txt")
