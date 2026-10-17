from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

import db

app = FastAPI()
templates = Jinja2Templates(directory="templates")
db.init_db()

TOPICS = [
    "artificial intelligence", "technology", "business", "politics",
    "cricket", "football", "health", "science", "world news",
    "pakistan", "entertainment", "education", "finance", "climate",
]


def current_user(request: Request):
    uid = request.cookies.get("uid")
    if uid and uid.isdigit():
        return db.get_user(int(uid))
    return None


@app.get("/")
def home(request: Request):
    if current_user(request):
        return RedirectResponse("/paper")
    return RedirectResponse("/onboarding")


@app.get("/onboarding")
def onboarding(request: Request):
    return templates.TemplateResponse(request, "onboarding.html", {"topics": TOPICS})


@app.post("/onboarding")
def save_onboarding(
    name: str = Form(...),
    minutes: int = Form(10),
    topics: list[str] = Form(default=[]),
    extra: str = Form(""),
):
    weights = {t: 1.0 for t in topics}
    for kw in extra.split(","):
        kw = kw.strip().lower()
        if kw:
            weights[kw] = 0.8
    if not weights:
        weights = {"world news": 1.0}
    uid = db.create_user(name.strip() or "Reader", minutes, weights)
    resp = RedirectResponse("/paper", status_code=303)
    resp.set_cookie("uid", str(uid), max_age=60 * 60 * 24 * 365)
    return resp


@app.get("/paper")
def paper(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/onboarding")
    weights = db.get_weights(user["id"])
    return templates.TemplateResponse(
        request, "paper.html", {"user": user, "weights": weights}
    )


@app.get("/logout")
def logout():
    resp = RedirectResponse("/onboarding")
    resp.delete_cookie("uid")
    return resp