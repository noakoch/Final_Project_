from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def shopping_list():
    food_items = {
        'אורז': {'price': 5},
        'פסטה': {'price': 10},
        'בשר': {'price': 20},
        'ירקות': {'price': 15},
        'פירות': {'price': 10}
    }
    shopping_list = []
    if request.method == 'POST':
        budget = int(request.form['budget'])
        allergies = request.form['allergies'].split(',')
        selected_foods = request.form.getlist('food_items')

        # דוגמה פשוטה ליצירת רשימת קניות מבוססת אלגוריתם
        total_price = 0
        for food in selected_foods:
            if food in allergies:
                continue
            price = food_items[food]['price']
            if total_price + price <= budget:
                shopping_list.append(food)
                total_price += price

    return render_template('index.html', food_items=food_items, shopping_list=shopping_list)


if __name__ == '__main__':
    app.run(debug=True)
