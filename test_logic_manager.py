"""Offline tests for Calora.
These tests describe current behavior, including validation limitations.
Only pure modules are imported: no Gemini SDK, dotenv, API key, or data files.
"""
import copy
import json

import pytest

import manager.ai_handler_manager as handler
import manager.logic_manager as logic


# sample user details for calculating targets and choosing meals
# fixture provides reusable sample data for the tests.
# each test using this fixture gets fresh data, so changes made in one test won't affect another test
@pytest.fixture
def user_profile():
    return {
        "name": "Nisha", "age": 21, "gender": "female", "weight_kg": 52,
        "height_cm": 165, "activity_level": "sedentary", "goal": "maintain",
        "dietary_restrictions": [], "meal_preference": "rice dishes",
        "meal_source": "both", "pantry_ingredients": ["eggs", "chicken", "rice"],
        "daily_budget": 10.5,
    }


# created sample meal data for the tests
def meal(slot="Breakfast", name="Eggs on Toast", calories=400, cost=2.5, **changes):
    #hardcoded Gemini-style recommendation with the exact expected fields
    result = {
        "meal_type": slot, "meal_name": name, "meal_source_type": "home_cooked",
        "calories": calories, "protein_g": 25, "carbs_g": 40, "fat_g": 15,
        "estimated_cost": cost, "portion_size": "1 serving",
        "pantry_ingredients_used": ["eggs"],
        "ingredients": ["2 eggs", "2 slices wholemeal bread"],
        "recipe_steps": ["Boil eggs for 10 minutes.", "Toast bread and serve."],
    }
    result.update(changes)
    return result


# sample AI response with 10 meal recommendations
@pytest.fixture
def response():
    # ten realistic options
    return {
        "estimated_nutrition_targets": {
            "calorie_target": 1650, "protein_target_g": 90,
            "carb_target_g": 185, "fat_target_g": 55,
        },
        "recommendations": [
# created a sample meal instead of requesting one from Gemini
# tests can change details such as calories, cost or ingredients to check how the program handles different situations
            meal(),
            meal("Lunch", "Chicken Rice", 500, 4.5, meal_source_type="eat_out",
                 pantry_ingredients_used=[], ingredients=[], recipe_steps=[]),
            meal("Dinner", "Chicken and Rice Bowl", 520, 3.5,
                 pantry_ingredients_used=["chicken", "rice"],
                 ingredients=["150g chicken breast", "1 cup cooked rice"],
                 recipe_steps=["Cook chicken thoroughly.", "Serve with rice."]),
            meal("Breakfast", "Boiled Eggs and Toast", 250, 1.2),
            meal("Lunch", "Garlic Chicken Pasta", 480, 3),
            meal("Dinner", "Yong Tau Foo", 420, 6, meal_source_type="eat_out",
                 pantry_ingredients_used=[], ingredients=[], recipe_steps=[]),
            meal("Lunch", "Sliced Fish Soup", 380, 5.5, meal_source_type="eat_out",
                 pantry_ingredients_used=[], ingredients=[], recipe_steps=[]),
            meal("Dinner", "Salmon Rice Bowl", 600, 7),
            meal("Breakfast", "Kaya Toast Set", 350, 3.5, meal_source_type="eat_out",
                 pantry_ingredients_used=[], ingredients=[], recipe_steps=[]),
            meal("Lunch", "Vegetable Rice Bowl", 650, 4),
        ],
    }


# sample user details for calculating targets and choosing meals
@pytest.fixture
def profile():
    return {
        "name": "Nisha", "age": 21, "gender": "female", "weight_kg": 52,
        "height_cm": 165, "activity_level": "sedentary", "goal": "maintain",
        "dietary_restrictions": [], "meal_preference": "rice dishes",
        "meal_source": "both", "pantry_ingredients": ["eggs", "chicken", "rice"],
        "daily_budget": 10.5,
    }


