import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import db
import edition

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


def show(request: Request, user, row):
    return templates.TemplateResponse(request, "paper.html", {
        "user": user,
        "ed": json.loads(row["data"]),
        "edition_id": row["id"],
        "edition_date": row["edition_date"],
    })


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
    row = db.get_edition_for_date(user["id"], str(date.today()))
    if not row:
        return RedirectResponse("/generate", status_code=303)
    return show(request, user, row)


@app.get("/generate")
def generate(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/onboarding")
    data = edition.build_edition(user)
    db.save_edition(user["id"], str(date.today()), data)
    return RedirectResponse("/paper", status_code=303)


@app.get("/edition/{eid}")
def old_edition(request: Request, eid: int):
    user = current_user(request)
    if not user:
        return RedirectResponse("/onboarding")
    row = db.get_edition_by_id(user["id"], eid)
    if not row:
        return RedirectResponse("/archive")
    return show(request, user, row)


@app.get("/edition/{eid}/pdf")
def edition_pdf(request: Request, eid: int):
    user = current_user(request)
    if not user:
        return RedirectResponse("/onboarding")
    row = db.get_edition_by_id(user["id"], eid)
    if not row:
        return RedirectResponse("/archive")

    weights = db.get_weights(user["id"])
    interests = ", ".join(sorted(weights, key=weights.get, reverse=True)[:4])
    html = templates.get_template("pdf.html").render({
        "user": user,
        "ed": json.loads(row["data"]),
        "edition_date": row["edition_date"],
        "interests": interests,
    })

    out = Path("pdfs")
    out.mkdir(exist_ok=True)
    html_path = out / f"edition_{eid}.html"
    pdf_path = out / f"edition_{eid}.pdf"
    html_path.write_text(html, encoding="utf-8")
    subprocess.run(
        [sys.executable, "make_pdf.py", str(html_path), str(pdf_path)], check=True
    )
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"morning-paper-{row['edition_date']}.pdf",
    )


@app.get("/archive")
def archive(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/onboarding")
    return templates.TemplateResponse(request, "archive.html", {
        "user": user,
        "editions": db.list_editions(user["id"]),
    })


@app.get("/logout")
def logout():
    resp = RedirectResponse("/onboarding")
    resp.delete_cookie("uid")
    return resp