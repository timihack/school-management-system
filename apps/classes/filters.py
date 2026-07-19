from dataclasses import dataclass


@dataclass
class ClassLevelFilterParams:
    search: str

    @classmethod
    def from_request(cls, request) -> "ClassLevelFilterParams":
        return cls(search=request.GET.get("search", "").strip())