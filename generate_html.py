import pandas as pd
import webbrowser
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote




# Read the Excel file with the updated path
file_path = 'C:/Users/נעה/PycharmProjects/finish_project/data listi2.xlsx'
ingredients_data = pd.read_excel(file_path, sheet_name='Ingredients')
dishes_data = pd.read_excel(file_path, sheet_name='Dishs')

# Convert dish and ingredient names to lowercase for comparison.
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
            if not any(allergy in row[f'Ingredients {i}'] for allergy in allergies for i in range(1, 6) if
                       pd.notna(row[f'Ingredients {i}'])):
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

    if required_dish: #todo: is it in dp?
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

    dishes_data = filter_dishes(dishes_data, allergies) # מסנן את האלרגיות
    budget_int = int(budget)
    n = len(dishes_data)
    dp = [[0] * (budget_int + 1) for _ in range(n + 1)] # יצירת טבלה שכל שורה בה היא מנה וכל עמודה היא תקציב בטווח שבין 0 לתקציב שהמשתמש הכניס

    for i in range(1, n + 1): # מילוי הטבלה בהתאם כך שמחיר המנה לא עובר את התקציב
        dish = dishes_data.iloc[i - 1]
        dish_cost = calculate_dish_cost(dish, ingredients_data) # האילוץ
        dish_value = dish['Nutritional Value']
        for b in range(budget_int + 1):
            if dish_cost > b:#אם מנה לא בתקציב
                dp[i][b] = dp[i - 1][b]#אם עלות המנה גבוהה מהתקציב אז אנחנו לא יכולים להוסיף אותה ומעתיקים את הערך מטבלת התכנון של המנה הקודמת באותו התקציב
            else: #אם מנה כן בצקציב בודק אם כדי לקחת אותה
                dp[i][b] = max(dp[i - 1][b], dp[i - 1][b - int(dish_cost)] + dish_value) #  בוחר אם כדי לקחת את המנה ביחס לעבר חייב להבין אתה השורה הזאת טוב

    selected_dishes = []# במידה ויש מנה מבוקשת התקציב יורד לפי המנה המבוקשת
    b = budget_int
    if required_dish:
        required_dish_row = dishes_data[dishes_data['Dish'] == required_dish].iloc[0]
        selected_dishes.append(required_dish_row)
        b -= int(calculate_dish_cost(required_dish_row, ingredients_data))

    for i in range(n, 0, -1):#
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

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')

        # -------------------------
        # טיפול ב-Sign Up
        # -------------------------
        if self.path == '/signup':
            print("Sign Up POST request received")
            print("Raw POST data:", post_data)

            try:
                data = {key: unquote(value) for key, value in (x.split('=') for x in post_data.split('&'))}
                print("Parsed POST data:", data)
            except Exception as e:
                print("Error parsing POST data:", e)
                self.send_error(400, "Bad Request: Unable to parse POST data")
                return

            try:
                user_data = {
                    "First Name": data['first_name'],
                    "Last Name": data['last_name'],
                    "Email": data['email'],
                    "Phone": data['phone'],
                    "Address": data['address'],
                    "Username": data['username'],
                    "Password": data['password']
                }
                file_path = 'users.xlsx'
                if not os.path.exists(file_path):
                    df = pd.DataFrame(columns=user_data.keys())
                    df.to_excel(file_path, index=False)

                df = pd.read_excel(file_path)
                if user_data['Username'] in df['Username'].values:
                    print("Username already exists")
                    self._set_headers()
                    self.wfile.write(b"<h1>Username already exists. Please choose another one.</h1>")
                    return

                new_row = pd.DataFrame([user_data])
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_excel(file_path, index=False)
                print("User data saved to Excel successfully")

            except Exception as e:
                print("Error saving user data:", e)
                self.send_error(500, "Internal Server Error: Unable to save user data")
                return

            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

        # -------------------------
        # טיפול ב-Log In
        # -------------------------
        elif self.path == '/login':
            print("Log In POST request received")
            print("Raw POST data:", post_data)

            try:
                data = {key: unquote(value) for key, value in (x.split('=') for x in post_data.split('&'))}
                print("Parsed POST data:", data)
            except Exception as e:
                print("Error parsing POST data:", e)
                self.send_error(400, "Bad Request: Unable to parse POST data")
                return

            username = data['username']
            password = data['password']

            file_path = 'users.xlsx'
            if not os.path.exists(file_path):
                print("Users file not found")
                self.send_error(500, "Internal Server Error: Users file not found")
                return

            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                print("Error reading Excel file:", e)
                self.send_error(500, "Internal Server Error: Unable to read Excel file")
                return

            if username not in df['Username'].values:
                print("Username not found")
                self._set_headers()
                self.wfile.write(b"<h1>Username not found. Please sign up first.</h1>")
                return

            user_row = df[df['Username'] == username]
            if user_row['Password'].values[0] != password:
                print("Incorrect password")
                self._set_headers()
                self.wfile.write(b"<h1>Incorrect password. Please try again.</h1>")
                return

            print("Log in successful")
            self.send_response(302)
            self.send_header('Location', '/dashboard')
            self.end_headers()

        # -------------------------
        # טיפול ב-Process (טופס יצירת רשימה חדשה)
        # -------------------------
        elif self.path == '/process':  # עיבוד נתוני הטופס
            print("Processing new list request")
            try:
                # ניתוח הנתונים שהגיעו כ-JSON
                data = json.loads(post_data)
                print("Parsed form data:", data)

                budget = float(data['budget'])
                required_dish = data['requiredDish'].strip().lower() if data['requiredDish'] else None
                allergies = [allergy.strip().lower() for allergy in data['allergies'].split(',')] if data[
                    'allergies'] else []

                print(f"Budget: {budget}, Required Dish: {required_dish}, Allergies: {allergies}")

                # הפעלת האלגוריתם
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

                # החזרת תוצאות למשתמש
                self._set_headers()
                self.wfile.write(self._html(output))

            except Exception as e:
                print("Error processing form data:", e)
                self.send_error(500, "Internal Server Error: Unable to process form data")

    def do_GET(self):
        # מסדר את הנתיב כך שיתעלם מסימן שאלה ופרמטרים
        path = self.path.split('?')[0]

        if path == '/create_new_list':  # עמוד יצירת רשימה חדשה
            self._set_headers()
            with open('input_form.html', 'r') as file:
                html_content = file.read()
            self.wfile.write(self._html(html_content))

        elif path == '/':  # עמוד הבית
            self._set_headers()
            with open('index.html', 'r') as file:
                html_content = file.read()
            self.wfile.write(self._html(html_content))

        elif path == '/signup':  # עמוד ההרשמה
            self._set_headers()
            with open('signup.html', 'r') as file:
                html_content = file.read()
            self.wfile.write(self._html(html_content))

        elif path == '/login':  # עמוד הכניסה
            self._set_headers()
            with open('login.html', 'r') as file:
                html_content = file.read()
            self.wfile.write(self._html(html_content))

        elif path == '/dashboard':  # עמוד הבחירה לאחר Log In
            self._set_headers()
            with open('dashboard.html', 'r') as file:
                html_content = file.read()
            self.wfile.write(self._html(html_content))

        else:  # נתיב לא נמצא
            self.send_error(404, f"The path '{self.path}' does not exist")


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}...')
    httpd.serve_forever()


if __name__ == "__main__":
    webbrowser.open('http://localhost:8000')
    run()