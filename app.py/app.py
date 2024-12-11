from flask import Flask, render_template, request
from algorithm import create_shopping_list  # ייבוא הפונקציה מהקובץ החדש

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        budget = request.form['budget']
        allergies = request.form['allergies']
        selected_foods = request.form.getlist('food_items')

        # קריאה לפונקציה מתוך algorithm.py
        shopping_list = create_shopping_list(budget, allergies, selected_foods)

        return render_template('index.html', shopping_list=shopping_list)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
