# Thêm các module cần thiết ở đầu file
import os
# Nhớ import jsonify ở đầu file
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
import mysql.connector
import hashlib
import random
import string
import csv # Thư viện xử lý file CSV
import io # Thư viện để đọc file upload như file text
from werkzeug.utils import secure_filename # Để xử lý tên file an toàn
from datetime import datetime, timedelta # Thư viện để xử lý thời gian
import json # Thư viện để xử lý dữ liệu cho biểu đồ
# Thêm uuid để tạo tên file duy nhất, tránh trùng lặp
import uuid 
# secure_filename đã có sẵn, kiểm tra lại
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key = 'day_la_khoa_bi_mat_cua_ban' # Nhớ thay đổi khóa này trong thực tế

# Cấu hình thư mục upload cho game ĐHBC
UPLOAD_FOLDER_DHBC = 'static/uploads/dhbc'
if not os.path.exists(UPLOAD_FOLDER_DHBC):
    os.makedirs(UPLOAD_FOLDER_DHBC)
app.config['UPLOAD_FOLDER_DHBC'] = UPLOAD_FOLDER_DHBC




# --- Cấu hình kết nối MySQL ---
def ket_noi_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "shuttle.proxy.rlwy.net"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "vrdBSgzRhtLjSRkEIjnPLKJTLWXebVym"),
        database=os.getenv("DB_NAME", "railway"),
        port=int(os.getenv("DB_PORT", 39810))
    )

# --- Hàm tiện ích: Tạo mã lớp ngẫu nhiên ---
def tao_ma_lop(length=6):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# --- Các route xác thực người dùng (Giữ nguyên) ---
@app.route('/')
def trang_chu():
    return redirect(url_for('dang_nhap'))

@app.route('/dang-nhap', methods=['GET', 'POST'])
def dang_nhap():
    if request.method == 'POST':
        ten_dang_nhap = request.form['ten_dang_nhap']
        mat_khau_chua_ma_hoa = request.form['mat_khau']
        mat_khau = hashlib.sha256(mat_khau_chua_ma_hoa.encode()).hexdigest()

        db = ket_noi_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM NguoiDung WHERE tenDangNhap = %s AND matKhau = %s", (ten_dang_nhap, mat_khau))
        nguoi_dung = cursor.fetchone()
        cursor.close()
        db.close()

        if nguoi_dung:
            session['da_dang_nhap'] = True
            session['id'] = nguoi_dung['id']
            session['ten_dang_nhap'] = nguoi_dung['tenDangNhap']
            session['ho_va_ten'] = nguoi_dung['hoVaTen']
            session['vai_tro'] = nguoi_dung['vaiTro']

            if nguoi_dung['vaiTro'] == 'GiaoVien':
                return redirect(url_for('trang_giao_vien'))
            else:
                return redirect(url_for('trang_hoc_sinh'))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng!", "error")
            
    return render_template('dang_nhap.html')

@app.route('/dang-ky', methods=['GET', 'POST'])
def dang_ky():
    if request.method == 'POST':
        ho_ten = request.form['ho_ten']
        ten_dang_nhap = request.form['ten_dang_nhap']
        email = request.form['email']
        mat_khau_chua_ma_hoa = request.form['mat_khau']
        gioi_tinh = request.form['gioi_tinh']
        vai_tro = request.form['vai_tro']
        mat_khau = hashlib.sha256(mat_khau_chua_ma_hoa.encode()).hexdigest()

        try:
            db = ket_noi_db()
            cursor = db.cursor()
            sql = "INSERT INTO NguoiDung (hoVaTen, tenDangNhap, email, matKhau, gioiTinh, vaiTro) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (ho_ten, ten_dang_nhap, email, mat_khau, gioi_tinh, vai_tro)
            cursor.execute(sql, val)
            db.commit()
            cursor.close()
            db.close()
            flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for('dang_nhap'))
        except mysql.connector.Error as err:
            # THAY ĐỔI Ở ĐÂY: Dùng render_template thay vì redirect
            flash("Lỗi: Tên đăng nhập hoặc email đã tồn tại!", "error")
            # Khi render_template, thông báo lỗi sẽ được hiển thị ngay trên trang đăng ký
            return render_template('dang_ky.html') 

    return render_template('dang_ky.html')

@app.route('/dang-xuat')
def dang_xuat():
    session.clear()
    return redirect(url_for('dang_nhap'))

# --- Các route của Giáo viên (Giữ nguyên) ---
@app.route('/giao-vien')
def trang_giao_vien():
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))
    
    id_giao_vien = session['id']
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM LopHoc WHERE idGiaoVien = %s ORDER BY ngayTao DESC", (id_giao_vien,))
    danh_sach_lop = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('trang_giao_vien.html', danh_sach_lop=danh_sach_lop)

@app.route('/tao-lop', methods=['POST'])
def tao_lop():
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    ten_lop = request.form['ten_lop']
    id_giao_vien = session['id']
    ma_lop = tao_ma_lop()

    db = ket_noi_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO LopHoc (tenLop, maLop, idGiaoVien) VALUES (%s, %s, %s)", (ten_lop, ma_lop, id_giao_vien))
    db.commit()
    cursor.close()
    db.close()
    
    flash(f"Đã tạo lớp '{ten_lop}' thành công!", "success")
    return redirect(url_for('trang_giao_vien'))

@app.route('/sua-lop/<int:id_lop>', methods=['POST'])
def sua_lop(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    ten_lop_moi = request.form['ten_lop_moi']
    id_giao_vien = session['id']

    db = ket_noi_db()
    cursor = db.cursor()
    cursor.execute("UPDATE LopHoc SET tenLop = %s WHERE id = %s AND idGiaoVien = %s", (ten_lop_moi, id_lop, id_giao_vien))
    db.commit()
    cursor.close()
    db.close()
    
    flash("Đã cập nhật tên lớp thành công.", "success")
    return redirect(url_for('trang_giao_vien'))

@app.route('/xoa-lop/<int:id_lop>', methods=['POST'])
def xoa_lop(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    id_giao_vien = session['id']

    db = ket_noi_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, id_giao_vien))
    db.commit()
    cursor.close()
    db.close()
    
    flash("Đã xóa lớp học.", "success")
    return redirect(url_for('trang_giao_vien'))

