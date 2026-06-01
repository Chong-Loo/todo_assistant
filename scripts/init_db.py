from app.db import init_db, get_db_path


def main():
    init_db()

    print("SQLite 数据库初始化完成")
    print(f"数据库文件位置: {get_db_path()}")


if __name__ == "__main__":
    main()