"""
Лабораторная работа №1, Вариант 18
Разработка веб-приложения на Flask для обработки изображений
периодическими функциями (sin/cos)

Задание: Веб-приложение должно формировать новое изображение на основе
исходного путем умножения изображения на периодическую функцию sin или cos
с нормировкой, период изменения задает пользователь, аргумент функции
определяется вертикальной или горизонтальной составляющей. Нарисовать
график распределения цветов для нового и исходного изображения.

Автор: Студент ТУСУР, ФДО
Красильников В.В.
Дата: 2026
"""

# ============================================
# ИМПОРТ НЕОБХОДИМЫХ БИБЛИОТЕК
# ============================================

# Стандартные библиотеки Python
import os                    # Работа с операционной системой, файлами и путями
import secrets              # Генерация криптографически безопасных случайных чисел

# Библиотеки для обработки изображений и данных
import numpy as np          # Работа с многомерными массивами и математические операции
from PIL import Image,ImageDraw, ImageFont       # Открытие, обработка и сохранение изображений

# Библиотеки для построения графиков
import matplotlib           # Библиотека для визуализации данных
matplotlib.use('Agg')       # Используем non-interactive backend для работы с веб-приложением
import matplotlib.pyplot as plt  # Интерфейс для построения графиков

# Библиотеки для добавления времени на обработанную картинку
from datetime import datetime # Работа со временем

# Библиотеки для работы с данными в памяти
import io                   # Работа с потоками данных в памяти
import base64              # Кодирование/декодирование данных в формат Base64

# Flask и связанные библиотеки для веб-разработки
from flask import Flask, render_template, flash  # Основной фреймворк Flask
from flask_wtf import FlaskForm, RecaptchaField  # Формы и капча
from wtforms import SelectField, FloatField, SubmitField, BooleanField  # Поля формы
from wtforms.validators import DataRequired, NumberRange  # Валидаторы полей
from flask_wtf.file import FileField, FileAllowed, FileRequired  # Загрузка файлов
from flask_bootstrap import Bootstrap  # Bootstrap для стилизации

# Загрузка переменных окружения из файла .env
from dotenv import load_dotenv
from pathlib import Path  # Работа с путями файловой системы

# ============================================
# ИНИЦИАЛИЗАЦИЯ И КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ
# ============================================

# Отладочная информация о файле .env
env_path = Path('.env')
print("=" * 50)
print("🔍 ПРОВЕРКА ФАЙЛА .env")
print(f"📁 Текущая директория: {Path.cwd()}")
print(f"📄 Файл .env существует: {env_path.exists()}")

if env_path.exists():
    content = env_path.read_text()
    print(f"📄 Строк в .env: {len(content.splitlines())}")
    # Выводим имена переменных (без значений для безопасности)
    for line in content.splitlines():
        if line.strip() and not line.startswith('#'):
            var_name = line.split('=')[0].strip()
            print(f"   ✓ {var_name}")

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем значения переменных окружения
recaptcha_public = os.getenv('RECAPTCHA_PUBLIC_KEY')
recaptcha_private = os.getenv('RECAPTCHA_PRIVATE_KEY')
secret_key = os.getenv('SECRET_KEY')

# Выводим информацию о загруженных ключах
print(f"\n🔑 ЗАГРУЖЕННЫЕ ПЕРЕМЕННЫЕ:")
print(f"   RECAPTCHA_PUBLIC_KEY: {'✓ Загружен' if recaptcha_public else '✗ None'}")
print(f"   RECAPTCHA_PRIVATE_KEY: {'✓ Загружен' if recaptcha_private else '✗ None'}")
print(f"   SECRET_KEY: {'✓ Загружен' if secret_key else '✗ None'}")

# Проверка наличия необходимых ключей
if not recaptcha_public or not recaptcha_private:
    print("\n⚠️  ВНИМАНИЕ: reCAPTCHA ключи не загружены!")
    print("   Создайте файл .env в корне проекта:")
    print("   RECAPTCHA_PUBLIC_KEY=ваш_публичный_ключ")
    print("   RECAPTCHA_PRIVATE_KEY=ваш_приватный_ключ")
    print("   SECRET_KEY=ваш_секретный_ключ")
print("=" * 50)

# Создание экземпляра приложения Flask
app = Flask(__name__)

# Конфигурация приложения
app.config['SECRET_KEY'] = secret_key or secrets.token_hex(32)  # Секретный ключ для защиты
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Папка для загрузки файлов
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Максимальный размер файла: 16 МБ

