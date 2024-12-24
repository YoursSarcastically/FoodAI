# Import statements
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import numpy as np

# Must be the first Streamlit command
st.set_page_config(
    page_title="Magic Meal Planner ✨",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load the data
@st.cache_data
def load_data():
    data = pd.read_csv('Indian_Foods_1000_Unique (1).csv')
    return data

# Helper functions
def calculate_bmi(weight, height):
    """Calculate BMI given weight (kg) and height (m)."""
    return weight / (height ** 2)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def get_meal_emoji(category):
    """Return appropriate emoji for each meal category."""
    emoji_map = {
        'Breakfast': '🍳',
        'Lunch': '🍱',
        'Dinner': '🍽️',
        'Snack': '🍪'
    }
    return emoji_map.get(category.strip(), '🍽️')

def get_bmi_emoji(category):
    """Return appropriate emoji for BMI category."""
    emoji_map = {
        'Underweight': '⚖️',
        'Normal weight': '✅',
        'Overweight': '⚠️',
        'Obese': '❗'
    }
    return emoji_map.get(category, '⚖️')

def generate_meal_plan(data, calorie_target, veg_pref, meal_preferences):
    """Generate a meal plan based on calorie target, preferences, and meal distributions."""
    filtered_data = data[data['Veg/Non-Veg'].str.contains(veg_pref.split()[0], case=False)]  # Split to handle emoji
    daily_plans = []

    for day in range(7):
        daily_plan = []
        remaining_calories = calorie_target

        for category, percentage in meal_preferences.items():
            category_target_calories = calorie_target * (percentage / 100)
            category_foods = filtered_data[
                (filtered_data['Category'].str.contains(category, case=False)) &
                (filtered_data['Calories (kcal)'] <= category_target_calories * 1.2)
            ]

            if not category_foods.empty:
                category_foods['calorie_diff'] = abs(category_foods['Calories (kcal)'] - category_target_calories)
                recommended = category_foods.nsmallest(1, 'calorie_diff')
                daily_plan.append(recommended)
                remaining_calories -= recommended['Calories (kcal)'].iloc[0]

        if daily_plan:
            day_df = pd.concat(daily_plan)
            day_df['Day'] = f'Day {day + 1}'
            daily_plans.append(day_df)

    return pd.concat(daily_plans) if daily_plans else pd.DataFrame()

# Load data
data = load_data()

# Main title
st.title("🍱 Magic Meal Planner - Your Personal Food Journey! ✨")

# Add a welcoming message
st.markdown("""
    ### 👋 Welcome to Your Personalized Meal Planning Experience!
    Let's create a delicious and healthy meal plan together! 🌟
""")

# Create two columns for the layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎯 Step 1: Tell Us About Yourself")

    input_col1, input_col2, input_col3 = st.columns(3)

    with input_col1:
        age = st.number_input("🎂 Age", min_value=0, max_value=120, value=25)
        height = st.number_input("📏 Height (cm)", min_value=100, max_value=250, value=170) / 100
        activity_level = st.selectbox("💪 Lifestyle", [
            "Sedentary (Office Job) 💻",
            "Light Active (Light Exercise) 🚶",
            "Moderate Active (Regular Exercise) 🏃",
            "Very Active (Athlete) 🏋️"
        ])

    with input_col2:
        gender = st.selectbox("👤 Gender", ["Male", "Female", "Other"])
        current_weight = st.number_input("⚖️ Current Weight (kg)", min_value=20, max_value=200, value=70)
        veg_pref = st.selectbox("🥗 Food Preference", ["Veg 🌱", "Non-Veg 🍗"])

    with input_col3:
        fitness_goal = st.selectbox("🎯 Fitness Goal", [
            "Lose Weight 📉",
            "Maintain Weight ⚖️",
            "Gain Weight 📈"
        ])
        target_weight = st.number_input("🎯 Target Weight (kg)", min_value=20, max_value=200, value=current_weight)
        cuisine_pref = st.multiselect("🍽️ Preferred Cuisines", 
                                    options=data['Tags'].str.split(',').explode().unique(),
                                    default=['North Indian'])

with col2:
    st.header("🍽️ Customize Your Meals")
    st.write("Adjust how you want your daily calories distributed:")

    breakfast_pct = st.slider("🌅 Breakfast %", 0, 40, 25)
    lunch_pct = st.slider("🌞 Lunch %", 0, 40, 30)
    dinner_pct = st.slider("🌙 Dinner %", 0, 40, 30)
    snacks_pct = st.slider("🍪 Snacks %", 0, 40, 15)

    # Normalize percentages
    total_pct = breakfast_pct + lunch_pct + dinner_pct + snacks_pct
    meal_preferences = {
        'Breakfast': (breakfast_pct / total_pct) * 100,
        'Lunch': (lunch_pct / total_pct) * 100,
        'Dinner': (dinner_pct / total_pct) * 100,
        'Snack': (snacks_pct / total_pct) * 100
    }

# Calculate BMI and calorie needs
bmi = calculate_bmi(current_weight, height)
bmi_category = get_bmi_category(bmi)

# Calculate base metabolic rate (BMR)
if gender == "Male":
    bmr = 88.362 + (13.397 * current_weight) + (4.799 * height * 100) - (5.677 * age)
else:
    bmr = 447.593 + (9.247 * current_weight) + (3.098 * height * 100) - (4.330 * age)

# Activity level multipliers
activity_multipliers = {
    "Sedentary (Office Job) 💻": 1.2,
    "Light Active (Light Exercise) 🚶": 1.375,
    "Moderate Active (Regular Exercise) 🏃": 1.55,
    "Very Active (Athlete) 🏋️": 1.725
}

# Calculate TDEE and target calories
tdee = bmr * activity_multipliers[activity_level]
if "Lose Weight" in fitness_goal:
    calorie_target = tdee - 500
elif "Gain Weight" in fitness_goal:
    calorie_target = tdee + 500
else:
    calorie_target = tdee

# Display health metrics
with st.expander("🏥 Your Health Metrics"):
    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric("📊 BMI", f"{bmi:.1f}")
        st.write(f"Category: {bmi_category} {get_bmi_emoji(bmi_category)}")

    with metric_col2:
        st.metric("🔥 Base Metabolic Rate", f"{bmr:.0f} kcal")

    with metric_col3:
        st.metric("🎯 Daily Calorie Target", f"{calorie_target:.0f} kcal")

# Generate meal plan
meal_plan = generate_meal_plan(data, calorie_target, veg_pref, meal_preferences)

if not meal_plan.empty:
    st.header("📅 Your Weekly Meal Adventure!")

    tab1, tab2, tab3 = st.tabs([
        "🍽️ Meal Schedule",
        "📊 Nutrition Analysis",
        "💡 Smart Recommendations"
    ])

    with tab1:
        for day in meal_plan['Day'].unique():
            with st.expander(f"📅 {day}"):
                day_meals = meal_plan[meal_plan['Day'] == day]
                for _, meal in day_meals.iterrows():
                    st.write(f"{get_meal_emoji(meal['Category'])} **{meal['Category']}**: {meal['Food Name']}")
                    st.write(f"🔢 Nutrients: {meal['Calories (kcal)']:.0f} kcal | "
                            f"🥩 Protein: {meal['Protein (g)']:.1f}g | "
                            f"🌾 Carbs: {meal['Carbs (g)']:.1f}g | "
                            f"🥑 Fat: {meal['Fat (g)']:.1f}g")

    with tab2:
        st.write("### 📈 Your Nutrition Analytics")
        col1, col2 = st.columns(2)

        with col1:
            # Daily calorie distribution
            fig1 = px.bar(meal_plan, x='Day', y='Calories (kcal)', color='Category',
                         title="Calorie Distribution by Day and Meal 🍽️",
                         barmode='stack')
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Nutrient distribution radar chart
            avg_nutrients = meal_plan[['Protein (g)', 'Carbs (g)', 'Fat (g)']].mean()
            fig2 = go.Figure()
            fig2.add_trace(go.Scatterpolar(
                r=avg_nutrients.values,
                theta=avg_nutrients.index,
                fill='toself',
                name='Average Daily Nutrients'
            ))
            fig2.update_layout(title="Nutritional Balance 🎯")
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.write("### 💡 Smart Recommendations Just for You!")

        # Add personalized recommendations
        if avg_nutrients['Protein (g)'] < (current_weight * 0.8):
            st.warning("🥩 Consider increasing your protein intake for better results!")

        if "Lose Weight" in fitness_goal and avg_nutrients['Carbs (g)'] > 200:
            st.info("🌾 Try reducing carbohydrate intake for better weight loss results")

        if bmi_category == "Underweight" and "Gain Weight" in fitness_goal:
            st.info("🥑 Focus on protein-rich foods and healthy fats for healthy weight gain")

    # Add feedback section
    st.header("🎯 Rate Your Experience")
    col1, col2 = st.columns(2)

    with col1:
        rating = st.slider("How happy are you with this plan? 😊", 1, 5, 3)
        st.write(f"Your rating: {'⭐' * rating}")

    with col2:
        if rating < 4:
            feedback = st.text_area("💭 How can we make this better for you?")
            if st.button("📮 Submit Feedback"):
                st.success("🙏 Thank you for your feedback!")

else:
    st.error("😕 Oops! We couldn't generate a meal plan with these preferences. Let's try adjusting them!")




# Add footer
st.markdown("""
---
### 🌟 Made with love for healthy eating! 🥗
Remember: Every meal is a chance to nourish your body! 💪
""")