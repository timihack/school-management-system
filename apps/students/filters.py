from dataclasses import dataclass
from typing import Optional


@dataclass
class StudentFilterParams:
  """
  Parses query-string parameters for the student list page
  (?search=...&status=active). Kept separate from the view so the
  same GET-param parsing can be reused by a future CSV export view
  without duplicating it.
  """

  search: str
  status: str  # 'all' | 'active' | 'inactive'

  @classmethod
  def from_request(cls, request) -> "StudentFilterParams":
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
  