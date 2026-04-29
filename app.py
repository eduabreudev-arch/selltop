from app import create_app

app = create_app()

if __name__ == "__main__":
    print("\n Selltop rodando em http://localhost:5000\n")
    app.run(host="0.0.0.0", debug=True, port=5000)