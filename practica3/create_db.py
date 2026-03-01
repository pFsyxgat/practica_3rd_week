import sqlite3
import os

DB_NAME = 'database.db'

def create_tables(conn):
    """Создание таблиц, индексов и включение поддержки внешних ключей."""
    cursor = conn.cursor()
    # включаем проверку внешних ключей
    cursor.execute('PRAGMA foreign_keys = ON;')
    
    # таблица ролей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    ''')
    
    # таблица прав доступа
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    ''')
    
    # связь
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
        );
    ''')
    
    # таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
        );
    ''')
    
    # индексы для ускорения поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);')
    
    conn.commit()
    print(" Таблицы созданы успешно.")

def insert_test_data(conn):
    """Заполнение таблиц начальными (тестовыми) данными."""
    cursor = conn.cursor()
    
    # дбавляем роли
    roles = [('Администратор',), ('Менеджер',), ('Пользователь',)]
    cursor.executemany('INSERT OR IGNORE INTO roles (name) VALUES (?);', roles)
    
    # добавляем права
    permissions = [('create_user',), ('edit_user',), ('delete_user',), ('view_reports',)]
    cursor.executemany('INSERT OR IGNORE INTO permissions (name) VALUES (?);', permissions)
    
    # назначаем права ролям
    # админ - с полными правами
    admin_id = cursor.execute('SELECT id FROM roles WHERE name = ?', ('Администратор',)).fetchone()[0]
    for perm_name in ['create_user', 'edit_user', 'delete_user', 'view_reports']:
        perm_id = cursor.execute('SELECT id FROM permissions WHERE name = ?', (perm_name,)).fetchone()[0]
        cursor.execute('INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?);', (admin_id, perm_id))
    
    # менеджер
    manager_id = cursor.execute('SELECT id FROM roles WHERE name = ?', ('Менеджер',)).fetchone()[0]
    for perm_name in ['create_user', 'edit_user', 'view_reports']:
        perm_id = cursor.execute('SELECT id FROM permissions WHERE name = ?', (perm_name,)).fetchone()[0]
        cursor.execute('INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?);', (manager_id, perm_id))
    
    # юзер - без доп прав
    user_role_id = cursor.execute('SELECT id FROM roles WHERE name = ?', ('Пользователь',)).fetchone()[0]
    
    # добавляем пользователей
    users = [
        ('admin', 'hash1', 'Иван Петров', admin_id),
        ('manager1', 'hash2', 'Мария Иванова', manager_id),
        ('user1', 'hash3', 'Пётр Сидоров', user_role_id),
    ]
    cursor.executemany('INSERT OR IGNORE INTO users (login, password_hash, full_name, role_id) VALUES (?, ?, ?, ?);', users)
    
    conn.commit()
    print(" Тестовые данные добавлены.")

def run_queries(conn):
    """Демонстрация всех требуемых SQL-запросов."""
    cursor = conn.cursor()
    print("\n" + "="*50)
    print("       ПРИМЕРЫ ВЫПОЛНЕНИЯ ЗАПРОСОВ")
    print("="*50)
    
    # ID ролей
    admin_id = cursor.execute('SELECT id FROM roles WHERE name = ?', ('Администратор',)).fetchone()[0]
    manager_id = cursor.execute('SELECT id FROM roles WHERE name = ?', ('Менеджер',)).fetchone()[0]
    user_role_id = cursor.execute('SELECT id FROM roles WHERE name = ?', ('Пользователь',)).fetchone()[0]
    
    # выборка с сортировкой
    print("\n▶ Все пользователи с их ролями (сортировка по дате создания):")
    cursor.execute('''
        SELECT u.login, u.full_name, r.name AS role
        FROM users u
        JOIN roles r ON u.role_id = r.id
        ORDER BY u.created_at;
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:10} | {row[1]:20} | {row[2]}")
    
    # фильтрация по условию
    print("\n▶ Пользователи с ролью 'Менеджер':")
    cursor.execute('''
        SELECT login, full_name
        FROM users
        WHERE role_id = ?;
    ''', (manager_id,))
    for row in cursor.fetchall():
        print(f"   {row[0]:10} | {row[1]}")
    
    # добавление новой записи
    print("\n▶ Добавление нового пользователя 'new_user'...")
    try:
        cursor.execute('''
            INSERT INTO users (login, password_hash, full_name, role_id)
            VALUES (?, ?, ?, ?);
        ''', ('new_user', 'hash4', 'Новый Пользователь', manager_id))
        conn.commit()
        print("    Пользователь добавлен.")
    except sqlite3.IntegrityError as e:
        print(f"    Ошибка добавления: {e}")
    
    # изменение данных
    print("\n▶ Изменение имени пользователя 'user1' на 'Пётр Петров':")
    cursor.execute('''
        UPDATE users
        SET full_name = ?
        WHERE login = ?;
    ''', ('Пётр Петров', 'user1'))
    conn.commit()
    print("   Имя обновлено.")
    
    # удаление записи
    print("\n▶ Удаление пользователя 'new_user':")
    cursor.execute('DELETE FROM users WHERE login = ?;', ('new_user',))
    conn.commit()
    print("    Пользователь удалён.")
    
    # запрет удаления роли, если есть связанные пользователи
    print("\n▶ Попытка удалить роль 'Администратор' (должна быть ошибка из-за внешнего ключа):")
    try:
        cursor.execute('DELETE FROM roles WHERE name = ?;', ('Администратор',))
        conn.commit()
        print("    Роль удалена (это не должно было произойти!).")
    except sqlite3.IntegrityError as e:
        print(f"   Ошибка, как и ожидалось: {e}")
    
    # сортировка по другому полю
    print("\n▶ Пользователи, отсортированные по полному имени (А-Я):")
    cursor.execute('SELECT login, full_name FROM users ORDER BY full_name;')
    for row in cursor.fetchall():
        print(f"   {row[0]:10} | {row[1]}")
    
    # фильтрация с LIKE
    print("\n▶ Пользователи, логин которых начинается с 'admin':")
    cursor.execute('SELECT login, full_name FROM users WHERE login LIKE ?;', ('admin%',))
    for row in cursor.fetchall():
        print(f"   {row[0]:10} | {row[1]}")
    
    # контроль уникальности логина 
    print("\n▶ Попытка добавить пользователя с существующим логином 'admin':")
    try:
        cursor.execute('''
            INSERT INTO users (login, password_hash, full_name, role_id)
            VALUES (?, ?, ?, ?);
        ''', ('admin', 'hash_dup', 'Дубликат', admin_id))
        conn.commit()
        print("    Пользователь добавлен (это не должно было произойти!).")
    except sqlite3.IntegrityError as e:
        print(f"    Ошибка: {e}")

