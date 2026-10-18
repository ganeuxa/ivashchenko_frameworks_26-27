from utils import next_id


def add_material(
    materials: dict[int, dict],
    name: str,
    unit: str,
    min_balance: int,
) -> int:
    """Добавляет материал и возвращает его номер."""
    existing_names = {item["name"].lower() for item in materials.values()}
    if name.lower() in existing_names:
        raise ValueError(f"Материал «{name}» уже есть")
    material_id = next_id(materials)
    materials[material_id] = {
        "name": name,
        "unit": unit,
        "min_balance": min_balance,
    }
    return material_id


def get_material(materials: dict[int, dict], material_id: int) -> dict:
    """Возвращает материал по номеру."""
    if material_id not in materials:
        raise ValueError(f"Материала с номером {material_id} нет")
    return materials[material_id]


def find_materials(materials: dict[int, dict], query: str) -> dict[int, dict]:
    """Ищет материалы по части названия без учёта регистра."""
    query = query.lower()
    return {
        material_id: material
        for material_id, material in materials.items()
        if query in material["name"].lower()
    }


def sort_materials(materials: dict[int, dict]) -> list[tuple[int, dict]]:
    """Сортирует материалы по названию."""
    return sorted(materials.items(), key=lambda item: item[1]["name"].lower())
