#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) não encontrado."
  echo "Instale: https://cli.github.com/"
  exit 1
fi

TAG="${1:-}"
if [[ -z "$TAG" ]]; then
  echo "Uso: $0 <tag>"
  echo "Exemplo: $0 v1.0.0"
  echo ""
  echo "Cria a tag, envia ao remoto e dispara o build no GitHub Actions:"
  exit 1
fi

if ! git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag local '$TAG' não existe. Crie e envie antes:"
  echo "  git tag $TAG"
  echo "  git push origin $TAG"
  exit 1
fi

echo "Enviando tag $TAG (se ainda não estiver no remoto)..."
git push origin "$TAG" 2>/dev/null || true

echo "Aguardando workflow de build para $TAG..."
sleep 5
RUN_ID=""
for _ in $(seq 1 30); do
  RUN_ID="$(gh run list --workflow=build-windows.yml --limit 5 --json databaseId,headBranch -q \
    ".[] | select(.headBranch==\"$TAG\") | .databaseId" 2>/dev/null | head -1)"
  if [[ -n "$RUN_ID" ]]; then
    break
  fi
  sleep 2
done

if [[ -z "$RUN_ID" ]]; then
  echo "Não foi possível encontrar a execução do workflow para $TAG."
  echo "Verifique em: gh run list --workflow=build-windows.yml"
  exit 1
fi

gh run watch "$RUN_ID"

echo ""
echo "Baixando artefato VBANSender.exe..."
mkdir -p dist
gh run download "$RUN_ID" -n VBANSender-windows -D dist/
echo "Arquivo em: $ROOT/dist/VBANSender.exe"