def test_parse_validate_and_build_happy_path(response, profile):
    # kept copies to check that the original inputs aren't changed
    original = copy.deepcopy(response)
    original_profile = copy.deepcopy(profile)
    parsed = handler.parse_response(" \n" + json.dumps(response) + "\t ")
    assert parsed == response
    assert handler.validate_response(parsed)
    plan = logic.build_meal_plan(parsed["recommendations"], profile)
    assert plan["is_complete"] is True
    assert plan["missing_slots"] == []
    assert {slot: value["name"] for slot, value in plan["meals"].items()} == {
        "breakfast": "Eggs on Toast", "lunch": "Chicken Rice",
        "dinner": "Chicken and Rice Bowl",
    }
    assert plan["daily_calorie_target"] == pytest.approx(1542.3) #decimal calculations can have tiny rounding differences approx checks that the result is close to the expected value.
    assert plan["total_calories"] == 1420

    # a plan exactly at the budget should still be allowed.

    assert plan["total_cost"] == 10.5
    assert plan["within_budget"] is True  # Equality is within budget.
    assert plan["meals"]["dinner"]["pantry_ingredients_used"] == ["150g chicken breast", "1 cup cooked rice"]
    assert response == original
    assert profile == original_profile


# running the same test once for each value listed below
# lets us check several inputs without repeating the test code
@pytest.mark.parametrize("text", [None, "", " \n\t", "{", '{"recommendations":}',
                                     "null", "[]", "{}", "not JSON"])
def test_invalid_response_returns_none_and_logs(text):
    # Expected rejection logs are captured, keeping normal pytest output clean.
    with pytest.MonkeyPatch.context() as patch:
        from unittest.mock import Mock
        logger = Mock()
        patch.setattr(handler, "logger", logger)
        assert handler.parse_response(text) is None
        logger.warning.assert_called()


@pytest.mark.parametrize("wrapper", ["```json\n{}\n```", "```\n{}\n```",
                                       "Here is your plan: {}", "{} trailing text"])
def test_parser_rejects_fences_and_prose(response, wrapper):
    assert handler.parse_response(wrapper.format(json.dumps(response))) is None


@pytest.mark.parametrize("value", [123, {"recommendations": []}, [1]])
def test_non_text_parser_input_raises_type_error(value):
    #non-text input should raise a TypeError
    with pytest.raises(TypeError):
        handler.parse_response(value)


@pytest.mark.parametrize("section", ["top", "targets", "meal"])
@pytest.mark.parametrize("operation", ["missing", "extra"])
def test_schema_requires_exact_fields(response, section, operation):
    target = {"top": response, "targets": response["estimated_nutrition_targets"],
              "meal": response["recommendations"][0]}[section]
    if operation == "missing":
        # Check every required field, not just one representative field.
        for field in list(target):
            value = target.pop(field)
            assert handler.parse_response(json.dumps(response)) is None
            target[field] = value
    else:
        target["unexpected"] = "extra"
        assert handler.parse_response(json.dumps(response)) is None


@pytest.mark.parametrize("field", ["meal_type", "meal_name", "portion_size",
    "meal_source_type", "calories", "protein_g", "carbs_g", "fat_g",
    "estimated_cost", "pantry_ingredients_used", "ingredients", "recipe_steps"])
def test_wrong_recommendation_field_types(response, field):
    response["recommendations"][0][field] = None
    assert not handler.validate_recommendation(response["recommendations"][0])
    assert handler.parse_response(json.dumps(response)) is None


@pytest.mark.parametrize("field", ["calorie_target", "protein_target_g",
                                   "carb_target_g", "fat_target_g"])
def test_wrong_target_field_type(response, field):
    response["estimated_nutrition_targets"][field] = "100"
    assert not handler.validate_nutrition_targets(response["estimated_nutrition_targets"])
    assert handler.parse_response(json.dumps(response)) is None


@pytest.mark.parametrize("count", [0, 1, 9, 10, 11])
def test_exactly_ten_recommendations(count):
    assert handler.validate_recommendations([meal() for _ in range(count)]) is (count == 10)


@pytest.mark.parametrize("value", [None, "", 3, [], {}])
def test_validators_reject_invalid_container_shapes(value):
    assert not handler.validate_nutrition_targets(value)
    assert not handler.validate_recommendation(value)
    assert not handler.validate_recommendations(value)
    assert not handler.validate_response(value)