@app.route('/chi-tiet-lop/<int:id_lop>')
def chi_tiet_lop(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()
    cursor.close()
    db.close()

    if not lop_hoc:
        flash("Không tìm thấy lớp học hoặc bạn không có quyền truy cập.", "error")
        return redirect(url_for('trang_giao_vien'))
    
    return render_template('chi_tiet_lop.html', lop_hoc=lop_hoc)

# --- Các route quản lý học sinh (Phiên bản sửa lỗi và cải tiến) ---



# --- Các route quản lý học sinh (Phiên bản sửa lỗi KeyError) ---

@app.route('/lop/<int:id_lop>/quan-li-hoc-sinh', methods=['GET'])
def quan_li_hoc_sinh(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    # SỬA LỖI Ở ĐÂY: Dùng session['id']
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()

    if not lop_hoc:
        flash("Lớp học không tồn tại hoặc bạn không có quyền truy cập.", "error")
        return redirect(url_for('trang_giao_vien'))

    query = """
        SELECT nd.id, nd.hoVaTen, nd.tenDangNhap, nd.email, nd.gioiTinh
        FROM NguoiDung nd
        JOIN ThanhVienLop tvl ON nd.id = tvl.idHocSinh
        WHERE tvl.idLop = %s AND nd.vaiTro = 'HocSinh'
        ORDER BY nd.hoVaTen
    """
    cursor.execute(query, (id_lop,))
    danh_sach_hs = cursor.fetchall()
    
    cursor.close()
    db.close()

    return render_template('quan_li_hoc_sinh.html', lop_hoc=lop_hoc, danh_sach_hs=danh_sach_hs)

@app.route('/lop/<int:id_lop>/import-csv', methods=['POST'])
def import_csv(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    file = request.files.get('file_csv')
    if not file or file.filename == '':
        flash("Không có file nào được chọn", "error")
        return redirect(url_for('quan_li_hoc_sinh', id_lop=id_lop))

    if not file.filename.lower().endswith('.csv'):
        flash("Chỉ chấp nhận file định dạng .csv", "error")
        return redirect(url_for('quan_li_hoc_sinh', id_lop=id_lop))

    stream = io.TextIOWrapper(file.stream, 'utf-8')
    csv_reader = csv.reader(stream, delimiter=';')
    
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    so_hs_them_moi = 0
    so_hs_da_co = 0
    so_loi = 0
    
    next(csv_reader) # Bỏ qua dòng tiêu đề

    for row in csv_reader:
        try:
            # THAY ĐỔI 1: Đọc cột theo cấu trúc CSV mới
            ten_dang_nhap = row[0]
            mat_khau_chua_ma_hoa = row[1]
            ho_va_ten = row[2]  # Đọc thẳng cột họ và tên
            email = row[3]
            gioi_tinh = row[4]

            # THAY ĐỔI 2: (Nên có) Kiểm tra giá trị của cột giới tính
            # Đảm bảo giá trị hợp lệ ('Nam', 'Nu', 'Khac') trước khi thêm vào DB
            gioi_tinh_hop_le = gioi_tinh.capitalize() # Tự động viết hoa chữ cái đầu (nam -> Nam)
            if gioi_tinh_hop_le not in ['Nam', 'Nu']:
                so_loi += 1
                continue # Bỏ qua dòng này nếu giới tính không hợp lệ

            mat_khau_ma_hoa = hashlib.sha256(mat_khau_chua_ma_hoa.encode()).hexdigest()

            cursor.execute("SELECT id, vaiTro FROM NguoiDung WHERE tenDangNhap = %s OR email = %s", (ten_dang_nhap, email))
            nguoi_dung = cursor.fetchone()
            
            id_hoc_sinh = None
            if nguoi_dung:
                if nguoi_dung['vaiTro'] == 'GiaoVien':
                    so_loi += 1
                    continue

                id_hoc_sinh = nguoi_dung['id']
                so_hs_da_co += 1
            else:
                # THAY ĐỔI 3: Cập nhật lệnh INSERT để thêm `gioiTinh`
                cursor.execute("""
                    INSERT INTO NguoiDung (hoVaTen, tenDangNhap, email, matKhau, gioiTinh, vaiTro)
                    VALUES (%s, %s, %s, %s, %s, 'HocSinh')
                """, (ho_va_ten, ten_dang_nhap, email, mat_khau_ma_hoa, gioi_tinh_hop_le))
                db.commit()
                id_hoc_sinh = cursor.lastrowid
                so_hs_them_moi += 1

            if id_hoc_sinh:
                cursor.execute("INSERT IGNORE INTO ThanhVienLop (idHocSinh, idLop) VALUES (%s, %s)", (id_hoc_sinh, id_lop))
                db.commit()

        except IndexError:
            # Bắt lỗi nếu một dòng không đủ 5 cột
            so_loi += 1
            continue

    cursor.close()
    db.close()

    flash(f"Import hoàn tất! Thêm mới: {so_hs_them_moi}, Đã tồn tại: {so_hs_da_co}, Dòng bị lỗi/bỏ qua: {so_loi}", "success")
    return redirect(url_for('quan_li_hoc_sinh', id_lop=id_lop))

@app.route('/lop/<int:id_lop>/xoa-hoc-sinh/<int:id_hoc_sinh>', methods=['POST'])
def xoa_hoc_sinh_khoi_lop(id_lop, id_hoc_sinh):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))
    
    db = ket_noi_db()
    cursor = db.cursor()

    # SỬA LỖI Ở ĐÂY: Dùng session['id']
    cursor.execute("SELECT id FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_cua_giao_vien = cursor.fetchone()

    if lop_cua_giao_vien:
        cursor.execute("DELETE FROM ThanhVienLop WHERE idLop = %s AND idHocSinh = %s", (id_lop, id_hoc_sinh))
        db.commit()
        flash("Đã xóa học sinh khỏi lớp.", "success")
    else:
        flash("Bạn không có quyền thực hiện hành động này.", "error")

    cursor.close()
    db.close()
    
    return redirect(url_for('quan_li_hoc_sinh', id_lop=id_lop))

@app.route('/chinh-sua-hoc-sinh/<int:id_hoc_sinh>', methods=['POST'])
def chinh_sua_hoc_sinh(id_hoc_sinh):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))
        
    id_lop = request.form.get('id_lop')
    ho_va_ten = request.form.get('ho_va_ten')
    email = request.form.get('email')
    gioi_tinh = request.form.get('gioi_tinh') # Lấy thêm giới tính từ form
    
    db = ket_noi_db()
    cursor = db.cursor()

    # Kiểm tra quyền sở hữu (giữ nguyên)
    cursor.execute("""
        SELECT tvl.idHocSinh FROM ThanhVienLop tvl
        JOIN LopHoc lh ON tvl.idLop = lh.id
        WHERE tvl.idHocSinh = %s AND tvl.idLop = %s AND lh.idGiaoVien = %s
    """, (id_hoc_sinh, id_lop, session['id']))
    
    hoc_sinh_hop_le = cursor.fetchone()

    if not hoc_sinh_hop_le:
        flash("Bạn không có quyền chỉnh sửa thông tin học sinh này.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('quan_li_hoc_sinh', id_lop=id_lop))
    
    # Kiểm tra giá trị giới tính hợp lệ
    if gioi_tinh not in ['Nam', 'Nu']:
        flash("Giá trị giới tính không hợp lệ.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('quan_li_hoc_sinh', id_lop=id_lop))

    try:
        # Cập nhật câu lệnh UPDATE để thêm cả gioiTinh
        sql_query = "UPDATE NguoiDung SET hoVaTen = %s, email = %s, gioiTinh = %s WHERE id = %s"
        # Cập nhật tuple giá trị tương ứng
        values = (ho_va_ten, email, gioi_tinh, id_hoc_sinh)
        cursor.execute(sql_query, values)
        db.commit()
        flash("Cập nhật thông tin học sinh thành công!", "success")
    except mysql.connector.Error as err:
        flash(f"Lỗi: Email có thể đã tồn tại!", "error")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('quan_li_hoc_sinh', id_lop=id_lop))
# --- Các route tạo bài kiểm tra và trò chơi ---
@app.route('/lop/<int:id_lop>/tao-bai-kiem-tra')
def tao_bai_kiem_tra(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()
    cursor.close()
    db.close()

    if not lop_hoc:
        flash("Không tìm thấy lớp học hoặc bạn không có quyền truy cập.", "error")
        return redirect(url_for('trang_giao_vien'))

    return render_template('tao_bai_kiem_tra_hub.html', lop_hoc=lop_hoc)



# --- Các route con cho chức năng tạo bài kiểm tra ---
@app.route('/lop/<int:id_lop>/ngan-hang-cau-hoi')
def ngan_hang_cau_hoi(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))
    
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()
    cursor.close()
    db.close()

    if not lop_hoc:
        flash("Không tìm thấy lớp học.", "error")
        return redirect(url_for('trang_giao_vien'))

    return render_template('ngan_hang_cau_hoi_hub.html', lop_hoc=lop_hoc)

# Dán và thay thế hàm này trong file app.py của bạn
@app.route('/lop/<int:id_lop>/tao-bai-kiem-tra-moi', methods=['GET', 'POST'])
def tao_bai_kiem_tra_moi(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    id_giao_vien = session['id']
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        # Phần xử lý POST (lưu bài kiểm tra) không có gì thay đổi
        try:
            ten_bkt = request.form.get('ten_bai_kiem_tra')
            thong_tin_bkt = request.form.get('thong_tin_bai_kiem_tra')
            thoi_gian = int(request.form.get('thoi_gian_lam_bai'))
            mat_khau = request.form.get('mat_khau')
            so_lan_toi_da = int(request.form.get('so_lan_toi_da'))
            cac_id_cau_hoi = request.form.getlist('cau_hoi_ids')

            if not cac_id_cau_hoi:
                flash("Bạn phải chọn ít nhất một câu hỏi cho bài kiểm tra.", "error")
                return redirect(request.url)

            mat_khau_db = mat_khau if mat_khau else None
            sql_bkt = """
                INSERT INTO BaiKiemTra (tenBaiKiemTra, thongTin, thoiGianLamBai, matKhau, soLanLamBaiToiDa, idLop, idGiaoVien)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_bkt, (ten_bkt, thong_tin_bkt, thoi_gian, mat_khau_db, so_lan_toi_da, id_lop, id_giao_vien))
            id_bkt_moi = cursor.lastrowid

            sql_chitiet_bkt = "INSERT INTO ChiTietBaiKiemTra (idBaiKiemTra, idCauHoi, diem) VALUES (%s, %s, %s)"
            for id_ch in cac_id_cau_hoi:
                diem_cau_hoi = float(request.form.get(f'diem_cau_hoi_{id_ch}', 1.0))
                cursor.execute(sql_chitiet_bkt, (id_bkt_moi, int(id_ch), diem_cau_hoi))

            db.commit()
            flash(f"Đã tạo bài kiểm tra '{ten_bkt}' thành công!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Tạo bài kiểm tra thất bại: {e}", "error")
        finally:
            cursor.close()
            db.close()
        return redirect(url_for('danh_sach_bai_kiem_tra', id_lop=id_lop))

    # Xử lý GET request để hiển thị trang
    loai_cau_hoi_filter = request.args.get('loai', 'TatCa')
    form_data = {
        'ten_bai_kiem_tra': request.args.get('ten_bai_kiem_tra', ''),
        'thong_tin_bai_kiem_tra': request.args.get('thong_tin_bai_kiem_tra', ''),
        'thoi_gian_lam_bai': request.args.get('thoi_gian_lam_bai', '45'),
        'mat_khau': request.args.get('mat_khau', ''),
        'so_lan_toi_da': request.args.get('so_lan_toi_da', '1')
    }
    
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    if not lop_hoc:
        flash("Lớp học không tồn tại.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))

    # [CẬP NHẬT] Lấy thêm thông tin phương án trả lời
    params = [id_giao_vien]
    query_base = """
        SELECT 
            nhch.id, nhch.noiDung, nhch.loaiCauHoi,
            pa.noiDung AS phuongAnNoiDung, pa.laDapAnDung
        FROM NganHangCauHoi nhch
        LEFT JOIN PhuongAn pa ON nhch.id = pa.idCauHoi
        WHERE nhch.idGiaoVien = %s
    """
    if loai_cau_hoi_filter != 'TatCa':
        query_base += " AND nhch.loaiCauHoi = %s"
        params.append(loai_cau_hoi_filter)
    query_base += " ORDER BY nhch.ngayTao DESC, nhch.id, pa.id"
    
    cursor.execute(query_base, params)
    results = cursor.fetchall()
    
    # [CẬP NHẬT] Tái cấu trúc dữ liệu để nhóm các phương án vào câu hỏi
    cau_hoi_dict = {}
    for row in results:
        cau_hoi_id = row['id']
        if cau_hoi_id not in cau_hoi_dict:
            cau_hoi_dict[cau_hoi_id] = {'id': row['id'], 'noiDung': row['noiDung'], 'loaiCauHoi': row['loaiCauHoi'], 'phuongAn': []}
        if row['phuongAnNoiDung'] is not None:
            cau_hoi_dict[cau_hoi_id]['phuongAn'].append({'noiDung': row['phuongAnNoiDung'], 'laDapAnDung': row['laDapAnDung']})
    
    danh_sach_cau_hoi = list(cau_hoi_dict.values())
    cursor.close()
    db.close()
    
    return render_template('tao_bai_kiem_tra_moi.html', 
                           lop_hoc=lop_hoc, 
                           danh_sach_cau_hoi=danh_sach_cau_hoi,
                           loai_filter_hien_tai=loai_cau_hoi_filter,
                           form_data=form_data)
# [CẬP NHẬT] Biến hàm này thành hàm chức năng
@app.route('/lop/<int:id_lop>/danh-sach-bai-kiem-tra')
def danh_sach_bai_kiem_tra(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    if not lop_hoc:
        flash("Lớp học không tồn tại.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))
    
    # Lấy danh sách bài kiểm tra và đếm số câu hỏi
    query = """
        SELECT bkt.*, COUNT(ctbkt.idCauHoi) as soLuongCauHoi
        FROM BaiKiemTra bkt
        LEFT JOIN ChiTietBaiKiemTra ctbkt ON bkt.id = ctbkt.idBaiKiemTra
        WHERE bkt.idLop = %s AND bkt.idGiaoVien = %s
        GROUP BY bkt.id
        ORDER BY bkt.ngayTao DESC
    """
    cursor.execute(query, (id_lop, session['id']))
    danh_sach_bkt = cursor.fetchall()

    cursor.close()
    db.close()
    
    return render_template('danh_sach_bai_kiem_tra.html', lop_hoc=lop_hoc, danh_sach_bkt=danh_sach_bkt)

# [MỚI] Thêm route để xóa bài kiểm tra
@app.route('/xoa-bai-kiem-tra/<int:id_bkt>', methods=['POST'])
def xoa_bai_kiem_tra(id_bkt):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    id_lop = request.form.get('id_lop')
    
    db = ket_noi_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM BaiKiemTra WHERE id = %s AND idGiaoVien = %s", (id_bkt, session['id']))
    db.commit()
    cursor.close()
    db.close()

    flash("Đã xóa bài kiểm tra thành công.", "success")
    return redirect(url_for('danh_sach_bai_kiem_tra', id_lop=id_lop))

# [MỚI] Thêm route để sửa bài kiểm tra
# Dán và thay thế hàm này trong file app.py của bạn
# Dán và thay thế hàm này trong file app.py của bạn
@app.route('/lop/<int:id_lop>/sua-bai-kiem-tra/<int:id_bkt>', methods=['GET', 'POST'])
def sua_bai_kiem_tra(id_lop, id_bkt):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        # Phần xử lý POST không thay đổi
        try:
            ten_bkt = request.form.get('ten_bai_kiem_tra')
            thong_tin_bkt = request.form.get('thong_tin_bai_kiem_tra')
            thoi_gian = int(request.form.get('thoi_gian_lam_bai'))
            mat_khau = request.form.get('mat_khau')
            so_lan_toi_da = int(request.form.get('so_lan_toi_da'))
            cac_id_cau_hoi = request.form.getlist('cau_hoi_ids')

            if not cac_id_cau_hoi:
                flash("Bạn phải chọn ít nhất một câu hỏi cho bài kiểm tra.", "error")
                return redirect(request.url)

            mat_khau_db = mat_khau if mat_khau else None
            sql_update_bkt = """
                UPDATE BaiKiemTra SET tenBaiKiemTra=%s, thongTin=%s, thoiGianLamBai=%s, matKhau=%s, soLanLamBaiToiDa=%s
                WHERE id=%s AND idGiaoVien=%s
            """
            cursor.execute(sql_update_bkt, (ten_bkt, thong_tin_bkt, thoi_gian, mat_khau_db, so_lan_toi_da, id_bkt, session['id']))
            cursor.execute("DELETE FROM ChiTietBaiKiemTra WHERE idBaiKiemTra = %s", (id_bkt,))
            sql_chitiet_bkt = "INSERT INTO ChiTietBaiKiemTra (idBaiKiemTra, idCauHoi, diem) VALUES (%s, %s, %s)"
            for id_ch in cac_id_cau_hoi:
                diem_cau_hoi = float(request.form.get(f'diem_cau_hoi_{id_ch}', 1.0))
                cursor.execute(sql_chitiet_bkt, (id_bkt, int(id_ch), diem_cau_hoi))
            db.commit()
            flash("Cập nhật bài kiểm tra thành công!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Cập nhật thất bại: {e}", "error")
        finally:
            cursor.close()
            db.close()
        return redirect(url_for('danh_sach_bai_kiem_tra', id_lop=id_lop))

    # Xử lý GET: Lấy thông tin để điền vào form
    loai_filter_hien_tai = request.args.get('loai', 'TatCa')
    
    cursor.execute("SELECT * FROM BaiKiemTra WHERE id = %s AND idGiaoVien = %s", (id_bkt, session['id']))
    bai_kiem_tra_db = cursor.fetchone()
    if not bai_kiem_tra_db:
        flash("Bài kiểm tra không tồn tại.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('danh_sach_bai_kiem_tra', id_lop=id_lop))

    # [CẬP NHẬT] Lấy dữ liệu từ URL nếu có, nếu không thì lấy từ DB
    # Logic này sẽ ưu tiên dữ liệu người dùng vừa nhập khi chuyển bộ lọc
    bai_kiem_tra = {
        'tenBaiKiemTra': request.args.get('ten_bai_kiem_tra', bai_kiem_tra_db['tenBaiKiemTra']),
        'thongTin': request.args.get('thong_tin_bai_kiem_tra', bai_kiem_tra_db['thongTin']),
        'thoiGianLamBai': request.args.get('thoi_gian_lam_bai', bai_kiem_tra_db['thoiGianLamBai']),
        'matKhau': request.args.get('mat_khau', bai_kiem_tra_db['matKhau']),
        'soLanLamBaiToiDa': request.args.get('so_lan_toi_da', bai_kiem_tra_db['soLanLamBaiToiDa']),
        'id': bai_kiem_tra_db['id'] # Giữ lại id để dùng trong form action
    }

    cursor.execute("SELECT idCauHoi, diem FROM ChiTietBaiKiemTra WHERE idBaiKiemTra = %s", (id_bkt,))
    cau_hoi_da_chon_rows = cursor.fetchall()
    cau_hoi_da_chon = {row['idCauHoi']: row['diem'] for row in cau_hoi_da_chon_rows}

    # Lấy toàn bộ câu hỏi KÈM phương án trong ngân hàng
    params = [session['id']]
    query_base = """
        SELECT nhch.id, nhch.noiDung, nhch.loaiCauHoi, pa.noiDung AS phuongAnNoiDung, pa.laDapAnDung
        FROM NganHangCauHoi nhch LEFT JOIN PhuongAn pa ON nhch.id = pa.idCauHoi
        WHERE nhch.idGiaoVien = %s
    """
    if loai_filter_hien_tai != 'TatCa':
        query_base += " AND nhch.loaiCauHoi = %s"
        params.append(loai_filter_hien_tai)
    query_base += " ORDER BY nhch.ngayTao DESC, nhch.id, pa.id"
    cursor.execute(query_base, params)
    results = cursor.fetchall()

    cau_hoi_dict = {}
    for row in results:
        cau_hoi_id = row['id']
        if cau_hoi_id not in cau_hoi_dict:
            cau_hoi_dict[cau_hoi_id] = {'id': row['id'], 'noiDung': row['noiDung'], 'loaiCauHoi': row['loaiCauHoi'], 'phuongAn': []}
        if row['phuongAnNoiDung'] is not None:
            cau_hoi_dict[cau_hoi_id]['phuongAn'].append({'noiDung': row['phuongAnNoiDung'], 'laDapAnDung': row['laDapAnDung']})
    
    danh_sach_cau_hoi = list(cau_hoi_dict.values())
    
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('sua_bai_kiem_tra.html', 
                           lop_hoc=lop_hoc, 
                           bai_kiem_tra=bai_kiem_tra,
                           danh_sach_cau_hoi=danh_sach_cau_hoi,
                           cau_hoi_da_chon=cau_hoi_da_chon,
                           loai_filter_hien_tai=loai_filter_hien_tai)
# TÌM VÀ THAY THẾ TOÀN BỘ HÀM NÀY TRONG app.py

@app.route('/lop/<int:id_lop>/thong-ke-ket-qua/<int:id_bkt>')
def thong_ke_ket_qua(id_lop, id_bkt):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    cursor.execute("SELECT * FROM BaiKiemTra WHERE id = %s", (id_bkt,))
    bai_kiem_tra = cursor.fetchone()

    if not lop_hoc or not bai_kiem_tra:
        flash("Không tìm thấy thông tin hợp lệ.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('danh_sach_bai_kiem_tra', id_lop=id_lop))

    # [CẬP NHẬT] Thêm kq.thoiGianBatDau vào câu truy vấn
    query = """
        SELECT kq.diemSo, kq.thoiGianNopBai, kq.thoiGianBatDau, nd.hoVaTen
        FROM KetQuaBaiKiemTra kq
        LEFT JOIN NguoiDung nd ON kq.idHocSinh = nd.id
        WHERE kq.idBaiKiemTra = %s
        ORDER BY kq.diemSo DESC
    """
    cursor.execute(query, (id_bkt,))
    danh_sach_ket_qua = cursor.fetchall()

    # [THÊM MỚI] Tính toán thời gian làm bài cho mỗi học sinh
    for kq in danh_sach_ket_qua:
        if kq['thoiGianNopBai'] and kq['thoiGianBatDau']:
            thoi_gian_lam = kq['thoiGianNopBai'] - kq['thoiGianBatDau']
            kq['thoiGianLamBai'] = int(thoi_gian_lam.total_seconds())
        else:
            kq['thoiGianLamBai'] = None

    # ... phần xử lý dữ liệu thống kê khác giữ nguyên ...
    tong_diem = 0
    diem_cao_nhat = 0
    diem_thap_nhat = 10 
    labels = [f"{i}-{i+1}" for i in range(10)]
    labels[-1] = "9-10"
    data = [0] * 10 

    if danh_sach_ket_qua:
        ket_qua_hop_le = [kq for kq in danh_sach_ket_qua if kq['diemSo'] is not None]
        if ket_qua_hop_le:
            diem_thap_nhat = ket_qua_hop_le[-1]['diemSo']
            for kq in ket_qua_hop_le:
                diem = kq['diemSo']
                tong_diem += diem
                if diem > diem_cao_nhat:
                    diem_cao_nhat = diem
                
                if diem == 10:
                    data[9] += 1
                else:
                    index = int(diem)
                    data[index] += 1
            
            diem_trung_binh = tong_diem / len(ket_qua_hop_le)
        else:
             diem_trung_binh = 0
             diem_thap_nhat = 0
    else:
        diem_trung_binh = 0
        diem_thap_nhat = 0

    cursor.close()
    db.close()

    return render_template('thong_ke_ket_qua.html', 
                           lop_hoc=lop_hoc, 
                           bai_kiem_tra=bai_kiem_tra,
                           danh_sach_ket_qua=danh_sach_ket_qua,
                           diem_trung_binh=diem_trung_binh,
                           diem_cao_nhat=diem_cao_nhat,
                           diem_thap_nhat=diem_thap_nhat,
                           chart_labels=json.dumps(labels),
                           chart_data=json.dumps(data))
# --- Các route con cho Ngân hàng câu hỏi (Giữ nguyên) ---
@app.route('/lop/<int:id_lop>/nhap-cau-hoi-thu-cong', methods=['GET', 'POST'])
def nhap_cau_hoi_thu_cong(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()
    
    if not lop_hoc:
        flash("Không tìm thấy lớp học.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))

    if request.method == 'POST':
        try:
            # Lấy dữ liệu chung
            noi_dung_cau_hoi = request.form.get('noi_dung_cau_hoi')
            loai_cau_hoi = request.form.get('loai_cau_hoi')
            id_giao_vien = session['id']

            # 1. Thêm câu hỏi vào bảng NganHangCauHoi
            sql_cau_hoi = "INSERT INTO NganHangCauHoi (noiDung, loaiCauHoi, idGiaoVien) VALUES (%s, %s, %s)"
            cursor.execute(sql_cau_hoi, (noi_dung_cau_hoi, loai_cau_hoi, id_giao_vien))
            id_cau_hoi_moi = cursor.lastrowid # Lấy ID của câu hỏi vừa tạo

            # 2. Thêm các phương án trả lời tùy theo loại câu hỏi
            sql_phuong_an = "INSERT INTO PhuongAn (idCauHoi, noiDung, laDapAnDung) VALUES (%s, %s, %s)"

            if loai_cau_hoi == 'TracNghiem':
                dap_an_dung = request.form.get('dap_an_dung_tn') # vd: 'pa_1'
                for i in range(1, 5):
                    noi_dung_pa = request.form.get(f'phuong_an_{i}')
                    la_dap_an_dung = (f'pa_{i}' == dap_an_dung)
                    cursor.execute(sql_phuong_an, (id_cau_hoi_moi, noi_dung_pa, la_dap_an_dung))
            
            elif loai_cau_hoi == 'DungSaiNhieuY':
                for i in range(1, 5):
                    noi_dung_y = request.form.get(f'y_{i}')
                    dap_an_y = request.form.get(f'dap_an_y_{i}') # 'Dung' hoặc 'Sai'
                    la_dap_an_dung = (dap_an_y == 'Dung')
                    cursor.execute(sql_phuong_an, (id_cau_hoi_moi, noi_dung_y, la_dap_an_dung))

            elif loai_cau_hoi == 'TraLoiNgan':
                dap_an_ngan = request.form.get('dap_an_ngan')
                cursor.execute(sql_phuong_an, (id_cau_hoi_moi, dap_an_ngan, True))

            db.commit()
            flash("Tạo câu hỏi mới thành công!", "success")
        except Exception as e:
            db.rollback() # Hoàn tác nếu có lỗi
            flash(f"Đã xảy ra lỗi: {e}", "error")

        cursor.close()
        db.close()
        return redirect(url_for('nhap_cau_hoi_thu_cong', id_lop=id_lop))

    # Nếu là GET request, chỉ hiển thị trang
    cursor.close()
    db.close()
    return render_template('nhap_cau_hoi_thu_cong.html', lop_hoc=lop_hoc)

@app.route('/lop/<int:id_lop>/nhap-cau-hoi-tu-dong', methods=['GET', 'POST'])
def nhap_cau_hoi_tu_dong(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()
    
    if not lop_hoc:
        flash("Không tìm thấy lớp học.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))

    if request.method == 'POST':
        file = request.files.get('file_txt')
        if not file or file.filename == '':
            flash("Bạn chưa chọn file nào.", "error")
            return redirect(request.url)

        if not file.filename.lower().endswith('.txt'):
            flash("Chỉ chấp nhận file định dạng .txt", "error")
            return redirect(request.url)

        try:
            content = file.stream.read().decode("utf-8")
            normalized_content = content.replace('\r\n', '\n')
            cau_hoi_blocks = normalized_content.strip().split('\n\n')
            
            so_cau_hoi_them = 0
            id_giao_vien = session['id']

            for block in cau_hoi_blocks:
                lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
                if not lines: continue

                loai_cau_hoi = 'TracNghiem' # Mặc định
                if lines[0].upper().startswith('TYPE:'):
                    type_text = lines[0][5:].strip()
                    if type_text in ['DungSaiNhieuY', 'TraLoiNgan']:
                        loai_cau_hoi = type_text
                    lines.pop(0) # Xóa dòng TYPE: khỏi danh sách

                # --- Xử lý câu hỏi Trắc Nghiệm ---
                if loai_cau_hoi == 'TracNghiem' and len(lines) == 6:
                    noi_dung_cau_hoi, pa_a, pa_b, pa_c, pa_d, answer_line = lines
                    sql_cau_hoi = "INSERT INTO NganHangCauHoi (noiDung, loaiCauHoi, idGiaoVien) VALUES (%s, 'TracNghiem', %s)"
                    cursor.execute(sql_cau_hoi, (noi_dung_cau_hoi, id_giao_vien))
                    id_cau_hoi_moi = cursor.lastrowid
                    
                    dap_an_text = answer_line[8:].upper().strip()
                    phuong_an_list = [pa_a[3:], pa_b[3:], pa_c[3:], pa_d[3:]]
                    dap_an_dung_index = ['A', 'B', 'C', 'D'].index(dap_an_text)
                    
                    sql_phuong_an = "INSERT INTO PhuongAn (idCauHoi, noiDung, laDapAnDung) VALUES (%s, %s, %s)"
                    for i, pa_noi_dung in enumerate(phuong_an_list):
                        cursor.execute(sql_phuong_an, (id_cau_hoi_moi, pa_noi_dung, i == dap_an_dung_index))
                    so_cau_hoi_them += 1

                # --- Xử lý câu hỏi Trả Lời Ngắn ---
                elif loai_cau_hoi == 'TraLoiNgan' and len(lines) == 2:
                    noi_dung_cau_hoi, answer_line = lines
                    sql_cau_hoi = "INSERT INTO NganHangCauHoi (noiDung, loaiCauHoi, idGiaoVien) VALUES (%s, 'TraLoiNgan', %s)"
                    cursor.execute(sql_cau_hoi, (noi_dung_cau_hoi, id_giao_vien))
                    id_cau_hoi_moi = cursor.lastrowid

                    dap_an_ngan = answer_line[8:].strip()
                    cursor.execute("INSERT INTO PhuongAn (idCauHoi, noiDung, laDapAnDung) VALUES (%s, %s, %s)",
                                   (id_cau_hoi_moi, dap_an_ngan, True))
                    so_cau_hoi_them += 1

                # --- Xử lý câu hỏi Đúng/Sai nhiều ý ---
                elif loai_cau_hoi == 'DungSaiNhieuY' and len(lines) == 6:
                    noi_dung_cau_hoi, y1, y2, y3, y4, answer_line = lines
                    sql_cau_hoi = "INSERT INTO NganHangCauHoi (noiDung, loaiCauHoi, idGiaoVien) VALUES (%s, 'DungSaiNhieuY', %s)"
                    cursor.execute(sql_cau_hoi, (noi_dung_cau_hoi, id_giao_vien))
                    id_cau_hoi_moi = cursor.lastrowid

                    cac_y = [y1, y2, y3, y4]
                    dap_an_list = [dap_an.strip().upper() for dap_an in answer_line[8:].split(',')]

                    if len(dap_an_list) == 4:
                        for i, noi_dung_y in enumerate(cac_y):
                            la_dap_an_dung = (dap_an_list[i] == 'D')
                            cursor.execute("INSERT INTO PhuongAn (idCauHoi, noiDung, laDapAnDung) VALUES (%s, %s, %s)",
                                           (id_cau_hoi_moi, noi_dung_y, la_dap_an_dung))
                        so_cau_hoi_them += 1
            
            db.commit()
            flash(f"Import thành công! Đã thêm {so_cau_hoi_them} câu hỏi mới vào ngân hàng.", "success")

        except Exception as e:
            db.rollback()
            flash(f"Đã xảy ra lỗi khi xử lý file: {e}", "error")

        cursor.close()
        db.close()
        return redirect(url_for('nhap_cau_hoi_tu_dong', id_lop=id_lop))

    cursor.close()
    db.close()
    return render_template('nhap_cau_hoi_tu_dong.html', lop_hoc=lop_hoc)
@app.route('/lop/<int:id_lop>/xem-cau-hoi-da-tao')
def xem_cau_hoi_da_tao(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    loai_cau_hoi_filter = request.args.get('loai', 'TatCa')
    
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()
    if not lop_hoc:
        flash("Không tìm thấy lớp học.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))

    id_giao_vien = session['id']
    
    params = [id_giao_vien]
    query_base = """
        SELECT 
            nhch.id, nhch.noiDung, nhch.loaiCauHoi,
            pa.noiDung AS phuongAnNoiDung, pa.laDapAnDung
        FROM NganHangCauHoi nhch
        LEFT JOIN PhuongAn pa ON nhch.id = pa.idCauHoi
        WHERE nhch.idGiaoVien = %s
    """
    if loai_cau_hoi_filter != 'TatCa':
        query_base += " AND nhch.loaiCauHoi = %s"
        params.append(loai_cau_hoi_filter)
    
    query_base += " ORDER BY nhch.ngayTao DESC, nhch.id, pa.id"
    
    cursor.execute(query_base, params)
    results = cursor.fetchall()
    
    cau_hoi_dict = {}
    for row in results:
        cau_hoi_id = row['id']
        if cau_hoi_id not in cau_hoi_dict:
            cau_hoi_dict[cau_hoi_id] = {'id': row['id'], 'noiDung': row['noiDung'], 'loaiCauHoi': row['loaiCauHoi'], 'phuongAn': []}
        if row['phuongAnNoiDung'] is not None:
            cau_hoi_dict[cau_hoi_id]['phuongAn'].append({'noiDung': row['phuongAnNoiDung'], 'laDapAnDung': row['laDapAnDung']})
    
    danh_sach_cau_hoi = list(cau_hoi_dict.values())
    cursor.close()
    db.close()

    return render_template('xem_cau_hoi_da_tao.html', lop_hoc=lop_hoc, danh_sach_cau_hoi=danh_sach_cau_hoi, loai_filter_hien_tai=loai_cau_hoi_filter)
# [MỚI] Route để xóa câu hỏi (giữ nguyên)
@app.route('/xoa-cau-hoi/<int:id_cau_hoi>', methods=['POST'])
def xoa_cau_hoi(id_cau_hoi):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    id_lop = request.form.get('id_lop')
    id_giao_vien = session['id']

    db = ket_noi_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM NganHangCauHoi WHERE id = %s AND idGiaoVien = %s", (id_cau_hoi, id_giao_vien))
    db.commit()
    
    cursor.close()
    db.close()
    
    flash("Đã xóa câu hỏi thành công.", "success")
    return redirect(url_for('xem_cau_hoi_da_tao', id_lop=id_lop))
@app.route('/lop/<int:id_lop>/sua-cau-hoi/<int:id_cau_hoi>', methods=['GET', 'POST'])
def sua_cau_hoi(id_lop, id_cau_hoi):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            noi_dung_cau_hoi = request.form.get('noi_dung_cau_hoi')
            
            # 1. Cập nhật nội dung câu hỏi chính
            cursor.execute("UPDATE NganHangCauHoi SET noiDung = %s WHERE id = %s AND idGiaoVien = %s", 
                           (noi_dung_cau_hoi, id_cau_hoi, session['id']))

            # 2. Xóa các phương án cũ
            cursor.execute("DELETE FROM PhuongAn WHERE idCauHoi = %s", (id_cau_hoi,))

            # 3. Thêm lại các phương án mới (giống logic của trang tạo)
            loai_cau_hoi = request.form.get('loai_cau_hoi') # Lấy từ input ẩn
            sql_phuong_an = "INSERT INTO PhuongAn (idCauHoi, noiDung, laDapAnDung) VALUES (%s, %s, %s)"

            if loai_cau_hoi == 'TracNghiem':
                dap_an_dung = request.form.get('dap_an_dung_tn')
                for i in range(1, 5):
                    noi_dung_pa = request.form.get(f'phuong_an_{i}')
                    la_dap_an_dung = (f'pa_{i}' == dap_an_dung)
                    cursor.execute(sql_phuong_an, (id_cau_hoi, noi_dung_pa, la_dap_an_dung))
            
            elif loai_cau_hoi == 'DungSaiNhieuY':
                for i in range(1, 5):
                    noi_dung_y = request.form.get(f'y_{i}')
                    dap_an_y = request.form.get(f'dap_an_y_{i}')
                    la_dap_an_dung = (dap_an_y == 'Dung')
                    cursor.execute(sql_phuong_an, (id_cau_hoi, noi_dung_y, la_dap_an_dung))

            elif loai_cau_hoi == 'TraLoiNgan':
                dap_an_ngan = request.form.get('dap_an_ngan')
                cursor.execute(sql_phuong_an, (id_cau_hoi, dap_an_ngan, True))

            db.commit()
            flash("Cập nhật câu hỏi thành công!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Lỗi khi cập nhật: {e}", "error")
        
        cursor.close()
        db.close()
        return redirect(url_for('xem_cau_hoi_da_tao', id_lop=id_lop))
        
    # Xử lý GET request: Lấy thông tin câu hỏi để điền vào form
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    
    cursor.execute("SELECT * FROM NganHangCauHoi WHERE id = %s AND idGiaoVien = %s", (id_cau_hoi, session['id']))
    cau_hoi = cursor.fetchone()
    
    if not cau_hoi or not lop_hoc:
        flash("Không tìm thấy câu hỏi hoặc lớp học.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))

    cursor.execute("SELECT * FROM PhuongAn WHERE idCauHoi = %s ORDER BY id", (id_cau_hoi,))
    phuong_an = cursor.fetchall()
    cau_hoi['phuongAn'] = phuong_an
    
    cursor.close()
    db.close()
    
    return render_template('sua_cau_hoi.html', lop_hoc=lop_hoc, cau_hoi=cau_hoi)
# [CẬP NHẬT & MỚI] Các route của Học sinh
@app.route('/hoc-sinh')
def trang_hoc_sinh():
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))

    id_hoc_sinh = session['id']
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT lh.id, lh.tenLop, nd.hoVaTen as tenGiaoVien
        FROM LopHoc lh
        JOIN ThanhVienLop tvl ON lh.id = tvl.idLop
        JOIN NguoiDung nd ON lh.idGiaoVien = nd.id
        WHERE tvl.idHocSinh = %s
    """
    cursor.execute(query, (id_hoc_sinh,))
    danh_sach_lop = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('trang_hoc_sinh.html', danh_sach_lop=danh_sach_lop)

@app.route('/tham-gia-lop', methods=['POST'])
def tham_gia_lop():
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))

    ma_lop = request.form.get('ma_lop')
    id_hoc_sinh = session['id']
    
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id FROM LopHoc WHERE maLop = %s", (ma_lop,))
        lop_hoc = cursor.fetchone()

        if lop_hoc:
            id_lop = lop_hoc['id']
            cursor.execute("INSERT INTO ThanhVienLop (idHocSinh, idLop) VALUES (%s, %s)", (id_hoc_sinh, id_lop))
            db.commit()
            flash("Tham gia lớp học thành công!", "success")
        else:
            flash("Mã lớp không tồn tại.", "error")

    except mysql.connector.Error as err:
        db.rollback()
        flash("Bạn đã ở trong lớp học này rồi.", "warning")
    
    cursor.close()
    db.close()
    return redirect(url_for('trang_hoc_sinh'))

