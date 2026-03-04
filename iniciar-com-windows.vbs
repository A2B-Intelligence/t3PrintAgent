' Inicia o agente de impressão sem exibir janela.
' Coloque um atalho deste arquivo em:
'   C:\Users\SEU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & """ && run-silent.bat", 0, False