# Конфигурация reCAPTCHA v2 (защита от ботов)
app.config['RECAPTCHA_PUBLIC_KEY'] = recaptcha_public  # Публичный ключ (виден в браузере)
app.config['RECAPTCHA_PRIVATE_KEY'] = recaptcha_private  # Приватный ключ (только на сервере)
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'}  # Тема виджета капчи

# Конфигурация для локальной разработки
app.config['TESTING'] = False  # Отключает проверку reCAPTCHA при разработке

# Для продакшена (при деплое) используется:
# app.config['TESTING'] = False

app.config['WTF_CSRF_ENABLED'] = True  # Включение защиты CSRF

# Инициализация расширения Bootstrap для стилизации
bootstrap = Bootstrap(app)

# Создание папки для загрузок, если она не существует
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ============================================
# КЛАСС ФОРМЫ ЗАГРУЗКИ ИЗОБРАЖЕНИЯ
# ============================================

class ImageUploadForm(FlaskForm):
    """
    Класс формы для загрузки и обработки изображения.

    Содержит поля для:
    - Загрузки файла изображения
    - Выбора периодической функции (sin/cos)
    - Указания периода изменения
    - Выбора направления модуляции (горизонтальное/вертикальное)
    - Проверки reCAPTCHA (защита от ботов)
    """

    # Поле для загрузки файла изображения
    image = FileField('Выберите изображение:', validators=[
        FileRequired(),  # Файл обязателен
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'], 'Только изображения!')
    ])

    # Выбор периодической функции (sin или cos)
    function = SelectField('Периодическая функция:',
                           choices=[('sin', 'Синус (sin)'), ('cos', 'Косинус (cos)')],
                           default='sin')

    # Поле для ввода периода изменения (число с плавающей точкой)
    period = FloatField('Период изменения (пикселей):',
                        validators=[
                            DataRequired(),  # Обязательное поле
                            NumberRange(min=1, max=1000)  # Диапазон от 1 до 1000
                        ],
                        default=50.0)

    # Выбор направления модуляции
    direction = SelectField('Направление:',
                            choices=[
                                ('horizontal', 'Горизонтальное'),
                                ('vertical', 'Вертикальное')
                            ],
                            default='horizontal')

    # НОВОЕ ПОЛЕ: чекбокс для добавления времени
    add_timestamp = BooleanField('Добавить время создания')

    # Поле reCAPTCHA для защиты от автоматических ботов
    recaptcha = RecaptchaField()

    # Кнопка отправки формы
    submit = SubmitField('Обработать изображение')


# ============================================
# ФУНКЦИЯ СОЗДАНИЯ ГИСТОГРАММЫ ЦВЕТОВ
# ============================================

def create_color_histogram(image, title):
    """
    Создает гистограмму распределения цветов изображения.

    Параметры:
        image (PIL.Image): Изображение в формате PIL
        title (str): Заголовок гистограммы

    Возвращает:
        str: Base64-кодированная строка изображения гистограммы

    Гистограмма показывает распределение значений пикселей
    по каждому цветовому каналу (R, G, B) или по интенсивности
    для черно-белых изображений.
    """

    # Создаем новую фигуру для графика размером 10x4 дюйма
    plt.figure(figsize=(10, 4))

    # Проверяем, является ли изображение цветным (RGB)
    if image.mode == 'RGB':
        # Разделяем изображение на три цветовых канала
        r, g, b = image.split()
        colors = ['red', 'green', 'blue']  # Цвета для отображения на графике
        channels = [r, g, b]  # Список каналов

        # Строим гистограмму для каждого канала
        for color, channel in zip(colors, channels):
            # Преобразуем канал в массив numpy и "выравниваем" его в одномерный массив
            # bins=256 - количество столбцов гистограммы (по одному на каждое значение 0-255)
            # alpha=0.7 - прозрачность для наложения графиков
            # density=True - нормализация площади гистограммы до 1
            plt.hist(np.array(channel).flatten(), bins=256, color=color,
                     alpha=0.7, label=color.upper(), density=True)
    else:
        # Для черно-белых изображений строим одну гистограмму
        plt.hist(np.array(image).flatten(), bins=256, color='gray',
                 alpha=0.7, label='Intensity', density=True)

    # Настройка заголовка и подписей осей
    plt.title(f'Распределение цветов - {title}')
    plt.xlabel('Значение пикселя')  # Значения от 0 до 255
    plt.ylabel('Плотность')  # Нормализованная плотность
    plt.legend()  # Отображение легенды с названиями каналов
    plt.grid(True, alpha=0.3)  # Сетка на графике с прозрачностью 0.3

    # Сохраняем график в буфер памяти (не на диск)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')  # dpi=100 - качество
    buf.seek(0)  # Возвращаем указатель в начало буфера
    plt.close()  # Закрываем фигуру для освобождения памяти

    # Кодируем изображение в формат Base64 для передачи в HTML
    return base64.b64encode(buf.getvalue()).decode('utf-8')


