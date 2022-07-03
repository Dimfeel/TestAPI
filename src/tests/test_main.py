import json

from fastapi.testclient import TestClient

from app.main import app, database

from .shop_test import load_data, merge_catalogs, read_wrong_data, read_data
from .shop_test import load_offer_updates, read_shop_with_offer_updates, read_sales
from .shop_test import merge_catalogs, read_statistic

client = TestClient(app)

with open("/src/tests/data_input.json") as file:
    data_input = json.load(file)
    
with open("/src/tests/data_output.json") as file:
    data_output = json.load(file)

def test_wrong_input():
    """Тест ошибочного ввода (отсутствует parent в базе)"""
    
    response = client.post("/imports", json=data_input["test1_input"])
    assert response.status_code == 400
    assert response.json() == data_output["error_output"]
    
def test_input():
    """Тест правильного ввода данных"""
    
    response = client.post("/imports", json=data_input["test2_input"])
    database.clear_collection()
    assert response.status_code == 200
    
def test_shop_1():
    """
    Первая часть теста на примере магазина с товарами:
    1. Загрузка исходных данных
    2. Считывание несуществующего товара
    3. Считывание товара, каталога, всего магазина
    """
    
    # 1. Загрузка исходных данных
    load_data(client, data_input)
    # 2. Считывание несуществующего товара
    read_wrong_data(client, data_output)
    # 3. Считывание товара, каталога, всего магазина
    read_data(client, data_output)
    
def test_shop_2():
    """
    Вторая часть теста на примере магазина с товарами:
    1. Загружаем обновления цен товаров
    2. Считываем каталог магазина с обновленными товарами
    3. Проверяем обновления товаров за 24 часа
    """
    # 1. Загружаем обновления цен товаров
    load_offer_updates(client, data_input)
    # 2. Считываем каталог магазина с обновленными товарами
    read_shop_with_offer_updates(client, data_output)
    # 3. Проверяем обновления товаров за 24 часа
    read_sales(client, data_output)
    
def test_shop_3():
    """
    Третья часть теста на примере магазина с товарами:
    1. Объединяем каталоги смартфонов и планшетов
    2. Считываем статистику по товарам/каталогам
    """
    
    # 1. Объединяем каталоги смартфонов и планшетов
    merge_catalogs(client, data_input, data_output)
    # 2. Считываем статистику по товарам/каталогам
    read_statistic(client, data_output)
    
    # Очищаем коллекцию
    database.clear_collection()
    