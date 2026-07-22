from dataclasses import dataclass


@dataclass
class SessionFilterParams:
    search: str

    @classmethod
    def from_request(cls, request) -> "SessionFilterParams":
        return cls(search=request.GET.get("search", "").strip())