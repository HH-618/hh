"""`list_pets` tool: adapts GET /api/v1/pets from the Go REST API."""

from __future__ import annotations

import time
from typing import Any, Literal

from pydantic import BaseModel, Field, NonNegativeInt, model_validator

from ..errors import McpToolError, ValidationError
from ..logging_config import log_tool_call
from ..rest_client import PetHospitalRestClient

# --- Enums mirroring GET /api/v1/meta -------------------------------------

Species = Literal["犬", "猫", "兔", "鸟", "仓鼠", "爬宠", "其他"]
Status = Literal["待就诊", "就诊中", "住院中", "已康复", "慢性病随访"]
SortBy = Literal[
    "id", "name", "ownerName", "species", "doctor", "disease",
    "status", "totalCost", "visitCount", "createdAt", "updatedAt",
]
Order = Literal["asc", "desc"]


# --- Sub-models for nested records / charges -------------------------------

class MedicalRecord(BaseModel):
    id: str | None = None
    visitDate: str | None = None
    doctor: str | None = None
    diagnosis: str | None = None
    symptoms: str | None = None
    treatment: str | None = None
    prescription: list[str] | None = None
    weightKg: float | None = None
    temperature: float | None = None
    followUp: str | None = None
    charge: float | None = None
    createdAt: str | None = None


class ChargeItem(BaseModel):
    id: str | None = None
    item: str | None = None
    category: str | None = None
    amount: float | None = None
    doctor: str | None = None
    date: str | None = None


class PetItem(BaseModel):
    id: str
    name: str
    species: str | None = None
    breed: str | None = None
    gender: str | None = None
    ageMonths: int | None = None
    color: str | None = None
    chipNo: str | None = None
    ownerName: str | None = None
    ownerPhone: str | None = None
    ownerAddr: str | None = None
    doctor: str | None = None
    disease: str | None = None
    status: str | None = None
    allergy: str | None = None
    note: str | None = None
    records: list[MedicalRecord] | None = None
    charges: list[ChargeItem] | None = None
    totalCost: float | None = None
    visitCount: int | None = None
    createdAt: str | None = None
    updatedAt: str | None = None


# --- Input / output models --------------------------------------------------

class ListPetsInput(BaseModel):
    """Parameters for `list_pets`; mirrors GET /api/v1/pets query string."""

    model_config = {"extra": "forbid"}

    q: str | None = Field(None, description="Full-text keyword search (AND across space-separated terms)")
    name: str | None = Field(None, description="Filter by pet name (partial match)")
    ownerName: str | None = Field(None, description="Filter by owner name (partial match)")
    ownerPhone: str | None = Field(None, description="Filter by owner phone (exact match)")
    species: Species | None = Field(None, description="Filter by species")
    doctor: str | None = Field(None, description="Filter by attending doctor")
    disease: str | None = Field(None, description="Filter by disease / diagnosis")
    status: Status | None = Field(None, description="Filter by visit status")
    min: NonNegativeInt | None = Field(None, description="Minimum total cost (yuan)")
    max: NonNegativeInt | None = Field(None, description="Maximum total cost (yuan)")
    sortBy: SortBy | None = Field(None, description="Sort field")
    order: Order | None = Field("asc", description="Sort direction")
    page: int = Field(1, ge=1, description="Page number, starts at 1")
    pageSize: int = Field(20, ge=1, le=500, description="Items per page, 1..500")

    @model_validator(mode="after")
    def _check_range(self) -> "ListPetsInput":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("`min` must be <= `max`")
        return self


class ListPetsOutput(BaseModel):
    """Successful response matching the Go API `data` envelope."""

    items: list[PetItem]
    total: int
    page: int
    pageSize: int
    totalPages: int
    totalCost: float | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


# --- Tool handler -----------------------------------------------------------

async def list_pets(
    params: ListPetsInput,
    rest_client: PetHospitalRestClient,
) -> ListPetsOutput:
    """Search and list pet records from the hospital.

    Use this tool when the user asks to browse, filter, search, sort or paginate
    pet archives — e.g. "show all dogs waiting for treatment", "find pets owned by
    张三", "top 10 highest spending cats", or "page 2 of chronic-follow-up cases".

    Args:
        params: Filtering, sorting and pagination parameters.
        rest_client: Injected REST client.

    Returns:
        A page of pet items plus pagination totals and aggregate total cost.
    """
    started = time.perf_counter()
    params_dict = params.model_dump(mode="json", exclude_none=True)
    status = "ok"
    error: McpToolError | None = None

    try:
        data = await rest_client.get_pets(params_dict)
        # Validate the shape we expect; let Pydantic coerce / drop unknown fields.
        output = ListPetsOutput.model_validate(data)
        return output
    except McpToolError as exc:
        status = "error"
        error = exc
        raise
    except Exception as exc:
        status = "error"
        error = ValidationError(f"Unexpected error: {exc!r}")
        raise error from exc
    finally:
        duration_ms = (time.perf_counter() - started) * 1000
        log_tool_call(
            tool_name="list_pets",
            params=params_dict,
            status=status,
            duration_ms=duration_ms,
            extra={"error": error.to_dict()["error"]} if error else None,
        )
