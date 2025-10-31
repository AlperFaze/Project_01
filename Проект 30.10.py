import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QPushButton, QListWidget,
                             QListWidgetItem, QDialog, QLabel, QLineEdit,
                             QTextEdit, QDialogButtonBox, QMessageBox, QDateTimeEdit
                             )
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont


class TaskDialog(QDialog):
    def __init__(self, parent=None, task_data=None):
        super().__init__(parent)
        self.task_data = task_data
        self.is_edit_mode = task_data is not None

        title = "Редактировать задачу" if self.is_edit_mode else "Новая задача"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 300)

        self.initUI()

        if self.is_edit_mode:
            self.new_data()

    def initUI(self):
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
        button_box.accepted.connect(self.accepting)
        button_box.rejected.connect(self.reject)

        layout.addLayout(title_layout)
        layout.addLayout(desc_layout)
        layout.addLayout(deadline_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def new_data(self):
        self.title_input.setText(self.task_data['title'])
        self.desc_input.setPlainText(self.task_data['description'])

        datetime_str = self.task_data['deadline']
        datetime = QDateTime.fromString(datetime_str, "dd.MM.yyyy HH:mm")
        if datetime.isValid():
            self.deadline_input.setDateTime(datetime)

    def accepting(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название задачи!")
            return

        self.accept()

    def get_data(self):
        if self.is_edit_mode:
            return {
                'title': self.title_input.text().strip(),
                'description': self.desc_input.toPlainText().strip(),
                'deadline': self.deadline_input.dateTime().toString("dd.MM.yyyy HH:mm"),
                'date_of_creation': self.task_data['date_of_creation']
            }

        else:
            return {
                'title': self.title_input.text().strip(),
                'description': self.desc_input.toPlainText().strip(),
                'deadline': self.deadline_input.dateTime().toString("dd.MM.yyyy HH:mm"),
                'date_of_creation': QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm")
            }


class TaskItemWidget(QWidget):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        top_layout = QHBoxLayout()

        title_label = QLabel(self.task_data['title'])
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        create_label = QLabel(f"Создан: {self.task_data['date_of_creation']}")
        create_label.setStyleSheet("color: #666; font-size: 16px;")
        deadline_label = QLabel(f"До: {self.task_data['deadline']}")
        deadline_label.setStyleSheet("color: #666; font-size: 16px;")

        top_layout.addWidget(title_label, 1)
        top_layout.addWidget(create_label)
        top_layout.addWidget(deadline_label)

        if self.task_data['description']:
            desc_label = QLabel(self.task_data['description'])
            desc_label.setStyleSheet("color: #555; font-size: 15px; margin-top: 2px;")
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(40)
            layout.addLayout(top_layout)
            layout.addWidget(desc_label)
        else:
            layout.addLayout(top_layout)

        self.setLayout(layout)
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


class CompletedTaskItemWidget(QWidget):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        top_layout = QHBoxLayout()

        title_label = QLabel(self.task_data['title'])
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("text-decoration: line-through; color: #888;")

        completed_label = QLabel(f"Выполнено: {self.task_data['completed_at']}")
        completed_label.setStyleSheet("color: #4CAF50; font-size: 14px;")

        top_layout.addWidget(title_label, 1)
        top_layout.addWidget(completed_label)

        if self.task_data['description']:
            desc_label = QLabel(self.task_data['description'])
            desc_label.setStyleSheet("color: #555; font-size: 15px; margin-top: 2px;")
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(40)
            layout.addLayout(top_layout)
            layout.addWidget(desc_label)
        else:
            layout.addLayout(top_layout)

        self.setLayout(layout)
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("To-Do приложение")
        self.resize(700, 500)

        self.tasks = []
        self.tasks_completed = []

        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.tab_widget = QTabWidget()

        self.tasks_tab = QWidget()
        self.setup_tasks_tab()

        self.completed_tab = QWidget()
        self.setup_completed_tab()

        self.about_tab = QWidget()
        self.set_about_tab()

        self.tab_widget.addTab(self.tasks_tab, "Список задач")
        self.tab_widget.addTab(self.completed_tab, "Выполнено")
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

        buttons_layout.addWidget(self.create_task_btn)
        buttons_layout.addWidget(self.edit_task_btn)
        buttons_layout.addWidget(self.complete_task_btn)
        buttons_layout.addWidget(self.delete_task_btn)
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

    def setup_completed_tab(self):
        layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()

        self.clear_completed_btn = QPushButton("Очистить выполненные")
        self.clear_completed_btn.clicked.connect(self.clear_completed)
        self.clear_completed_btn.setStyleSheet("""
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

        buttons_layout.addWidget(self.clear_completed_btn)
        buttons_layout.addStretch()

        self.tasks_list_c = QListWidget()
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

        layout.addLayout(buttons_layout)
        layout.addWidget(self.tasks_list_c)

        self.completed_tab.setLayout(layout)

    def set_about_tab(self):
        layout = QVBoxLayout()

        about_text = QLabel(
            "<p>Скоро здесь что-нибудь будет</p>"
            "<p>Осталось добавить:</p>"
            "<p>сохранение задач в sql-базу</p>"

        )
        about_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        about_text.setWordWrap(True)

        layout.addWidget(about_text)
        self.about_tab.setLayout(layout)

    def create_task(self):
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_data()
            self.add_task_to_list(task_data)

    def complete_task(self):  # перенос задачи из общего списка в список выполненных
        current_row = self.tasks_list.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу выполнения")
            return

        task_data = self.tasks[current_row]

        task_data['completed_at'] = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm")

        del self.tasks[current_row]

        self.tasks_completed.append(task_data)

        self.refresh_tasks_list()
        self.refresh_completed_list()

    def clear_completed(self):  # очищение списка выполненных задач
        if not self.tasks_completed:
            QMessageBox.information(self, "Ошибка", "Нет выполненных задач")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Очистить все выполненные задачи?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.tasks_completed.clear()
            self.refresh_completed_list()

    def edit_task(self):
        current_row = self.tasks_list.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для редактирования")
            return

        task_data = self.tasks[current_row]

        old_date_of_creation = task_data.get("date_of_creation",
                                             QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm"))

        dialog = TaskDialog(self, task_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_task_data = dialog.get_data()
            updated_task_data["date_of_creation"] = old_date_of_creation
            self.tasks[current_row] = updated_task_data

            self.refresh_tasks_list()

    def delete_task(self):
        current_row = self.tasks_list.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для удаления")
            return

        del self.tasks[current_row]
        self.refresh_tasks_list()

    def add_task_to_list(self, task_data):
        self.tasks.append(task_data)
        self.refresh_tasks_list()

    def refresh_tasks_list(self):
        self.tasks_list.clear()

        for task_data in self.tasks:
            task_widget = TaskItemWidget(task_data)

            list_item = QListWidgetItem(self.tasks_list)
            list_item.setSizeHint(task_widget.sizeHint())

            self.tasks_list.addItem(list_item)
            self.tasks_list.setItemWidget(list_item, task_widget)

    def refresh_completed_list(self):
        self.tasks_list_c.clear()

        for task_data in self.tasks_completed:
            task_widget = CompletedTaskItemWidget(task_data)

            list_item = QListWidgetItem(self.tasks_list_c)
            list_item.setSizeHint(task_widget.sizeHint())

            self.tasks_list_c.addItem(list_item)
            self.tasks_list_c.setItemWidget(list_item, task_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QMainWindow {
            background-color: #dff2ee;
        }
        QTabWidget::pane {
            border: 1px solid #C2C7CB;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #d3e0dc;
            border: 1px solid #C4C4C3;
            padding: 8px 20px;
        }
        QTabBar::tab:selected {
            background-color: #c2cfcb;
            border-bottom-color: #c2cfcb;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