def test_validator_current_limitations(response):
    # Numeric booleans/negative values and arbitrary list entries are accepted.
    item = response["recommendations"][0]
    item.update(calories=True, protein_g=-1, ingredients=[123], meal_type="Snack")
    assert handler.validate_recommendation(item)
    response["estimated_nutrition_targets"]["calorie_target"] = False
    assert handler.validate_response(response)
    item["meal_source_type"] = "in"
    assert not handler.validate_recommendation(item)


def test_target_math_and_profile_pipeline(profile):
    assert logic.calculate_bmr("male", 70, 175, 30) == 1648.75
    assert logic.calculate_bmr("MALE", 70, 175, 30) == 1648.75
    assert logic.calculate_bmr("female", 70, 175, 30) == 1482.75
    assert logic.calculate_bmr("M", 70, 175, 30) == 1648.75
    assert logic.calculate_per_meal_calorie_target(1500) == 500
    assert logic.calculate_per_meal_calorie_target(0) == 0
    targets = logic.calculate_targets(profile)
    assert targets["bmr"] == 1285.25
    assert targets["tdee"] == pytest.approx(1542.3)
    assert targets["daily_calorie_target"] == pytest.approx(1542.3)
    assert targets["per_meal_calorie_target"] == pytest.approx(514.1)
    assert targets["per_meal_macro_targets"] == {"protein_g": 38.6, "carbs_g": 51.4, "fat_g": 17.1}


@pytest.mark.parametrize("activity,multiplier", [
    ("sedentary", 1.2), ("light", 1.375), ("moderate", 1.55),
    ("moderately active", 1.55), ("active", 1.725), ("very_active", 1.9),
    ("very active", 1.9), ("unknown", 1.2)])
def test_activity_multipliers(activity, multiplier):
    assert logic.calculate_tdee(1000, activity) == pytest.approx(1000 * multiplier)


@pytest.mark.parametrize("gender", ["male", "MALE", "M", "m"])
def test_male_gender_aliases_use_male_bmr_formula(gender):
    assert logic.calculate_bmr(gender, 70, 175, 30) == 1648.75


@pytest.mark.parametrize("goal,target,macros", [
    ("lose", 1000, {"protein_g": 78.8, "carbs_g": 78.8, "fat_g": 30}),
    ("maintain", 1500, {"protein_g": 67.5, "carbs_g": 90, "fat_g": 30}),
    ("gain", 1800, {"protein_g": 78.8, "carbs_g": 90, "fat_g": 25}),
    ("unknown", 1500, {"protein_g": 67.5, "carbs_g": 90, "fat_g": 30})])
def test_goal_adjustments_and_macro_splits(goal, target, macros):
    assert logic.calculate_daily_calorie_target(1500, goal) == target
    assert logic.calculate_macro_targets(900, goal) == macros


def test_ingredients_and_slot_normalization():
    assert logic.get_ingredient_names(["2 eggs", {"item": "chicken", "quantity": 150,
        "unit": "g"}, {}, "", None, 5]) == ["2 eggs", "chicken"]
    assert logic.get_ingredient_names(None) == []
    items = [meal("  BREAKFAST\t"), meal("Lunch"), meal("Snack"), {}]
    assert logic.group_candidates_by_slot(items) == {
        "breakfast": [items[0]], "lunch": [items[1]], "dinner": []}
    assert logic.group_candidates_by_slot(None) == {slot: [] for slot in logic.MEAL_SLOTS}


def test_dietary_filter_checks_name_and_ingredients():
    items = [meal(name="Peanut Butter Toast", ingredients=[]),
             meal(ingredients=[{"item": "peanut oil"}]), meal()]
    assert logic.apply_dietary_safety_rule(items, ["PEANUT"]) == [items[2]]
    assert logic.apply_dietary_safety_rule(items, []) == items
    assert logic.apply_dietary_safety_rule(items, ["no peanut"]) == items  # Literal substring.
    assert logic.apply_dietary_safety_rule(items, [""]) == items


def test_eat_out_allergen_in_ingredients_is_filtered_even_if_name_omits_it():
    hidden_fish = meal(
        "Lunch",
        "Economical Rice with Chicken",
        meal_source_type="eat_out",
        ingredients=["rice", "chicken", "fish sauce"],
        recipe_steps=[],
        pantry_ingredients_used=[],
    )
    safe_dish = meal(
        "Lunch",
        "Chicken Rice",
        meal_source_type="eat_out",
        ingredients=["rice", "chicken"],
        recipe_steps=[],
        pantry_ingredients_used=[],
    )

    assert logic.apply_dietary_safety_rule(
        [hidden_fish, safe_dish], "fish allergy"
    ) == [safe_dish]


