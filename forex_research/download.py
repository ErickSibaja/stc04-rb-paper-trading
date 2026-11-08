"""Download Dukascopy hourly BID/ASK for EURUSD; historical research only."""
import subprocess
from pathlib import Path
out=Path("forex-data");out.mkdir(exist_ok=True)
for side in ("bid","ask"):
    name=f"eurusd-h1-{side}"
    cmd=["npx","--yes","dukascopy-node@1.51.1","-i","eurusd","-from","2024-01-01",
         "-to","2026-10-01","-t","h1","-p",side,"-f","csv",
         "-dir",str(out),"-fn",name,"--retries","3","--batch-pause","1000"]
    subprocess.run(cmd,check=True,timeout=1200)
    if not (out/(name+".csv")).is_file():raise RuntimeError("Missing "+name)
