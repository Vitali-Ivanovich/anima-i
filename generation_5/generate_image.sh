#!/bin/bash
# generate_image.sh — генерация изображения через Hugging Face Inference API
# Использование: bash generate_image.sh "промпт" /путь/к/output.jpg
# Использует HF_TOKEN из окружения

HF_TOKEN="${HF_TOKEN}"
PROMPT="$1"
OUTPUT="${2:-/tmp/generated_image.jpg}"

if [[ -z "$HF_TOKEN" ]]; then
  echo "❌ HF_TOKEN не задан" >&2
  exit 1
fi

if [[ -z "$PROMPT" ]]; then
  echo "❌ Промпт не задан" >&2
  exit 1
fi

echo "🎨 Генерирую изображение..."
echo "   Промпт: $PROMPT"

curl -s -X POST \
  "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell" \
  -H "Authorization: Bearer ${HF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"inputs\": \"$PROMPT\"}" \
  -o "$OUTPUT"

# Проверяем что получили изображение, а не JSON с ошибкой
TYPE=$(file "$OUTPUT" | grep -i "image")
if [[ -z "$TYPE" ]]; then
  echo "❌ Ошибка генерации:" >&2
  cat "$OUTPUT" >&2
  exit 1
fi

echo "✅ Изображение сохранено: $OUTPUT"
