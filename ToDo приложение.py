import csv
import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QListWidget, QListWidgetItem, QDialog, QLabel, QLineEdit,
    QTextEdit, QDialogButtonBox, QMessageBox, QDateTimeEdit, QMenu, QWidgetAction, QFileDialog
)
from PyQt6.QtCore import Qt, QDateTime, QSize, QPoint, QTimer, QFile, QFileInfo, QDir
from PyQt6.QtGui import QFont, QPixmap


class DatabaseManager:
    def __init__(self, db_name="todo_app 111.db"):
        self.db_name = db_name
        self.init_database()

    def connect(self):
        return sqlite3.connect(self.db_name)

    def init_database(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()

        cursor.execute("PRAGMA table_info(tasks)")
        cols = [r[1] for r in cursor.fetchall()]
        if "image_path" not in cols:
            try:
                cursor.execute("ALTER TABLE tasks ADD COLUMN image_path TEXT")
                conn.commit()
            except Exception:
                pass

        conn.close()

    def get_all_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id, title, description, deadline, date_of_creation, completed, completed_at, image_path FROM tasks'
            ' ORDER BY completed, deadline'
        )
        tasks = []
        for row in cursor.fetchall():
            task = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'deadline': row[3],
                'date_of_creation': row[4],
                'completed': bool(row[5]),
                'completed_at': row[6],
                'image_path': row[7],
            }
            task['tags'] = self.get_tags_for_task(task['id'])
            tasks.append(task)

        conn.close()
        return tasks

    def add_task(self, task_data):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO tasks (title, description, deadline, date_of_creation, completed, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['deadline'],
            task_data['date_of_creation'],
            0,
            task_data.get('image_path')
        ))

        task_id = cursor.lastrowid
        conn.commit()
        conn.close()

        tags = [t.strip() for t in task_data.get('tags', []) if t.strip()]
        if tags:
            self.add_tags_to_task(task_id, tags)

        return task_id

    def update_task(self, task_id, task_data):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tasks 
            SET title = ?, description = ?, deadline = ?, date_of_creation = ?, image_path = ?
            WHERE id = ?
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['deadline'],
            task_data['date_of_creation'],
            task_data.get('image_path'),
            task_id
        ))

        conn.commit()
        conn.close()

        tags = [t.strip() for t in task_data.get('tags', []) if t.strip()]
        self.clear_tags_for_task(task_id)
        if tags:
            self.add_tags_to_task(task_id, tags)

    def delete_task(self, task_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM task_tags WHERE task_id = ?', (task_id,))
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()

    def complete_task(self, task_id):
        conn = self.connect()
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
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tasks 
            SET completed = 0, completed_at = NULL
            WHERE id = ?
        ''', (task_id,))

        conn.commit()
        conn.close()

    def clear_completed_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM tasks WHERE completed = 1')
        rows = cursor.fetchall()
        task_ids = [r[0] for r in rows]
        for tid in task_ids:
            cursor.execute('DELETE FROM task_tags WHERE task_id = ?', (tid,))
        cursor.execute('DELETE FROM tasks WHERE completed = 1')

        conn.commit()
        conn.close()

    def get_or_create_tag(self, tag_name):
        tag_name = tag_name.strip()
        if not tag_name:
            return None

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
        row = cursor.fetchone()

        if row:
            tag_id = row[0]
        else:
            cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
            tag_id = cursor.lastrowid
            conn.commit()

        conn.close()
        return tag_id

    def get_all_tags(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM tags ORDER BY name")
        tags = [{'id': r[0], 'name': r[1]} for r in cursor.fetchall()]
        conn.close()
        return tags

    def add_tags_to_task(self, task_id, tags):
        if not tags:
            return
        conn = self.connect()
        cursor = conn.cursor()

        for tag in tags:
            tag_id = self.get_or_create_tag(tag)
            if tag_id:
                cursor.execute(
                    "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                    (task_id, tag_id)
                )

        conn.commit()
        conn.close()

    def get_tags_for_task(self, task_id):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tags.name
            FROM tags
            JOIN task_tags ON tags.id = task_tags.tag_id
            WHERE task_tags.task_id = ?
            ORDER BY tags.name
        """, (task_id,))

        tags = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tags

    def clear_tags_for_task(self, task_id):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
        conn.commit()
        conn.close()


class TagMultiSelectDropdown(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.selected = []
        self.button = QPushButton("Выбрать теги")
        self.button.setMinimumWidth(220)
        self.button.clicked.connect(self.show_menu)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.menu = None
        self.list_widget = None
        self.input_new = None

        self.refresh_tags()

    def sizeHint(self):
        return QSize(240, 28)

    def refresh_tags(self):
        self.all_tags = self.db.get_all_tags()

    def show_menu(self):
        self.refresh_tags()
        self.menu = QMenu(self)

        container = QWidget()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(6, 6, 6, 6)
        container.setLayout(vbox)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        for t in self.all_tags:
            item = QListWidgetItem(t['name'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if t['name'] in self.selected else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, t['id'])
            self.list_widget.addItem(item)

        self.list_widget.setMaximumHeight(200)
        vbox.addWidget(self.list_widget)

        h_new = QHBoxLayout()
        self.input_new = QLineEdit()
        self.input_new.setPlaceholderText("Новый тег")
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.handle_add_new_tag)
        h_new.addWidget(self.input_new)
        h_new.addWidget(add_btn)
        vbox.addLayout(h_new)

        done_btn = QPushButton("Готово")
        done_btn.clicked.connect(self.accept_and_close_menu)
        vbox.addWidget(done_btn)

        action = QWidgetAction(self.menu)
        action.setDefaultWidget(container)
        self.menu.addAction(action)

        self.menu.exec(self.button.mapToGlobal(QPoint(0, self.button.height())))

    def handle_add_new_tag(self):
        text = self.input_new.text().strip()
        if not text:
            return
        self.db.get_or_create_tag(text)
        self.input_new.clear()
        self.refresh_tags()
        self.list_widget.clear()
        for t in self.all_tags:
            item = QListWidgetItem(t['name'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if t['name'] in self.selected else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, t['id'])
            self.list_widget.addItem(item)

    def accept_and_close_menu(self):
        chosen = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                chosen.append(item.text())
        self.selected = chosen
        self.update_button_text()
        if self.menu:
            self.menu.close()

    def update_button_text(self):
        if not self.selected:
            self.button.setText("Выбрать теги")
        else:
            display = ", ".join(self.selected)
            if len(display) > 35:
                display = display[:32] + "..."
            self.button.setText(display)

    def get_selected_tags(self):
        return list(self.selected)

    def set_selected_tags(self, tags):
        self.selected = list(tags or [])
        self.update_button_text()


class TaskDialog(QDialog):
    def __init__(self, parent=None, task_data=None, db_manager: DatabaseManager = None):
        super().__init__(parent)
        self.db = db_manager
        self.task_data = task_data or {}
        self.is_edit_mode = task_data is not None

        title = "Редактировать задачу" if self.is_edit_mode else "Новая задача"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(520, 480)

        self.source_image_path = None
        self.image_file_name = None

        self.init_ui()

        if self.is_edit_mode:
            self.fill_existing_data()

    def init_ui(self):
        layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        title_label = QLabel("Название:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Введите название задачи")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)

        desc_layout = QVBoxLayout()
        desc_label = QLabel("Описание:")
        self.desc_input = QTextEdit()
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

        tag_layout = QHBoxLayout()
        tag_label = QLabel("Теги:")
        self.tag_dropdown = TagMultiSelectDropdown(self.db)
        tag_layout.addWidget(tag_label)
        tag_layout.addWidget(self.tag_dropdown)

        image_layout = QHBoxLayout()
        image_label = QLabel("Картинка:")

        self.attach_button = QPushButton("Прикрепить")
        self.attach_button.clicked.connect(self.select_image)

        self.view_button = QPushButton("Показать")
        self.view_button.setEnabled(False)
        self.view_button.clicked.connect(self.show_image)

        image_layout.addWidget(image_label)
        image_layout.addWidget(self.attach_button)
        image_layout.addWidget(self.view_button)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(title_layout)
        layout.addLayout(desc_layout)
        layout.addLayout(deadline_layout)
        layout.addLayout(tag_layout)
        layout.addLayout(image_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def fill_existing_data(self):
        self.title_input.setText(self.task_data.get('title', ''))
        self.desc_input.setPlainText(self.task_data.get('description', ''))

        datetime_str = self.task_data.get('deadline', '')
        datetime = QDateTime.fromString(datetime_str, "dd.MM.yyyy HH:mm")
        if datetime.isValid():
            self.deadline_input.setDateTime(datetime)

        tags = self.task_data.get('tags', [])
        self.tag_dropdown.set_selected_tags(tags)

        img_name = self.task_data.get('image_path')
        if img_name:
            self.image_file_name = img_name
            self.view_button.setEnabled(True)

    def validate_and_accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название задачи!")
            return
        self.accept()

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not file_path:
            return

        self.source_image_path = file_path
        info = QFileInfo(file_path)
        self.image_file_name = info.fileName()
        self.view_button.setEnabled(True)

    def show_image(self):
        if not self.image_file_name:
            return

        full_path = "images/" + self.image_file_name

        if not QFile.exists(full_path):
            QMessageBox.warning(self, "Ошибка", "Файл изображения не найден!")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Просмотр изображения")

        label = QLabel(dialog)
        pix = QPixmap(full_path)
        label.setPixmap(pix.scaled(700, 700, Qt.AspectRatioMode.KeepAspectRatio))

        v = QVBoxLayout()
        v.addWidget(label)
        dialog.setLayout(v)
        dialog.exec()

    def get_task_data(self):
        data = {
            'title': self.title_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'deadline': self.deadline_input.dateTime().toString("dd.MM.yyyy HH:mm"),
            'tags': self.tag_dropdown.get_selected_tags(),
            'image_path': self.image_file_name
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
        layout.setContentsMargins(10, 6, 10, 6)

        top_layout = QHBoxLayout()

        self.title_label = QLabel(self.task_data['title'])
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        self.create_label = QLabel(f"Создан: {self.task_data['date_of_creation']}")
        self.create_label.setStyleSheet("color: #666; font-size: 12px;")

        self.deadline_label = QLabel(f"До: {self.task_data['deadline']}")
        self.deadline_label.setStyleSheet("color: #666; font-size: 12px;")

        top_layout.addWidget(self.title_label, 1)
        top_layout.addWidget(self.create_label)
        top_layout.addWidget(self.deadline_label)

        tags_layout = QHBoxLayout()
        tags_layout.setContentsMargins(0, 5, 0, 0)

        layout.addLayout(top_layout)

        if self.task_data.get('description'):
            self.desc_label = QLabel(self.task_data['description'])
            self.desc_label.setStyleSheet("color: #555; font-size: 13px; margin-top: 2px;")
            self.desc_label.setWordWrap(True)
            self.desc_label.setMaximumHeight(40)
            layout.addWidget(self.desc_label)

        if self.task_data.get('tags'):
            tags_layout = QHBoxLayout()
            tags_layout.setContentsMargins(0, 5, 0, 0)
            for q in self.task_data['tags']:
                self.tag_label = QLabel(f"{q}🏷️")
                self.tag_label.setStyleSheet(
                    "background-color: green;"
                    "color: white;"
                    "padding: 2px 6px;"
                    "border-radius: 8px;"
                    "font-size: 13px;"
                    "margin: 1px;"
                    "font-weight: bold;")
                tags_layout.addWidget(self.tag_label)

            tags_layout.addStretch()

            layout.addLayout(tags_layout)
            """tags_text = "🏷️, ".join(self.task_data['tags']) + '🏷️'
            self.tag_label = QLabel(f"{tags_text}")
            self.tag_label.setStyleSheet("color: black; padding: 3px 8px; border-radius: 10px; font-size: 10px; margin: 1px; font-weight: bold;")
            layout.addWidget(self.tag_label)"""

        if self.task_data.get('image_path'):
            self.open_img_btn = QPushButton("Показать картинку")
            self.open_img_btn.setStyleSheet("font-size: 12px;")
            self.open_img_btn.clicked.connect(self.open_image)
            layout.addWidget(self.open_img_btn)

        if self.task_data.get('completed', False):
            self.completed_label = QLabel(f"Выполнено: {self.task_data.get('completed_at', '')}")
            self.completed_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold;")
            layout.addWidget(self.completed_label)

        self.setLayout(layout)
        self.update_appearance()

        self.is_overdue = self.check_overdue()
        if self.is_overdue:
            overdue_label = QLabel("Задача просрочена")
            overdue_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")
            layout.addWidget(overdue_label)

    def check_overdue(self):
        deadline_dt = QDateTime.fromString(self.task_data['deadline'], "dd.MM.yyyy HH:mm")
        return (not self.task_data.get('completed', False)) and deadline_dt < QDateTime.currentDateTime()

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

        if getattr(self, "is_overdue", False):
            self.setStyleSheet("""
                TaskItemWidget {
                    border: 2px solid #ff0000;
                    border-radius: 5px;
                    background-color: #ffe5e5;
                    margin: 2px;
                }
            """)
            self.title_label.setStyleSheet("color: #b30000; font-weight: bold;")
            return

    def open_image(self):
        file_name = self.task_data.get("image_path")
        if not file_name:
            return

        full_path = "images/" + file_name

        if not QFile.exists(full_path):
            QMessageBox.warning(self, "Ошибка", "Файл не найден.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Просмотр изображения")

        label = QLabel(dialog)
        pix = QPixmap(full_path)
        label.setPixmap(pix.scaled(700, 700, Qt.AspectRatioMode.KeepAspectRatio))

        v = QVBoxLayout()
        v.addWidget(label)
        dialog.setLayout(v)
        dialog.exec()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("To-Do приложение")
        self.resize(820, 560)

        self.db = DatabaseManager()
        self.tasks = self.db.get_all_tasks()

        images_dir = QDir("images")
        if not images_dir.exists():
            QDir().mkdir("images")

        timer = QTimer(self)
        timer.timeout.connect(self.refresh_tasks_list)
        timer.start(60000)

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
        self.tasks_list.itemDoubleClicked.connect(self.edit_task)

        layout.addLayout(buttons_layout)
        layout.addWidget(self.tasks_list)

        self.tasks_tab.setLayout(layout)

        self.refresh_tasks_list()

    def setup_about_tab(self):
        layout = QVBoxLayout()

        about_text = QLabel(
            "<h2>To-Do приложение</h2>"
            "<p>Приложение для управления задачами с сохранением в базу данных.</p>"
        )
        about_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        about_text.setWordWrap(True)

        layout.addWidget(about_text)
        self.about_tab.setLayout(layout)

        save_buttom = QPushButton('Сохранить в csv-файл')
        save_buttom.clicked.connect(self.save_to_csv)
        layout.addWidget(save_buttom)

    def save_to_csv(self):
        file1, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV Files (*.csv)")

        self.tasks = self.db.get_all_tasks()

        prepared_tasks = []
        for task in self.tasks:
            t = task.copy()
            t["tags"] = ", ".join(t.get("tags", []))
            prepared_tasks.append(t)

        if not prepared_tasks:
            QMessageBox.information(self, "Информация", "Нет задач для сохранения.")
            return

        fieldnames = list(prepared_tasks[0].keys())

        try:
            with open(file1, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(prepared_tasks)

            QMessageBox.information(self, "Готово", "CSV сохранён.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def create_task(self):
        dialog = TaskDialog(self, None, db_manager=self.db)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()

            if getattr(dialog, "source_image_path", None):
                info = QFileInfo(dialog.source_image_path)
                base = info.completeBaseName()
                ext = info.suffix()
                file_name = dialog.image_file_name
                dest_path = "images/" + file_name

                counter = 1
                while QFile.exists(dest_path):
                    file_name = f"{base}_{counter}.{ext}"
                    dest_path = "images/" + file_name
                    counter += 1

                QFile.copy(dialog.source_image_path, dest_path)
                task_data['image_path'] = file_name
            else:
                task_data['image_path'] = None

            task_id = self.db.add_task(task_data)
            task_data['id'] = task_id
            task_data['completed'] = False
            task_data['completed_at'] = None
            task_data['tags'] = self.db.get_tags_for_task(task_id)

            self.tasks.append(task_data)
            self.refresh_tasks_list()

    def edit_task(self):
        current_row = self.tasks_list.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для редактирования")
            return

        task_data = self.tasks[current_row]
        dialog = TaskDialog(self, task_data, db_manager=self.db)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_task_data = dialog.get_task_data()

            if getattr(dialog, "source_image_path", None):
                info = QFileInfo(dialog.source_image_path)
                base = info.completeBaseName()
                ext = info.suffix()
                file_name = dialog.image_file_name
                dest_path = "images/" + file_name

                counter = 1
                while QFile.exists(dest_path):
                    file_name = f"{base}_{counter}.{ext}"
                    dest_path = "images/" + file_name
                    counter += 1

                QFile.copy(dialog.source_image_path, dest_path)
                updated_task_data['image_path'] = file_name
            else:
                updated_task_data['image_path'] = task_data.get('image_path')

            self.db.update_task(task_data['id'], updated_task_data)

            updated_task_data['id'] = task_data['id']
            updated_task_data['completed'] = task_data['completed']
            updated_task_data['completed_at'] = task_data.get('completed_at')
            updated_task_data['tags'] = self.db.get_tags_for_task(task_data['id'])

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
        self.tasks = self.db.get_all_tasks()

        self.tasks.sort(
            key=lambda t: (t['completed'], QDateTime.fromString(t['deadline'], "dd.MM.yyyy HH:mm"))
        )

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
