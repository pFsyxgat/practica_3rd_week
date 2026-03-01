PRAGMA foreign_keys = ON;

-- Создание таблиц
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);

-- Вставка тестовых данных
INSERT OR IGNORE INTO roles (name) VALUES ('Администратор'), ('Менеджер'), ('Пользователь');

INSERT OR IGNORE INTO permissions (name) VALUES ('create_user'), ('edit_user'), ('delete_user'), ('view_reports');

-- Права для администратора
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'Администратор' AND p.name IN ('create_user', 'edit_user', 'delete_user', 'view_reports');

-- Права для менеджера
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'Менеджер' AND p.name IN ('create_user', 'edit_user', 'view_reports');

-- Пользователи
INSERT OR IGNORE INTO users (login, password_hash, full_name, role_id)
SELECT 'admin', 'hash1', 'Иван Петров', id FROM roles WHERE name = 'Администратор'
UNION ALL
SELECT 'manager1', 'hash2', 'Мария Иванова', id FROM roles WHERE name = 'Менеджер'
UNION ALL
SELECT 'user1', 'hash3', 'Пётр Сидоров', id FROM roles WHERE name = 'Пользователь';

-- Демонстрация запросов

SELECT '--- Все пользователи с ролями (сортировка по дате создания) ---' AS info;
SELECT u.login, u.full_name, r.name AS role
FROM users u
JOIN roles r ON u.role_id = r.id
ORDER BY u.created_at;

SELECT '--- Пользователи с ролью "Менеджер" ---' AS info;
SELECT login, full_name
FROM users
WHERE role_id = (SELECT id FROM roles WHERE name = 'Менеджер');

SELECT '--- Добавление нового пользователя "new_user" ---' AS info;
INSERT INTO users (login, password_hash, full_name, role_id)
SELECT 'new_user', 'hash4', 'Новый Пользователь', id FROM roles WHERE name = 'Менеджер';
SELECT 'Пользователь добавлен.' AS result;

SELECT '--- Изменение имени пользователя "user1" на "Пётр Петров" ---' AS info;
UPDATE users
SET full_name = 'Пётр Петров'
WHERE login = 'user1';
SELECT 'Имя обновлено.' AS result;

SELECT '--- Удаление пользователя "new_user" ---' AS info;
DELETE FROM users WHERE login = 'new_user';
SELECT 'Пользователь удалён.' AS result;

SELECT '--- Попытка удалить роль "Администратор" (должна быть ошибка из-за внешнего ключа) ---' AS info;
DELETE FROM roles WHERE name = 'Администратор';

SELECT '--- Пользователи, отсортированные по полному имени (А-Я) ---' AS info;
SELECT login, full_name FROM users ORDER BY full_name;

SELECT '--- Пользователи, логин которых начинается с "admin" ---' AS info;
SELECT login, full_name FROM users WHERE login LIKE 'admin%';

SELECT '--- Попытка добавить пользователя с существующим логином "admin" ---' AS info;
INSERT INTO users (login, password_hash, full_name, role_id)
SELECT 'admin', 'hash_dup', 'Дубликат', id FROM roles WHERE name = 'Администратор';