# ============================================
# ФУНКЦИЯ ПРИМЕНЕНИЯ ПЕРИОДИЧЕСКОЙ ФУНКЦИИ
# ============================================

def apply_periodic_function(image, function_type, period, direction, add_timestamp=False):
    """
    Применяет периодическую функцию (sin или cos) к изображению с нормировкой.

    Алгоритм работы:
    1. Преобразует изображение в массив чисел с плавающей точкой
    2. Нормализует значения пикселей в диапазон [0, 1]
    3. Создает координатную сетку для заданного периода
    4. Вычисляет периодическую функцию (sin/cos) на сетке
    5. Нормирует функцию в диапазон [0, 1]
    6. Умножает изображение на модулирующую функцию
    7. Возвращает обработанное изображение

    Параметры:
        image (PIL.Image): Исходное изображение
        function_type (str): Тип функции - 'sin' или 'cos'
        period (float): Период функции в пикселях
        direction (str): Направление - 'horizontal' или 'vertical'

    Возвращает:
        PIL.Image: Обработанное изображение
    """

    # Преобразуем изображение в массив numpy с типом float32
    img_array = np.array(image, dtype=np.float32)

    # Нормализуем значения пикселей в диапазон [0, 1]
    # Если максимальное значение больше 1 (обычно 255 для изображений),
    # делим все значения на 255
    if img_array.max() > 1:
        img_array = img_array / 255.0

    # Получаем размеры изображения: высота и ширина
    height, width = img_array.shape[:2]

    # Создаем координатную сетку для периодической функции
    # Создаем массивы координат x и y
    # x: от 0 до 2π * (ширина / период) - это обеспечивает заданный период
    # Например, если период = 50 пикселей, то функция sin(2π*x/50)
    # будет иметь период 50 пикселей
    x = np.linspace(0, 2 * np.pi * (width / period), width)

    y = np.linspace(0, 2 * np.pi * (height / period), height)

    # Создаем двумерную сетку координат с помощью meshgrid
    if direction == 'horizontal':
        # Горизонтальное направление: функция зависит от координаты x
        X, _ = np.meshgrid(x, y)  # X - матрица координат x, _ - игнорируем координаты y
        periodic_func = X
    else:  # vertical
        # Вертикальное направление: функция зависит от координаты y
        _, Y = np.meshgrid(x, y)  # Y - матрица координат y
        periodic_func = Y

    # Применяем выбранную периодическую функцию
    if function_type == 'sin':
        modulation = np.sin(periodic_func)
    else:  # cos
        modulation = np.cos(periodic_func)

    # Нормировка функции в диапазон [0, 1]
    # sin и cos дают значения в диапазоне [-1, 1]
    # (modulation + 1) / 2 преобразует [-1, 1] в [0, 1]
    # Пример: sin(0) = 0 → (0 + 1) / 2 = 0.5
    #         sin(π/2) = 1 → (1 + 1) / 2 = 1
    #         sin(-π/2) = -1 → (-1 + 1) / 2 = 0
    modulation = (modulation + 1) / 2.0

    # Применяем модуляцию к изображению
    # Для цветных изображений (3D массив: высота × ширина × каналы)
    if len(img_array.shape) == 3:  # Color image
        # [:, :, np.newaxis] добавляет новую ось для правильного умножения
        # Результат: каждое значение пикселя умножается на соответствующее
        # значение модулирующей функции
        result = img_array * modulation[:, :, np.newaxis]
    else:  # Grayscale (2D массив: высота × ширина)
        result = img_array * modulation

    # Ограничиваем значения в диапазоне [0, 1] (защита от переполнения)
    result = np.clip(result, 0, 1)

    # Конвертируем обратно в 8-битное изображение (0-255)
    result = (result * 255).astype(np.uint8)

    processed_image = Image.fromarray(result)

    # ДОБАВЛЕНИЕ ВРЕМЕНИ (только если чекбокс отмечен)
    if add_timestamp:
        draw = ImageDraw.Draw(processed_image)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Автоматический выбор шрифта (работает на всех ОС)
        try:
            # Windows
            font = ImageFont.truetype("arial.ttf", 42)
        except:
            try:
                # Linux/Mac
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
            except:
                # Резервный вариант
                font = ImageFont.load_default()

        # Получаем размеры текста через textbbox
        bbox = draw.textbbox((0, 0), timestamp, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Позиция: правый нижний угол с отступом 10 пикселей
        x = width - text_width - 10
        y = height - text_height - 10

        # Тень для читаемости
        draw.text((x + 1, y + 1), timestamp, fill=(0, 0, 0, 128), font=font)
        # Основной текст белым
        draw.text((x, y), timestamp, fill=(255, 255, 255), font=font)

    # Создаем объект PIL Image из массива numpy
    return processed_image


# ============================================
# МАРШРУТ ГЛАВНОЙ СТРАНИЦЫ
# ============================================

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Обработчик главной страницы приложения.

    Методы:
        GET - отображает пустую форму для загрузки изображения
        POST - обрабатывает загруженное изображение и показывает результат

    Логика работы:
    1. Создает форму загрузки изображения
    2. Проверяет валидность формы (включая reCAPTCHA)
    3. Загружает и обрабатывает изображение
    4. Создает гистограммы для исходного и обработанного изображений
    5. Кодирует изображения в Base64 для отображения в шаблоне
    6. Возвращает шаблон с результатами
    """

    # Создаем экземпляр формы
    form = ImageUploadForm()

    # Проверяем, была ли форма отправлена и прошла ли валидацию
    if form.validate_on_submit():
        # Выводим отладочную информацию
        print("\n✅ Форма прошла валидацию!")
        print(f"   Функция: {form.function.data}")
        print(f"   Период: {form.period.data}")
        print(f"   Направление: {form.direction.data}")

        try:
            # Получаем загруженный файл из формы
            file = form.image.data

            # Открываем изображение с помощью PIL
            original_image = Image.open(file)

            # Конвертируем изображение в RGB, если оно в другом формате
            # (например, RGBA, CMYK, L (grayscale))
            if original_image.mode != 'RGB':
                original_image = original_image.convert('RGB')

            # Получаем параметры обработки из формы
            function_type = form.function.data
            period = form.period.data
            direction = form.direction.data

            # ПОЛУЧАЕМ ЗНАЧЕНИЕ ЧЕКБОКСА
            add_timestamp = form.add_timestamp.data

            # ПЕРЕДАЕМ ПАРАМЕТР В ФУНКЦИЮ

            # Применяем периодическую функцию к изображению
            processed_image = apply_periodic_function(
                original_image, function_type, period, direction, add_timestamp
            )

            # Создаем гистограммы распределения цветов
            original_histogram = create_color_histogram(original_image, "Исходное")
            processed_histogram = create_color_histogram(processed_image, "Обработанное")

            # Кодируем исходное изображение в формат Base64
            original_buffer = io.BytesIO()
            original_image.save(original_buffer, format='PNG')
            original_base64 = base64.b64encode(original_buffer.getvalue()).decode('utf-8')

            # Кодируем обработанное изображение в формат Base64
            processed_buffer = io.BytesIO()
            processed_image.save(processed_buffer, format='PNG')
            processed_base64 = base64.b64encode(processed_buffer.getvalue()).decode('utf-8')

            print("✅ Обработка завершена успешно!\n")

            # Возвращаем шаблон с результатами обработки
            return render_template('index.html',
                                   form=form,
                                   original_image=original_base64,
                                   processed_image=processed_base64,
                                   original_histogram=original_histogram,
                                   processed_histogram=processed_histogram,
                                   function_type=function_type,
                                   period=period,
                                   direction=direction)

        except Exception as e:
            # Обработка ошибок при обработке изображения
            print(f"❌ Ошибка обработки: {str(e)}")
            flash(f'Ошибка обработки: {str(e)}', 'error')

    else:
        # Форма не прошла валидацию - выводим ошибки
        if form.errors:
            print("\n❌ Форма НЕ прошла валидацию!")
            print(f"   Ошибки: {form.errors}")
            # Показываем ошибки пользователю
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Ошибка в поле "{field}": {error}', 'error')

    # Отображаем пустую форму (при первом заходе или при ошибке)
    return render_template('index.html', form=form)

# ============================================
# ТОЧКА ВХОДА В ПРИЛОЖЕНИЕ
# ============================================

if __name__ == '__main__':
    """
    Запуск приложения Flask.
    
    Параметры:
        debug=True - режим отладки (только для разработки!)
        host='127.0.0.1' - локальный хост
        port=5000 - порт для подключения
    """
    print("\n🚀 ЗАПУСК ПРИЛОЖЕНИЯ")
    print(f"   Адрес: http://127.0.0.1:5000")
    print("=" * 50 + "\n")

    # Запуск веб-сервера Flask
    app.run(debug=True, host='127.0.0.1', port=5000)
