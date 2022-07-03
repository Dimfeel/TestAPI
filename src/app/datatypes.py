import datetime

from uuid import UUID
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, validator

class ShopUnitImport(BaseModel):
    """Товар или категория"""

    id: str = Field(
        ...,
        description="Уникальный идентфикатор",
    )
    name: str = Field(
        ...,
        description="Имя элемента",
    )
    parentId: Optional[str] = Field(
        None,
        description="UUID родительской категории",
    )
    type: Literal["OFFER", "CATEGORY"] = Field(
        ...,
        description="Тип элемента - категория или товар",
    )
    price: Optional[int] = Field(
        None,
        description="Целое число, для категорий поле должно содержать null.",
    )
    
    @validator("id")
    def is_id_is_uuid(cls, id):
        """Проверка, является ли id валидным uuid."""
        try:
            _ = UUID(id, version=4)
        except ValueError:
            raise ValueError(f"Offer {id} must be valid uuid value")
        return id
    
    @validator("parentId")
    def is_parentId_is_uuid_or_None(cls, v, values, **kwargs):
        """Проверка, является ли parentId валидным uuid или None."""
        if v == values["id"]:
            raise ValueError(f"id and parentId can't be the same")
        if v is None:
            return v
        try:
            _ = UUID(v, version=4)
        except ValueError:
            raise ValueError(f"ParentId {v} must be valid uuid value or None")
        return v
        
    @validator("price")
    def validate_price(cls, v, values, **kwargs):
        """Проверка, что цена для категории равна None"""
        if "type" not in values:
            return
        if values["type"] == "CATEGORY" and v is not None:
            raise ValueError("Price for 'CATEGORY' must be null")
        if values["type"] == "OFFER" and v < 0:
            raise ValueError("Price for 'OFFER' must >= 0")
        return v
        
class ShopUnit(BaseModel):
    """Товар или категория"""

    id: str = Field(
        ...,
        description="Уникальный идентфикатор",
    )
    name: str = Field(
        ...,
        description="Имя элемента",
    )
    date: str = Field(
        ...,
        description="Время последнего обновления элемента"
    )
    parentId: Optional[str] = Field(
        None,
        description="UUID родительской категории",
    )
    type: Literal["OFFER", "CATEGORY"] = Field(
        ...,
        description="Тип элемента - категория или товар",
    )
    price: Optional[int] = Field(
        None,
        description="Целое число, для категории - это средняя цена \
        всех дочерних товаров(включая товары подкатегорий). \
        Если цена является не целым числом, \
        округляется в меньшую сторону до целого числа. \
        Если категория не содержит товаров цена равна null.",
    )
    children: List["ShopUnit"] = Field(
        None,
        description="Список всех дочерних товаров\категорий. \
        Для товаров поле равно null.",
    )

class ShopUnitImportRequest(BaseModel):
    items: List[ShopUnitImport] = Field(
        ...,
        description="Импортируемые элементы",
    )
    updateDate: str = Field(
        ...,
        description="Время обновления добавляемых товаров/категорий"
    )
    
    @validator("updateDate")
    def validate_date(date):
        """Проверка, соответствует ли дата ISO 8601"""
        try:
            _ = datetime.datetime.fromisoformat(date.replace('Z', ''))
        except:
            raise ValueError("updateDate must be in ISO 8601 format")
        return date.replace('Z', '')

class ShopUnitStatisticUnit(BaseModel):
    id: str = Field(
        ...,
        description="Уникальный идентфикатор",
    )
    name: str = Field(
        ...,
        description="Имя элемента",
    )
    parentId: Optional[str] = Field(
        None,
        description="UUID родительской категории",
    )
    type: Literal["OFFER", "CATEGORY"] = Field(
        ...,
        description="Тип элемента - категория или товар",
    )
    price: Optional[int] = Field(
        None,
        description="Целое число, для категорий поле должно содержать null.",
    )
    date: str = Field(
        ...,
        description="Время последнего обновления элемента"
    )
    
class ShopUnitStatisticResponse(BaseModel):
    items: List[ShopUnitStatisticUnit] = Field(
        ...,
        description="История в произвольном порядке."
    )

class Error(BaseModel):
    code: int = Field(
        ...,
        description="Код ошибки"
    )
    message: str = Field(
        ...,
        description="Текст ошибки"
    )
    
if __name__ == "__main__":
    
    shop_unit_import_example_dict_1 = {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66a444",
      "name": "Оффер",
      "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a333",
      "price": 234,
      "type": "OFFER"
    }
    
    shop_unit_import_example_dict_2 = {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66a444",
      "name": "Оффер",
      "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a333",
      "price": 233444,
      "type": "OFFER"
    }
    
    shop_unit_import_example_1 = ShopUnitImport(**shop_unit_import_example_dict_1)
    shop_unit_import_example_2 = ShopUnitImport(**shop_unit_import_example_dict_2)
    
    shop_unit_import_request_example_dict = {
        "items": [
            shop_unit_import_example_1,
            shop_unit_import_example_2
        ],
        "updateDate": "2022-05-28T21:12:01.000Z"
    }
    shop_unit_import_request_example = ShopUnitImportRequest(
        **shop_unit_import_request_example_dict
    )
    
    print(shop_unit_import_request_example.__dict__)
    
