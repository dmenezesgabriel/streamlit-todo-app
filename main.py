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
        todo.title = title
        todo.completed = completed
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
        {"id": todo.id, "title": todo.title, "completed": todo.completed}
        for todo in todos
    ]
    return pd.DataFrame(data).reset_index(drop=True).set_index("id")


def main():
    st.set_page_config(
        page_title="TODO CRUD", page_icon=":guardsman:", layout="wide"
    )

    if st.button("Refresh"):
        st.rerun()

    data = get_data()

    with st.popover("Add TODO"):
        with st.form("Add TODO", border=False):
            title = st.text_input("Title")
            if st.form_submit_button("Submit"):
                create_todo(title)
                st.rerun()

    if not len(data):
        st.warning("No TODOs, add above")
        return

    edited_df = st.data_editor(
        data,
        key="data_editor",
        column_config={
            "title": st.column_config.TextColumn(
                "Title",
            ),
            "completed": st.column_config.NumberColumn(
                "Completed",
            ),
        },
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
    )

    data_editor_events = st.session_state.data_editor
    edited_rows = data_editor_events["edited_rows"]
    if edited_rows:
        for row_position, changed_attributes in edited_rows.items():
            # old_row = data.iloc[row_position]
            new_row = edited_df.iloc[row_position]
            index = new_row.name
            new_row_dict = new_row.to_dict()
            update_todo(index, **new_row_dict)
            st.rerun()
            # id = row.name
            # changed_attributes


if __name__ == "__main__":
    main()
