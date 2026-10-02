"""Dependency-free web app for displaying the logic manager's meal plan."""

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from logic_manager import build_input_record, generate_plan

HOST = "127.0.0.1"
PORT = 8000


def page(body: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calora meal planner</title><style>
:root {{ --ink: #20382f; --green: #28624d; --coral: #d56b48; --paper: #fffdf8; --line: #d7dfd4; --muted: #68766b; font-family: "Trebuchet MS", sans-serif; color: var(--ink); background: #f4efe4; }}
* {{ box-sizing: border-box; }} body {{ margin: 0; background: radial-gradient(circle at 90% 0%, #f5d5bd 0, transparent 30%), linear-gradient(135deg, #f4efe4, #dfece2); min-height: 100vh; }}
main {{ max-width: 1100px; margin: auto; padding: 36px 22px 64px; }}
.brand {{ display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 60px; }} .mark {{ color: var(--coral); font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }} .date {{ color: var(--muted); font-size: .9rem; }}
h1 {{ color: var(--green); font-family: Georgia, serif; font-size: clamp(2.8rem, 7vw, 6rem); font-weight: 400; letter-spacing: 0; line-height: .92; margin: 0 0 18px; max-width: 760px; }}
h2 {{ color: var(--green); font-family: Georgia, serif; font-size: 1.65rem; font-weight: 400; margin: 0 0 12px; }} h3 {{ font-family: Georgia, serif; font-weight: 400; }}
.lede {{ color: var(--muted); font-size: 1.08rem; line-height: 1.6; max-width: 650px; }}
form, .summary, .meal {{ background: rgba(255, 253, 248, .88); border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 14px 32px rgba(47, 73, 56, .06); }}
form {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 18px; margin: 34px 0; padding: 28px; }} .group-title {{ grid-column: 1 / -1; border-bottom: 1px solid var(--line); color: var(--green); font-family: Georgia, serif; font-size: 1.35rem; padding-bottom: 10px; }}
label {{ display: grid; gap: 7px; font-size: .85rem; font-weight: 700; grid-column: span 3; }} label.wide {{ grid-column: span 6; }}
input, select, button {{ background: #fffefb; color: var(--ink); font: inherit; padding: 12px; border: 1px solid #b8c9bc; border-radius: 4px; }} input:focus, select:focus {{ border-color: var(--coral); outline: 3px solid rgba(213, 107, 72, .15); }}
button {{ grid-column: 1 / -1; background: var(--coral); color: white; border: 0; cursor: pointer; font-weight: 700; margin-top: 8px; padding: 14px; transition: transform .2s, background .2s; }} button:hover {{ background: #b95537; transform: translateY(-2px); }}
.summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; overflow: hidden; margin: 26px 0 34px; }} .summary div {{ background: var(--paper); padding: 20px; }} .summary strong {{ display: block; color: var(--green); font-family: Georgia, serif; font-size: 1.65rem; font-weight: 400; margin-bottom: 4px; }}
.meals {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }} .meal {{ padding: 22px; }} .meal h3 {{ color: var(--coral); font-size: 1.3rem; margin: 0 0 20px; text-transform: capitalize; }}
.detail {{ border-top: 1px solid var(--line); line-height: 1.5; margin: 0; padding: 11px 0; }} .pantry, .notice {{ background: #fff0cc; padding: 11px 13px; border-left: 4px solid var(--coral); line-height: 1.5; }}
.muted {{ color: var(--muted); font-family: "Trebuchet MS", sans-serif; font-size: .82rem; }} a {{ color: var(--green); font-weight: bold; }}
@media (max-width: 760px) {{ .brand {{ margin-bottom: 42px; }} form {{ grid-template-columns: repeat(2, 1fr); padding: 20px; }} label, label.wide {{ grid-column: span 1; }} label.wide, .group-title, button {{ grid-column: 1 / -1; }} .meals {{ grid-template-columns: 1fr; }} }}
@media (max-width: 480px) {{ main {{ padding: 24px 15px 42px; }} .brand {{ align-items: flex-start; flex-direction: column; gap: 6px; }} form {{ display: block; }} label {{ margin-bottom: 15px; }} .summary {{ grid-template-columns: 1fr; }} }}
</style></head><body><main>{body}</main></body></html>"""


def render_form() -> str:
    return """<header class="brand"><span class="mark">Calora / daily table</span><span class="date">A gentler way to plan today</span></header>
<h1>Let's plan today's meals.</h1>
<p class="lede">A thoughtful meal plan shaped around your body, your budget, and what you already have in the kitchen.</p>
<form method="post" action="/plan">
<div class="group-title">Your profile</div>
<label>Age<input name="age" type="number" min="1" value="25" required></label>
<label>Gender<select name="gender"><option>female</option><option>male</option></select></label>
<label>Height (cm)<input name="height_cm" type="number" value="165" required></label>
<label>Weight (kg)<input name="weight_kg" type="number" value="65" required></label>
<label>Activity level<select name="activity_level"><option>sedentary</option><option>light</option><option selected>moderate</option><option>active</option><option>very_active</option></select></label>
<label>Goal<select name="goal"><option selected>lose</option><option>maintain</option><option>gain</option></select></label>
<label>Target calories<input name="target_calories" type="number" placeholder="Press Enter to skip"></label>
<div class="group-title">Today's preferences</div>
<label>Restrictions/allergies<input name="restrictions" placeholder="e.g. prawn"></label>
<label class="wide">Cravings / food type<input name="cravings" value="western"></label>
<label>Meal source<select name="meal_source"><option>eat_out</option><option>home_cooked</option><option selected>both</option></select></label>
<label class="wide">Ingredients on hand<input name="ingredients" value="pasta, garlic, potato, chicken, lettuce, cucumber"></label>
<label>Daily budget<input name="budget" type="number" min="1" step="0.01" value="20"></label>
<button type="submit">Build today's meal plan &rarr;</button></form>"""


def render_plan(result: dict) -> str:
    data = result["data"]
    cards = "".join(
        f"""<article class="meal"><h3>{escape(str(meal['slot']))}: {escape(str(meal['name']))} <span class="muted">({escape(str(meal['source']))})</span></h3>
<p class="detail"><strong>Calories:</strong> {escape(str(meal['calories']))} - {escape(str(meal['calorie_status']))}</p>
<p class="detail"><strong>Macros:</strong> Protein {escape(str(meal['protein']))} / Carbs {escape(str(meal['carbs']))} / Fat {escape(str(meal['fat']))}</p>
{f'<p class="pantry"><strong>Uses from your pantry:</strong> {escape(", ".join(meal["pantry"]))}</p>' if meal.get("pantry") else ''}
<p class="detail"><strong>Cost:</strong> {escape(str(meal['cost_label']))}</p></article>"""
        for meal in data["meals"]
    )
    notice = f"<p class=\"notice\">{escape(result['notice'])}. Showing the local logic result.</p>" if result.get("notice") else ""
    return f"""<header class="brand"><span class="mark">Calora / daily table</span><span class="date">Your plan is ready</span></header>
<h1>Your meal plan</h1><p class="lede">Generated by {escape(result['source'])}. Here is the shape of your day, one satisfying plate at a time.</p>{notice}
<section class="summary"><div><strong>{data['total_calories']} kcal</strong>total calories</div><div><strong>{data['total_cost']:.2f}</strong>estimated cost</div><div><strong>{escape(str(data['daily_target']))} kcal</strong>daily target</div></section>
<h2>Why this plan</h2><p>{escape(data['why'])}</p><section class="meals">{cards}</section>
<p>Summary: {data['saved_count']} past meal plan(s) saved</p><p><a href="/">Create another plan</a></p>"""


class CaloraHandler(BaseHTTPRequestHandler):
    def send_page(self, content: str) -> None:
        payload = page(content).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        self.send_page(render_form())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        values = parse_qs(self.rfile.read(length).decode("utf-8"))
        form_data = {key: value[0] for key, value in values.items()}
        self.send_page(render_plan(generate_plan(build_input_record(form_data))))

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == "__main__":
    print(f"Calora is running at http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), CaloraHandler).serve_forever()
