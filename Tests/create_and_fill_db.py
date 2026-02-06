import random
from datetime import date, timedelta
from tkinter.font import names
from typing import Optional, Type, Callable, List
from peewee import DoesNotExist
from framework import DBManager
from Peewee.Classes.MainClasses import *
from Peewee.Classes.Content import *




class MyDataGenerator:
    lat_alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                    'U', 'V', 'W', 'X', 'Y', 'Z']

    content_themes = {
        ContentType.message: [
            'О состоянии дел ...',
            'О выполненных мероприятиях ...',
            'О прогрессе при решении задач ...',
            'О ходе выполнения работ ...'
        ],
        ContentType.document: [
            'Доклад ... (должностного лица)',
            'Порядок работы ...',
            'Перспективы ...',
            'Анализ хода результатов ...',
            'Методические рекомендации по ...',
            'Об итогах проведения ... (мероприятия)',
            'Каталог продукции ...',
            'Перечень ...',
            'Прайс лист на ...',
            'Каталог деталей и запасных частей ...'
        ],
        ContentType.reference: [
            'Справка по теме ...',
            'Копия справки по теме ...',
            'Выдержки из документа ...'
        ],
        ContentType.sample: [
            'Образец продукции ...',
            'Деталь ... образца продукции ...',
            'Программное обеспечение для ...'
        ],
        ContentType.identity: [
            'Паспорт на изделие ...',
            'Руководство пользователя ...',
            'Принципиальная схема ...',

        ]
    }


    @staticmethod
    def generateSerialNumber(separator:str, *section_lengths:int)->str:
        result:List[str] = []
        for section_length in section_lengths:
            subresult:List[str] = []
            for i in range(section_length):
                if random.choice([True, False]):
                    subresult.append(random.choice(MyDataGenerator.lat_alphabet))
                else:
                    subresult.append(str(random.randrange(10)))
            result.append(''.join(subresult))
        return separator.join(result)

    @staticmethod
    def getWorkingGroupID(employee:Employee, cur_date:date) ->Optional[int]:
        if employee.working_group_id is None: return None
        if employee.working_group_start is None: return None
        if employee.working_group_start > cur_date: return None
        if employee.working_group_end is None: return employee.working_group_id
        if employee.working_group_end <= cur_date: return employee.working_group_id
        return None

    def __init__(self, db_path:str):
        classes = [
            Rank,
            ProcessUnit,
            Department,
            WorkingGroup,
            Employee,
            Task,
            Rater,
            Rating,
            RatingList,
            Attachment,
            File,
            Content
        ]
        DBManager(classes,db_path)
        self.connected = DBManager().connectDB(db_path)

    def __del__(self):
        DBManager().closeDB()

    def _fillRanks(self):
        if not DBManager().connected: return
        if not Rank.table_exists():
            Rank.create_table()
            print(f'Таблица "{Rank._meta.table_name}"({Rank.__doc__}) создана...')
        Rank.create(name='кандидат технических наук', short= 'ктн')
        Rank.create(name='доктор технических наук', short='дтн')
        Rank.create(name='кандидат математических наук', short='кмн')
        Rank.create(name='доктор математических наук', short='дмн')
        print(f'Тестовые данные в таблицу "{Rank._meta.table_name}"({Rank.__doc__}) были внесены...')

    def _fillProcessUnits(self):
        if not DBManager().connected: return
        if not ProcessUnit.table_exists():
            ProcessUnit.create_table()
            print(f'Таблица "{ProcessUnit._meta.table_name}"({ProcessUnit.__doc__}) создана...')
        ProcessUnit.create(number='Ф001', name='Филиал № 1', short='Ф1')
        print(f'Тестовые данные в таблицу "{ProcessUnit._meta.table_name}"({ProcessUnit.__doc__}) были внесены...')

    def _fillDepartments(self):
        if not DBManager().connected: return
        if not Department.table_exists():
            Department.create_table()
            print(f'Таблица "{Department._meta.table_name}"({Department.__doc__}) создана...')
        Department.create(name='1 отдел', short='1 отд.', process_unit=ProcessUnit.select().where(ProcessUnit.number=='Ф001').get())
        Department.create(name='2 отдел', short='2 отд.', process_unit=ProcessUnit.select().where(ProcessUnit.number=='Ф001').get())
        print(f'Тестовые данные в таблицу "{Department._meta.table_name}"({Department.__doc__}) были внесены...')

    def _fillWorkingGroups(self):
        if not DBManager().connected: return
        if not WorkingGroup.table_exists():
            WorkingGroup.create_table()
            print(f'Таблица "{WorkingGroup._meta.table_name}"({WorkingGroup.__doc__}) создана...')
        WorkingGroup.create(name='1 рабочая группа', department=Department.select().where(Department.short=='1 отд.').get())
        WorkingGroup.create(name='2 рабочая группа', department=Department.select().where(Department.short=='2 отд.').get())
        print(f'Тестовые данные в таблицу "{WorkingGroup._meta.table_name}"({WorkingGroup.__doc__}) были внесены...')

    def _fillEmployees(self):
        if not DBManager().connected: return
        if not Employee.table_exists():
            Employee.create_table()
            print(f'Таблица "{Employee._meta.table_name}"({Employee.__doc__}) создана...')
        Employee.create(last_name='Иванов', first_name='Иван', second_name='Иванович', rank=Rank.select().where(Rank.short=='ктн').get(),
                        department=Department.select().where(Department.short=='1 отд.').get(), post='СНС',
                        working_group=WorkingGroup.select().where(WorkingGroup.name=='1 рабочая группа').get(),
                        working_group_post = 'сотрудник', working_group_start=date(2025,1,1),
                        working_group_end=date(2025,6,30))
        Employee.create(last_name='Петров', first_name='Петр', second_name='Петрович', rank=Rank.select().where(Rank.short=='дтн').get(),
                        department=Department.select().where(Department.short=='1 отд.').get(), post='СНС',
                        working_group=WorkingGroup.select().where(WorkingGroup.name=='1 рабочая группа').get(),
                        working_group_post = 'руководитель', working_group_start=date(2025,1,1))
        Employee.create(last_name='Сидоров', first_name='Сидор', second_name='Сидорович',
                        department=Department.select().where(Department.short=='1 отд.').get(), post='МНС',
                        working_group=WorkingGroup.select().where(WorkingGroup.name=='1 рабочая группа').get(),
                        working_group_post = 'сотрудник', working_group_start=date(2025,7,15),
                        working_group_end=date(2025,12,29))
        Employee.create(last_name='Алексеев', first_name='Алексей', second_name='Алексеевич', rank=Rank.select().where(Rank.short=='кмн').get(),
                        department=Department.select().where(Department.short == '2 отд.').get(), post='НС',
                        working_group=WorkingGroup.select().where(WorkingGroup.name == '2 рабочая группа').get(),
                        working_group_post='сотрудник', working_group_start=date(2025, 1, 1),
                        working_group_end=date(2025, 9, 17))
        Employee.create(last_name='Дмитриев', first_name='Дмитрий', second_name='Дмитриевич', rank=Rank.select().where(Rank.short=='дмн').get(),
                        department=Department.select().where(Department.short == '2 отд.').get(), post='СНС',
                        working_group=WorkingGroup.select().where(WorkingGroup.name == '2 рабочая группа').get(),
                        working_group_post='руководитель', working_group_start=date(2025, 1, 1))
        Employee.create(last_name='Евгениев', first_name='Евгений', second_name='Евгениевич',
                        department=Department.select().where(Department.short == '2 отд.').get(), post='МНС',
                        working_group=WorkingGroup.select().where(WorkingGroup.name == '2 рабочая группа').get(),
                        working_group_post='сотрудник', working_group_start=date(2025, 1, 1),
                        working_group_end=date(2025, 10, 11))
        Employee.create(last_name='Федоров', first_name='Федор', second_name='Федорович',
                        department=Department.select().where(Department.short == '2 отд.').get(), post='МНС')
        Employee.create(last_name='Удотов', first_name='Иван', second_name='Ильич',
                        department=Department.select().where(Department.short == '1 отд.').get(), post='МНС')
        print(f'Тестовые данные в таблицу "{Employee._meta.table_name}"({Employee.__doc__}) были внесены...')

    def _fillTasks(self):
        if not DBManager().connected: return
        if not Task.table_exists():
            Task.create_table()
            print(f'Таблица "{Task._meta.table_name}"({Task.__doc__}) создана...')
        Task.create(code='А001', comment='Основная задача №1', type=TaskType.oz)
        Task.create(code='А002', comment='Основная задача №2', type=TaskType.oz)
        Task.create(code='А003', comment='Основная задача №3', type=TaskType.oz)
        Task.create(code='Ж876', comment='Основная задача №9686', type=TaskType.oz)
        Task.create(code='ДЗ01', comment='Дополнительная задача №1', type=TaskType.dz)
        Task.create(code='ДЗ02', comment='Дополнительная задача №2', type=TaskType.dz)
        Task.create(code='ДЗ83', comment='Дополнительная задача №83', type=TaskType.dz)
        Task.create(code='ДЗ355', comment='Дополнительная задача №355', type=TaskType.dz)
        print(f'Тестовые данные в таблицу "{Task._meta.table_name}"({Task.__doc__}) были внесены...')

    def _fillRaters(self):
        if not DBManager().connected: return
        if not Rater.table_exists():
            Rater.create_table()
            print(f'Таблица "{Rater._meta.table_name}"({Rater.__doc__}) создана...')
        Rater.create(number='001', name='Организация № 1', short='ОРГ1')
        Rater.create(number='002', name='Организация № 2', short='ОРГ2')
        Rater.create(number='001', name='Организация № 208', short='ОРГ208')
        print(f'Тестовые данные в таблицу "{Rater._meta.table_name}"({Rater.__doc__}) были внесены...')


    def firstBaseInitialisation(self):
        """Первоначальное создание таблиц и их заплолнение"""
        # Заполнение таблиц
        self._fillRanks()
        self._fillProcessUnits()
        self._fillDepartments()
        self._fillWorkingGroups()
        self._fillEmployees()
        self._fillTasks()
        self._fillRaters()
        # Создание таблиц
        if not RatingList.table_exists():
            RatingList.create_table()
            print(f'Таблица "{RatingList._meta.table_name}"({RatingList.__doc__}) создана...')
        if not Rating.table_exists():
            Rating.create_table()
            print(f'Таблица "{Rating._meta.table_name}"({Rating.__doc__}) создана...')
        if not File.table_exists():
            File.create_table()
            print(f'Таблица "{File._meta.table_name}"({File.__doc__}) создана...')
        if not Content.table_exists():
            Content.create_table()
            print(f'Таблица "{Content._meta.table_name}"({Content.__doc__}) создана...')


    @staticmethod
    def getRandomID(peewee_class:Type[BaseModel], *where_expressions) -> Optional[int]:
        """Получение рандомного id из соотв. таблицы, по условиям where_expressions"""
        if not issubclass(peewee_class, BaseModel): return None
        id_list:List[int] = []
        if len(where_expressions) > 0:
            id_list = [element.id for element in peewee_class.select(peewee_class.id).where(where_expressions)]
        else:
            id_list = [element.id for element in peewee_class.select(peewee_class.id)]
        if len(id_list) == 0: return None
        return random.choice(id_list)

    @staticmethod
    def doSomethingPeriodical(from_date:date, to_date:date, func:Callable, period_days:int=1, min_records_per_period:int=1,
                              max_records_per_period:int=3, ish_prefix='01/', vh_prefix='02/'):
        """Псевдослучайная вставка записей в БД с определенной периодичностью (from_date - с, to_date - по, func - функция вставки,
        period_days - продолжительность периода в днях, max_records_per_period - максимальной количество вставляемых записей в одном периоде,
        ish_prefix - начало номера для исходящих, vh_prefix - начало номера для входящих)"""
        current_date = from_date
        ish_number = 1
        vh_number = 1
        while current_date <= to_date:
            add_rec = random.randrange(min_records_per_period, max_records_per_period + 1)
            for i in range(add_rec):
                print(f'{i + 1}-й раз за {current_date.strftime("%d.%m.%Y")}')
                func(current_date, ish_prefix+str(ish_number), vh_prefix + str(vh_number))
                ish_number += 1
                vh_number += 1
            current_date = current_date + timedelta(days=period_days)


    @staticmethod
    def contentToStr(content:Content) ->str:
        """Представление данных из экземпляра Content в с троковом виде"""
        result:List[str] = [f'Наименование: "{content.name}"']
        if not content.doc_number is None:
            tmp = f'Исходящий: {content.doc_number}'
            if not content.doc_date is None:
                tmp += f' от {content.doc_date.strftime("%d.%m.%Y")}'
            result.append(tmp)
        result.append(f'Тип: "{str(content.type)}')
        if content.type == ContentType.identity or content.type == ContentType.sample:
            result.append(f'Номер (зав./док.): {content.serial_number}')
            result.append(f'Год выпуска/выдачи: {content.produce_year}')
            if content.type == ContentType.sample:
                result.append(f'Стоимость: {content.cost}')
        result.append(f'Задача: "{content.task.representation()}"')
        result.append(f'Отправитель: {content.sender.representation()}')
        result.append(f'Отдел: {content.department.short}')
        result.append(f'Исполнитель: {content.employee.representation()}')
        if not content.working_group is None:
            result.append(f'Рабочая группа: {content.working_group.name}')
        if not content.rating is None:
            result.append(f'Оценка: {str(content.rating.value)}')
            if not content.rating.rating_list is None:
                result.append(f'Лист оценки: {content.rating.rating_list.number} от {content.rating.rating_list.date.strftime("%d.%m.%Y")}')
        return ', '.join(result)

    @staticmethod
    def insertRandomContent(d:date, ish_number:str, vh_number:str, document_process_delta_days:int = 14):
        """Добавление записи с псевдослучайными данными в Content"""
        if not DBManager().connected: return
        content = Content()
        # Исходящий
        content.doc_number = ish_number
        content.doc_date = d
        # Тип
        content.type = random.choice([cont_type for cont_type in ContentType])
        # Наименование
        content.name = random.choice(MyDataGenerator.content_themes[content.type])
        # Задача, серийный номер (номер документа), экономический эффект
        if content.type == ContentType.identity or content.type == ContentType.sample:
            if content.type == ContentType.identity:
                content.serial_number = MyDataGenerator.generateSerialNumber(' ', 2, 4, 6)
            else:
                content.serial_number = MyDataGenerator.generateSerialNumber('-', 4,4,4,4)
                content.economy = round(random.uniform(500, 5000000), 2)
            content.task_id = MyDataGenerator.getRandomID(Task, Task.type == TaskType.oz)
            content.produce_year = random.randrange(1980, date.today().year)
        else:
            content.task_id = MyDataGenerator.getRandomID(Task, Task.type == TaskType.dz)
        # Адресат
        content.rater_id = MyDataGenerator.getRandomID(Rater)
        # Сотрудник
        content.employee_id = MyDataGenerator.getRandomID(Employee)
        # Филиал (от сотрудника)
        content.sender = content.employee.department.process_unit
        # Отдел (от сотрудника)
        content.department = content.employee.department
        # РГ (от сотрудника)
        content.working_group = MyDataGenerator.getWorkingGroupID(content.employee, d)
        # Оценка
        vh_date = d + timedelta(days=document_process_delta_days)   # Вычисляем дату входящего документа
        # Если есть документ с оценкой за число vh_date - берем его, иначе - создаем новый
        try:
            rating_list = RatingList.get(RatingList.date == vh_date)
            try:
                rating = Rating.get(Rating.rating_list == rating_list)
            except DoesNotExist:
                rating = Rating.create(value=random.choice([RatingValue.interesting, RatingValue.valuable, RatingValue.important]),
                                       document=rating_list)
        except DoesNotExist:
            rating_list = RatingList.create(number=vh_number, date=vh_date)
            rating = Rating.create(value=random.choice([RatingValue.interesting, RatingValue.valuable, RatingValue.important]),
                                   rating_list=rating_list)
        content.rating = rating
        content.save()
        print(MyDataGenerator.contentToStr(content))


""" Пример использования:"""
if __name__ == '__main__':
    generator = MyDataGenerator('..\\test.db')
    # Инициализация БД + добавление тестовых значений для таблиц
    generator.firstBaseInitialisation()
    # Псевдослучайное заполнение Content
    generator.doSomethingPeriodical(date(2024,10,1),date(2026,7,31), generator.insertRandomContent, max_records_per_period=5)

