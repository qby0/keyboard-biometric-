# Persona by Text – Распознавание автора текста и клавиатурная биометрия

Проект для семестрового задания: определение личности пользователя по стилю текста (стилометрия) и по динамике набора (клавиатурная биометрия).

## Возможности
- Текстовая авторизация (стилометрия): логистическая регрессия на char/word n‑граммах (TF‑IDF)
- Клавиатурная биометрия: признаки по временам удержания и межклавиатурным задержкам + логистическая регрессия
- Веб‑приложение для сбора датасета динамики набора
- CLI для обучения/оценки/предсказаний и отчетов

## Установка
```bash
python3 -m pip install -e .
```
Если бинарные скрипты не в PATH, используйте `python3 -m`.

## Структура данных
- Стилометрия (текст): `data_text/{user}/*.txt`
- Клавиатура: `keystroke_data/{user}/*.json`
  - JSON либо массив событий, либо объект `{ events: [...] }` как в веб‑приложении

## Сбор датасета клавиатуры
```bash
python3 -m persona_by_text.webapp
# откройте http://localhost:8000 и записывайте образцы
```
Файлы сохраняются в `./keystroke_data/{user}/...json`.

## Обучение/оценка
- Стилометрия:
```bash
python3 -m persona_by_text train --data data_text --model-out model_text.joblib
python3 -m persona_by_text evaluate --model model_text.joblib --data data_text
python3 -m persona_by_text predict --model model_text.joblib --text "пример текста"
```
- Клавиатура:
```bash
python3 -m persona_by_text ks-train --data keystroke_data --model-out ks_model.joblib
python3 -m persona_by_text ks-evaluate --model ks_model.joblib --data keystroke_data
```

## Отчеты и визуализации
```bash
python3 -m persona_by_text report --model model_text.joblib --data data_text --out reports/text_report
python3 -m persona_by_text ks-report --model ks_model.joblib --data keystroke_data --out reports/ks_report
```
Отчеты содержат матрицу ошибок, метрики, распределения вероятностей. (См. раздел ниже.)

## Примерные датасеты
- `examples/text_data/author_a/*.txt`, `author_b/*.txt` — короткие заглушки
- `examples/keystroke_data/user_a/*.json`, `user_b/*.json` — синтетические примеры

## Запуск через Docker
```bash
make docker-build
make docker-run
```
После запуска: `python3 -m persona_by_text ...`

## Тесты
```bash
python3 -m pip install -r requirements-dev.txt
pytest -q
```

## Лицензия
MIT. См. `LICENSE`.

## Замечания по качеству
- Для надежности нужна достаточная выборка: десятки образцов на пользователя.
- Лучше фиксированная фраза для клавиатурной биометрии.
- Модели простые, но воспроизводимые; легко заменить на более сложные.
