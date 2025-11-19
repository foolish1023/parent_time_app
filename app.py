from flask import Flask, render_template, request, jsonify
from datetime import datetime, date
import json
import os
import random

app = Flask(__name__)

# 名言リスト
QUOTES = [
    "時間こそが最も貴重な資産である。",
    "人生は今この瞬間の積み重ね。",
    "後悔するなら、今動こう。",
    "家族との時間は、お金では買えない。",
    "限られた時間だからこそ、意味がある。",
    "今日という日は二度と来ない。",
    "親との時間は、人生で最も大切な投資。",
    "明日ではなく、今日会おう。",
    "時間を無駄にすることは、人生を無駄にすること。",
    "思い出は、一番の財産。",
    "親に感謝できる時間は限られている。",
    "今この瞬間を大事にしよう。",
    "人生の質は、大切な人との時間で決まる。",
    "会いたいなら、迷わず会おう。",
    "時間は誰にでも平等。どう使うかはあなた次第。",
    "親と過ごす時間は、二度と戻らない。",
    "いま、ここ。それが全て。"
]

def get_life_expectancy(gender: str) -> int:
    """平均寿命を返す（日本のざっくり統計）"""
    if gender == "male":
        return 81
    return 87  # female or default

def get_remaining_years(gender: str, age: int) -> int:
    """現在の年齢から平均寿命までの残り年数を計算"""
    life_expectancy = get_life_expectancy(gender)
    remaining = life_expectancy - age
    return max(0, remaining)

@app.route("/", methods=["GET", "POST"])
def index():
    quote = random.choice(QUOTES)

    if request.method == "POST":
        try:
            # 自分の情報
            my_birthdate_str = request.form.get("my_birthdate")
            my_gender = request.form.get("my_gender")

            if not my_birthdate_str or not my_gender:
                raise ValueError("生年月日または性別の情報が不足しています。")

            my_birthdate = datetime.strptime(my_birthdate_str, "%Y-%m-%d").date()
            today = date.today()
            my_age = (today - my_birthdate).days // 365

            # 親の情報
            parent_age_str = request.form.get("parent_age")
            parent_gender = request.form.get("parent_gender")
            if not parent_age_str or not parent_gender:
                raise ValueError("親の情報が不足しています。")

            parent_age = int(parent_age_str)

            # 親との時間情報
            visits_per_year = int(request.form.get("visits") or 0)
            days_per_visit = int(request.form.get("stay") or 0)
            hours_per_day = float(request.form.get("hours") or 0.0)

            # 自分・親の平均寿命と残り時間
            my_life_expectancy = get_life_expectancy(my_gender)
            parent_life_expectancy = get_life_expectancy(parent_gender)

            my_life_left = get_remaining_years(my_gender, my_age)
            parent_life_left = get_remaining_years(parent_gender, parent_age)

            # 親と一緒にいられる期間（どちらが先に亡くなるか）
            time_together_years = min(my_life_left, parent_life_left)

            annual_meeting_days = visits_per_year * days_per_visit
            annual_meeting_hours = annual_meeting_days * hours_per_day

            total_meeting_days = annual_meeting_days * time_together_years
            total_meeting_hours = annual_meeting_hours * time_together_years

            # 大切な人たちの情報（可変長）
            names = request.form.getlist("relation_name[]")
            ages = request.form.getlist("relation_age[]")
            daily_hours_list = request.form.getlist("relation_daily_hours[]")
            leave_ages = request.form.getlist("relation_leave_age[]")

            relations = []
            total_rel_years = 0.0
            total_rel_days = 0.0
            total_rel_hours = 0.0

            for name, age_str, dh_str, leave_str in zip(names, ages, daily_hours_list, leave_ages):
                name = (name or "").strip()
                if not name:
                    # 名前が空ならスキップ
                    continue
                try:
                    age = int(age_str)
                except (TypeError, ValueError):
                    continue
                try:
                    daily_hours = float(dh_str)
                except (TypeError, ValueError):
                    daily_hours = 0.0
                try:
                    leave_age = int(leave_str)
                except (TypeError, ValueError):
                    leave_age = 18

                remaining_years = max(0, leave_age - age)
                remaining_days = remaining_years * 365
                remaining_hours = remaining_days * daily_hours

                total_rel_years += remaining_years
                total_rel_days += remaining_days
                total_rel_hours += remaining_hours

                relations.append({
                    "name": name,
                    "age": age,
                    "years": remaining_years,
                    "days": remaining_days,
                    "hours": remaining_hours,
                })

            result = {
                # 自分
                "my_age": my_age,
                "my_life_expectancy": my_life_expectancy,
                "my_life_left": my_life_left,
                "my_days_left": my_life_left * 365,
                "my_hours_left": my_life_left * 365 * 24,

                # 親
                "parent_age": parent_age,
                "parent_gender": "男性" if parent_gender == "male" else "女性",
                "parent_life_expectancy": parent_life_expectancy,
                "parent_life_left": parent_life_left,
                "parent_days_left": parent_life_left * 365,
                "parent_hours_left": parent_life_left * 365 * 24,

                # 親と会える時間
                "time_together_years": time_together_years,
                "time_together_days": total_meeting_days,
                "time_together_hours": int(total_meeting_hours),

                # 大切な人たち
                "relations": relations,
                "relations_total_years": total_rel_years,
                "relations_total_days": total_rel_days,
                "relations_total_hours": total_rel_hours,
            }

            return render_template("index.html", result=result, quote=quote)

        except Exception as e:
            return render_template("index.html", result=None, error=str(e), quote=quote)

    # GET: 初期表示
    return render_template("index.html", result=None, quote=quote)

@app.route("/api/dreams", methods=["GET", "POST", "DELETE"])
def dreams():
    dreams_file = "dreams.json"

    if request.method == "GET":
        if os.path.exists(dreams_file):
            with open(dreams_file, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        return jsonify([])

    elif request.method == "POST":
        data = request.json or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify([])

        dreams_list = []
        if os.path.exists(dreams_file):
            with open(dreams_file, "r", encoding="utf-8") as f:
                dreams_list = json.load(f)

        new_id = max([d.get("id", -1) for d in dreams_list] or [-1]) + 1
        dreams_list.append({"id": new_id, "text": text, "done": False})

        with open(dreams_file, "w", encoding="utf-8") as f:
            json.dump(dreams_list, f, ensure_ascii=False, indent=2)

        return jsonify(dreams_list)

    elif request.method == "DELETE":
        data = request.json or {}
        target_id = data.get("id")
        if target_id is None:
            return jsonify([])

        dreams_list = []
        if os.path.exists(dreams_file):
            with open(dreams_file, "r", encoding="utf-8") as f:
                dreams_list = json.load(f)

        dreams_list = [d for d in dreams_list if d.get("id") != target_id]

        with open(dreams_file, "w", encoding="utf-8") as f:
            json.dump(dreams_list, f, ensure_ascii=False, indent=2)

        return jsonify(dreams_list)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
