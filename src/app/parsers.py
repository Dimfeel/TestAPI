import datetime

from typing import List, Union
from uuid import UUID

from .datatypes import ShopUnit, ShopUnitImport, ShopUnitImportRequest 
from .database import ShopUnitDatabase

ShopUnits = Union[ShopUnit, ShopUnitImport, ShopUnitImportRequest]

def parse_shop_unit_import_request(input: ShopUnitImportRequest) -> List[ShopUnitDatabase]:
    """Подготовка входных данных к загрузке в базу данных"""
    
    date = input.updateDate
    
    output = []
    for item in input.items:
        output.append(ShopUnitDatabase(updateDate=datetime.datetime.fromisoformat(date), **item.__dict__))
    
    return output
    
def get_ids_types_from_shop_units(shop_units: List[ShopUnits]) -> List[str]:
    """Считываем id и type из списка новых ShopUnits"""
    ids_types = dict()
    
    for shop_unit in shop_units:
        if shop_unit.id not in ids_types:
            ids_types[shop_unit.id] = shop_unit.type
        else:
            raise ValueError(f"Multiple id in one request")
    
    return ids_types

def get_parent_ids_from_shop_units(shop_units: List[ShopUnits]) -> List[str]:
    """Считываем parentId из списка новых ShopUnits"""
    parent_ids = []
    
    for shop_unit in shop_units:
        if (parent_id:=shop_unit.parentId) is not None and parent_id not in parent_ids:
            parent_ids.append(parent_id)
    
    return parent_ids

def validate_id(id: str) -> None:
    """Проверка, является ли входной id валидным uuid."""
    try:
        _ = UUID(id, version=4)
    except ValueError:
        raise ValueError(f"Offer {id} must be valid uuid value")
    
def validate_date(date):
    """Проверка, соответствует ли дата ISO 8601"""
    try:
        _ = datetime.datetime.fromisoformat(date.replace('Z', ''))
    except:
        raise ValueError(f"{date} must be in ISO 8601 format")
    return date.replace('Z', '')
    
