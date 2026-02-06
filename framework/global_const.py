# строки для заполнения пустых или двоичных полей в интерфейсе
defaultNoneDisplayedText = '<пусто>'
defaultTrueDisplayedText = 'Да'
defaultFalseDisplayedText = 'Нет'
defaultBlobDisplayedText = '<двоичные данные>'

# внутренний формат строковой даты, утвержденный у нас, и рекомендуемый для работы с peewee - ГГГГ-ММ-ДД
preferred_date_format = '%Y-%m-%d'

# строковые форматы дат, которые peewee будет обрабатывать автоматически и приводить к date при загрузке из БД
correct_dates = [
    preferred_date_format,
    '%d-%m-%Y',
    '%Y.%m.%d',
    '%d.%m.%Y',
]