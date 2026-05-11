from app import create_app

app = create_app()

if __name__ == "__main__":
    # Desactivamos el reloader porque los logs de iperf3 causan reinicios infinitos
    app.run(debug=True, use_reloader=False, port=5000, host="0.0.0.0")