def test_eat_out_dish_with_unknown_ingredients_is_excluded_for_restricted_user():
    unknown_dish = meal(
        "Lunch",
        "Economical Rice with Chicken",
        meal_source_type="eat_out",
        ingredients=[],
        recipe_steps=[],
        pantry_ingredients_used=[],
    )

    assert logic.apply_dietary_safety_rule([unknown_dish], "fish") == []


@pytest.mark.parametrize("source,count", [("home_cooked", 1), ("eat_out", 1),
    ("both", 2), (None, 2), ("", 2), ("in", 0)])
def test_source_filter_actual_behavior(source, count):
    items = [meal(), meal(meal_source_type="eat_out")]
    assert len(logic.apply_source_preference_rule(items, source)) == count


def test_scoring_ranking_and_source_fallback():
    macros = {"protein_g": 25, "carbs_g": 40, "fat_g": 15}
    best = meal(name="Best", calories=500, cost=5)
    cheaper = meal(name="Cheaper", calories=500, cost=0)
    worse_macro = meal(name="Less Protein", calories=500, cost=0, protein_g=20)
    worse_calorie = meal(name="Low Calories", calories=499, cost=0)
    items = [worse_calorie, worse_macro, best, cheaper]
    original = copy.deepcopy(items)
    ranked = logic.rank_slot_candidates(items, 500, macros, [], "both")
    assert [m["meal_name"] for m in ranked] == ["Cheaper", "Best", "Less Protein", "Low Calories"]
    assert items == original
    assert ranked[0]["_calorie_distance"] == ranked[0]["_macro_distance"] == 0
    assert logic.calculate_calorie_distance(meal(calories=450), 500) == 50
    assert logic.calculate_calorie_distance({}, 500) == 500
    assert logic.calculate_macro_distance(worse_macro, macros) == 5
    assert logic.calculate_macro_distance({}, {}) == 0
    assert logic.cost_component({}) == float("inf")
    assert logic.cost_component({"estimated_cost": 0}) == 0
    assert logic.select_top_candidate(ranked) == ranked[0]
    assert logic.select_top_candidate([]) is None
    assert logic.rank_slot_candidates([], 500, macros, [], "both") == []
    # A wrong-source option survives only when no preferred-source option remains.
    out = meal(meal_source_type="eat_out", calories=500)
    assert logic.rank_slot_candidates([out, best], 500, macros, [], "home_cooked")[0]["meal_source_type"] == "home_cooked"
    assert logic.rank_slot_candidates([out], 500, macros, [], "home_cooked")[0]["meal_source_type"] == "eat_out"


def test_requested_cuisine_breaks_tie_after_nutrition_fit():
    macros = {"protein_g": 25, "carbs_g": 40, "fat_g": 15}
    chinese = meal("Lunch", "Chicken Rice", calories=500, cost=5)
    western = meal("Lunch", "Grilled Chicken Sandwich", calories=500, cost=5)

    ranked = logic.rank_slot_candidates(
        [chinese, western], 500, macros, [], "both", "western"
    )

    assert ranked[0]["meal_name"] == "Grilled Chicken Sandwich"


def test_requested_cuisine_does_not_override_better_nutrition_fit():
    macros = {"protein_g": 25, "carbs_g": 40, "fat_g": 15}
    western_less_fitting = meal("Lunch", "Grilled Chicken Sandwich", calories=400, cost=5)
    chinese_better_fitting = meal("Lunch", "Chicken Rice", calories=500, cost=5)

    ranked = logic.rank_slot_candidates(
        [western_less_fitting, chinese_better_fitting], 500, macros, [], "both", "western"
    )

    assert ranked[0]["meal_name"] == "Chicken Rice"
    assert logic.rank_slot_candidates([meal(name="Peanut")], 500, macros, ["peanut"], "both") == []


