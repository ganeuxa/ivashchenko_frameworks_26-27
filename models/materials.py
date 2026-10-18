from utils import next_id


class Material:
    """Расходный материал."""

    def __init__(
        self,
        material_id: int,
        name: str,
        unit: str,
        min_balance: int,
    ) -> None:
        if not Material.validate_min_balance(min_balance):
            raise ValueError("Минимальный остаток не может быть меньше нуля")
        self.id = material_id
        self.name = name
        self.unit = unit
        self.min_balance = min_balance

    @staticmethod
    def validate_min_balance(min_balance: int) -> bool:
        """Проверяет, что минимальный остаток не отрицательный."""
        return min_balance >= 0

    @classmethod
    def from_data(cls, data: dict) -> "Material":
        """Создаёт материал из записи JSON."""
        return cls(data["id"], data["name"], data["unit"], data["min_balance"])

    def to_data(self) -> dict:
        """Превращает материал в запись для JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "unit": self.unit,
            "min_balance": self.min_balance,
        }

    def needs_reorder(self, total_balance: int) -> bool:
        """Пора ли дозаказывать при таком общем остатке."""
        return total_balance < self.min_balance

    def __str__(self) -> str:
        return f"{self.name} ({self.unit})"


def add_material(
    materials: list[Material],
    name: str,
    unit: str,
    min_balance: int,
) -> Material:
    """Создаёт материал и добавляет его в список."""
    existing_names = {material.name.lower() for material in materials}
    if name.lower() in existing_names:
        raise ValueError(f"Материал «{name}» уже есть")
    material = Material(
        next_id(material.id for material in materials),
        name,
        unit,
        min_balance,
    )
    materials.append(material)
    return material


def find_material_by_id(
    materials: list[Material],
    material_id: int,
) -> Material | None:
    """Ищет материал по номеру, если нет, возвращает None."""
    for material in materials:
        if material.id == material_id:
            return material
    return None


def get_material_by_id(
    materials: list[Material],
    material_id: int,
) -> Material:
    """Возвращает материал по номеру или выдаёт ошибку."""
    material = find_material_by_id(materials, material_id)
    if material is None:
        raise ValueError(f"Материала с номером {material_id} нет")
    return material


def find_materials(materials: list[Material], query: str) -> list[Material]:
    """Ищет материалы по части названия без учёта регистра."""
    query = query.lower()
    return [
        material for material in materials if query in material.name.lower()
    ]


def sort_materials(materials: list[Material]) -> list[Material]:
    """Сортирует материалы по названию."""
    return sorted(materials, key=lambda material: material.name.lower())
