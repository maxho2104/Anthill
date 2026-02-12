import sys
import os
from PyQt5 import QtWidgets, QtCore
from typing import List, Dict, Any
from peewee import JOIN, fn

# Добавляем родительскую директорию в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Peewee.Classes.Content import Content
from Peewee.Classes.MainClasses import *
from framework import DBManager, Settings
from QueryWidget import QueryWidget

# Заголовок таблицы
headers = [
    "Исходящий",
    "Тип",
    "Название",
    "Задача",
    "Оценивающий",
    "Филиал",
    "Отдел",
    "Исполнитель",
    "Оценка",
    "Коментарий",
]


def user_data(
    model_data: List[Dict[str, Any]], index: QtCore.QModelIndex, role: int
) -> Any:
    """Пользовательская функция для отображения данных в таблице"""
    if (
        not index.isValid()
        or index.row() >= len(model_data)
        or index.column() >= len(headers)
    ):
        return None
    if role == QtCore.Qt.DisplayRole:
        if index.column() == headers.index("Исходящий"):
            return f"{model_data[index.row()]['content_doc_number']} от {model_data[index.row()]['content_doc_date'].strftime('%d.%m.%Y')}"
        elif index.column() == headers.index("Тип"):
            return str(model_data[index.row()]["content_type"])
        elif index.column() == headers.index("Название"):
            return model_data[index.row()]["content_name"]
        elif index.column() == headers.index("Задача"):
            return model_data[index.row()]["task_code"]
        elif index.column() == headers.index("Оценивающий"):
            return model_data[index.row()]["rater_name"]
        elif index.column() == headers.index("Филиал"):
            return model_data[index.row()]["process_unit_name"]
        elif index.column() == headers.index("Отдел"):
            return model_data[index.row()]["department_short"]
        elif index.column() == headers.index("Исполнитель"):
            res = (
                model_data[index.row()]["employee_last_name"]
                + " "
                + model_data[index.row()]["employee_first_name"].strip().upper()[0]
            ) + "."
            if not model_data[index.row()]["employee_second_name"] is None:
                res += " " + model_data[index.row()]["employee_second_name"][0] + "."
            if not model_data[index.row()]["employee_rank_short"] is None:
                res = model_data[index.row()]["employee_rank_short"] + " " + res
            return res
        elif index.column() == headers.index("Оценка"):
            if model_data[index.row()]["ratings_count"] > 1:
                return f"{str(model_data[index.row()]['rating_value'])} / {model_data[index.row()]['ratings_count']}"
            else:
                return str(model_data[index.row()]["rating_value"])
        elif index.column() == headers.index("Коментарий"):
            return model_data[index.row()]["content_comment"]
    return None


def use_PyQt5():
    app = QtWidgets.QApplication([])
    # Подзапрос
    subquery = (
        Content.select(Content.rating_id, fn.COUNT(Content.id).alias("count"))
        .group_by(Content.rating_id)
        .alias("ratings_count")
    )
    # Создание запроса
    query = (
        Content.select(
            Content.id,
            Content.doc_number.alias("content_doc_number"),
            Content.doc_date.alias("content_doc_date"),
            Content.type.alias("content_type"),
            Content.name.alias("content_name"),
            Content.task.code.alias("task_code"),
            Rater.name.alias("rater_name"),
            Employee.last_name.alias("employee_last_name"),
            Employee.first_name.alias("employee_first_name"),
            Employee.second_name.alias("employee_second_name"),
            Rank.short.alias("employee_rank_short"),
            Department.short.alias("department_short"),
            ProcessUnit.name.alias("process_unit_name"),
            Rating.value.alias("rating_value"),
            subquery.c.count.alias("ratings_count"),
            Content.comment.alias("content_comment"),
        )
        .join(Task, on=(Content.task == Task.id))
        .switch(Content)
        .join(Rater)
        .switch(Content)
        .join(Employee)
        .join(Rank, JOIN.LEFT_OUTER)
        .switch(Content)
        .join(Department, JOIN.LEFT_OUTER)
        .join(ProcessUnit)
        .switch(Content)
        .join_from(Content, Rating, JOIN.LEFT_OUTER, on=(Content.rating == Rating.id))
        .join(subquery, JOIN.LEFT_OUTER, on=(Content.rating_id == subquery.c.rating_id))
    )

    # Создание функции

    """# Создание модели
    model = BatchedQueryModel(query=query, header_names=headers, user_data_func=user_data)"""
    # Создание таблицы
    widget = QueryWidget(query=query, header_names=headers, user_data_func=user_data)
    widget.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    """Здесь запускается тест"""
    # Настройки
    Settings(".\\settings.json")
    Settings().load()
    # Указываем классы, с которыми хотим работать
    DBManager(
        [
            Content,
            Rank,
            ProcessUnit,
            Department,
            WorkingGroup,
            Employee,
            Rater,
            File,
            RatingList,
            Rating,
            Task,
        ])
    # Подключаем базу
    DBManager().connectDB("..\\test.db")
    # DBManager().connectDB("test.db")
    use_PyQt5()

    # Отключаемся от базы
    DBManager().closeDB()
