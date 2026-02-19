#!/bin/bash

echo "=== Starting Gunicorn Production Server ==="
gunicorn --bind 127.0.0.1:5000 wsgi:app &
APP_PID=$!

sleep 180

echo "Gunicorn PID: $APP_PID"

if kill -0 $APP_PID 2>/dev/null; then
    echo "✅ Gunicorn запущен по адресу  http://127.0.0.1:5000"
    echo "⏳ Ждем 5 секунд..."
    sleep 5
    echo "🛑 Остановка Gunicorn..."
    kill -TERM $APP_PID
    wait $APP_PID 2>/dev/null
    echo "✅ Gunicorn process остановлен"
else
    echo "❌ ERROR: Gunicorn ошибка при старте"
    exit 1
fi

echo "=== Скрипт успешно завершен ==="
exit 0