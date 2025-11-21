import sys
import sqlite3
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QPushButton, QListWidget,
                             QListWidgetItem, QDialog, QLabel, QLineEdit,
                             QTextEdit, QDialogButtonBox, QMessageBox, QDateTimeEdit
                             )
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont


class DatabaseManager:
    def __init__(self, db_name="todo_app.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT NOT NULL,
                date_of_creation TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                completed_at TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def get_all_tasks(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM tasks ORDER BY completed, deadline')

        tasks = []
        for row in cursor.fetchall():
            task = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'deadline': row[3],
                'date_of_creation': row[4],
                'completed': bool(row[5]),
                'completed_at': row[6]
            }
            tasks.append(task)

        conn.close()
        return tasks

    def add_task(self, task_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO tasks (title, description, deadline, date_of_creation, completed)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['deadline'],
            task_data['date_of_creation'],
            0
        ))

        conn.commit()
        task_id = cursor.lastrowid
        conn.close()

        return task_id

    def update_task(self, task_id, task_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tasks 
            SET title = ?, description = ?, deadline = ?, date_of_creation = ?
            WHERE id = ?
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['deadline'],
            task_data['date_of_creation'],
            task_id
        ))

        conn.commit()
        conn.close()

    def delete_task(self, task_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

        conn.commit()
        conn.close()

    def complete_task(self, task_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        completed_at = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm")

        cursor.execute('''
            UPDATE tasks 
            SET completed = 1, completed_at = ?
            WHERE id = ?
        ''', (completed_at, task_id))

        conn.commit()
        conn.close()

    def uncomplete_task(self, task_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tasks 
            SET completed = 0, completed_at = NULL
            WHERE id = ?
        ''', (task_id,))

        conn.commit()
        conn.close()

    def clear_completed_tasks(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM tasks WHERE completed = 1')

        conn.commit()
        conn.close()


class TaskDialog(QDialog):
    def __init__(self, parent=None, task_data=None):
        super().__init__(parent)
        self.task_data = task_data
        self.is_edit_mode = task_data is not None

        title = "Редактировать задачу" if self.is_edit_mode else "Новая задача"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 300)

        self.init_ui()

        if self.is_edit_mode:
            self.fill_existing_data()

    def init_ui(self):
        layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        title_label = QLabel("Название задачи:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Введите название задачи")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)

        desc_layout = QVBoxLayout()
        desc_label = QLabel("Описание задачи:")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Введите описание задачи")
        self.desc_input.setMaximumHeight(100)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)

        deadline_layout = QHBoxLayout()
        deadline_label = QLabel("Дедлайн:")
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setDateTime(QDateTime.currentDateTime())
        self.deadline_input.setMinimumDateTime(QDateTime.currentDateTime())
        self.deadline_input.setCalendarPopup(True)
        deadline_layout.addWidget(deadline_label)
        deadline_layout.addWidget(self.deadline_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(title_layout)
        layout.addLayout(desc_layout)
        layout.addLayout(deadline_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def fill_existing_data(self):
        self.title_input.setText(self.task_data['title'])
        self.desc_input.setPlainText(self.task_data['description'])

        datetime_str = self.task_data['deadline']
        datetime = QDateTime.fromString(datetime_str, "dd.MM.yyyy HH:mm")
        if datetime.isValid():
            self.deadline_input.setDateTime(datetime)

    def validate_and_accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название задачи!")
            return

        self.accept()

    def get_task_data(self):
        data = {
            'title': self.title_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'deadline': self.deadline_input.dateTime().toString("dd.MM.yyyy HH:mm"),
        }

        if self.is_edit_mode:
            data['date_of_creation'] = self.task_data['date_of_creation']
        else:
            data['date_of_creation'] = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm")

        return data


class TaskItemWidget(QWidget):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.init_ui()
        self.update_appearance()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        top_layout = QHBoxLayout()

        self.title_label = QLabel(self.task_data['title'])
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        self.create_label = QLabel(f"Создан: {self.task_data['date_of_creation']}")
        self.create_label.setStyleSheet("color: #666; font-size: 14px;")

        self.deadline_label = QLabel(f"До: {self.task_data['deadline']}")
        self.deadline_label.setStyleSheet("color: #666; font-size: 14px;")

        top_layout.addWidget(self.title_label, 1)
        top_layout.addWidget(self.create_label)
        top_layout.addWidget(self.deadline_label)

        if self.task_data.get('completed', False):
            self.completed_label = QLabel(f"Выполнено: {self.task_data.get('completed_at', '')}")
            self.completed_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold;")
            layout.addLayout(top_layout)
            layout.addWidget(self.completed_label)
        else:
            layout.addLayout(top_layout)

        if self.task_data['description']:
            self.desc_label = QLabel(self.task_data['description'])
            self.desc_label.setStyleSheet("color: #555; font-size: 13px; margin-top: 2px;")
            self.desc_label.setWordWrap(True)
            self.desc_label.setMaximumHeight(40)
            layout.addWidget(self.desc_label)

        self.setLayout(layout)
        self.update_appearance()

    def update_appearance(self):
        if self.task_data.get('completed', False):
            self.setStyleSheet("""
                TaskItemWidget {
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                    background-color: #f8fff8;
                    margin: 2px;
                }
            """)
            self.title_label.setStyleSheet("text-decoration: line-through; color: #888;")
        else:
            self.setStyleSheet("""
                TaskItemWidget {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    background-color: #f9f9f9;
                    margin: 2px;
                }
                TaskItemWidget:hover {
                    background-color: #e9e9e9;
                    border-color: #999;
                }
            """)
            self.title_label.setStyleSheet("")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("To-Do приложение")
        self.resize(700, 500)

        self.db = DatabaseManager()

        self.tasks = self.db.get_all_tasks()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.tab_widget = QTabWidget()

        self.tasks_tab = QWidget()
        self.setup_tasks_tab()

        self.about_tab = QWidget()
        self.setup_about_tab()

        self.tab_widget.addTab(self.tasks_tab, "Список задач")
        self.tab_widget.addTab(self.about_tab, "О программе")

        main_layout.addWidget(self.tab_widget)

    def setup_tasks_tab(self):
        layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()

        self.create_task_btn = QPushButton("Создать задачу")
        self.create_task_btn.clicked.connect(self.create_task)
        self.create_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.edit_task_btn = QPushButton("Редактировать задачу")
        self.edit_task_btn.clicked.connect(self.edit_task)
        self.edit_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)

        self.complete_task_btn = QPushButton("Выполнить задачу")
        self.complete_task_btn.clicked.connect(self.complete_task)
        self.complete_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)

        self.uncomplete_task_btn = QPushButton("Вернуть в работу")
        self.uncomplete_task_btn.clicked.connect(self.uncomplete_task)
        self.uncomplete_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)

        self.delete_task_btn = QPushButton("Удалить задачу")
        self.delete_task_btn.clicked.connect(self.delete_task)
        self.delete_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        self.clear_completed_btn = QPushButton("Очистить выполненные")
        self.clear_completed_btn.clicked.connect(self.clear_completed)
        self.clear_completed_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)

        buttons_layout.addWidget(self.create_task_btn)
        buttons_layout.addWidget(self.edit_task_btn)
        buttons_layout.addWidget(self.complete_task_btn)
        buttons_layout.addWidget(self.uncomplete_task_btn)
        buttons_layout.addWidget(self.delete_task_btn)
        buttons_layout.addWidget(self.clear_completed_btn)
        buttons_layout.addStretch()

        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 1px solid #2196F3;
            }
        """)
        self.tasks_list.itemDoubleClicked.connect(self.edit_task)

        layout.addLayout(buttons_layout)
        layout.addWidget(self.tasks_list)

        self.tasks_tab.setLayout(layout)

        self.refresh_tasks_list()

    def setup_about_tab(self):
        layout = QVBoxLayout()

        about_text = QLabel(
            "<h2>To-Do приложение</h2>"
            "<p>Приложение для управления задачами с сохранением в базу данных</p>"
            "</ul>"
        )
        about_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        about_text.setWordWrap(True)

        layout.addWidget(about_text)
        self.about_tab.setLayout(layout)

    def create_task(self):
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            task_id = self.db.add_task(task_data)
            task_data['id'] = task_id
            task_data['completed'] = False
            task_data['completed_at'] = None

            self.tasks.append(task_data)
            self.refresh_tasks_list()

    def edit_task(self):
        current_row = self.tasks_list.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для редактирования")
            return

        task_data = self.tasks[current_row]
        dialog = TaskDialog(self, task_data)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_task_data = dialog.get_task_data()
            self.db.update_task(task_data['id'], updated_task_data)

            updated_task_data['id'] = task_data['id']
            updated_task_data['completed'] = task_data['completed']
            updated_task_data['completed_at'] = task_data['completed_at']

            self.tasks[current_row] = updated_task_data
            self.refresh_tasks_list()

    def complete_task(self):
        current_row = self.tasks_list.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для выполнения")
            return

        task_data = self.tasks[current_row]
        if not task_data['completed']:
            self.db.complete_task(task_data['id'])

            task_data['completed'] = True
            task_data['completed_at'] = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm")

            self.refresh_tasks_list()

    def uncomplete_task(self):
        current_row = self.tasks_list.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для возврата в работу")
            return

        task_data = self.tasks[current_row]
        if task_data['completed']:
            self.db.uncomplete_task(task_data['id'])

            task_data['completed'] = False
            task_data['completed_at'] = None

            self.refresh_tasks_list()

    def delete_task(self):
        current_row = self.tasks_list.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для удаления")
            return

        task_data = self.tasks[current_row]

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить задачу '{task_data['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_task(task_data['id'])

            del self.tasks[current_row]
            self.refresh_tasks_list()

    def clear_completed(self):
        completed_tasks = [task for task in self.tasks if task['completed']]
        if not completed_tasks:
            QMessageBox.information(self, "Информация", "Нет выполненных задач для очистки")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить все выполненные задачи?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_completed_tasks()

            self.tasks = [task for task in self.tasks if not task['completed']]
            self.refresh_tasks_list()

    def refresh_tasks_list(self):
        self.tasks_list.clear()

        for task_data in self.tasks:
            task_widget = TaskItemWidget(task_data)

            list_item = QListWidgetItem(self.tasks_list)
            list_item.setSizeHint(task_widget.sizeHint())

            self.tasks_list.addItem(list_item)
            self.tasks_list.setItemWidget(list_item, task_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QTabWidget::pane {
            border: 1px solid #C2C7CB;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #E1E1E1;
            border: 1px solid #C4C4C3;
            padding: 8px 20px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom-color: white;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())