@pytest.mark.parametrize("function,cases", [
    (logic.tag_calorie_range, [(399.99, "Low (<400 kcal)"), (400, "Moderate (400-700 kcal)"),
        (700, "Moderate (400-700 kcal)"), (700.01, "High (>700 kcal)")]),
    (logic.tag_protein, [(9.99, "Low (<10g)"), (10, "Moderate (10-20g)"),
        (20, "Moderate (10-20g)"), (20.01, "High (>20-30g)"),
        (30, "High (>20-30g)"), (30.01, "Very High (>30g)")]),
    (logic.tag_carbs, [(14.99, "Low (<15g)"), (15, "Moderate (15-30g)"),
        (30, "Moderate (15-30g)"), (30.01, "High (>30-60g)"),
        (60, "High (>30-60g)"), (60.01, "Very High (>60g)")]),
    (logic.tag_fat, [(4.99, "Low (<5g)"), (5, "Moderate (5-10g)"),
        (10, "Moderate (5-10g)"), (10.01, "High (>10-20g)"),
        (20, "High (>10-20g)"), (20.01, "Very High (>20g)")]),
    (logic.tag_cost, [(None, "Unknown"), (0, "Budget (<$5)"), (4.99, "Budget (<$5)"),
        (5, "Moderate (<$10)"), (9.99, "Moderate (<$10)"),
        (10, "Moderate (<$15)"), (14.99, "Moderate (<$15)"),
        (15, "High (<$20)"), (19.99, "High (<$20)"), (20, "Premium (>$20)")]),
])
def test_all_tag_boundaries(function, cases):
    for value, expected in cases:
        assert function(value) == expected


@pytest.mark.parametrize("calories,expected", [(399.99, "under_target"),
    (400, "on_target"), (600, "on_target"), (600.01, "over_target")])
def test_calorie_fit_inclusive_twenty_percent_boundary(calories, expected):
    assert logic.tag_calorie_fit(calories, 500) == expected
    assert logic.tag_calorie_fit(500, 500, tolerance=0) == "on_target"


def test_pantry_matching_and_exact_annotation():
    item = meal(ingredients=["150g Chicken breast", {"item": "rice"}],
                pantry_ingredients_used=["invented"])
    pantry = ["CHICKEN", "rice", "salmon"]
    assert logic.find_pantry_ingredients_used(item["ingredients"], pantry) == ["CHICKEN", "rice"]
    assert logic.find_pantry_ingredients_used(None, pantry) == []
    assert logic.find_pantry_ingredients_used(item["ingredients"], []) == []
    assert logic.annotate_meal(item, 500, pantry) == {
        "name": "Eggs on Toast", "source_type": "home_cooked",
        "calorie_range": "Moderate (400-700 kcal)", "calorie_tag": "on_target",
        "protein_tag": "High (>20-30g)", "carbs_tag": "High (>30-60g)",
        "fat_tag": "High (>10-20g)", "cost_tier": "Budget (<$5)",
        "pantry_ingredients_used": ["150g Chicken breast", {"item": "rice"}]
    }


@pytest.mark.parametrize("no_restrictions", ["nil", "none", "no", "no restrictions", ""])
def test_textual_no_restrictions_does_not_filter_candidates(no_restrictions):
    candidate = meal()
    assert logic.apply_dietary_safety_rule([candidate], no_restrictions) == [candidate]


def test_comma_separated_dietary_restrictions_are_individual_terms():
    peanut_meal = meal(name="Peanut Butter Toast")
    safe_meal = meal(name="Eggs on Toast")
    assert logic.apply_dietary_safety_rule(
        [peanut_meal, safe_meal], "peanut, shellfish"
    ) == [safe_meal]


@pytest.mark.parametrize(
    "restriction",
    ["fish allergy", "allergy to fish", "allergic to fish", "I am allergic to fish"],
)
def test_allergy_phrasing_filters_eat_out_dishes_by_name(restriction):
    fish_dish = meal(
        "Lunch",
        "Economical Rice with Chicken and Fish",
        meal_source_type="eat_out",
        ingredients=[],
        recipe_steps=[],
        pantry_ingredients_used=[],
    )
    safe_dish = meal(
        "Lunch",
        "Chicken Rice",
        meal_source_type="eat_out",
        ingredients=["chicken", "rice"],
    )
    profile = {
        "name": "Nisha", "age": 21, "gender": "female", "weight_kg": 52,
        "height_cm": 165, "activity_level": "sedentary", "goal": "maintain",
        "dietary_restrictions": restriction, "meal_source": "both",
        "pantry_ingredients": [], "daily_budget": 10.5,
    }
    recommendations = [
        meal("Breakfast"),
        fish_dish,
        safe_dish,
        meal("Dinner"),
    ]

    plan = logic.build_meal_plan(recommendations, profile)
    assert plan["meals"]["lunch"]["name"] == "Chicken Rice"


