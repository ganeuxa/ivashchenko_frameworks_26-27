-- Запросы проекта «Учёт расходных материалов».
-- Каждый запрос подписан меткой «-- name: ...», по ней его находит
-- db/queries.py. Знак ? означает параметр: значение передаётся
-- отдельно от текста запроса.


-- ===== Выборка списков =====

-- name: materials_list
-- Все материалы по алфавиту. Нужны для выпадающего списка
-- на странице «Где взять материал».
SELECT id, name, unit, min_balance
FROM materials
ORDER BY name;

-- name: materials_with_totals
-- Материалы с общим остатком на всех складах. Страница «Материалы».
-- LEFT JOIN оставляет материал, даже если его нет ни на одном складе.
SELECT m.id, m.name, m.unit, m.min_balance,
       COALESCE(SUM(s.quantity), 0) AS total
FROM materials AS m
LEFT JOIN stock AS s ON s.material_id = m.id
GROUP BY m.id, m.name, m.unit, m.min_balance
ORDER BY m.name;

-- name: warehouses_with_positions
-- Склады и сколько разных материалов на каждом. Страница «Склады».
SELECT w.id, w.name, w.location,
       COUNT(s.material_id) AS positions
FROM warehouses AS w
LEFT JOIN stock AS s ON s.warehouse_id = w.id AND s.quantity > 0
GROUP BY w.id, w.name, w.location
ORDER BY w.name;


-- ===== Фильтрация WHERE =====

-- name: material_by_id
-- Один материал по номеру. Карточка материала.
SELECT id, name, unit, min_balance
FROM materials
WHERE id = ?;

-- name: warehouse_by_id
-- Один склад по номеру. Карточка склада.
SELECT id, name, location
FROM warehouses
WHERE id = ?;

-- name: warehouses_with_quantity
-- Склады, где материала не меньше нужного количества.
-- Параметры: номер материала и количество. Страница «Где взять материал».
SELECT w.id, w.name, w.location, s.quantity
FROM stock AS s
JOIN warehouses AS w ON w.id = s.warehouse_id
WHERE s.material_id = ? AND s.quantity >= ?
ORDER BY s.quantity DESC, w.name;


-- ===== Соединение таблиц JOIN =====

-- name: material_stock
-- На каких складах лежит материал и сколько. Карточка материала.
SELECT w.id AS warehouse_id, w.name AS warehouse_name, s.quantity
FROM stock AS s
JOIN warehouses AS w ON w.id = s.warehouse_id
WHERE s.material_id = ? AND s.quantity > 0
ORDER BY w.name;

-- name: warehouse_stock
-- Что лежит на складе и сколько материала всего на всех складах.
-- Карточка склада.
SELECT m.id AS material_id, m.name AS material_name, m.unit,
       m.min_balance, s.quantity,
       (SELECT SUM(all_s.quantity)
        FROM stock AS all_s
        WHERE all_s.material_id = m.id) AS total
FROM stock AS s
JOIN materials AS m ON m.id = s.material_id
WHERE s.warehouse_id = ? AND s.quantity > 0
ORDER BY m.name;

-- name: operations_list
-- История операций с названиями материала и складов, новые сверху.
-- Оба параметра: тип операции или NULL, чтобы показать все.
-- LEFT JOIN со складом назначения, потому что он есть только у перемещения.
SELECT o.id, o.type AS operation_type,
       CASE o.type
           WHEN 'receipt' THEN 'Приход'
           WHEN 'write_off' THEN 'Расход'
           ELSE 'Перемещение'
       END AS title,
       o.material_id, m.name AS material_name, m.unit,
       o.warehouse_id, w.name AS warehouse_name,
       o.target_warehouse_id, t.name AS target_name,
       o.quantity, o.performed_at, o.is_cancelled
FROM operations AS o
JOIN materials AS m ON m.id = o.material_id
JOIN warehouses AS w ON w.id = o.warehouse_id
LEFT JOIN warehouses AS t ON t.id = o.target_warehouse_id
WHERE ? IS NULL OR o.type = ?
ORDER BY o.performed_at DESC, o.id DESC;