def interactive(conn):
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON;')
    print("\n" + "="*50)
    print("       ИНТЕРАКТИВНЫЙ РЕЖИМ (введите 'exit' для выхода)")
    print("="*50)
    while True:
        try:
            query = input("\nSQL> ").strip()
            if query.lower() in ('exit', 'quit'):
                break
            if not query:
                continue
            cursor.execute(query)
            if query.lower().startswith('select'):
                rows = cursor.fetchall()
                if rows:
                    col_names = [description[0] for description in cursor.description]
                    print(' | '.join(col_names))
                    print('-' * 50)
                    for row in rows:
                        print(' | '.join(str(x) for x in row))
                else:
                    print("(no rows)")
            else:
                conn.commit()
                print(f" Запрос выполнен, затронуто строк: {cursor.rowcount}")
        except Exception as e:
            print(f" Ошибка: {e}")

def main():
    # удалениестарого файла дб
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Старая база данных {DB_NAME} удалена.")
    
    conn = sqlite3.connect(DB_NAME)
    conn.execute('PRAGMA foreign_keys = ON;')  
    
    create_tables(conn)
    insert_test_data(conn)
    run_queries(conn)
    
    ans = input("\nХотите выполнить свои SQL-запросы? (y/n): ").strip().lower()
    if ans == 'y':
        interactive(conn)
    
    conn.close()
    print(f"\n Работа завершена. Файл базы данных '{DB_NAME}' создан и готов к использованию.")

if __name__ == '__main__':
    main()