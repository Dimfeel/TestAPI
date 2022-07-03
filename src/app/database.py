import pymongo
import datetime
import math

from typing import List, Set, Tuple
from dotenv import dotenv_values

from .datatypes import ShopUnitImport
from .datatypes import ShopUnit
from .datatypes import ShopUnitStatisticResponse, ShopUnitStatisticUnit

class ShopUnitDatabase(ShopUnitImport):
    """
    Формат хранения данных в бд. 
    Аналогичен ShopUnitImport с полем updateDate.
    """
    updateDate: datetime.datetime


class DatabaseDriver:
    """
    Драйвер для MongoDB
    """

    def __init__(self) -> None:
        """
        Инициализация драйвера MongoDB 
        (создается client соединение и подключается к коллекции products_and_categories).
        """
        
        config = dotenv_values("/src/.env")
        
        TESTING = config["TESTING"]
        
        self._client: pymongo.MongoClient = pymongo.MongoClient(
            host="mongodb",
            username=config["MONGODB_USERNAME"],
            password=config["MONGODB_PASSWORD"],
            port=27017)
        
        db = self._client["price_comparison_db"]
        
        if not TESTING:
            self._collection: pymongo.collection.Collection = db["products_and_categories"]
        else:
            self._collection: pymongo.collection.Collection = db["products_and_categories_test"]
            
    def clear_collection(self):
        """Очистка коллекции"""
        self._collection.delete_many({})
        
    def write_shop_unit_database_to_collection(self, shop_unit: ShopUnitDatabase) -> None:
        """Запись объекта ShopUnitDatabase в базу."""
        self._collection.insert_one(shop_unit.__dict__)
        
    def write_list_shop_unit_database_to_collection(self, shop_units: List[ShopUnitDatabase]) -> None:
        """Запись списка объектов ShopUnitDatabase в базу."""
        for shop_unit in shop_units:
            self.write_shop_unit_database_to_collection(shop_unit)
            
    def check_ids_new_shop_units(self, new_ids_types: List[dict], new_parent_ids: List[str]) -> None:
        """
        1. Проверка отсутствия новых id в уже существующих id с разным type.
        2. Запись объектов с одинаковыми id и type в бд.
        3. Проверка существования parentIds в бд или в новых ShopUnits
        """
        # Словарь существующих товаров и их типов
        old_ids_types = dict()
        
        # Считываем id и type элемента из базы, 
        # запоминаем id категорий из базы
        # и выполняем 1 и 2 задачи
        for old_id_type in self._collection.find({}, {"id": 1, "type": 1}):
            # Если id из базы есть в списке новых id
            if old_id_type["id"] in new_ids_types:
                # Если их type не совпадает
                if new_ids_types[old_id_type["id"]] != old_id_type["type"]:
                    # Вызываем исключение
                    raise ValueError(
                        f"Unit with id={old_id_type['id']} has different type with the already exist in db.")
            # Если id из базы отсутствует в списке новых id
            else:
                # Запоминаем этот id и его type
                old_ids_types[old_id_type["id"]] = old_id_type["type"]
        
        # Проверяем new_parent_ids
        for new_parent_id in new_parent_ids:
            if new_parent_id not in new_ids_types and new_parent_id not in old_ids_types:
                raise ValueError(f"Parent element with id {new_parent_id} not exist")
            else:
                if new_parent_id in new_ids_types and new_ids_types[new_parent_id] == "OFFER":
                    raise ValueError(f"{new_parent_id} is 'OFFER', not 'CATEGORY'")
                elif new_parent_id in old_ids_types and old_ids_types[new_parent_id] == "OFFER":
                    raise ValueError(f"{new_parent_id} is 'OFFER', not 'CATEGORY'")
                
    def recursive_delete_childs(self, childs: Set[Tuple[str, str]], id) -> None:
        """Рекурсивный поиск подкаталогов для удаления"""
        
        elements = self._collection.find({"parentId": id}, {"id": 1, "parentId": 1, "type": 1})
        
        for element in elements:
            childs.add((element["id"], element["parentId"]))
            if element["type"] == "CATEGORY":
                self.recursive_delete_childs(childs, element["id"])
    
    def delete_by_id(self, id: str) -> None:
        """
        Удаление элемента по идентификатору.
        При удалении категории удаляются все дочерние элементы.
        """
        if self.get_type_by_id(id) == "CATEGORY":
            childs = set()
            self.recursive_delete_childs(childs, id)
            for child in childs:
                self._collection.delete_many({"id": child[0], "parentId": child[1]})
        self._collection.delete_many({"id": id})
    
    def get_latest_record_shop_unit(self, id: str) -> ShopUnitDatabase:
        """
        Получение новейшей записи о товаре/категории
        """
        
        try:
            unit = self._collection.find({"id": id}).sort("updateDate", pymongo.DESCENDING).limit(1)[0]
            del unit["_id"]
            shop_unit_database = ShopUnitDatabase(**unit)
            
            return shop_unit_database
        except:
            raise ValueError(f"Unit with id {id} missing in db")
        
    def get_info(self, id: str) -> ShopUnit:
        """Получение информации о товаре/категории"""
        
        shop_unit_database_dict = self.get_latest_record_shop_unit(id).__dict__
        
        iso_date = shop_unit_database_dict["updateDate"].isoformat() + ".000Z"
        
        del shop_unit_database_dict["updateDate"]
        
        shop_unit = ShopUnit(
            **shop_unit_database_dict, 
            date=iso_date)
        
        if shop_unit.type == "CATEGORY":
            storage = []
            
            price_count = self.recursive_get_childrens(storage, shop_unit.id)
                    
            shop_unit.children = storage
            if len(storage) > 0:
                shop_unit.price = math.floor(price_count[0]/price_count[1])
            
        return shop_unit
        
        
    def get_childrens_ids(self, parent_id: str) -> List[str]:
        """Считывание ids элементов c указанным parent_id"""
        
        elements_ids = self._collection.find({"parentId": parent_id}, {"id": 1})
        
        ids = []
        for element_id in elements_ids:
            if element_id["id"] not in ids:
                ids.append(element_id["id"])
        
        return ids
        
    def recursive_get_childrens(self, storage: List[ShopUnit], parent_id: str) -> tuple:
        """Рекурсивное считывание товаров и подкаталогов"""
        
        #Суммарная стоимость и количество товаров текущего каталога
        price = 0
        count = 0
        
        #Считываем id дочерних элементов категории
        ids = self.get_childrens_ids(parent_id)
        
        for id in ids:
            # Получаем актуальную информацию об элементе
            shop_unit_database_dict = self.get_latest_record_shop_unit(id).__dict__
            # Преобразуем дату
            iso_date = shop_unit_database_dict["updateDate"].isoformat() + ".000Z"
            # Удаляем дату из словаря
            del shop_unit_database_dict["updateDate"]
            # Переводим в класс ShopUnit
            shop_unit = ShopUnit(
            **shop_unit_database_dict, 
            date=iso_date)
            
            # Если нашлась подкатегория
            if shop_unit.type == "CATEGORY":
                # Рекурсивно считываем данные подкатегории
                new_storage = []
                price_count = self.recursive_get_childrens(new_storage, shop_unit.id)
                
                # Записываем children и среднюю цену категории
                shop_unit.children = new_storage
                if len(new_storage) > 0:
                    shop_unit.price = math.floor(price_count[0]/price_count[1])
                
                # Увеличиваем суммарную стоимость и кол-во товаров категории
                price += price_count[0]
                count += price_count[1]
            # Если просто товар
            else:
                # Просто увеличиваем стоимость категории и кол-во товаров
                price += shop_unit.price
                count += 1
            
            # Пополняем список childs
            storage.append(shop_unit)
        
        # Возвращаем суммарную стоимость и количество товаров категории
        return (price, count)
    
    def get_ids_parent_actual(self, ids: dict, parend_id: str, date: datetime.datetime) -> List[str]:
        """
        Проверка, действительно указанные _ids имеют актульную
        принадлежность к parent_id на момент date.
        Возвращает валидные _ids
        """
        _ids = list()
        for id in ids:
            data = self._collection.find(
                {"id": id, 
                 "updateDate": {"$lte": date}    
                }, 
                {"parentId": 1, 
                 "updateDate": 1}).sort("updateDate", pymongo.DESCENDING).limit(1)[0]
            if data["parentId"] == parend_id:
                _ids.append(ids[id]["_id"])
        return _ids
        
    
    def get_childrens_by_date(self, parend_id: str, date: datetime.datetime) -> List[int]:
        """Возвращает список _id (MongoDB) элементов с parend_id на момент date"""
        
        elements = self._collection.find(
            {"parentId": parend_id, 
             "updateDate": {"$lte": date}
            }, {"id": 1, "updateDate": 1})
        
        ids = dict()
        for element in elements:
            if element["id"] not in ids:
                ids[element["id"]] = {
                    "_id": element["_id"], 
                    "updateDate": element["updateDate"]}
            elif ids[element["id"]]["updateDate"] < element["updateDate"] :
                ids[element["id"]] = {
                    "_id": element["_id"], 
                    "updateDate": element["updateDate"]}
        
        _ids = self.get_ids_parent_actual(ids, parend_id, date)
        
        return _ids
    
    def get_update_dates_by_id(self, id: str) -> Set[datetime.datetime]:
        """Считывает все даты обновления элемента по id"""
        
        dates = set()
        
        for date in self._collection.find({"id": id}, {"updateDate": 1}):
            dates.add(date["updateDate"])
        
        return dates
            
    def recursive_find_update_dates(self, parent_id: str, update_dates: Set[datetime.datetime]) -> None:
        """Поиск всех дат обновления категории"""
        
        #Считываем id дочерних элементов категории
        ids = self.get_childrens_ids(parent_id)
        
        for id in ids:
            update_dates.update(self.get_update_dates_by_id(id))
            if self.get_type_by_id(id) == "CATEGORY":
                self.recursive_find_update_dates(id, update_dates)
                
    def find_update_dates(self, id: str) -> Set[datetime.datetime]:
        """Поиск всех дат обновления товара/категории"""
        
        update_dates = self.get_update_dates_by_id(id)
        if self.get_type_by_id(id) == "CATEGORY":
            self.recursive_find_update_dates(id, update_dates)
        
        return update_dates
    
    def get_shop_unit_database_by_bd_id(self, _id: str) -> ShopUnitDatabase:
        """
        Получение записи о товаре/категории по _id
        """
        
        try:
            unit = self._collection.find_one({"_id": _id})
            del unit["_id"]
            shop_unit_database = ShopUnitDatabase(**unit)
            
            return shop_unit_database
        except:
            raise ValueError(f"Unit with id {id} missing in db")
    
    def recursive_get_statistic(self, parent_id: str, date: datetime.datetime):
        """Рекурсивное получение статистики по категории за date"""
        
        #Суммарная стоимость и количество товаров текущего каталога
        price = 0
        count = 0
        
        #Считываем id дочерних элементов категории
        _ids = self.get_childrens_by_date(parent_id, date)
        
        for _id in _ids:
            # Получаем актуальную информацию об элементе
            shop_unit_database = self.get_shop_unit_database_by_bd_id(_id)
            
            # Если нашлась подкатегория
            if shop_unit_database.type == "CATEGORY":
                # Рекурсивно считываем данные подкатегории
                price_count = self.recursive_get_statistic(shop_unit_database.id, date)
                
                # Увеличиваем суммарную стоимость и кол-во товаров категории
                price += price_count[0]
                count += price_count[1]
            # Если просто товар
            else:
                # Просто увеличиваем стоимость категории и кол-во товаров
                price += shop_unit_database.price
                count += 1
        
        # Возвращаем суммарную стоимость и количество товаров категории
        return (price, count)
    
    def get_actual_shop_unit_database(self, id: str, date: datetime.datetime) -> ShopUnitDatabase:
        """Получение актуальной ShopUnitDatabase по id на момент date"""
        
        unit = self._collection.find(
                {"id": id, 
                 "updateDate": {"$lte": date}    
                }).sort("updateDate", pymongo.DESCENDING).limit(1)[0]
        
        del unit["_id"]
        shop_unit_database = ShopUnitDatabase(**unit)
            
        return shop_unit_database
                
    def get_statistic(self, id: str, start_date: str, end_date: str) -> ShopUnitStatisticResponse:
        """Получение статистики товара за определенный промежуток времени"""
        
        start_datetime = datetime.datetime.fromisoformat(start_date)
        end_datetime = datetime.datetime.fromisoformat(end_date)
        
        update_dates = self.find_update_dates(id)
        
        dates = list()
        
        for update_date in update_dates:
            if update_date >= start_datetime and update_date < end_datetime:
                dates.append(update_date)
                
        type = self.get_type_by_id(id)
        
        items = []
        for date in dates:
            shop_unit_database_dict = self.get_actual_shop_unit_database(id, date).__dict__
    
            del shop_unit_database_dict["updateDate"]
    
            shop_unit_statistic_unit = ShopUnitStatisticUnit(
                **shop_unit_database_dict, 
                date=date.isoformat() + ".000Z")
            
            if type == "CATEGORY":
                price_count = self.recursive_get_statistic(shop_unit_statistic_unit.id, date)
                if price_count[1] > 0:
                    shop_unit_statistic_unit.price = math.floor(price_count[0]/price_count[1])
            
            items.append(shop_unit_statistic_unit)
            
        shop_unit_statistic_response = ShopUnitStatisticResponse(items=items)

        return shop_unit_statistic_response
    
    def get_type_by_id(self, id: str) -> str:
        """Возвращает type элемента с id"""
        
        return self._collection.find_one({"id": id}, {"type": 1})["type"]
    
    def get_updated_offers(self, start_date: datetime.datetime, end_date: datetime.datetime) -> List[ShopUnitDatabase]:
        """Получение списка обновленных товаров на интервале"""
        
        elements = self._collection.find(
            {"type": "OFFER", "updateDate": {"$gte": start_date, "$lte": end_date}
        })
        
        units = []
        
        for element in elements:
            del element["_id"]
            shop_unit_database = ShopUnitDatabase(**element)
            units.append(shop_unit_database)
        
        return units
    
    def get_sales(self, date: str) -> ShopUnitStatisticResponse:
        """Функция для получения обновленных товаров за сутки от date"""
        
        _datetime = datetime.datetime.fromisoformat(date)
        start_date = _datetime - datetime.timedelta(days=1)
        end_date = _datetime
        
        updated_units = self.get_updated_offers(start_date, end_date)
        
        data = dict()
        
        for updated_unit in updated_units:
            if updated_unit.id not in data:
                data[updated_unit.id] = updated_unit.__dict__
            elif updated_unit.updateDate > data[updated_unit.id]["updateDate"]:
                data[updated_unit.id] = updated_unit.__dict__
                
        items = []
        
        for unit in data.values():
            iso_date = unit["updateDate"].isoformat() + ".000Z"
            del unit["updateDate"]
            items.append(ShopUnitStatisticUnit(
                **unit, 
                date=iso_date))
            
                
        shop_unit_statistic_response = ShopUnitStatisticResponse(items=items)
        
        return shop_unit_statistic_response
        
if __name__ == "__main__":
    a = DatabaseDriver()
    
    print(a.get_statistic(
        "3fa85f64-5717-4562-b3fc-2c963f66a002",
        "2022-05-28T10:00:00",
        "2022-05-28T14:00:00"))
        
    
    
