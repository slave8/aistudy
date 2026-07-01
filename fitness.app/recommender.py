LEVEL_RULES = {
    "입문자": {"ratio": 0.35, "sets": 3, "reps": 12, "rest": 75, "calorie": 0.06},
    "초보자": {"ratio": 0.45, "sets": 3, "reps": 10, "rest": 90, "calorie": 0.075},
    "중급자": {"ratio": 0.65, "sets": 4, "reps": 8, "rest": 120, "calorie": 0.09},
    "상급자": {"ratio": 0.8, "sets": 5, "reps": 6, "rest": 150, "calorie": 0.11},
}

GOAL_WEIGHT = {
    "근력 증가": 1.1,
    "근비대": 1.0,
    "체지방 감량": 0.85,
    "건강 관리": 0.75,
}


def recommend_workout(exercise, level, weight_kg, goal):
    rule = LEVEL_RULES[level]
    recommended_weight = weight_kg * rule["ratio"] * GOAL_WEIGHT[goal]
    recommended_weight = max(2.5, round(recommended_weight / 2.5) * 2.5)

    minutes = rule["sets"] * 3
    calories = round(minutes * weight_kg * rule["calorie"])

    return {
        "name": exercise["name"],
        "category": exercise["category"],
        "group": exercise["group"],
        "part": exercise["part"],
        "weight": recommended_weight,
        "sets": rule["sets"],
        "reps": rule["reps"],
        "rest": rule["rest"],
        "minutes": minutes,
        "calories": calories,
        "youtube": exercise["youtube"],
    }