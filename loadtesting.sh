#!/bin/bash

OUTPUT_FILE="load_testing.txt"
STATIC_URL="http://localhost/sample.html"
DYNAMIC_URL="http://localhost/"
NGINX_CACHE_PATH="/tmp/nginx_cache"

if ! curl -sf "$STATIC_URL" >/dev/null; then
    echo "❌ Статический файл недоступен: $STATIC_URL"
    exit 1
fi
if ! curl -sf "http://localhost:9091/" >/dev/null; then
    echo "❌ Gunicorn не отвечает на :9091"
    exit 1
fi

echo "✅ Проверки пройдены. Начинаем тесты..."
> "$OUTPUT_FILE"

get_rps() {
    local url="$1"
    local duration="${2:-30}"
    wrk -t4 -c100 -d${duration}s "$url" 2>/dev/null | awk '/Requests\/sec/ {print $2}'
}

echo "1. Статика через nginx..."
R1=$(get_rps "$STATIC_URL" 30)

echo "2. Статика через gunicorn..."
R2=$(get_rps "http://localhost:9091/sample.html" 30)

echo "3. Динамика напрямую через gunicorn..."
R3=$(get_rps "http://localhost:9091/" 30)

echo "4. Динамика через nginx БЕЗ кэша..."
sudo rm -rf "$NGINX_CACHE_PATH"/*
sudo pkill -9 nginx
sleep 2
cat > /tmp/nginx_no_cache.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app_backend {
        server 127.0.0.1:9091;
    }

    server {
        listen 80;
        server_name localhost;
        root /home/ondaandar/learn_and_work/web-project-technopark/questions/static;

        location / {
            proxy_pass http://app_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF
sudo nginx -c /tmp/nginx_no_cache.conf
sleep 1
R4=$(get_rps "$DYNAMIC_URL" 30)

echo "5. Динамика через nginx С КЭШЕМ..."
sudo pkill -9 nginx
sleep 2
sudo nginx -c /home/ondaandar/learn_and_work/web-project-technopark/nginx.conf
sleep 1
curl -sf "$DYNAMIC_URL" >/dev/null
if curl -sfI "$DYNAMIC_URL" | grep -q "X-Cache-Status: HIT"; then
    echo "   ✅ Кэш работает: HIT подтверждён"
fi
R5=$(get_rps "$DYNAMIC_URL" 30)

{
    echo "Сравнение производительности: nginx vs gunicorn (wrk)"
    echo ""
    echo "Дата теста: $(date)"
    echo "Статический URL: $STATIC_URL"
    echo "Динамический URL: $DYNAMIC_URL"
    echo ""
    echo "Результаты (Requests/sec):"
    echo "1. Статика через nginx:         $R1"
    echo "2. Статика через gunicorn:      $R2"
    echo "3. Динамика через gunicorn:     $R3"
    echo "4. Динамика через nginx (proxy): $R4"
    echo "5. Динамика + proxy_cache:      $R5"
    echo ""
    echo "Выводы:"

    SPEEDUP_STATIC=$(awk "BEGIN {printf \"%.1f\", $R1 / $R2}")
    echo "1. Статика через nginx быстрее в ${SPEEDUP_STATIC} раз, чем через gunicorn."

    SPEEDUP_CACHE=$(awk "BEGIN {printf \"%.1f\", $R5 / $R4}")
    echo "2. proxy_cache ускоряет в ${SPEEDUP_CACHE} раз по сравнению с проксированием без кэша."

} > "$OUTPUT_FILE"

echo "✅ Готово! Результаты в $OUTPUT_FILE"