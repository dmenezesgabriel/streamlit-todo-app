from typing import cast
from uuid import uuid4

import pandas as pd
import streamlit as st
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Create SQLite database
DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(DATABASE_URL)

# Define TODO model
Base = declarative_base()


class Todo(Base):
    __tablename__ = "todos"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    completed = Column(Integer, default=0)


# Create table if not exists
Base.metadata.create_all(bind=engine)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_todos():
    db = SessionLocal()
    todos = db.query(Todo).all()
    db.close()
    return todos


def get_todo(id: str):
    db = SessionLocal()
    todo = db.query(Todo).filter(Todo.id == id).first()
    db.close()
    return todo


def create_todo(title: str):
    db = SessionLocal()
    todo_id = str(uuid4())  # Generating UUID for the todo
    todo = Todo(id=todo_id, title=title)
    db.add(todo)
    db.commit()
    db.close()
    return todo


def update_todo(id: str, title: str, completed: int):
    db = SessionLocal()
    todo = db.query(Todo).filter(Todo.id == id).first()
    if todo:
        todo.title = cast(Column["str"], title)
        todo.completed = cast(Column["int"], completed)
        db.commit()
    db.close()


def delete_todo(id: str):
    db = SessionLocal()
    todo = db.query(Todo).filter(Todo.id == id).first()
    if todo:
        db.delete(todo)
        db.commit()
    db.close()


def get_data():
    todos = get_todos()
    data = [
        {
            "id": todo.id,
            "title": todo.title,
            "completed": todo.completed,
            "delete": False,
        }
        for todo in todos
    ]
    return pd.DataFrame(data).reset_index(drop=True).set_index("id")


def main():
    st.set_page_config(
        page_title="TODO CRUD",
        page_icon=":white_check_mark:",
        layout="centered",
    )

    data = get_data()

    st.html(  # Bad practice mess with st guts, but it's just an example
        """
        <style>
            div[data-testid="column"] {
                width: fit-content !important;
                flex: unset;
            }
            div[data-testid="column"] * {
                width: fit-content !important;
            }
        </style>
        """,
    )

    st.header("🧗 TODO CRUD", divider="rainbow")
    with st.container():
        columns = st.columns([1, 1])
        with columns[0]:
            if st.button("⟳ Refresh"):
                st.rerun()

        with columns[1]:
            with st.popover("➕ New"):
                with st.form("Add TODO", border=False):
                    title = st.text_input("Title")
                    if st.form_submit_button("Submit"):
                        create_todo(title)
                        st.rerun()

    if not len(data):
        st.warning("No TODOs, add above")
        st.stop()

    edited_df = st.data_editor(
        data,
        key="data_editor",
        column_config={
            "title": st.column_config.TextColumn(
                "🎯 Title",
            ),
            "completed": st.column_config.CheckboxColumn(
                "✅ Completed",
            ),
            "delete": st.column_config.CheckboxColumn(
                "❌ Delete",
            ),
        },
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
    )

    data_editor_events = st.session_state.data_editor
    edited_rows = data_editor_events["edited_rows"]

    if not edited_rows:
        return
    for row_position, changed_attributes in edited_rows.items():
        # old_row = data.iloc[row_position]
        new_row = edited_df.iloc[row_position]
        index = new_row.name
        new_row_dict = new_row.to_dict()
        if new_row_dict["delete"]:
            delete_todo(index)
        else:
            update_todo(
                id=index,
                title=new_row_dict["title"],
                completed=new_row_dict["completed"],
            )

        st.rerun()


if __name__ == "__main__":
    main()
