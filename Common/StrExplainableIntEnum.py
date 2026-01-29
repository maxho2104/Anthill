from enum import IntEnum
from typing import Optional, Union, Tuple, List, Dict

class StrExplainableIntEnum(IntEnum):
    """Базовый класс для IntEnum c возможностью получения строкового описания"""
    @classmethod
    def _get_explanation_dict(cls) -> Optional[Dict[int, Union[str, List[str], Tuple[str]]]]:
        """Возвращает словарь с текстовыми описаниями значений (переопределять в потомках)"""
        return None

    def _get_str(self, index:int = 0)->str:
        """Возвращает текстовое описание значения"""
        result = f'{self.__class__.__name__} без описания (значение {self.value})'
        explanation = self.__class__._get_explanation_dict()
        if not explanation is None and isinstance(explanation, dict):
            if self.value in explanation.keys():
                if isinstance(explanation[self.value],str):
                    result = explanation[self.value]
                elif isinstance(explanation[self.value], (list, tuple)):
                    if index < len(explanation[self.value]):
                        result = explanation[self.value][index]
        return result

    def __str__(self):
        """Возвращает первое попавшееся текстовое описание"""
        return self._get_str()

    @classmethod
    def get_int_value(cls, text:str) -> Optional[int]:
        """Возвращает целочисленное значение по описанию"""
        result = None
        explanation = cls._get_explanation_dict()
        if not explanation is None and isinstance(explanation, dict):
            for k,v in explanation.items():
                if isinstance(v, str) and text.lower() == v.lower():
                    result = k
                    break
                elif isinstance(v, (list, tuple)):
                    finded = False
                    for index in range(len(v)):
                        if v[index].lower() == text.lower():
                            result = k
                            finded = True
                            break
                    if finded:
                        break
        return result