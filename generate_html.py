current_user = None  # משתנה גלובלי לאחסון שם המשתמש המחובר

import pandas as pd
import webbrowser
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

# נתיב לקובץ האקסל
file_path = 'C:/Users/נעה/PycharmProjects/new_finish/data listi2.xlsx'
ingredients_data = pd.read_excel(file_path, sheet_name='Ingredients')
dishes_data = pd.read_excel(file_path, sheet_name='Dishs')

# Convert dish and ingredient names to lowercase for comparison
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
        return total_cost

    # בדיקה אם המנה המועדפת מתנגשת עם אלרגיות
    if required_dish:
        dish_row = dishes_data[dishes_data['Dish'] == required_dish]
        if not dish_row.empty:
            for i in range(1, 6):
                ingredient = dish_row.iloc[0][f'Ingredients {i}']
                if pd.notna(ingredient) and ingredient in allergies:
                    return f"The dish '{required_dish}' contains '{ingredient}'. Please change your selection accordingly."

    filtered_dishes = filter_dishes(dishes_data, allergies)
    selected_dishes = []
    total_cost, total_value = 0, 0
    ingredients_list = []

    for _, dish in filtered_dishes.iterrows():
        cost = calculate_dish_cost(dish, ingredients_data)
        if cost + total_cost <= budget:
            selected_dishes.append(dish['Dish'])
            total_cost += cost
            total_value += dish['Nutritional Value']
            for i in range(1, 6):
                ingredient = dish[f'Ingredients {i}']
                if pd.notna(ingredient):
                    ingredients_list.append(ingredient)

    remaining_budget = budget - total_cost
    return selected_dishes, ingredients_list, total_cost, total_value, remaining_budget




