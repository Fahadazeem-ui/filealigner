import base64
from pathlib import Path
parts = [Path(f"scripts_write_ui_p{i}.txt").read_text().strip() for i in range(3)]
data = base64.b64decode("".join(parts))
Path("scripts_write_ui.py").write_bytes(data)
print("restored", len(data))
exec(compile(data, "scripts_write_ui.py", "exec"))
