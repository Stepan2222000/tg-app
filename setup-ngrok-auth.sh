#!/bin/bash

echo "=========================================="
echo "  Настройка ngrok authtoken"
echo "=========================================="
echo ""
echo "1. Зайдите на https://dashboard.ngrok.com/get-started/your-authtoken"
echo "2. Скопируйте ваш authtoken"
echo "3. Вставьте его ниже:"
echo ""
read -p "Введите authtoken: " AUTHTOKEN

if [ -z "$AUTHTOKEN" ]; then
  echo "❌ Authtoken не указан"
  exit 1
fi

# Настройка ngrok
ngrok config add-authtoken "$AUTHTOKEN"

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Authtoken настроен успешно!"
  echo ""
  echo "Теперь перезапустите туннель:"
  echo "  pkill ngrok"
  echo "  ngrok http 80"
else
  echo "❌ Ошибка при настройке authtoken"
  exit 1
fi
