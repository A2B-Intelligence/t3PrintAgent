"""
Gera config.json com credenciais embutidas a partir do JSON da Service Account.

Uso:
  python gerar-config.py service-account.json
  python gerar-config.py caminho/para/firebase-adminsdk-xxx.json

Cria config.json na mesma pasta, pronto para uso. O usuário final só precisa
desse arquivo - transparente, sem arquivos extras.
"""
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def main():
    if len(sys.argv) < 2:
        print("Uso: python gerar-config.py <arquivo-service-account.json> [database]")
        print("Exemplo: python gerar-config.py firebase-adminsdk-xxx.json")
        print("         python gerar-config.py firebase-adminsdk-xxx.json a2beats-db-dev")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Arquivo não encontrado: {json_path}")
        sys.exit(1)

    with open(json_path, encoding='utf-8') as f:
        firebase_creds = json.load(f)

    if firebase_creds.get('type') != 'service_account':
        print("ERRO: O arquivo não parece ser uma Service Account do Firebase.")
        sys.exit(1)

    database = sys.argv[2] if len(sys.argv) > 2 else None
    if not database:
        database = input("Database Firestore (Enter para a2beats-db-dev): ").strip() or "a2beats-db-dev"

    config = {
        "database": database,
        "firebase": firebase_creds,
    }

    out_path = BASE_DIR / "config.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"config.json criado em: {out_path}")
    print("Pronto para uso. Copie apenas este arquivo para a máquina Windows.")


if __name__ == "__main__":
    main()
