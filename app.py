import os
import secrets
import time
from functools import wraps

import pronotepy
from flask import Flask, Response, render_template, request

app = Flask(__name__)

CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "300"))
_cache = {}  # period name -> (timestamp, data)


def _login():
    url = os.environ["PRONOTE_URL"]
    user = os.environ["PRONOTE_USERNAME"]
    password = os.environ["PRONOTE_PASSWORD"]
    ent = os.environ.get("PRONOTE_ENT")  # e.g. "ac_lyon" -> pronotepy.ent.ac_lyon
    if ent:
        return pronotepy.Client(url, username=user, password=password,
                                ent=getattr(pronotepy.ent, ent))
    return pronotepy.Client(url, username=user, password=password)


def _num(value):
    """Convert Pronote values like '12,5' to float; None for 'Absent', etc."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _fetch(period_name=None):
    client = _login()
    if not client.logged_in:
        raise RuntimeError("Pronote login failed")

    periods = [p.name for p in client.periods]
    period = next((p for p in client.periods if p.name == period_name),
                  client.current_period)

    grades_by_subject = {}
    for g in period.grades:
        value, out_of = _num(g.grade), _num(g.out_of)
        grades_by_subject.setdefault(g.subject.name, []).append({
            "date": g.date.strftime("%d/%m/%Y") if g.date else "",
            "sort_date": g.date.isoformat() if g.date else "",
            "grade": g.grade,
            "out_of": g.out_of,
            "coefficient": g.coefficient,
            "class_average": g.average,
            "comment": g.comment,
            "value20": (value / out_of * 20) if value is not None and out_of else None,
        })

    subjects = []
    for avg in period.averages:
        name = avg.subject.name
        grades = sorted(grades_by_subject.get(name, []),
                        key=lambda x: x["sort_date"], reverse=True)
        subjects.append({
            "name": name,
            "average": _num(avg.student),
            "class_average": _num(avg.class_average),
            "min": _num(avg.min),
            "max": _num(avg.max),
            "grades": grades,
        })
    subjects.sort(key=lambda s: s["name"])

    valid = [s["average"] for s in subjects if s["average"] is not None]
    calculated = sum(valid) / len(valid) if valid else None

    return {
        "student": client.info.name,
        "period": period.name,
        "periods": periods,
        "subjects": subjects,
        "calculated_average": calculated,
        "pronote_average": _num(period.overall_average),
        "class_overall_average": _num(period.class_overall_average),
        "updated": time.strftime("%d/%m/%Y %H:%M"),
    }


def get_data(period_name=None):
    key = period_name or ""
    cached = _cache.get(key)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return cached[1]
    data = _fetch(period_name)
    _cache[key] = (time.time(), data)
    return data


def require_auth(f):
    """HTTP basic auth so your grades aren't public on your domain."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        expected = os.environ.get("APP_PASSWORD")
        if not expected:
            return Response("APP_PASSWORD is not set on the server.", 500)
        auth = request.authorization
        if not auth or not secrets.compare_digest(auth.password or "", expected):
            return Response("Login required", 401,
                            {"WWW-Authenticate": 'Basic realm="Pronote"'})
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
@require_auth
def index():
    try:
        data = get_data(request.args.get("period"))
    except Exception as e:  # show a readable error instead of a 500 page
        return render_template("index.html", error=str(e), data=None), 502
    return render_template("index.html", data=data, error=None)


@app.template_filter("fmt")
def fmt(value):
    return "–" if value is None else f"{value:.2f}".replace(".", ",")


if __name__ == "__main__":
    app.run(debug=True)
