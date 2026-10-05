try { $Host.UI.RawUI.WindowTitle = "HECTOR E2E - init" } catch {}
Set-Location "D:\Vs Code\VS code\Hector\hector\api"
& "D:\Vs Code\VS code\Hector\.venv\Scripts\python.exe" -u main.py init *>&1 |
    Tee-Object -FilePath "D:\Vs Code\VS code\Hector\hector\api\init_e2e.log"
