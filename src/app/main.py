from fastapi import FastAPI
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .database import DatabaseDriver
from .datatypes import ShopUnitImportRequest

from .parsers import parse_shop_unit_import_request, get_ids_types_from_shop_units
from .parsers import get_parent_ids_from_shop_units, validate_id, validate_date

app = FastAPI(title="Didenok API")

database = DatabaseDriver()

class CustomException(Exception):
    def __init__(self, name: str) -> None:
        self.name = name

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exception: CustomException) -> JSONResponse:
    return JSONResponse (
        status_code = 400, 
        content = {
            "code": 400,
            "message": "Validation Failed",
            }
        )
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(exc)
    return JSONResponse (
        status_code = 400, 
        content = {
            "code": 400,
            "message": "Validation Failed",
            }
        )

@app.post(
    "/imports",
    description="Импортирует новые товары и/или категории.",
)
async def imports(input: ShopUnitImportRequest) -> None:
    
    try:
        # Преобразуем в List[ShopUnitDatabase]
        parsed_input = parse_shop_unit_import_request(input)
        # Считываем id и type новых ShopUnits
        new_ids_types = get_ids_types_from_shop_units(parsed_input)
        # Считываем parentId новых ShopUnits
        new_parent_ids = get_parent_ids_from_shop_units(parsed_input)
        # Проверяем ids (см. описание функции)
        database.check_ids_new_shop_units(new_ids_types, new_parent_ids)
        # Записываем в бд новые ShopUnits
        database.write_list_shop_unit_database_to_collection(parsed_input)
    
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        raise CustomException(name = "Validation Failed")
    
@app.delete(
    "/delete/{id}",
    description="Удалить элемент по идентификатору."
)
async def delete_shop_unit(id: str) -> None:
    
    try:
        validate_id(id)
        database.delete_by_id(id)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        raise CustomException(name = "Validation Failed")
    
@app.get(
    '/nodes/{id}',
    description="Получить информацию об элементе по идентификатору."
)
async def get_info(id: str) -> None:
    try:
        validate_id(id)
        return database.get_info(id)
    except Exception as e:
        print(e)
        raise CustomException(name = "Validation Failed")
    
@app.get(
    '/sales',
    description="Получение списка **товаров**, цена которых была обновлена " \
        "за последние 24 часа включительно [now() - 24h, now()] " \
        "от времени переданном в запросе."
)
async def get_sales(date: str) -> None:
    try:
        date = validate_date(date)
        return database.get_sales(date)
    except Exception as e:
        print(e)
        raise CustomException(name = "Validation Failed")

@app.get(
    '/node/{id}/statistic',
    description="Получение статистики (истории обновлений) по " \
        "товару/категории за заданный полуинтервал [from, to). " \
        "Статистика по удаленным элементам недоступна."
) 
async def get_statistic(id: str, start_date: str, end_date: str) -> None:
    try:
        validate_id(id)
        start_date = validate_date(start_date)
        end_date = validate_date(end_date)
        return database.get_statistic(id, start_date, end_date)
    except Exception as e:
        print(e)
        raise CustomException(name = "Validation Failed")
    

        