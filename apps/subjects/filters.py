from dataclasses import dataclass
from typing import Optional


@dataclass
class SubjectFilterParams:
    search: str
    status: str  # "all" | "active" | "inactive"

    @classmethod
    def from_request(cls, request) -> "SubjectFilterParams":
        return cls(
            search=request.GET.get("search", "").strip(),
            status=request.GET.get("status", "all"),
        )

    @property
    def is_active_filter(self) -> Optional[bool]:
        if self.status == "active":
            return True
        if self.status == "inactive":
            return False
        return None