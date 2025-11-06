from flask import Flask

app = Flask(__name__)

@app.route("/test")
def test():
    return "Server is running"

if __name__ == "__main__":
    print("Starting server...")  # 打印启动提示
    app.run(host="0.0.0.0", port=5000, debug=True)  # 启用debug模式，显示错误