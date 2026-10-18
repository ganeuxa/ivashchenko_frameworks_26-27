import pytest

from models import Material
from models.materials import (
    add_material,
    find_material_by_id,
    find_materials,
    sort_materials,
)


def test_material_creation():
    material = Material(1, "Бумага А4", "пачка", 10)
    assert material.id == 1
    assert material.name == "Бумага А4"
    assert material.unit == "пачка"
    assert material.min_balance == 10


def test_material_str():
    assert str(Material(1, "Бумага А4", "пачка", 10)) == "Бумага А4 (пачка)"


def test_negative_min_balance_forbidden():
    assert not Material.validate_min_balance(-1)
    with pytest.raises(ValueError):
        Material(1, "Бумага А4", "пачка", -1)


def test_needs_reorder():
    material = Material(1, "Бумага А4", "пачка", 10)
    assert material.needs_reorder(5)
    assert not material.needs_reorder(10)


def test_from_data():
    data = {"id": 3, "name": "Ручка", "unit": "шт", "min_balance": 50}
    material = Material.from_data(data)
    assert material.name == "Ручка"
    assert material.to_data() == data


def test_add_material():
    materials = []
    material = add_material(materials, "Бумага А4", "пачка", 10)
    assert materials == [material]
    assert material.id == 1


def test_add_duplicate_material_forbidden():
    materials = []
    add_material(materials, "Бумага А4", "пачка", 10)
    with pytest.raises(ValueError):
        add_material(materials, "бумага а4", "пачка", 5)


def test_find_materials_ignores_case():
    materials = []
    paper = add_material(materials, "Бумага А4", "пачка", 10)
    add_material(materials, "Картридж HP 85A", "шт", 3)
    assert find_materials(materials, "БУМАГА") == [paper]


def test_find_material_by_id():
    materials = []
    paper = add_material(materials, "Бумага А4", "пачка", 10)
    assert find_material_by_id(materials, 1) is paper
    with pytest.raises(ValueError):
        find_material_by_id(materials, 99)


def test_sort_materials_by_name():
    materials = []
    add_material(materials, "Ручка", "шт", 50)
    add_material(materials, "Бумага", "пачка", 10)
    names = [material.name for material in sort_materials(materials)]
    assert names == ["Бумага", "Ручка"]
