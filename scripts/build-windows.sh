#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) não encontrado."
  echo "Instale: https://cli.github.com/"
  echo "Ou faça push na branch main para disparar o build automaticamente."
  exit 1
fi

echo "Disparando build Windows no GitHub Actions..."
gh workflow run build-windows.yml --ref main 2>/dev/null || gh workflow run build-windows.yml

echo "Aguardando conclusão (pode levar alguns minutos)..."
sleep 5
RUN_ID="$(gh run list --workflow=build-windows.yml --branch main --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID"

echo ""
echo "Baixando artefato VBANSender.exe..."
mkdir -p dist
gh run download "$RUN_ID" -n VBANSender-windows -D dist/
echo "Arquivo em: $ROOT/dist/VBANSender.exe"
