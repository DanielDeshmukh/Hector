try { $Host.UI.RawUI.WindowTitle = "HECTOR E2E - next dev" } catch {}
Set-Location "D:\Vs Code\VS code\Hector\hector"
& "C:\Program Files\nodejs\npm.cmd" run dev *>&1 |
    Tee-Object -FilePath "D:\Vs Code\VS code\Hector\hector\next_e2e.log"
