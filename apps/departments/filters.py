from dataclasses import dataclass


@dataclass
class DepartmentFilterParams:
    search: str

    @classmethod
    def from_request(cls, request) -> "DepartmentFilterParams":
        return cls(search=request.GET.get("search", "").strip())