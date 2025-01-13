from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Database Model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # brand
    description = db.Column(db.String(100), nullable=False)  # model
    price = db.Column(db.Float, nullable=False)  # price


# Route untuk menampilkan data
@app.route('/')
def index():
    items = Item.query.all()
    return render_template('index.html', items=items)

# Route untuk menambahkan data
@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']

    if not price:
        flash("Price tidak boleh kosong!", "danger")
        return redirect(url_for('index'))

    try:
        price = float(price)  # Pastikan price dapat dikonversi menjadi angka
    except ValueError:
        flash("Price harus berupa angka!", "danger")
        return redirect(url_for('index'))

    new_item = Item(name=name, description=description, price=price)
    db.session.add(new_item)
    db.session.commit()
    flash("Data berhasil ditambahkan!", "success")
    return redirect(url_for('index'))


# Route untuk menghapus data
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    item = Item.query.get_or_404(id)  # Cari item berdasarkan ID
    try:
        db.session.delete(item)       # Hapus item dari database
        db.session.commit()           # Commit perubahan
        flash("Data berhasil dihapus!", "success")
    except Exception as e:
        db.session.rollback()         # Rollback jika terjadi error
        flash(f"Terjadi kesalahan: {e}", "danger")
    return redirect(url_for('index'))


# Route untuk mengedit data
@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id):
    item = Item.query.get_or_404(id)  # Cari item berdasarkan ID
    if request.method == 'POST':      # Jika form dikirim (update data)
        try:
            item.name = request.form['name']
            item.description = request.form['description']
            item.price = request.form['price']
            db.session.commit()  # Commit perubahan
            flash("Data berhasil diupdate!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()  # Rollback jika terjadi error
            flash(f"Terjadi kesalahan: {e}", "danger")
            return redirect(url_for('index'))
    return render_template('update.html', item=item)  # Render form update

# Route untuk mengimpor file CSV
@app.route('/import', methods=['POST', 'GET'])
def import_csv():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            # Simpan file di folder uploads
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            # Baca dan proses file CSV
            data = pd.read_csv(filepath)
            for _, row in data.iterrows():
                if pd.isna(row['price']):
                    flash(f"Baris dengan brand '{row['brand']}' tidak memiliki price. Diabaikan.", "warning")
                    continue
                try:
                    price = float(row['price'])
                except ValueError:
                    flash(f"Price untuk brand '{row['brand']}' tidak valid. Diabaikan.", "warning")
                    continue
                
                new_item = Item(name=row['brand'], description=row['model'], price=price)
                db.session.add(new_item)
            db.session.commit()
            flash("Data dari file CSV berhasil diimpor!", "success")
        else:
            flash("Harap unggah file CSV yang valid.", "danger")
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.template_filter('format_number')
def format_number(value):
    try:
        # Memformat angka dengan pemisah ribuan koma, lalu mengganti koma dengan titik
        return f"{value:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return value  # Jika terjadi kesalahan, kembalikan nilai asli




if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Membuat tabel database jika belum ada
    app.run(debug=True)