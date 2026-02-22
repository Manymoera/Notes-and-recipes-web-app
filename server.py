from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
import requests 
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    notes = db.relationship(
        "Note",
        backref="category",
        cascade="all, delete",
        passive_deletes=True
    )

class CategoryRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    recipes = db.relationship(
        "Recipe",
        backref="category",
        cascade="all, delete",
        passive_deletes=True
    )

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    image_url = db.Column(db.String(500))
    source_url = db.Column(db.String(500))

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category_recipe.id", ondelete="CASCADE"),
        nullable=True
    )

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id", ondelete="CASCADE")
    )

with app.app_context():
    db.create_all()

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

    next_page = request.form.get("next", "/")

    return redirect(next_page)

@app.route("/add_category_recipe", methods=["POST"])
def add_category_recipe():
    name = request.form.get("name")
    if name:
        category = CategoryRecipe(name=name)
        db.session.add(category)
        db.session.commit()
    
    next_page = request.form.get("next", "/recipes")
    return redirect(next_page)

@app.route("/delete_category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    Note.query.filter_by(category_id=category.id).delete()
    db.session.delete(category)
    db.session.commit()

    next_page = request.form.get("next", "/")

    return redirect(next_page)

@app.route("/delete_category_recipe/<int:category_id>", methods=["POST"])
def delete_category_recipe(category_id):
    category = CategoryRecipe.query.get_or_404(category_id)

    # удаляем все рецепты этой категории
    Recipe.query.filter_by(category_id=category.id).delete()
    db.session.delete(category)
    db.session.commit()
    
    next_page = request.form.get("next", "/recipes")
    return redirect(next_page)

@app.route("/delete_recipe/<int:recipe_id>", methods=["POST"])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()

    next_page = request.form.get("next", "/recipes")
    return redirect(next_page)

@app.route("/add_note", methods=["POST"])
def add_note():
    title = request.form.get("title")
    content = request.form.get("content")
    category_id = request.form.get("category_id")

    if category_id:
        category_id = int(category_id)
    else:
        category_id = None

    note = Note(
        title=title,
        content=content,
        category_id=category_id
    )

    db.session.add(note)
    db.session.commit()

    return redirect(request.form.get("next", "/"))

@app.route("/delete_note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/add_recipe", methods=["POST"])
def add_recipe():
    url = request.form.get("url")
    category_id = request.form.get("category_id")
    if category_id:
        category_id = int(category_id)
    else:
        category_id = None

    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        # название
        title = soup.title.string if soup.title else "Без названия"

        # изображение (og:image)
        image = soup.find("meta", property="og:image")
        image_url = image["content"] if image else ""

        new_recipe = Recipe(
            title=title,
            image_url=image_url,
            source_url=url,
            category_id=category_id
        )

        db.session.add(new_recipe)
        db.session.commit()

    except:
        pass

    return redirect(url_for("recipes"))

@app.route("/recipes")
def recipes():
    categories = CategoryRecipe.query.all()
    active_category = request.args.get("category", type=int)
    if active_category:
        recipes = Recipe.query.filter_by(category_id=active_category).all()
    else:
        recipes = Recipe.query.all()
    
    return render_template(
        "recipes.html",
        categories=categories,
        recipes=recipes,
        active_category=active_category
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)