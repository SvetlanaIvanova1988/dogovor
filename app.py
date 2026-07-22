import io
import os
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, session, send_file
from xhtml2pdf import pisa

app = Flask(__name__)
# Значения ниже задаются в переменных окружения Render, а не в коде
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
PIN_CODE = os.environ.get("PIN_CODE", "1234")


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("pin") == PIN_CODE:
            session["authorized"] = True
            return redirect(url_for("form"))
        return render_template("login.html", error="Неверный пин-код")
    return render_template("login.html", error=None)


@app.route("/form", methods=["GET"])
def form():
    if not session.get("authorized"):
        return redirect(url_for("login"))
    return render_template("form.html", today=date.today().strftime("%d.%m.%Y"))


@app.route("/generate", methods=["POST"])
def generate():
    if not session.get("authorized"):
        return redirect(url_for("login"))

    data = request.form

    names = request.form.getlist("item_name")
    units = request.form.getlist("item_unit")
    quantities = request.form.getlist("item_qty")
    prices = request.form.getlist("item_price")

    items = []
    total = 0
    for i in range(len(names)):
        if not names[i].strip():
            continue
        qty = float(quantities[i] or 0)
        price = float(prices[i] or 0)
        amount = qty * price
        total += amount
        items.append({
            "num": len(items) + 1,
            "name": names[i],
            "unit": units[i],
            "qty": qty,
            "price": price,
            "amount": amount,
        })

    advance_percent = float(data.get("advance_percent") or 50)

    html = render_template(
        "contract.html",
        contract_number=data.get("contract_number"),
        contract_date=data.get("contract_date"),
        city=data.get("city") or "Москва",
        supplier_name=data.get("supplier_name"),
        supplier_inn=data.get("supplier_inn"),
        supplier_ogrnip=data.get("supplier_ogrnip"),
        supplier_address=data.get("supplier_address"),
        supplier_bank=data.get("supplier_bank"),
        supplier_account=data.get("supplier_account"),
        buyer_name=data.get("buyer_name"),
        buyer_inn=data.get("buyer_inn"),
        buyer_address=data.get("buyer_address"),
        items=items,
        total=total,
        advance_percent=advance_percent,
        advance_amount=total * advance_percent / 100,
        delivery_days=data.get("delivery_days"),
    )

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)
    pdf_buffer.seek(0)

    filename = f"contract_{data.get('contract_number', 'draft')}.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True)
