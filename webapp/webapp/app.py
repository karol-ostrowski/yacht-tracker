"""Flask web application serving the visualization layer of the pipeline."""
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    """Main page."""
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)