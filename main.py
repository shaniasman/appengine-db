from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    # Used for local testing only
    app.run(host='127.0.0.1', port=8080, debug=True)