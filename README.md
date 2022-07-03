# Тестовое задание Didenok API

FastAPI + MongoDB + Docker

Запуск контейнеров ```docker-compose up -d```

Для запуска тестов желательно установить флаг ```TESTING = False``` в ```.env```

Запуск тестов ```docker-compose exec api pytest -rP . ```

Можно удалить  ```database.clear_collection()```  в последней строчке файла ```src/tests/test_main.py``` и посмотреть тестовые данные через  ```http://127.0.0.1:8081/db/price_comparison_db/products_and_categories_test```,  а также запустить свои тестовые запросы в ```http://127.0.0.1/docs```