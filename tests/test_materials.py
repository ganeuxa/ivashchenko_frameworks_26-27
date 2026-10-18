import pytest

from materials import add_material, find_materials, sort_materials


def test_add_material():
    materials = {}
    material_id = add_material(materials, "Бумага А4", "пачка", 10)
    assert material_id == 1
    assert materials[1]["name"] == "Бумага А4"


def test_add_duplicate_material_forbidden():
    materials = {}
    add_material(materials, "Бумага А4", "пачка", 10)
    with pytest.raises(ValueError):
        add_material(materials, "бумага а4", "пачка", 5)


def test_find_materials_ignores_case():
    materials = {}
    add_material(materials, "Бумага А4", "пачка", 10)
    add_material(materials, "Картридж HP 85A", "шт", 3)
    assert list(find_materials(materials, "БУМАГА")) == [1]


def test_sort_materials_by_name():
    materials = {}
    add_material(materials, "Ручка", "шт", 50)
    add_material(materials, "Бумага", "пачка", 10)
    names = [material["name"] for _, material in sort_materials(materials)]
    assert names == ["Бумага", "Ручка"]