@app.route('/lop-hoc-sinh/<int:id_lop>')
def chi_tiet_lop_hoc_sinh(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))
    
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT lh.id, lh.tenLop, nd.hoVaTen as tenGiaoVien
        FROM LopHoc lh
        JOIN NguoiDung nd ON lh.idGiaoVien = nd.id
        WHERE lh.id = %s
    """
    cursor.execute(query, (id_lop,))
    lop_hoc = cursor.fetchone()

    cursor.close()
    db.close()

    if not lop_hoc:
        return redirect(url_for('trang_hoc_sinh'))

    return render_template('chi_tiet_lop_hoc_sinh.html', lop_hoc=lop_hoc)

@app.route('/lop-hoc-sinh/<int:id_lop>/lam-bai-kiem-tra')
def lam_bai_kiem_tra(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))
    
    id_hoc_sinh = session['id']
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    if not lop_hoc:
        cursor.close()
        db.close()
        return redirect(url_for('trang_hoc_sinh'))

    query = """
        SELECT 
            bkt.*,
            (SELECT COUNT(*) FROM KetQuaBaiKiemTra kq WHERE kq.idBaiKiemTra = bkt.id AND kq.idHocSinh = %s) as soLanDaLam
        FROM BaiKiemTra bkt
        WHERE bkt.idLop = %s
        ORDER BY bkt.ngayTao DESC
    """
    cursor.execute(query, (id_hoc_sinh, id_lop))
    danh_sach_bkt = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('danh_sach_bai_kiem_tra_hoc_sinh.html', lop_hoc=lop_hoc, danh_sach_bkt=danh_sach_bkt)
@app.route('/lop-hoc-sinh/<int:id_lop>/bat-dau-kiem-tra/<int:id_bkt>', methods=['GET', 'POST'])
def bat_dau_kiem_tra(id_lop, id_bkt):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM BaiKiemTra WHERE id = %s", (id_bkt,))
    bai_kiem_tra = cursor.fetchone()
    
    if not bai_kiem_tra:
        flash("Bài kiểm tra không tồn tại.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('lam_bai_kiem_tra', id_lop=id_lop))

    if request.method == 'POST':
        if bai_kiem_tra['matKhau']:
            mat_khau_nhap = request.form.get('mat_khau')
            if mat_khau_nhap != bai_kiem_tra['matKhau']:
                flash("Mật khẩu không chính xác!", "error")
                return redirect(request.url)
        
        return redirect(url_for('lam_bai_trac_nghiem', id_lop=id_lop, id_bkt=id_bkt))

    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    cursor.close()
    db.close()
    
    return render_template('bat_dau_kiem_tra.html', lop_hoc=lop_hoc, bai_kiem_tra=bai_kiem_tra)

@app.route('/lop-hoc-sinh/<int:id_lop>/lam-bai/<int:id_bkt>')
def lam_bai_trac_nghiem(id_lop, id_bkt):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM BaiKiemTra WHERE id = %s", (id_bkt,))
    bai_kiem_tra = cursor.fetchone()

    query = """
        SELECT nhch.id, nhch.noiDung, nhch.loaiCauHoi, pa.id as idPhuongAn, pa.noiDung as phuongAnNoiDung
        FROM ChiTietBaiKiemTra ctbkt
        JOIN NganHangCauHoi nhch ON ctbkt.idCauHoi = nhch.id
        LEFT JOIN PhuongAn pa ON nhch.id = pa.idCauHoi
        WHERE ctbkt.idBaiKiemTra = %s
        ORDER BY RAND() 
    """ 
    cursor.execute(query, (id_bkt,))
    results = cursor.fetchall()
    
    cau_hoi_dict = {}
    for row in results:
        cau_hoi_id = row['id']
        if cau_hoi_id not in cau_hoi_dict:
            cau_hoi_dict[cau_hoi_id] = {
                'id': row['id'],
                'noiDung': row['noiDung'],
                'loaiCauHoi': row['loaiCauHoi'],
                'phuongAn': []
            }
        if row['idPhuongAn'] is not None:
            cau_hoi_dict[cau_hoi_id]['phuongAn'].append({
                'id': row['idPhuongAn'],
                'noiDung': row['phuongAnNoiDung']
            })

    danh_sach_cau_hoi = list(cau_hoi_dict.values())
    
    thoi_gian_bat_dau = datetime.now()
    sql_ketqua = "INSERT INTO KetQuaBaiKiemTra (idBaiKiemTra, idHocSinh, diemSo, thoiGianBatDau) VALUES (%s, %s, 0, %s)"
    cursor.execute(sql_ketqua, (id_bkt, session['id'], thoi_gian_bat_dau))
    id_ket_qua = cursor.lastrowid
    db.commit()

    cursor.close()
    db.close()

    return render_template('lam_bai_trac_nghiem.html', 
                           bai_kiem_tra=bai_kiem_tra,
                           danh_sach_cau_hoi=danh_sach_cau_hoi,
                           id_ket_qua=id_ket_qua,
                           id_lop=id_lop)

@app.route('/nop-bai', methods=['POST'])
def nop_bai():
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))

    try:
        id_ket_qua = request.form.get('id_ket_qua')
        id_bkt = request.form.get('id_bkt')
        
        db = ket_noi_db()
        cursor = db.cursor(dictionary=True)

        query_dap_an = """
            SELECT 
                ctbkt.idCauHoi, ctbkt.diem, 
                nhch.loaiCauHoi,
                GROUP_CONCAT(pa.id ORDER BY pa.id) as dsIdPhuongAn,
                GROUP_CONCAT(pa.noiDung ORDER BY pa.id SEPARATOR '|||') as dsNoiDungPhuongAn,
                GROUP_CONCAT(pa.laDapAnDung ORDER BY pa.id) as dsDapAnDung
            FROM ChiTietBaiKiemTra ctbkt
            JOIN NganHangCauHoi nhch ON ctbkt.idCauHoi = nhch.id
            LEFT JOIN PhuongAn pa ON nhch.id = pa.idCauHoi
            WHERE ctbkt.idBaiKiemTra = %s
            GROUP BY ctbkt.idCauHoi
        """
        cursor.execute(query_dap_an, (id_bkt,))
        danh_sach_dap_an = {da['idCauHoi']: da for da in cursor.fetchall()}

        tong_diem = 0

        for id_cau_hoi, dap_an in danh_sach_dap_an.items():
            loai_cau_hoi = dap_an['loaiCauHoi']
            diem_cau_hoi = dap_an['diem']
            
            if loai_cau_hoi == 'TracNghiem':
                id_phuong_an_chon = request.form.get(f'cau_hoi_{id_cau_hoi}')
                if id_phuong_an_chon:
                    id_phuong_an_chon = int(id_phuong_an_chon)
                    cursor.execute("INSERT INTO ChiTietBaiLam (idKetQua, idCauHoi, idPhuongAnDaChon) VALUES (%s, %s, %s)",
                                   (id_ket_qua, id_cau_hoi, id_phuong_an_chon))
                    
                    dap_an_dung_id = -1
                    ds_pa_ids = [int(i) for i in dap_an['dsIdPhuongAn'].split(',')]
                    ds_da_dung = [int(i) for i in dap_an['dsDapAnDung'].split(',')]
                    for i in range(len(ds_pa_ids)):
                        if ds_da_dung[i] == 1:
                            dap_an_dung_id = ds_pa_ids[i]
                            break
                    if id_phuong_an_chon == dap_an_dung_id:
                        tong_diem += diem_cau_hoi
            
            elif loai_cau_hoi == 'DungSaiNhieuY':
                # Lấy danh sách ID phương án và đáp án đúng, đã được sắp xếp nhất quán
                ds_pa_ids = [int(i) for i in dap_an['dsIdPhuongAn'].split(',')]
                ds_da_dung_bool = [bool(int(i)) for i in dap_an['dsDapAnDung'].split(',')]
    
                so_y_dung = 0
                cau_tra_loi_chi_tiet = []

                # Lặp qua từng phương án của câu hỏi
                for i in range(len(ds_pa_ids)):
                    pa_id = ds_pa_ids[i]
                    la_dung_thuc_te = ds_da_dung_bool[i]  # Đáp án đúng là True hay False
                    
                    # Lấy lựa chọn của học sinh từ form (sẽ là 'Dung' hoặc 'Sai')
                    # Tên trường phải khớp với name trong file HTML
                    lua_chon_hs_str = request.form.get(f'cau_hoi_{id_cau_hoi}_{pa_id}')
                    
                    # Lưu lại lựa chọn của học sinh để xem lại bài làm
                    if lua_chon_hs_str:
                        cau_tra_loi_chi_tiet.append(f"{pa_id}:{lua_chon_hs_str}")
                    
                    # Chuyển lựa chọn của học sinh thành boolean để so sánh
                    hoc_sinh_chon_la_dung = (lua_chon_hs_str == 'Dung')
                    
                    # So sánh: Nếu lựa chọn của học sinh khớp với đáp án thực tế
                    if hoc_sinh_chon_la_dung == la_dung_thuc_te:
                        so_y_dung += 1

                # Lưu chuỗi trả lời chi tiết vào CSDL
                tra_loi_hs_str_db = ",".join(cau_tra_loi_chi_tiet)
                cursor.execute("INSERT INTO ChiTietBaiLam (idKetQua, idCauHoi, traLoiNgan) VALUES (%s, %s, %s)",
                            (id_ket_qua, id_cau_hoi, tra_loi_hs_str_db))

                # Tính điểm theo barem
                if so_y_dung == 4: tong_diem += diem_cau_hoi
                elif so_y_dung == 3: tong_diem += diem_cau_hoi * 0.5
                elif so_y_dung == 2: tong_diem += diem_cau_hoi * 0.25
                elif so_y_dung == 1: tong_diem += diem_cau_hoi * 0.1
                        
            
            elif loai_cau_hoi == 'TraLoiNgan':
                cau_tra_loi = request.form.get(f'cau_hoi_{id_cau_hoi}', '').strip()
                
                cursor.execute("INSERT INTO ChiTietBaiLam (idKetQua, idCauHoi, traLoiNgan) VALUES (%s, %s, %s)",
                               (id_ket_qua, id_cau_hoi, cau_tra_loi))
                
                if cau_tra_loi:
                    dap_an_dung = dap_an['dsNoiDungPhuongAn']
                    if dap_an_dung and cau_tra_loi.lower() == dap_an_dung.lower():
                        tong_diem += diem_cau_hoi

        cursor.execute("UPDATE KetQuaBaiKiemTra SET diemSo = %s, thoiGianNopBai = NOW() WHERE id = %s", (tong_diem, id_ket_qua))
        db.commit()
        cursor.close()
        db.close()
        
        return redirect(url_for('xem_ket_qua', id_ket_qua=id_ket_qua))

    except Exception as e:
        flash(f"Có lỗi xảy ra khi nộp bài: {e}", "error")
        return redirect(url_for('trang_hoc_sinh'))

@app.route('/ket-qua/<int:id_ket_qua>')
def xem_ket_qua(id_ket_qua):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))
        
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT kq.*, bkt.tenBaiKiemTra, bkt.idLop
        FROM KetQuaBaiKiemTra kq
        JOIN BaiKiemTra bkt ON kq.idBaiKiemTra = bkt.id
        WHERE kq.id = %s AND kq.idHocSinh = %s
    """
    cursor.execute(query, (id_ket_qua, session['id']))
    ket_qua = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if not ket_qua:
        return redirect(url_for('trang_hoc_sinh'))
        
    return render_template('ket_qua.html', ket_qua=ket_qua)


