#!/bin/bash
# Cria o pacote de atualizacao para enviar ao cliente (rodar no macOS/Linux).
#
# Uso:
#   ./criar-atualizacao.sh          -> usa a versao definida em agent.py (VERSION)
#   ./criar-atualizacao.sh 1.2.0    -> forca uma versao especifica
#
# Gera: PrintAgent-Update-vX.Y.Z.zip
set -e
cd "$(dirname "$0")"

VERSION="${1:-$(grep -m1 "^VERSION" agent.py | cut -d"'" -f2)}"
if [ -z "$VERSION" ]; then
    echo "ERRO: nao foi possivel detectar a versao. Informe: ./criar-atualizacao.sh 1.2.0"
    exit 1
fi

OUT="PrintAgent-Update-v${VERSION}.zip"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir "$TMP/update"

cp agent.py printer.py receipt_generator.py run.bat run-silent.bat \
   requirements.txt atualizar.bat "$TMP/update/"
echo "v${VERSION} - $(date +%Y-%m-%d)" > "$TMP/update/VERSION.txt"

cat > "$TMP/update/LEIA-ME.txt" <<'EOF'
========================================
ATUALIZACAO DO PRINT AGENT
========================================

1. Extraia a pasta "update" deste ZIP para DENTRO da pasta do
   PrintAgent (a pasta que contem agent.py e config.json).
   Exemplo: C:\t3-a2beats-PrintAgent\update

2. De um duplo-clique em: update\atualizar.bat
   (nao precisa fechar o agente antes - o atualizador encerra sozinho)

3. Pronto! O agente reinicia sozinho em uma nova janela.
   O config.json (credenciais) NAO e alterado.

Se algo der errado, a versao anterior fica salva na pasta backup\.
EOF

rm -f "$OUT"
(cd "$TMP" && zip -r "$OLDPWD/$OUT" update >/dev/null)

echo "Pacote criado: $OUT"
echo "Conteudo:"
unzip -l "$OUT" | sed -n '4,$p' | head -12
echo "Envie este ZIP ao cliente com as instrucoes do LEIA-ME.txt"
