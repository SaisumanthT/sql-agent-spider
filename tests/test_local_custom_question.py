from retail_sql_agent.local_sqlite import LocalSQLiteSession


def test_local_session_accepts_custom_question(tmp_path) -> None:
    db_path = tmp_path / "demo.db"
    db_path.touch()
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text("CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, customer_name TEXT);", encoding="utf-8")
    tasks_path = tmp_path / "questions.json"
    tasks_path.write_text("[]", encoding="utf-8")

    session = LocalSQLiteSession(
        db_path=db_path,
        schema_path=schema_path,
        tasks_path=tasks_path,
        mode="realistic",
    )
    task = session.reset(custom_question="Which customers are in New York?")
    assert task.question == "Which customers are in New York?"
    assert task.metadata["custom_question"] is True


def test_local_session_query_with_columns(tmp_path) -> None:
    db_path = tmp_path / "demo.db"
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text("CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, customer_name TEXT);", encoding="utf-8")
    tasks_path = tmp_path / "questions.json"
    tasks_path.write_text("[]", encoding="utf-8")

    import sqlite3

    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, customer_name TEXT)")
        connection.execute("INSERT INTO customers (customer_id, customer_name) VALUES (1, 'Acorn Retail')")
        connection.commit()

    session = LocalSQLiteSession(
        db_path=db_path,
        schema_path=schema_path,
        tasks_path=tasks_path,
        mode="realistic",
    )
    columns, rows = session.query_with_columns("SELECT customer_id, customer_name FROM customers")
    assert columns == ["customer_id", "customer_name"]
    assert rows == [(1, "Acorn Retail")]
