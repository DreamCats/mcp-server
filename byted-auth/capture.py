from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


@dataclass
class AuthCapture:
    interesting_headers: List[str] = field(
        default_factory=lambda: ["authorization", "set-cookie"]
    )
    auth_headers: List[str] = field(default_factory=list)
    set_cookie_headers: List[str] = field(default_factory=list)
    cookies: List[Dict] = field(default_factory=list)
    responses: List[Dict] = field(default_factory=list)

    def handle_response(self, response) -> None:
        headers = {k.lower(): v for k, v in response.headers.items()}
        captured = {}
        for header_name in self.interesting_headers:
            if header_name in headers:
                captured[header_name] = headers[header_name]

        if not captured:
            return

        if "authorization" in captured:
            self.auth_headers.append(captured["authorization"])
        if "set-cookie" in captured:
            self.set_cookie_headers.append(captured["set-cookie"])

        self.responses.append(
            {"url": response.url, "status": response.status, "headers": captured}
        )

    def record_cookies(self, cookies: List[Dict]) -> None:
        self.cookies = cookies or []

    def to_payload(
        self, login_url: str, final_url: Optional[str] = None
    ) -> Dict[str, object]:
        return {
            "login_url": login_url,
            "final_url": final_url,
            "headers": {
                "authorization": _dedupe(self.auth_headers),
                "set-cookie": _dedupe(self.set_cookie_headers),
            },
            "cookies": self.cookies,
            "responses": self.responses,
        }
