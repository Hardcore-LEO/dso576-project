# AI Workforce Investment Planner — Streamlit

## 部署到 Streamlit Community Cloud

1. 将本文件夹中的 app.py、generate_ai_workforce_planner.py 和 requirements.txt 上传至同一个 GitHub 仓库目录。
2. 在 Streamlit Community Cloud 创建应用并选择该仓库和分支。
3. Main file path 填写 app.py（如果放在子目录，填写相应路径）。
4. 点击 Deploy。

不要只上传 ZIP：先解压，再将里面的文件上传 GitHub。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 文件说明

- app.py：Streamlit 入口，将原网页嵌入可滚动的页面。
- generate_ai_workforce_planner.py：包含完整 HTML、JavaScript、CSS 和数据，无需另传 HTML。
- requirements.txt：部署环境需要的 Python 依赖。

页面沿用原 HTML 的浏览器端交互。浏览器本地保存的数据不会自动同步到服务器或其他用户。
