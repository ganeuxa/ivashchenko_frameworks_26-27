-- Учёт расходных материалов: структура базы данных.
-- IF NOT EXISTS позволяет выполнять файл повторно без ошибок.

-- Материалы, которые учитываем.
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL,
    min_balance INTEGER NOT NULL DEFAULT 0 CHECK (min_balance >= 0)
);

-- Склады. Адрес может быть не указан, тогда в поле NULL.
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    location TEXT
);

-- Остатки: сколько материала лежит на складе.
-- Пара «материал + склад» встречается один раз, поэтому она и есть
-- первичный ключ.
CREATE TABLE IF NOT EXISTS stock (
    material_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    PRIMARY KEY (material_id, warehouse_id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

-- Операции: приход, расход и перемещение.
-- target_warehouse_id заполнен только у перемещения, у остальных NULL.
-- is_cancelled: 0 операция проведена, 1 отменена.
-- performed_at хранится строкой ГГГГ-ММ-ДД ЧЧ:ММ, такие строки
-- правильно сравниваются и сортируются.
CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('receipt', 'write_off', 'transfer')),
    material_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    target_warehouse_id INTEGER,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    performed_at TEXT NOT NULL,
    is_cancelled INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (target_warehouse_id) REFERENCES warehouses(id)
);
