请将你想要的 Windows 图标文件命名为 `icon.ico` 并放到本目录（assets/icon.ico）。

要求：
- 推荐使用 256x256 或包含多分辨率 (16/32/48/256) 的 ICO 文件以获得较好显示效果。

打包时会在 spec 中引用 `assets/icon.ico`：
```powershell
pyinstaller todo_assistant.spec
```

如果你没有 ico 文件，可以用 PNG 转换为 ICO：
- 在线工具（例如 https://convertico.com/ 或 https://icoconvert.com/）
- 或使用 Pillow 生成：
```python
from PIL import Image
img = Image.open('icon.png')
img.save('assets/icon.ico', sizes=[(256,256),(48,48),(32,32),(16,16)])
```
