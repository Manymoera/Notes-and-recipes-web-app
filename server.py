from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ======================
# МОДЕЛИ
# ======================

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    notes = db.relationship(
        "Note",
        backref="category",
        cascade="all, delete",
        passive_deletes=True
    )


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id", ondelete="CASCADE")
    )


# ======================
# СОЗДАНИЕ БД
# ======================

with app.app_context():
    db.create_all()


# ======================
# РОУТЫ
# ======================

@app.route("/")
def index():
    category_id = request.args.get("category")

    categories = Category.query.all()

    query = Note.query
    if category_id:
        query = query.filter_by(category_id=category_id)

    notes = query.all()

    return render_template(
        "index.html",
        categories=categories,
        notes=notes,
        active_category=category_id
    )


@app.route("/add_category", methods=["POST"])
def add_category():
    name = request.form.get("name")
    if name:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()

    return redirect(url_for("index"))

@app.route("/delete_category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    # 1️⃣ Удаляем все заметки этой категории
    Note.query.filter_by(category_id=category.id).delete()

    # 2️⃣ Удаляем саму категорию
    db.session.delete(category)

    db.session.commit()

    return redirect(url_for("index"))


@app.route("/add_note", methods=["POST"])
def add_note():
    title = request.form.get("title")
    content = request.form.get("content")
    category_id = request.form.get("category_id")

    note = Note(
        title=title,
        content=content,
        category_id=category_id if category_id else None
    )

    db.session.add(note)
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/recipes")
def recipes():
    return render_template("recipes.html")

# ======================
# ЗАПУСК
# ======================

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)