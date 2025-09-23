def show_graph(app):
    try:
        mermaid_code = app.get_graph(xray=True).draw_mermaid()
        print("=== LangGraph 工作流 ===")
        print(mermaid_code)
        print("\n复制以上代码到在线编辑器生成图片：https://mermaid.live/")
    except Exception as e:
        print("生成 Mermaid 语法失败:", e)

