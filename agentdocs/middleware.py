"""Discovery headers and markdown content negotiation."""

from pathlib import Path

from django.http import HttpResponse

LLMS = Path(__file__).resolve().parent / "docs" / "llms.txt"

LINK = (
    '</.well-known/api-catalog>; rel="api-catalog", '
    '</auth.md>; rel="describedby"; type="text/markdown", '
    '</.well-known/agent-card.json>; rel="a2a-agent-card", '
    '</.well-known/ai-catalog.json>; rel="ai-catalog"'
)


class AgentDiscoveryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method in ("GET", "HEAD")
            and request.path == "/"
            and "text/markdown" in request.headers.get("Accept", "")
            and LLMS.is_file()
        ):
            content = LLMS.read_text(encoding="utf-8")
            response = HttpResponse(content, content_type="text/markdown; charset=utf-8")
            response["Link"] = LINK
            response["X-Markdown-Tokens"] = str(
                max(1, round(len(content.split()) / 0.75))
            )
            return response

        response = self.get_response(request)
        if response.get("Content-Type", "").startswith("text/html"):
            response["Link"] = LINK
        if request.path.startswith("/.well-known/"):
            response["Access-Control-Allow-Origin"] = "*"
        return response
