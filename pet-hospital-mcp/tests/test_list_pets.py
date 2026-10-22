"""Tests for list_pets tool: input validation, output models, error handling."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from pet_hospital_mcp.tools.list_pets import (
    ListPetsInput,
    ListPetsOutput,
    MedicalRecord,
    ChargeItem,
    PetItem,
)


class TestListPetsInputValidation:
    def test_defaults(self):
        params = ListPetsInput()
        assert params.page == 1
        assert params.pageSize == 20
        assert params.order == "asc"
        assert params.q is None

    def test_species_accepts_valid(self):
        for s in ["犬", "猫", "兔", "鸟", "仓鼠", "爬宠", "其他"]:
            assert ListPetsInput(species=s).species == s

    def test_species_rejects_invalid(self):
        with pytest.raises(PydanticValidationError):
            ListPetsInput(species="恐龙")

    def test_status_accepts_valid(self):
        for s in ["待就诊", "就诊中", "住院中", "已康复", "慢性病随访"]:
            assert ListPetsInput(status=s).status == s

    def test_status_rejects_invalid(self):
        with pytest.raises(PydanticValidationError):
            ListPetsInput(status="痊愈")

    def test_sortBy_accepts_valid(self):
        for f in [
            "id", "name", "ownerName", "species", "doctor", "disease",
            "status", "totalCost", "visitCount", "createdAt", "updatedAt",
        ]:
            assert ListPetsInput(sortBy=f).sortBy == f

    def test_sortBy_rejects_invalid(self):
        with pytest.raises(PydanticValidationError):
            ListPetsInput(sortBy="notAField")

    def test_order_accepts_asc_desc(self):
        assert ListPetsInput(order="asc").order == "asc"
        assert ListPetsInput(order="desc").order == "desc"

    def test_order_rejects_invalid(self):
        with pytest.raises(PydanticValidationError):
            ListPetsInput(order="sideways")

    def test_page_must_be_ge_1(self):
        with pytest.raises(PydanticValidationError):
            ListPetsInput(page=0)
        with pytest.raises(PydanticValidationError):
            ListPetsInput(page=-1)

    def test_pageSize_range(self):
        ListPetsInput(pageSize=1)
        ListPetsInput(pageSize=500)
        with pytest.raises(PydanticValidationError):
            ListPetsInput(pageSize=0)
        with pytest.raises(PydanticValidationError):
            ListPetsInput(pageSize=501)

    def test_min_max_non_negative(self):
        ListPetsInput(min=0, max=100)
        with pytest.raises(PydanticValidationError):
            ListPetsInput(min=-1)
        with pytest.raises(PydanticValidationError):
            ListPetsInput(max=-5)

    def test_min_le_max(self):
        ListPetsInput(min=100, max=500)
        ListPetsInput(min=100, max=100)
        with pytest.raises(PydanticValidationError):
            ListPetsInput(min=500, max=100)

    def test_rejects_unknown_fields(self):
        with pytest.raises(PydanticValidationError):
            ListPetsInput(bogus="xxx")

    def test_rejects_nan(self):
        with pytest.raises(PydanticValidationError):
            ListPetsInput(min=float("nan"))

    def test_rejects_inf(self):
        with pytest.raises(PydanticValidationError):
            ListPetsInput(max=float("inf"))

    def test_stringly_typed_numbers_coerced(self):
        # Pydantic should coerce numeric strings to int where possible
        params = ListPetsInput(page="3", pageSize="10")  # type: ignore[arg-type]
        assert params.page == 3
        assert params.pageSize == 10


class TestOutputModels:
    def test_pet_item_with_null_records_and_charges(self):
        item = PetItem(id="PET-1", name="Test", records=None, charges=None)
        assert item.records is None
        assert item.charges is None

    def test_pet_item_with_empty_arrays(self):
        item = PetItem(id="PET-1", name="Test", records=[], charges=[])
        assert item.records == []
        assert item.charges == []

    def test_pet_item_with_full_records(self):
        rec = MedicalRecord(
            id="MR-1",
            visitDate="2024-01-01",
            doctor="Dr. Li",
            diagnosis="cold",
            symptoms="cough",
            treatment="rest",
            prescription=["medicine"],
            weightKg=5.0,
            temperature=39.0,
            followUp="come back",
            charge=100.0,
            createdAt="2024-01-01T00:00:00Z",
        )
        ch = ChargeItem(
            id="CH-1",
            item="medicine",
            category="药品",
            amount=50.0,
            doctor="Dr. Li",
            date="2024-01-01",
        )
        item = PetItem(
            id="PET-1", name="Test", records=[rec], charges=[ch], totalCost=50.0
        )
        assert len(item.records) == 1
        assert len(item.charges) == 1
        assert item.totalCost == 50.0

    def test_list_pets_output_full(self):
        out = ListPetsOutput(
            items=[PetItem(id="PET-1", name="A"), PetItem(id="PET-2", name="B")],
            total=2,
            page=1,
            pageSize=2,
            totalPages=1,
            totalCost=100.0,
        )
        assert len(out.items) == 2
        assert out.total == 2
        assert out.totalPages == 1