-- name: operation_by_id
-- Одна операция со связанными данными. Карточка операции.
SELECT o.id, o.type AS operation_type,
       CASE o.type
           WHEN 'receipt' THEN 'Приход'
           WHEN 'write_off' THEN 'Расход'
           ELSE 'Перемещение'
       END AS title,
       o.material_id, m.name AS material_name, m.unit,
       o.warehouse_id, w.name AS warehouse_name,
       o.target_warehouse_id, t.name AS target_name,
       o.quantity, o.performed_at, o.is_cancelled
FROM operations AS o
JOIN materials AS m ON m.id = o.material_id
JOIN warehouses AS w ON w.id = o.warehouse_id
LEFT JOIN warehouses AS t ON t.id = o.target_warehouse_id
WHERE o.id = ?;

-- name: material_operations
-- Все операции по одному материалу по порядку. Карточка материала.
SELECT o.id, o.type AS operation_type,
       CASE o.type
           WHEN 'receipt' THEN 'Приход'
           WHEN 'write_off' THEN 'Расход'
           ELSE 'Перемещение'
       END AS title,
       o.material_id, m.name AS material_name, m.unit,
       o.warehouse_id, w.name AS warehouse_name,
       o.target_warehouse_id, t.name AS target_name,
       o.quantity, o.performed_at, o.is_cancelled
FROM operations AS o
JOIN materials AS m ON m.id = o.material_id
JOIN warehouses AS w ON w.id = o.warehouse_id
LEFT JOIN warehouses AS t ON t.id = o.target_warehouse_id
WHERE o.material_id = ?
ORDER BY o.performed_at, o.id;


-- ===== Агрегатные функции =====

-- name: summary_counts
-- Сводка для главной: сколько материалов, складов и проведённых операций.
SELECT (SELECT COUNT(*) FROM materials) AS materials_count,
       (SELECT COUNT(*) FROM warehouses) AS warehouses_count,
       (SELECT COUNT(*) FROM operations WHERE is_cancelled = 0)
           AS operations_count;

-- name: operations_by_type
-- Сколько проведено операций каждого типа, первая и последняя дата.
-- Отменённые не считаются. Страница «Статистика».
SELECT o.type AS operation_type,
       CASE o.type
           WHEN 'receipt' THEN 'Приход'
           WHEN 'write_off' THEN 'Расход'
           ELSE 'Перемещение'
       END AS title,
       COUNT(*) AS operations_count,
       MIN(o.performed_at) AS first_at,
       MAX(o.performed_at) AS last_at
FROM operations AS o
WHERE o.is_cancelled = 0
GROUP BY o.type
ORDER BY operations_count DESC;


-- ===== Группировка GROUP BY и фильтрация групп HAVING =====

-- name: operations_by_warehouse
-- Сколько проведённых операций прошло через каждый склад.
-- Страница «Статистика».
SELECT w.id, w.name, COUNT(o.id) AS operations_count
FROM warehouses AS w
LEFT JOIN operations AS o
    ON o.warehouse_id = w.id AND o.is_cancelled = 0
GROUP BY w.id, w.name
ORDER BY operations_count DESC, w.name;

-- name: consumption_by_material
-- Сколько каждого материала списано и сколько было списаний.
-- HAVING оставляет только материалы с расходом не меньше параметра.
-- Страница «Статистика».
SELECT m.id, m.name, m.unit,
       COUNT(o.id) AS write_offs,
       COALESCE(SUM(o.quantity), 0) AS consumed
FROM materials AS m
LEFT JOIN operations AS o
    ON o.material_id = m.id
    AND o.type = 'write_off'
    AND o.is_cancelled = 0
GROUP BY m.id, m.name, m.unit
HAVING COALESCE(SUM(o.quantity), 0) >= ?
ORDER BY consumed DESC, m.name;

-- name: low_stock
-- Материалы, которых на всех складах вместе меньше минимума.
-- WHERE тут не подойдёт: сумма остатков известна только после
-- группировки, поэтому условие стоит в HAVING. Главная страница.
SELECT m.id, m.name, m.unit, m.min_balance,
       COALESCE(SUM(s.quantity), 0) AS total
FROM materials AS m
LEFT JOIN stock AS s ON s.material_id = m.id
GROUP BY m.id, m.name, m.unit, m.min_balance
HAVING COALESCE(SUM(s.quantity), 0) < m.min_balance
ORDER BY m.name;