@app.route('/lop-hoc-sinh/<int:id_lop>/bai-da-lam')
def bai_da_lam(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))

    id_hoc_sinh = session['id']
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    if not lop_hoc:
        cursor.close()
        db.close()
        return redirect(url_for('trang_hoc_sinh'))

    query = """
        SELECT kq.id, kq.diemSo, kq.thoiGianNopBai, bkt.tenBaiKiemTra
        FROM KetQuaBaiKiemTra kq
        JOIN BaiKiemTra bkt ON kq.idBaiKiemTra = bkt.id
        WHERE bkt.idLop = %s AND kq.idHocSinh = %s
        ORDER BY kq.thoiGianNopBai DESC
    """
    cursor.execute(query, (id_lop, id_hoc_sinh))
    danh_sach_ket_qua = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('bai_da_lam.html', lop_hoc=lop_hoc, danh_sach_ket_qua=danh_sach_ket_qua)

@app.route('/xem-chi-tiet-bai-lam/<int:id_ket_qua>')
def xem_chi_tiet_bai_lam(id_ket_qua):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    # ... (các truy vấn lấy thông tin kết quả và bài làm giữ nguyên) ...
    query_kq = """
        SELECT kq.*, bkt.tenBaiKiemTra, bkt.idLop, l.tenLop
        FROM KetQuaBaiKiemTra kq
        JOIN BaiKiemTra bkt ON kq.idBaiKiemTra = bkt.id
        JOIN LopHoc l ON bkt.idLop = l.id
        WHERE kq.id = %s AND kq.idHocSinh = %s
    """
    cursor.execute(query_kq, (id_ket_qua, session['id']))
    ket_qua = cursor.fetchone()

    if not ket_qua:
        flash("Không tìm thấy bài làm.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_hoc_sinh'))

    cursor.execute("""
        SELECT ctbl.idCauHoi, ctbl.idPhuongAnDaChon, ctbl.traLoiNgan, nhch.loaiCauHoi 
        FROM ChiTietBaiLam ctbl
        JOIN NganHangCauHoi nhch ON ctbl.idCauHoi = nhch.id
        WHERE ctbl.idKetQua = %s
    """, (id_ket_qua,))
    bai_lam_rows = cursor.fetchall()
    
    bai_lam_dict = {}
    for row in bai_lam_rows:
        parsed_row = dict(row)
        if row['loaiCauHoi'] == 'DungSaiNhieuY' and row['traLoiNgan']:
            lua_chon_hs = {}
            for item in row['traLoiNgan'].split(','):
                if ':' in item:
                    pa_id_str, choice = item.split(':', 1)
                    lua_chon_hs[int(pa_id_str)] = choice
            parsed_row['lua_chon_dung_sai'] = lua_chon_hs
        bai_lam_dict[row['idCauHoi']] = parsed_row

    query_chitiet = """
        SELECT 
            nhch.id, nhch.noiDung, nhch.loaiCauHoi, ctbkt.diem,
            pa.id as idPhuongAn, pa.noiDung as phuongAnNoiDung, pa.laDapAnDung
        FROM ChiTietBaiKiemTra ctbkt
        JOIN NganHangCauHoi nhch ON ctbkt.idCauHoi = nhch.id
        LEFT JOIN PhuongAn pa ON nhch.id = pa.idCauHoi
        WHERE ctbkt.idBaiKiemTra = %s
        ORDER BY nhch.id, pa.id
    """
    cursor.execute(query_chitiet, (ket_qua['idBaiKiemTra'],))
    results = cursor.fetchall()
    
    # [THÊM MỚI] Tính tổng điểm tối đa và điểm đạt được cho từng câu
    tong_diem_toi_da = 0
    cau_hoi_dict = {}
    for row in results:
        cau_hoi_id = row['id']
        if cau_hoi_id not in cau_hoi_dict:
            tong_diem_toi_da += row['diem']
            cau_hoi_dict[cau_hoi_id] = {
                'id': row['id'], 'noiDung': row['noiDung'], 'loaiCauHoi': row['loaiCauHoi'],
                'diem': row['diem'], 'phuongAn': [], 'diemDatDuoc': 0, # Thêm key mới
                'traLoiNganCuaHS': None, 'lua_chon_dung_sai_cua_hs': {}
            }
        
        if cau_hoi_id in bai_lam_dict:
            cau_hoi_dict[cau_hoi_id]['traLoiNganCuaHS'] = bai_lam_dict[cau_hoi_id].get('traLoiNgan')
            cau_hoi_dict[cau_hoi_id]['lua_chon_dung_sai_cua_hs'] = bai_lam_dict[cau_hoi_id].get('lua_chon_dung_sai', {})

        if row['idPhuongAn'] is not None:
            da_chon = (cau_hoi_id in bai_lam_dict and 
                       bai_lam_dict[cau_hoi_id].get('idPhuongAnDaChon') == row['idPhuongAn'])
            
            cau_hoi_dict[cau_hoi_id]['phuongAn'].append({
                'id': row['idPhuongAn'], 'noiDung': row['phuongAnNoiDung'],
                'laDapAnDung': row['laDapAnDung'], 'daChon': da_chon
            })
    
    # Tính điểm đạt được sau khi đã có đủ thông tin
    for ch_id, ch_data in cau_hoi_dict.items():
        diem_cau_hoi = ch_data['diem']
        if ch_data['loaiCauHoi'] == 'TracNghiem':
            for pa in ch_data['phuongAn']:
                if pa['daChon'] and pa['laDapAnDung']:
                    ch_data['diemDatDuoc'] = diem_cau_hoi
                    break
        elif ch_data['loaiCauHoi'] == 'TraLoiNgan':
            tra_loi_hs = ch_data['traLoiNganCuaHS']
            dap_an_dung = ch_data['phuongAn'][0]['noiDung'] if ch_data['phuongAn'] else ''
            if tra_loi_hs and dap_an_dung and tra_loi_hs.lower() == dap_an_dung.lower():
                ch_data['diemDatDuoc'] = diem_cau_hoi
        elif ch_data['loaiCauHoi'] == 'DungSaiNhieuY':
            so_y_dung = 0
            lua_chon_hs = ch_data['lua_chon_dung_sai_cua_hs']
            for pa in ch_data['phuongAn']:
                lua_chon = lua_chon_hs.get(pa['id'])
                if (lua_chon == 'Dung' and pa['laDapAnDung']) or \
                   (lua_chon == 'Sai' and not pa['laDapAnDung']):
                    so_y_dung += 1
            if so_y_dung == 4: ch_data['diemDatDuoc'] = diem_cau_hoi
            elif so_y_dung == 3: ch_data['diemDatDuoc'] = diem_cau_hoi * 0.5
            elif so_y_dung == 2: ch_data['diemDatDuoc'] = diem_cau_hoi * 0.25
            elif so_y_dung == 1: ch_data['diemDatDuoc'] = diem_cau_hoi * 0.1
    
    danh_sach_cau_hoi = list(cau_hoi_dict.values())
    cursor.close()
    db.close()

    return render_template('xem_chi_tiet_bai_lam.html', 
                           ket_qua=ket_qua, 
                           danh_sach_cau_hoi=danh_sach_cau_hoi,
                           tong_diem_toi_da=tong_diem_toi_da) # Gửi tổng điểm tối đa

@app.route('/lop/<int:id_lop>/chi-tiet-bai-kiem-tra/<int:id_bkt>')
def chi_tiet_bai_kiem_tra(id_lop, id_bkt):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()
    cursor.execute("SELECT * FROM BaiKiemTra WHERE id = %s AND idGiaoVien = %s", (id_bkt, session['id']))
    bai_kiem_tra = cursor.fetchone()

    if not lop_hoc or not bai_kiem_tra:
        flash("Không tìm thấy thông tin hợp lệ.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))

    query = """
        SELECT 
            nhch.id, nhch.noiDung, nhch.loaiCauHoi,
            ctbkt.diem,
            pa.noiDung AS phuongAnNoiDung, pa.laDapAnDung
        FROM ChiTietBaiKiemTra ctbkt
        JOIN NganHangCauHoi nhch ON ctbkt.idCauHoi = nhch.id
        LEFT JOIN PhuongAn pa ON nhch.id = pa.idCauHoi
        WHERE ctbkt.idBaiKiemTra = %s
        ORDER BY nhch.id, pa.id
    """
    cursor.execute(query, (id_bkt,))
    results = cursor.fetchall()

    cau_hoi_dict = {}
    for row in results:
        cau_hoi_id = row['id']
        if cau_hoi_id not in cau_hoi_dict:
            cau_hoi_dict[cau_hoi_id] = {
                'id': row['id'], 'noiDung': row['noiDung'], 'loaiCauHoi': row['loaiCauHoi'],
                'diem': row['diem'], 'phuongAn': []
            }
        if row['phuongAnNoiDung'] is not None:
            cau_hoi_dict[cau_hoi_id]['phuongAn'].append({
                'noiDung': row['phuongAnNoiDung'], 'laDapAnDung': row['laDapAnDung']
            })
    
    danh_sach_cau_hoi = list(cau_hoi_dict.values())
    
    cursor.close()
    db.close()

    return render_template('chi_tiet_bai_kiem_tra.html', 
                           lop_hoc=lop_hoc, 
                           bai_kiem_tra=bai_kiem_tra, 
                           danh_sach_cau_hoi=danh_sach_cau_hoi)
 
 
 
 
 
 
 
 
 

 
@app.route('/lop/<int:id_lop>/tao-tro-choi')
def tao_tro_choi(id_lop):
    # Hàm này bây giờ sẽ là trang hub chung cho các trò chơi
    # Tạm thời, ta có thể redirect trực tiếp đến trang tạo ĐHBC
    return redirect(url_for('tao_tro_choi_dhbc', id_lop=id_lop))
 

@app.route('/lop/<int:id_lop>/tao-tro-choi-dhbc', methods=['GET', 'POST'])
def tao_tro_choi_dhbc(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))
    
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()

    if not lop_hoc:
        flash("Không tìm thấy lớp học.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))

    if request.method == 'POST':
        try:
            # Lấy thông tin chung của game
            ten_tro_choi = request.form.get('ten_tro_choi')
            thoi_gian_choi_str = request.form.get('thoi_gian_choi')
            mat_khau_choi = request.form.get('mat_khau_choi')
            id_giao_vien = session['id']

            # Chuyển đổi dữ liệu để lưu vào DB
            thoi_gian_choi_db = int(thoi_gian_choi_str) if thoi_gian_choi_str else None
            mat_khau_db = mat_khau_choi if mat_khau_choi else None

            # 1. Thêm game mới vào bảng TroChoiDHBC
            sql_game = """
                INSERT INTO TroChoiDHBC (tenTroChoi, thoiGianChoi, matKhau, idLop, idGiaoVien) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_game, (ten_tro_choi, thoi_gian_choi_db, mat_khau_db, id_lop, id_giao_vien))
            id_tro_choi_moi = cursor.lastrowid

            # 2. Lấy danh sách file, đáp án và gợi ý từ form
            cac_anh = request.files.getlist('anh_cau_hoi[]')
            cac_dap_an = request.form.getlist('dap_an[]')
            cac_goi_y = request.form.getlist('goi_y[]') # Lấy danh sách gợi ý
            
            # 3. Lặp qua từng câu hỏi để xử lý
            sql_cau_hoi = "INSERT INTO CauHoiDHBC (idTroChoi, tenFileAnh, dapAn, goiY) VALUES (%s, %s, %s, %s)"
            for i, file in enumerate(cac_anh):
                if file and file.filename != '':
                    filename_goc = secure_filename(file.filename)
                    ten_file_moi = str(uuid.uuid4()) + "_" + filename_goc
                    
                    file.path = os.path.join(app.config['UPLOAD_FOLDER_DHBC'], ten_file_moi)
                    file.save(file.path)
                    
                    dap_an = cac_dap_an[i]
                    goi_y = cac_goi_y[i] if cac_goi_y[i] else None # Lấy gợi ý tương ứng
                    
                    cursor.execute(sql_cau_hoi, (id_tro_choi_moi, ten_file_moi, dap_an, goi_y))
            
            db.commit()
            flash('Tạo trò chơi Đuổi Hình Bắt Chữ thành công!', 'success')
            return redirect(url_for('danh_sach_tro_choi_dhbc_gv', id_lop=id_lop))
        except Exception as e:
            db.rollback()
            flash(f"Đã xảy ra lỗi: {e}", "error")
        finally:
            cursor.close()
            db.close()
    
    return render_template('tao_tro_choi_dhbc.html', lop_hoc=lop_hoc)

    
    
 
@app.route('/lop-hoc-sinh/<int:id_lop>/danh-sach-tro-choi-dhbc')
def danh_sach_tro_choi_dhbc_hs(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'HocSinh':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (id_lop,))
    lop_hoc = cursor.fetchone()

    cursor.execute("SELECT * FROM TroChoiDHBC WHERE idLop = %s ORDER BY ngayTao DESC", (id_lop,))
    danh_sach_game = cursor.fetchall()

    cursor.close()
    db.close()

    if not lop_hoc:
        return redirect(url_for('trang_hoc_sinh'))

    return render_template('danh_sach_tro_choi_dhbc_hs.html', lop_hoc=lop_hoc, danh_sach_game=danh_sach_game)
 
 
 
 
@app.route('/bat-dau-dhbc/<int:id_tro_choi>', methods=['GET', 'POST'])
def bat_dau_dhbc(id_tro_choi):
    if 'da_dang_nhap' not in session: return redirect(url_for('dang_nhap'))
    
    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    # [CẬP NHẬT] Thêm JOIN để lấy tenLop
    sql_query = """
        SELECT tc.*, lh.tenLop 
        FROM TroChoiDHBC tc 
        JOIN LopHoc lh ON tc.idLop = lh.id 
        WHERE tc.id = %s
    """
    cursor.execute(sql_query, (id_tro_choi,))
    tro_choi = cursor.fetchone()
    
    cursor.close()
    db.close()

    if not tro_choi:
        flash("Không tìm thấy trò chơi này.", "error")
        return redirect(url_for('trang_hoc_sinh'))

    if request.method == 'POST':
        if tro_choi['matKhau']:
            mat_khau_nhap = request.form.get('mat_khau')
            if mat_khau_nhap != tro_choi['matKhau']:
                flash("Mật khẩu không chính xác!", "error")
                return redirect(url_for('bat_dau_dhbc', id_tro_choi=id_tro_choi))
        
        return redirect(url_for('choi_dhbc', id_tro_choi=id_tro_choi))
        
    return render_template('bat_dau_dhbc.html', tro_choi=tro_choi)

@app.route('/choi-dhbc/<int:id_tro_choi>')
def choi_dhbc(id_tro_choi):
    if 'da_dang_nhap' not in session: return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM TroChoiDHBC WHERE id = %s", (id_tro_choi,))
    tro_choi = cursor.fetchone()
    
    cursor.execute("SELECT id, tenFileAnh, goiY, dapAn FROM CauHoiDHBC WHERE idTroChoi = %s", (id_tro_choi,))
    cau_hoi_list = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    # Chuyển đổi list câu hỏi thành JSON để JavaScript sử dụng
    cau_hoi_json = json.dumps(cau_hoi_list)

    return render_template('choi_dhbc.html', tro_choi=tro_choi, cau_hoi_json=cau_hoi_json)

@app.route('/luu-ket-qua-dhbc', methods=['POST'])
def luu_ket_qua_dhbc():
    if 'da_dang_nhap' not in session:
        return jsonify({'status': 'error', 'message': 'Chưa đăng nhập'}), 401
        
    data = request.json
    id_tro_choi = data.get('id_tro_choi')
    diem_so = data.get('diem_so')
    thoi_gian_hoan_thanh = data.get('thoi_gian_hoan_thanh') # Thêm trường mới
    id_hoc_sinh = session['id']

    try:
        db = ket_noi_db()
        cursor = db.cursor()
        # Cập nhật câu lệnh SQL
        sql = "INSERT INTO KetQuaDHBC (idTroChoi, idHocSinh, diemSo, thoiGianHoanThanh) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (id_tro_choi, id_hoc_sinh, diem_so, thoi_gian_hoan_thanh))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
 
 
@app.route('/lop/<int:id_lop>/gv/danh-sach-dhbc')
def danh_sach_tro_choi_dhbc_gv(id_lop):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s AND idGiaoVien = %s", (id_lop, session['id']))
    lop_hoc = cursor.fetchone()

    cursor.execute("SELECT * FROM TroChoiDHBC WHERE idLop = %s ORDER BY ngayTao DESC", (id_lop,))
    danh_sach_game = cursor.fetchall()

    cursor.close()
    db.close()

    if not lop_hoc:
        return redirect(url_for('trang_giao_vien'))

    return render_template('danh_sach_tro_choi_dhbc_gv.html', lop_hoc=lop_hoc, danh_sach_game=danh_sach_game)


@app.route('/sua-tro-choi-dhbc/<int:id_tro_choi>', methods=['GET', 'POST'])
def sua_tro_choi_dhbc(id_tro_choi):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    # Lấy thông tin game hiện tại
    cursor.execute("SELECT * FROM TroChoiDHBC WHERE id = %s AND idGiaoVien = %s", (id_tro_choi, session['id']))
    tro_choi = cursor.fetchone()
    if not tro_choi:
        flash("Không tìm thấy trò chơi hoặc bạn không có quyền chỉnh sửa.", "error")
        cursor.close()
        db.close()
        return redirect(url_for('trang_giao_vien'))

    if request.method == 'POST':
        try:
            # 1. Cập nhật thông tin chung của game
            ten_tro_choi = request.form.get('ten_tro_choi')
            thoi_gian_choi_str = request.form.get('thoi_gian_choi')
            mat_khau_choi = request.form.get('mat_khau_choi')
            thoi_gian_choi_db = int(thoi_gian_choi_str) if thoi_gian_choi_str else None
            mat_khau_db = mat_khau_choi if mat_khau_choi else None

            sql_update_game = "UPDATE TroChoiDHBC SET tenTroChoi=%s, thoiGianChoi=%s, matKhau=%s WHERE id=%s"
            cursor.execute(sql_update_game, (ten_tro_choi, thoi_gian_choi_db, mat_khau_db, id_tro_choi))

            # 2. Xử lý các câu hỏi đã bị xóa
            ids_cau_hoi_da_xoa = request.form.get('cau_hoi_da_xoa', '').split(',')
            for id_ch_xoa in ids_cau_hoi_da_xoa:
                if id_ch_xoa.isdigit():
                    # (Tùy chọn) Xóa file ảnh cũ trên server trước khi xóa record
                    cursor.execute("DELETE FROM CauHoiDHBC WHERE id = %s", (id_ch_xoa,))
            
            # 3. Cập nhật các câu hỏi cũ
            ids_cau_hoi_cu = request.form.getlist('id_cau_hoi_cu[]')
            for id_ch_cu in ids_cau_hoi_cu:
                dap_an_moi = request.form.get(f'dap_an_cu_{id_ch_cu}')
                goi_y_moi = request.form.get(f'goi_y_cu_{id_ch_cu}')
                sql_update_ch = "UPDATE CauHoiDHBC SET dapAn=%s, goiY=%s WHERE id=%s"
                cursor.execute(sql_update_ch, (dap_an_moi, goi_y_moi if goi_y_moi else None, id_ch_cu))

            # 4. Thêm các câu hỏi mới
            cac_anh_moi = request.files.getlist('anh_cau_hoi_moi[]')
            cac_dap_an_moi = request.form.getlist('dap_an_moi[]')
            cac_goi_y_moi = request.form.getlist('goi_y_moi[]')
            
            sql_insert_ch = "INSERT INTO CauHoiDHBC (idTroChoi, tenFileAnh, dapAn, goiY) VALUES (%s, %s, %s, %s)"
            for i, file in enumerate(cac_anh_moi):
                if file and file.filename != '':
                    filename_goc = secure_filename(file.filename)
                    ten_file_moi = str(uuid.uuid4()) + "_" + filename_goc
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_DHBC'], ten_file_moi))
                    
                    cursor.execute(sql_insert_ch, (id_tro_choi, ten_file_moi, cac_dap_an_moi[i], cac_goi_y_moi[i] if cac_goi_y_moi[i] else None))

            db.commit()
            flash("Cập nhật trò chơi thành công!", "success")
            return redirect(url_for('danh_sach_tro_choi_dhbc_gv', id_lop=tro_choi['idLop']))
        
        except Exception as e:
            db.rollback()
            flash(f"Có lỗi xảy ra: {e}", "error")

    # Xử lý GET: Lấy danh sách câu hỏi hiện tại để hiển thị
    cursor.execute("SELECT * FROM CauHoiDHBC WHERE idTroChoi = %s", (id_tro_choi,))
    danh_sach_cau_hoi = cursor.fetchall()
    
    cursor.execute("SELECT * FROM LopHoc WHERE id = %s", (tro_choi['idLop'],))
    lop_hoc = cursor.fetchone()

    cursor.close()
    db.close()
    return render_template('sua_tro_choi_dhbc.html', tro_choi=tro_choi, danh_sach_cau_hoi=danh_sach_cau_hoi, lop_hoc=lop_hoc)    


@app.route('/xoa-tro-choi-dhbc/<int:id_tro_choi>', methods=['POST'])
def xoa_tro_choi_dhbc(id_tro_choi):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Kiểm tra xem giáo viên có sở hữu trò chơi này không
        cursor.execute("SELECT * FROM TroChoiDHBC WHERE id = %s AND idGiaoVien = %s", (id_tro_choi, session['id']))
        tro_choi = cursor.fetchone()

        if not tro_choi:
            flash("Không tìm thấy trò chơi hoặc bạn không có quyền xóa.", "error")
            return redirect(url_for('trang_giao_vien'))

        # 1. Lấy danh sách tất cả các file ảnh của game này TRƯỚC KHI xóa
        cursor.execute("SELECT tenFileAnh FROM CauHoiDHBC WHERE idTroChoi = %s", (id_tro_choi,))
        cac_cau_hoi = cursor.fetchall()

        # 2. Xóa game khỏi database (nhờ có ON DELETE CASCADE, các câu hỏi và kết quả sẽ tự động bị xóa theo)
        cursor.execute("DELETE FROM TroChoiDHBC WHERE id = %s", (id_tro_choi,))

        # 3. Xóa các file ảnh trên server
        for ch in cac_cau_hoi:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER_DHBC'], ch['tenFileAnh'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Lỗi khi xóa file ảnh {ch['tenFileAnh']}: {e}") # Ghi log lỗi ra terminal
        
        db.commit()
        flash("Đã xóa trò chơi thành công!", "success")

    except Exception as e:
        db.rollback()
        flash(f"Xóa trò chơi thất bại: {e}", "error")
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('danh_sach_tro_choi_dhbc_gv', id_lop=tro_choi['idLop']))

@app.route('/thong-ke-dhbc/<int:id_tro_choi>')
def thong_ke_dhbc(id_tro_choi):
    if 'da_dang_nhap' not in session or session['vai_tro'] != 'GiaoVien':
        return redirect(url_for('dang_nhap'))

    db = ket_noi_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Lấy thông tin của trò chơi và lớp học
        cursor.execute("""
            SELECT tc.*, lh.tenLop 
            FROM TroChoiDHBC tc 
            JOIN LopHoc lh ON tc.idLop = lh.id 
            WHERE tc.id = %s AND tc.idGiaoVien = %s
        """, (id_tro_choi, session['id']))
        tro_choi = cursor.fetchone()

        if not tro_choi:
            flash("Không tìm thấy trò chơi này.", "error")
            return redirect(url_for('trang_giao_vien'))

        # Lấy danh sách kết quả của học sinh, sắp xếp theo điểm số giảm dần
        cursor.execute("""
            SELECT kq.*, hs.hoVaTen 
            FROM KetQuaDHBC kq
            JOIN NguoiDung hs ON kq.idHocSinh = hs.id
            WHERE kq.idTroChoi = %s
            ORDER BY kq.diemSo DESC, kq.thoiGianHoanThanh ASC
        """, (id_tro_choi,))
        danh_sach_ket_qua = cursor.fetchall()

    finally:
        cursor.close()
        db.close()

    return render_template('thong_ke_dhbc.html', tro_choi=tro_choi, danh_sach_ket_qua=danh_sach_ket_qua)

# --- Chạy ứng dụng ---
if __name__ == '__main__':
    app.run(debug=True)