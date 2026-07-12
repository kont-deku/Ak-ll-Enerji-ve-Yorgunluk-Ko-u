from flask import Flask, render_template, request, redirect, url_for, session, flash
import database

app = Flask(__name__)
app.secret_key = "bu-anahtari-degistirin-lutfen"  # NOT: teslimden önce farklı, gizli bir değerle değiştirin

DB_PATH = "database/energy.db"


# --- Oturum Denetimi ve Güvenlik Filtresi ---
@app.before_request
def check_user_session():
    database.init_db()
    allowed_routes = ['login', 'register', 'static']
    if request.endpoint and request.endpoint not in allowed_routes and 'user_id' not in session:
        flash("Lütfen önce giriş yapın.", "error")
        return redirect(url_for('login'))


# --- Kullanıcı Kayıt Sistemi ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        if not username or not password or not email:
            flash("Lütfen tüm alanları doldurun.", "error")
            return render_template("register.html")

        is_success = database.register_user(username, password, email)
        if is_success:
            flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
            return redirect(url_for("login"))
        else:
            flash("Bu kullanıcı adı zaten alınmış.", "error")
            return render_template("register.html")

    return render_template("register.html")


# --- Kullanıcı Oturum Açma Sistemi ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = database.login_user(username, password)

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Tekrar hoş geldin, {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Hatalı kullanıcı adı veya şifre.", "error")
            return render_template("login.html")

    return render_template("login.html")


# --- Kullanıcı Oturum Kapatma Sistemi ---
@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla çıkış yapıldı.", "success")
    return redirect(url_for("login"))


# --- Ana Sayfa: Günlük Veri Girişi Formu ---
@app.route("/")
def index():
    return render_template("index.html")


# --- Form Verisini Doğrulama Yardımcı Fonksiyonu ---
def _parse_form_data(form):
    errors = []
    try:
        sleep_hours = float(form.get("sleep_hours", 0))
        water_amount = float(form.get("water_amount", 0))
        phone_hours = float(form.get("phone_hours", 0))
        sport_status = int(form.get("sport_status", 0))
        mood = form.get("mood", "")

        if not mood:
            errors.append("Lütfen ruh halini seç.")
    except (TypeError, ValueError):
        errors.append("Lütfen tüm alanları doğru formatta doldur.")
        return {}, errors

    data = {
        "sleep_hours": sleep_hours,
        "water_amount": water_amount,
        "phone_hours": phone_hours,
        "sport_status": sport_status,
        "mood": mood,
    }
    return data, errors


# --- Basit Enerji Puanı Hesaplama ---
def _calculate_energy_score(data, previous=None):
    sleep_score = min(data["sleep_hours"] / 8, 1) * 30
    water_score = min(data["water_amount"] / 2.5, 1) * 20
    phone_score = max(0, 1 - data["phone_hours"] / 8) * 20
    sport_score = 15 if data["sport_status"] else 0

    mood_map = {
        "çok_iyi": 15, "iyi": 12, "normal": 8, "kötü": 4, "çok_kötü": 0
    }
    mood_score = mood_map.get(data["mood"], 8)

    total = round(sleep_score + water_score + phone_score + sport_score + mood_score)
    total = max(0, min(100, total))

    if total >= 80:
        level = "Enerjik"
    elif total >= 60:
        level = "Dengeli"
    elif total >= 40:
        level = "Yorgun"
    else:
        level = "Tükenmiş"

    return total, level


# --- Analiz ve Kayıt İşlemi ---
@app.route("/analiz", methods=["POST"])
def analyze():
    data, errors = _parse_form_data(request.form)
    if errors:
        for err in errors:
            flash(err, "error")
        return redirect(url_for("index"))

    previous = database.get_previous_entry(user_id=session['user_id'])
    energy_score, energy_level = _calculate_energy_score(data, previous)

    entry_id = database.save_entry(
        user_id=session['user_id'],
        sleep_hours=data["sleep_hours"],
        water_amount=data["water_amount"],
        phone_hours=data["phone_hours"],
        sport_status=data["sport_status"],
        mood=data["mood"],
        energy_score=energy_score,
        energy_level=energy_level
    )

    return redirect(url_for("result", entry_id=entry_id))


# --- Sonuç Sayfası ---
@app.route("/result/<int:entry_id>")
def result(entry_id):
    entry = database.get_entry(entry_id)
    if not entry or entry["user_id"] != session["user_id"]:
        flash("Böyle bir kayıt bulunamadı.", "error")
        return redirect(url_for("index"))

    previous = database.get_previous_entry(
        user_id=session["user_id"],
        before_date=entry["entry_date"]
    )

    return render_template(
        "result.html",
        entry=entry,
        recommendations=[],
        previous=previous
    )


if __name__ == "__main__":
    app.run(debug=True)
