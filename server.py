import pandas as pd
import webbrowser
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# קריאת קובץ האקסל
file_path = "C:/Users/נעה/Desktop/תעשייה וניהול/שנה ב/סמסטר ב/חקבצ 2/פרויקט/data project.xlsx"
ingredients_data = pd.read_excel(file_path, sheet_name='Ingredients')
dishes_data = pd.read_excel(file_path, sheet_name='Dishs')

# המרת שמות מנות ומרכיבים לאותיות קטנות להשוואה
dishes_data['Dish'] = dishes_data['Dish'].str.lower()
for i in range(1, 6):
    dishes_data[f'Ingredients {i}'] = dishes_data[f'Ingredients {i}'].str.lower()

ingredients_data['Ingredient'] = ingredients_data['Ingredient'].str.lower()

def optimized_selection_dp(budget, required_dish, allergies, ingredients_data, dishes_data):
    def filter_dishes(dishes, allergies):
        if not allergies:
            return dishes
        filtered_dishes = []
        for index, row in dishes.iterrows():
            if not any(allergy in row[f'Ingredients {i}'] for allergy in allergies for i in range(1, 6) if pd.notna(row[f'Ingredients {i}'])):
                filtered_dishes.append(row)
        return pd.DataFrame(filtered_dishes)

    def calculate_dish_cost(dish, ingredients_data):
        total_cost = 0
        for i in range(1, 6):
            ingredient = dish[f'Ingredients {i}']
            if pd.notna(ingredient):
                ingredient_price_row = ingredients_data[ingredients_data['Ingredient'] == ingredient]
                if not ingredient_price_row.empty:
                    ingredient_price = ingredient_price_row['price'].values[0]
                    total_cost += ingredient_price
                else:
                    print(f"Warning: Ingredient '{ingredient}' not found in ingredients data.")
        return total_cost

    if required_dish:
        required_dish_row = dishes_data[dishes_data['Dish'] == required_dish]
        if required_dish_row.empty:
            return f"The dish '{required_dish}' is not in the database.", None, None, None, None, None
        for i in range(1, 6):
            ingredient = required_dish_row.iloc[0][f'Ingredients {i}']
            if pd.notna(ingredient) and any(allergy == ingredient for allergy in allergies):
                return f"The requested dish '{required_dish}' contains your allergy '{ingredient}' and cannot be selected.", None, None, None, None, None
        required_dish_cost = calculate_dish_cost(required_dish_row.iloc[0], ingredients_data)
        if required_dish_cost > budget:
            return f"The dish '{required_dish}' is over the budget of {budget}. Please select another dish or increase your budget.", None, None, None, None, None

    dishes_data = filter_dishes(dishes_data, allergies)
    budget_int = int(budget)
    n = len(dishes_data)
    dp = [[0] * (budget_int + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dish = dishes_data.iloc[i - 1]
        dish_cost = calculate_dish_cost(dish, ingredients_data)
        dish_value = dish['Nutritional Value']
        for b in range(budget_int + 1):
            if dish_cost > b:
                dp[i][b] = dp[i - 1][b]
            else:
                dp[i][b] = max(dp[i - 1][b], dp[i - 1][b - int(dish_cost)] + dish_value)

    selected_dishes = []
    b = budget_int
    if required_dish:
        required_dish_row = dishes_data[dishes_data['Dish'] == required_dish].iloc[0]
        selected_dishes.append(required_dish_row)
        b -= int(calculate_dish_cost(required_dish_row, ingredients_data))

    for i in range(n, 0, -1):
        if dp[i][b] != dp[i - 1][b]:
            dish = dishes_data.iloc[i - 1]
            if not required_dish or dish['Dish'] != required_dish:
                selected_dishes.append(dish)
                b -= int(calculate_dish_cost(dish, ingredients_data))

    ingredients = {}
    total_cost = 0
    for dish in selected_dishes:
        for i in range(1, 6):
            ingredient = dish[f'Ingredients {i}']
            if pd.notna(ingredient):
                ingredient_price_row = ingredients_data[ingredients_data['Ingredient'] == ingredient]
                if not ingredient_price_row.empty:
                    ingredient_price = ingredient_price_row['price'].values[0]
                    total_cost += ingredient_price
                    if ingredient in ingredients:
                        ingredients[ingredient] += 1
                    else:
                        ingredients[ingredient] = 1
                else:
                    print(f"Warning: Ingredient '{ingredient}' not found in ingredients data.")

    ingredients_list = [f"{ingredient}*{count}" if count > 1 else ingredient for ingredient, count in ingredients.items()]
    remaining_budget = budget - total_cost
    selected_dish_names = [dish['Dish'] for dish in selected_dishes]
    total_nutritional_value = sum(dish['Nutritional Value'] for dish in selected_dishes)

    return selected_dish_names, ingredients_list, total_cost, total_nutritional_value, remaining_budget

class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _html(self, message):
        return message.encode('utf8')

    def do_GET(self):
        self._set_headers()
        try:
            with open('input_form.html', 'r', encoding='utf-8') as file:
                html_content = file.read()
        except FileNotFoundError:
            html_content = "<html><body><h1>File not found</h1></body></html>"
        self.wfile.write(self._html(html_content))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        budget = float(data['budget'])
        required_dish = data['requiredDish'].strip().lower() if data['requiredDish'] else None
        allergies = [allergy.strip().lower() for allergy in data['allergies'].split(',')] if data['allergies'] else []

        result = optimized_selection_dp(budget, required_dish, allergies, ingredients_data, dishes_data)
        if result[1] is None:
            output = f"<div class='results'><p>{result[0]}</p></div>"
        else:
            selected_dish_names, ingredients_list, total_cost, total_nutritional_value, remaining_budget = result
            output = f"""
            <div class='results'>
                <p><span>The following dishes were selected:</span> {', '.join(selected_dish_names)}</p>
                <p><span>Ingredient list:</span> {', '.join(ingredients_list)}</p>
                <p><span>Total cost:</span> {total_cost:.3f}</p>
                <p><span>Nutritional value of the basket:</span> {total_nutritional_value:.3f}</p>
                <p><span>Remaining budget:</span> {remaining_budget:.3f}</p>
            </div>
            """

        self._set_headers()
        self.wfile.write(self._html(output))

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    webbrowser.open('http://localhost:8000')
    run()
