from fastapi.testclient import TestClient

def load_data(client: TestClient, data_input: dict) -> None:
    """Считываем данные магазина из JSONов"""
    
    print("Считываем данные 'Магазин электроники'", end="")
    for i in range(7):
        response = client.post("/imports", json=data_input[f"test3_input_{i+1}"])
        assert response.status_code == 200
        print(".", end="")
    print(" ОК")

def read_wrong_data(client: TestClient, data_output: dict) -> None:
    """Считываем товар с несуществующим id"""
    
    id = "3fa85f64-5717-4562-b3fc-2c963f66a444"
    
    response = client.get(f"/nodes/{id}")
    assert response.status_code == 400
    assert response.json() == data_output["error_output"]
    print("Считывание несуществующего товара... OK")
    
def read_data(client: TestClient, data_output: dict):
    """Считываем существующий товар, каталог с товарами, каталог с подкаталогами"""
    
    id_offer = "3fa85f64-5717-4562-b3fc-2c963f66a015"
    id_catalog = "3fa85f64-5717-4562-b3fc-2c963f66a002"
    id_shop = "3fa85f64-5717-4562-b3fc-2c963f66a001"
    
    print("Считываем товар...", end="")
    response = client.get(f"/nodes/{id_offer}")
    assert response.status_code == 200
    assert response.json() == data_output["test_3_output_1"]
    print(" ОК")
    
    print("Считываем каталог...", end="")
    response = client.get(f"/nodes/{id_catalog}")
    assert response.status_code == 200
    assert response.json() == data_output["test_3_output_2"]
    print(" ОК")
    
    print("Считываем весь магазин...", end="")
    response = client.get(f"/nodes/{id_shop}")
    assert response.status_code == 200
    assert response.json() == data_output["test_3_output_3"]
    print(" ОК")
    
    
def load_offer_updates(client: TestClient, data_input: dict) -> None:
    """Загружаем обновление товаров из JSONов"""
    
    print("Загружаем обновления товаров", end="")
    for i in range(3):
        response = client.post("/imports", json=data_input[f"test4_input_{i+1}"])
        assert response.status_code == 200
        print(".", end="")
    print(" ОК")
    
def read_shop_with_offer_updates(client: TestClient, data_output: dict):
    """Считываем каталог магазина с обновленными товарами"""
    
    id_shop = "3fa85f64-5717-4562-b3fc-2c963f66a001"
    
    print("Считываем весь магазин...", end="")
    response = client.get(f"/nodes/{id_shop}")
    assert response.status_code == 200
    assert response.json() == data_output["test_4_output_1"]
    print(" ОК")
    
def read_sales(client: TestClient, data_output: dict):
    """Проверяем обновления товаров за 24 часа"""
    
    data_1 = "2022-05-27T21:00:00.000Z"
    data_2 = "2022-05-28T21:11:00.000Z"
    data_3 = "2022-05-29T21:00:00.000Z"
    data_4 = "2022-05-29T21:15:00.000Z"
    
    print(f"Считываем обновления за {data_1} ...", end="")
    response = client.get(f"/sales", params={"date": data_1})
    assert response.status_code == 200
    assert response.json() == data_output["test_4_output_2"]
    print(" ОК")
    
    print(f"Считываем обновления за {data_2} ...", end="")
    response = client.get(f"/sales", params={"date": data_2})
    assert response.status_code == 200
    assert response.json() == data_output["test_4_output_3"]
    print(" ОК")
    
    print(f"Считываем обновления за {data_3} ...", end="")
    response = client.get(f"/sales", params={"date": data_3})
    assert response.status_code == 200
    assert response.json() == data_output["test_4_output_4"]
    print(" ОК")
    
    print(f"Считываем обновления за {data_4} ...", end="")
    response = client.get(f"/sales", params={"date": data_4})
    assert response.status_code == 200
    assert response.json() == data_output["test_4_output_5"]
    print(" ОК")
        
def merge_catalogs(client: TestClient, data_input: dict, data_output: dict) -> None:
    """Объединяем каталоги смартфонов и планшетов"""
    
    print("Загружаем обновления товаров и каталогов...", end="")
    response = client.post("/imports", json=data_input["test5"])
    assert response.status_code == 200
    print(" ОК")
    
    id_shop = "3fa85f64-5717-4562-b3fc-2c963f66a001"
    
    print("Считываем весь магазин...", end="")
    response = client.get(f"/nodes/{id_shop}")
    assert response.status_code == 200
    assert response.json() == data_output["test_5_output_1"]
    print(" ОК")
    
    id_tablets = "3fa85f64-5717-4562-b3fc-2c963f66a003"
    
    print("Удаляем старый каталог планшетов...", end="")
    response = client.delete(f"/delete/{id_tablets}")
    assert response.status_code == 200
    print(" ОК")
    
    print("Считываем весь магазин...", end="")
    response = client.get(f"/nodes/{id_shop}")
    assert response.status_code == 200
    assert response.json() == data_output["test_5_output_2"]
    print(" ОК")
    
def read_statistic(client: TestClient, data_output: dict) -> None:
    """Считываем статистику по товарам/каталогам"""
    
    # Статистика по смартфонам -> смартфонам и планшетам
    id_smartphones = "3fa85f64-5717-4562-b3fc-2c963f66a002"
    #до merge
    start_date_1 = "2022-05-28T10:00:00.000Z"
    end_date_1 = "2022-05-28T14:00:00.000Z"
    #после merge
    start_date_2 = "2022-05-28T10:00:00.000Z"
    end_date_2 = "2022-06-01T14:00:00.000Z"
    
    #Статистика по чехлу на Honor
    id_honor_case = "3fa85f64-5717-4562-b3fc-2c963f66a021"
    start_date_3 = "2022-05-28T10:00:00.000Z"
    end_date_3 = "2022-06-01T14:00:00.000Z"
    
    print(f"Считываем старую статистику по каталогу смартфонов...", end="")
    response = client.get(
        f"/node/{id_smartphones}/statistic", 
        params={
            "start_date": start_date_1,
            "end_date": end_date_1})
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item in data_output["test_5_output_3"]["items"]
    print(" ОК")
    
    print(f"Считываем новую статистику по каталогу смартфонов...", end="")
    response = client.get(
        f"/node/{id_smartphones}/statistic", 
        params={
            "start_date": start_date_2,
            "end_date": end_date_2})
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item in data_output["test_5_output_4"]["items"]
    print(" ОК")
    
    print(f"Считываем статистику по чехлу на Honor...", end="")
    response = client.get(
        f"/node/{id_honor_case}/statistic", 
        params={
            "start_date": start_date_3,
            "end_date": end_date_3})
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item in data_output["test_5_output_5"]["items"]
    print(" ОК")
    
    
    
    
    