def test_empty_partial_and_fully_filtered_plans(profile):
    assert logic.build_meal_plan([], profile) is None
    assert logic.build_meal_plan(None, profile) is None
    assert logic.build_meal_plan([meal("Snack"), {}], profile) is None
    profile["dietary_restrictions"] = ["peanut"]
    assert logic.build_meal_plan([meal(name="Peanut Toast")], profile) is None
    plan = logic.build_meal_plan([meal()], profile)
    assert plan["is_complete"] is False
    assert plan["missing_slots"] == ["lunch", "dinner"]
    text = logic.format_meal_plan(plan)
    assert "Breakfast: Eggs on Toast (home_cooked)" in text
    assert "Uses from your pantry: 2 eggs" in text
    assert "Missing meals: lunch, dinner" in text
    assert "Lunch:" not in text


@pytest.mark.parametrize("budget,within", [(None, True), (0, False), (2.49, False), (2.5, True)])
def test_plan_budget_boundaries(profile, budget, within):
    profile["daily_budget"] = budget
    plan = logic.build_meal_plan([meal()], profile)
    assert plan["within_budget"] is within


def test_unknown_and_free_costs(profile):
    unknown = logic.build_meal_plan([meal(cost=None)], profile)
    assert unknown["total_cost"] is None
    assert unknown["within_budget"] is True
    assert unknown["meals"]["breakfast"]["cost_tier"] == "Unknown"
    free = logic.build_meal_plan([meal(cost=0)], profile)
    assert free["total_cost"] == 0
    # Current implementation sums known costs even if another cost is unknown.
    mixed = logic.build_meal_plan([meal(cost=None), meal("Lunch", cost=2)], profile)
    assert mixed["total_cost"] == 2


def test_exact_explanation_and_full_plan_format(response, profile):
    assert logic.build_plan_explanation(1400, 1542.3, 11, 30, True) == (
        "Totals 1400 kcal against a 1542 kcal daily target; "
        "an estimated 11.00 — within your 30.00 daily budget.")
    assert "over your" in logic.build_plan_explanation(1400, 1542.3, 11, 10, False)
    for cost, budget in [(None, 30), (11, None)]:
        assert logic.build_plan_explanation(1400, 1542.3, cost, budget, True) == (
            "Totals 1400 kcal against a 1542 kcal daily target.")
    plan = logic.build_meal_plan(response["recommendations"], profile)
    text = logic.format_meal_plan(plan)
    assert text.startswith("=== Your Meal Plan ===\nWhy this plan: " + plan["explanation"])
    assert text.index("Breakfast:") < text.index("Lunch:") < text.index("Dinner:")
    assert "Macros: Protein High (>20-30g) / Carbs High (>30-60g) / Fat High (>10-20g)" in text
    assert "Cost: Budget (<$5)" in text
    assert "Missing meals:" not in text


def test_unvalidated_logic_inputs_raise_existing_exceptions(profile):
    # The logic layer expects parsed dictionaries; it is not a JSON parser.
    with pytest.raises(KeyError):
        logic.calculate_targets({})
    with pytest.raises(TypeError):
        logic.calculate_bmr("male", "70", 175, 30)
    with pytest.raises(TypeError):
        logic.build_meal_plan([meal(calories="400")], profile)
    with pytest.raises(AttributeError):
        logic.group_candidates_by_slot([None])
    with pytest.raises(AttributeError):
        logic.build_meal_plan("```json\n{}\n```", profile)
    with pytest.raises(AttributeError):
        logic.apply_dietary_safety_rule([meal()], [123])
    with pytest.raises(KeyError):
        logic.format_meal_plan({})


# Run this file's tests when the file is executed directly
# -q keeps the output short.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
