"""
Impressão totalmente silenciosa para Windows.

Converte HTML em PDF e imprime via SumatraPDF, sem exibir janelas ou diálogos.
"""
import os
import sys
import shutil
import subprocess
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

# Quando empacotado com PyInstaller, usa a pasta do .exe
BASE_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent

try:
    from xhtml2pdf import pisa
    HAS_XHTML2PDF = True
except Exception as e:
    print(f"[Printer] Aviso ao importar xhtml2pdf: {e}")
    HAS_XHTML2PDF = False

SUMATRA_PATHS = [
    Path(os.environ.get('ProgramFiles', 'C:\\Program Files')) / 'SumatraPDF' / 'SumatraPDF.exe',
    Path(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'SumatraPDF' / 'SumatraPDF.exe',
    BASE_DIR / 'SumatraPDF.exe',
]


def _find_sumatra() -> Optional[Path]:
    """Localiza o executável do SumatraPDF."""
    for path in SUMATRA_PATHS:
        if path.exists():
            return path
    exe = shutil.which('SumatraPDF.exe') or shutil.which('SumatraPDF')
    if exe:
        return Path(exe)
    return None


def _html_to_pdf(html_content: str, pdf_path: Path) -> bool:
    """Converte HTML em PDF usando xhtml2pdf, com logs de erro detalhados."""
    if not HAS_XHTML2PDF:
        return False
    try:
        with open(pdf_path, 'wb') as out:
            # Usa a string HTML diretamente (padrão recomendado pelo xhtml2pdf)
            status = pisa.CreatePDF(
                src=html_content,
                dest=out,
                encoding='utf-8',
            )

        if status.err:
            print("[Printer] Erro ao converter HTML para PDF (xhtml2pdf retornou erro).")
            # Tenta exibir detalhes se disponíveis
            errlist = getattr(status, "errlist", None)
            if errlist:
                print("[Printer] Detalhes do erro xhtml2pdf:")
                for err in errlist:
                    try:
                        print(f"  - {err}")
                    except Exception:
                        # Garante que não quebre por problemas de encoding na impressão do erro
                        print("  - [Printer] Erro ao exibir detalhe do erro.")

            # Salva HTML em um arquivo para debug
            try:
                debug_html = pdf_path.with_suffix(".html")
                with open(debug_html, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"[Printer] HTML de debug salvo em: {debug_html}")
            except Exception as e:
                print(f"[Printer] Não foi possível salvar HTML de debug: {e}")

            return False

        return True
    except Exception as e:
        print(f"[Printer] Exceção ao converter HTML para PDF: {e}")
        # Também tenta salvar o HTML para facilitar o debug
        try:
            debug_html = pdf_path.with_suffix(".html")
            with open(debug_html, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[Printer] HTML de debug salvo em: {debug_html}")
        except Exception as e2:
            print(f"[Printer] Não foi possível salvar HTML de debug após exceção: {e2}")
        return False


def print_to_default_printer(html_content: str) -> bool:
    """Imprime o conteúdo HTML de forma totalmente silenciosa."""
    if not HAS_XHTML2PDF:
        print("[Printer] ERRO: xhtml2pdf não instalado. Execute: pip install -r requirements.txt")
        return False

    sumatra = _find_sumatra()
    if not sumatra:
        print("[Printer] ERRO: SumatraPDF não encontrado.")
        print("         Instale em: https://www.sumatrapdfreader.org/")
        print(f"         Ou coloque SumatraPDF.exe em: {BASE_DIR}")
        return False

    temp_pdf = None
    success = False
    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_pdf = Path(f.name)

        if not _html_to_pdf(html_content, temp_pdf):
            print("[Printer] Erro ao converter HTML para PDF.")
            return False

        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0
        result = subprocess.run(
            # noscale: o PDF já é gerado no tamanho do cupom (80mm), então
            # imprime 1:1, sem encolher/centralizar (evita espaço em branco)
            [str(sumatra), '-print-to-default', '-print-settings', 'noscale', str(temp_pdf)],
            capture_output=True,
            timeout=30,
            creationflags=creationflags,
        )

        if result.returncode == 0:
            print("[Printer] Impressão enviada com sucesso (silenciosa).")
            success = True
            return True

        # Em caso de erro, mostra detalhes do SumatraPDF
        print(f"[Printer] SumatraPDF retornou código {result.returncode}")
        if result.stdout:
            try:
                print("[Printer] SumatraPDF stdout:")
                print(result.stdout.decode(errors="ignore"))
            except Exception:
                print("[Printer] Erro ao exibir stdout do SumatraPDF.")
        if result.stderr:
            try:
                print("[Printer] SumatraPDF stderr:")
                print(result.stderr.decode(errors="ignore"))
            except Exception:
                print("[Printer] Erro ao exibir stderr do SumatraPDF.")
        return False

    except subprocess.TimeoutExpired:
        print("[Printer] Timeout ao imprimir.")
        return False
    except Exception as e:
        print(f"[Printer] Erro: {e}")
        return False
    finally:
        if temp_pdf and temp_pdf.exists():
            if success:
                # Em caso de sucesso, remove o PDF temporário
                time.sleep(1)
                try:
                    temp_pdf.unlink()
                except OSError:
                    pass
            else:
                # Em caso de erro, mantém o PDF para debug
                print(f"[Printer] PDF mantido para debug em: {temp_pdf}")


def print_def_printer(html_content: str) -> bool:
    return print_to_default_printer(html_content)