class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _html(self, message):
        return message.encode('utf8')

    def do_POST(self):
        global current_user
        content_length = self.headers.get('Content-Length')
        if content_length is None or int(content_length) == 0:
            self.send_error(500, "Content-Length is missing or invalid.")
            return

        content_length = int(content_length)
        post_data = self.rfile.read(content_length).decode('utf-8')

        # התחברות משתמש
        if self.path == '/login':
            try:
                data = {key: unquote(value) for key, value in (x.split('=') for x in post_data.split('&'))}
                username = data['username']
                password = data['password']

                users_file = 'users.xlsx'
                if not os.path.exists(users_file):
                    self.send_error(500, "Users file not found")
                    return

                df = pd.read_excel(users_file)
                if username in df['Username'].values and df[df['Username'] == username]['Password'].values[
                    0] == password:
                    current_user = username
                    self.send_response(302)
                    self.send_header('Location', '/dashboard')
                    self.end_headers()
                else:
                    self._set_headers()
                    self.wfile.write(b"Incorrect username or password.")
            except Exception as e:
                self.send_error(500, f"Login error: {e}")

        # יצירת משתמש חדש (Sign Up)
        elif self.path == '/signup':
            try:
                # ניתוח הנתונים שהתקבלו
                data = {key: unquote(value) for key, value in (x.split('=') for x in post_data.split('&'))}
                username = data['username']
                password = data['password']

                users_file = 'users.xlsx'

                # יצירת קובץ משתמשים אם לא קיים
                if not os.path.exists(users_file):
                    df = pd.DataFrame(columns=['Username', 'Password'])
                else:
                    df = pd.read_excel(users_file)

                # בדיקה אם המשתמש כבר קיים
                if username in df['Username'].values:
                    self._set_headers()
                    self.wfile.write(b"Username already exists. Please choose another username.")
                else:
                    # הוספת המשתמש החדש
                    new_user = {'Username': username, 'Password': password}
                    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
                    df.to_excel(users_file, index=False)

                    # הפנייה לעמוד ההתחברות
                    self.send_response(302)
                    self.send_header('Location', '/login')
                    self.end_headers()
            except Exception as e:
                self.send_error(500, f"Signup error: {e}")

        # יצירת רשימה חדשה
        elif self.path == '/process':
            try:
                data = json.loads(post_data)
                budget = float(data['budget'])
                required_dish = data.get('requiredDish', '').strip().lower()
                allergies = [allergy.strip().lower() for allergy in data.get('allergies', '').split(',') if allergy]

                # בדיקת התנגשות בין המנה המועדפת לאלרגיות
                if required_dish:
                    required_dish_row = dishes_data[dishes_data['Dish'] == required_dish]
                    if not required_dish_row.empty:
                        for i in range(1, 6):
                            ingredient = required_dish_row[f'Ingredients {i}'].values[0]
                            if pd.notna(ingredient) and ingredient in allergies:
                                error_message = f"The dish '{required_dish}' contains '{ingredient}', which is in your allergies list. Please change your selection."
                                output = f"""
                                <div style="background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 10px;">
                                    <h3>Error:</h3>
                                    <p>{error_message}</p>
                                </div>
                                """
                                self._set_headers()
                                self.wfile.write(self._html(output))
                                return

                        # בדיקת האם המנה המועדפת אינה בתקציב
                        required_dish_cost = sum(
                            ingredients_data[
                                ingredients_data['Ingredient'] == required_dish_row[f'Ingredients {i}'].values[0]][
                                'price'].values[0]
                            for i in range(1, 6)
                            if pd.notna(required_dish_row[f'Ingredients {i}'].values[0])
                        )
                        if required_dish_cost > budget:
                            error_message = f"The required dish '{required_dish}' exceeds your budget of {budget}. Please adjust your selection or increase your budget."
                            output = f"""
                            <div style="background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 10px;">
                                <h3>Error:</h3>
                                <p>{error_message}</p>
                            </div>
                            """
                            self._set_headers()
                            self.wfile.write(self._html(output))
                            return

                # קריאה לפונקציה לחישוב הרשימה
                result = optimized_selection_dp(budget, required_dish, allergies, ingredients_data, dishes_data)
                selected_dishes, ingredients_list, total_cost, _, remaining_budget = result

                # התאמת שמות המנות לפורמט הקובץ
                normalized_dishes = [dish.strip().lower() for dish in selected_dishes]

                # חישוב הערך התזונתי
                total_nutritional_value = dishes_data.loc[
                    dishes_data['Dish'].str.lower().isin(normalized_dishes), 'Nutritional Value'
                ].dropna().astype(float).sum()

                # חישוב ערך תזונתי ממוצע
                average_nutritional_value = total_nutritional_value / len(selected_dishes) if selected_dishes else 0

                # עיבוד רשימת מצרכים עם כפילויות
                ingredient_counts = {}
                for ingredient in ingredients_list:
                    if ingredient in ingredient_counts:
                        ingredient_counts[ingredient] += 1
                    else:
                        ingredient_counts[ingredient] = 1
                formatted_ingredients = [
                    f"{ingredient}*{count}" if count > 1 else ingredient
                    for ingredient, count in ingredient_counts.items()
                ]

                # שמירת נתונים בקובץ היסטוריה
                history_file = "list_history.xlsx"
                new_entry = {
                    "username": current_user,
                    "date of list": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_cost": total_cost,
                    "total_nutritional_value": total_nutritional_value
                }
                for i, ingredient in enumerate(formatted_ingredients, start=1):
                    new_entry[f"Ingredient {i}"] = ingredient

                if not os.path.exists(history_file):
                    history_df = pd.DataFrame(columns=new_entry.keys())
                else:
                    history_df = pd.read_excel(history_file)

                history_df = pd.concat([history_df, pd.DataFrame([new_entry])], ignore_index=True)
                history_df.to_excel(history_file, index=False)

                # יצירת הפלט למשתמש
                output = f"""
                <div style="background-color: #f3e5f5; padding: 20px; border-radius: 10px;">
                    <p><b>Dishes:</b> {', '.join(selected_dishes)}</p>
                    <p><b>Ingredients:</b> {', '.join(formatted_ingredients)}</p>
                    <p><b>Total cost:</b> {total_cost}</p>
                    <p><b>Total nutritional value:</b> {total_nutritional_value}</p>
                    <p><b>Average nutritional value per dish:</b> {average_nutritional_value:.2f}</p>
                    <p><b>Remaining budget:</b> {remaining_budget}</p>
                </div>
                """
                self._set_headers()
                self.wfile.write(self._html(output))
            except Exception as e:
                self.send_error(500, f"Error processing list: {e}")

    def do_GET(self):
        # חלוקת הנתיב
        path = self.path.split('?')[0]

        try:
            # עמוד הבית
            if path == '/':
                self._set_headers()
                with open('index.html', 'r', encoding='utf-8') as file:
                    html_content = file.read()
                self.wfile.write(self._html(html_content))

            # עמוד ההרשמה
            elif path == '/signup':
                try:
                    self._set_headers()
                    with open('signup.html', 'r', encoding='utf-8') as file:
                        html_content = file.read()
                    self.wfile.write(self._html(html_content))
                except Exception as e:
                    self.send_error(500, f"Error loading Sign Up page: {e}")


            # עמוד ההתחברות
            elif path == '/login':
                self._set_headers()
                with open('login.html', 'r', encoding='utf-8') as file:
                    html_content = file.read()
                self.wfile.write(self._html(html_content))

            # עמוד לוח הבקרה
            elif path == '/dashboard':
                self._set_headers()
                with open('dashboard.html', 'r', encoding='utf-8') as file:
                    html_content = file.read()
                self.wfile.write(self._html(html_content))

            # עמוד יצירת רשימה חדשה
            elif path == '/create_new_list':
                self._set_headers()
                with open('input_form.html', 'r', encoding='utf-8') as file:
                    html_content = file.read()
                self.wfile.write(self._html(html_content))

            # עמוד היסטוריית רשימות
            elif path == '/view_history':
                self._set_headers()
                history_file = "list_history.xlsx"
                if os.path.exists(history_file):
                    df = pd.read_excel(history_file)

                    # סינון לפי משתמש מחובר
                    if current_user:
                        user_history = df[df['username'] == current_user]

                        if not user_history.empty:
                            # טיפול במצרכים - חיבור מצרכים כפולים
                            def format_ingredients(row):
                                ingredients = []
                                for col in row.index:
                                    if col.startswith("Ingredient") and pd.notna(row[col]):
                                        ingredients.append(row[col])
                                formatted_ingredients = {}
                                for ingredient in ingredients:
                                    if ingredient in formatted_ingredients:
                                        formatted_ingredients[ingredient] += 1
                                    else:
                                        formatted_ingredients[ingredient] = 1
                                return ', '.join(f"{ing}*{count}" if count > 1 else ing for ing, count in
                                                 formatted_ingredients.items())

                            # יצירת עמודה מעוצבת למצרכים
                            user_history['Formatted Ingredients'] = user_history.apply(format_ingredients, axis=1)

                            # מחיקת עמודות Ingredients המקוריות
                            ingredient_columns = [col for col in user_history.columns if col.startswith("Ingredient")]
                            user_history = user_history.drop(columns=ingredient_columns)

                            # הסתרת NaN והצגת טבלה HTML
                            html_content = user_history.fillna('').to_html(index=False, classes="table")
                        else:
                            html_content = "<h1>No list history found for your account.</h1>"
                    else:
                        html_content = "<h1>No user is currently logged in. Please log in first.</h1>"
                else:
                    html_content = "<h1>No list history found.</h1>"

                self.wfile.write(self._html(f"""
                <html>
                <head>
                    <title>List History</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; }}
                        .table {{ width: 100%; border-collapse: collapse; }}
                        .table th, .table td {{ border: 1px solid #ddd; padding: 8px; }}
                        .table th {{ background-color: #f2f2f2; text-align: left; }}
                    </style>
                </head>
                <body>
                    <h1>List History</h1>
                    {html_content}
                </body>
                </html>
                """))

            # תמיכה בתמונות
            elif path.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    file_path = path.lstrip('/')  # הסרת "/" מהנתיב
                    if os.path.exists(file_path):
                        self.send_response(200)
                        if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                            self.send_header('Content-type', 'image/jpeg')
                        elif file_path.endswith('.png'):
                            self.send_header('Content-type', 'image/png')
                        elif file_path.endswith('.gif'):
                            self.send_header('Content-type', 'image/gif')
                        self.end_headers()
                        with open(file_path, 'rb') as file:
                            self.wfile.write(file.read())
                    else:
                        self.send_error(404, f"File Not Found: {path}")
                except Exception as e:
                    self.send_error(500, f"Internal Server Error: {e}")

            # נתיב לא נמצא
            else:
                self.send_error(404, f"The path '{self.path}' does not exist")

        except Exception as e:
            print(f"Error in GET handler: {e}")
            self.send_error(500, "Internal Server Error")


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    webbrowser.open('http://localhost:8000')
    run()