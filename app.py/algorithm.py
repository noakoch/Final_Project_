# כאן נעתיק את הקוד של האלגוריתם שלך
def create_shopping_list(budget, allergies, selected_foods):
    # קוד האלגוריתם שלך
    import pandas as pd

    # Read the Excel file with the updated path
    file_path = 'C:/Users/נעה/Desktop/תעשייה וניהול/שנה ב/סמסטר ב/חקבצ 2/פרויקט/data project.xlsx'
    ingredients_data = pd.read_excel(file_path, sheet_name='Ingredients')
    dishes_data = pd.read_excel(file_path, sheet_name='Dishs')

    # Function to get user inputs
    def get_user_inputs():
        try:
            budget = float(input("Enter the maximum budget: "))
        except ValueError:
            print("Invalid value, please enter a number.")
            return get_user_inputs()
        required_dish = input("Enter a dish that must be included: ").strip().lower()
        allergies = input("Enter allergies (comma-separated): ").split(',')
        # Clean up allergies and convert to lowercase
        allergies = [allergy.strip().lower() for allergy in allergies if allergy.strip()]
        return budget, required_dish, allergies

    budget, required_dish, allergies = get_user_inputs()

    # Convert dish and ingredient names to lowercase for comparison
    dishes_data['Dish'] = dishes_data['Dish'].str.lower()
    for i in range(1, 6):
        dishes_data[f'Ingredients {i}'] = dishes_data[f'Ingredients {i}'].str.lower()

    ingredients_data['Ingredient'] = ingredients_data['Ingredient'].str.lower()

    # Algorithm for selecting optimal dishes
    def optimized_selection_dp(budget, required_dish, allergies, ingredients_data, dishes_data):
        # Filter dishes based on allergies
        def filter_dishes(dishes, allergies):
            if not allergies:
                return dishes
            filtered_dishes = []
            for index, row in dishes.iterrows():
                if not any(allergy in row[f'Ingredients {i}'] for allergy in allergies for i in range(1, 6) if
                           pd.notna(row[f'Ingredients {i}'])):
                    filtered_dishes.append(row)
            return pd.DataFrame(filtered_dishes)

        # Calculate the total cost of ingredients in a dish
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

        # Check the required dish before filtering the dishes
        while required_dish:
            required_dish_row = dishes_data[dishes_data['Dish'] == required_dish]
            if required_dish_row.empty:
                return f"The dish '{required_dish}' is not in the database.", None, None, None, None, None
            for i in range(1, 6):
                ingredient = required_dish_row.iloc[0][f'Ingredients {i}']
                if pd.notna(ingredient) and any(allergy == ingredient for allergy in allergies):
                    return f"The requested dish '{required_dish}' contains your allergy '{ingredient}' and cannot be selected.", None, None, None, None, None
            required_dish_cost = calculate_dish_cost(required_dish_row.iloc[0], ingredients_data)
            if required_dish_cost > budget:
                choice = input(
                    f"The dish you requested is over budget. Do you want to continue planning without it (a/n) or enter a new budget (b)? ").strip().lower()
                if choice == 'a':
                    required_dish = None
                elif choice == 'b':
                    try:
                        budget = float(input("Enter new budget: "))
                    except ValueError:
                        print("Invalid value, please enter a number.")
                        return optimized_selection_dp(budget, required_dish, allergies, ingredients_data, dishes_data)
                else:
                    return "No valid option selected.", None, None, None, None, None
            else:
                break

        # Filter dishes based on allergies
        dishes_data = filter_dishes(dishes_data, allergies)

        # Convert budget to an integer for table creation
        budget_int = int(budget)

        # Create dynamic programming table
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

        # Build the optimal solution
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

        # Calculate the ingredient list, total cost, and nutritional value of the basket
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

        # Prepare the ingredient list with appropriate quantities
        ingredients_list = [f"{ingredient}*{count}" if count > 1 else ingredient for ingredient, count in
                            ingredients.items()]

        remaining_budget = budget - total_cost
        selected_dish_names = [dish['Dish'] for dish in selected_dishes]
        total_nutritional_value = sum(dish['Nutritional Value'] for dish in selected_dishes)

        return selected_dish_names, ingredients_list, total_cost, total_nutritional_value, remaining_budget

    # Run the function and display the output
    result = optimized_selection_dp(budget, required_dish, allergies, ingredients_data, dishes_data)

    if result[1] is None:
        print(result[0])
    else:
        selected_dish_names, ingredients_list, total_cost, total_nutritional_value, remaining_budget = result
        print(f"The following dishes were selected: {selected_dish_names}")
        print(f"Ingredient list: {ingredients_list}")
        print(f"Total cost: {total_cost:.3f}")
        print(f"Nutritional value of the basket: {total_nutritional_value:.3f}")
        print(f"Remaining budget: {remaining_budget:.3f}")

