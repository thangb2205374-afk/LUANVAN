-- Tạo cơ sở dữ liệu nếu chưa tồn tại
CREATE DATABASE IF NOT EXISTS trochoi_tracnghiem CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE trochoi_tracnghiem;

-- Xóa các bảng theo thứ tự phụ thuộc để tránh lỗi
DROP TABLE IF EXISTS ChiTietBaiLam;
DROP TABLE IF EXISTS KetQuaBaiKiemTra;
DROP TABLE IF EXISTS ChiTietBaiKiemTra;
DROP TABLE IF EXISTS BaiKiemTra;
DROP TABLE IF EXISTS PhuongAn;
DROP TABLE IF EXISTS NganHangCauHoi;
DROP TABLE IF EXISTS ThanhVienLop;
DROP TABLE IF EXISTS LopHoc;
DROP TABLE IF EXISTS NguoiDung;

-- Bảng 1: Người Dùng
CREATE TABLE NguoiDung (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hoVaTen VARCHAR(100) NOT NULL,
    tenDangNhap VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    matKhau VARCHAR(255) NOT NULL,
    gioiTinh ENUM('Nam', 'Nu', 'Khac') NOT NULL,
    vaiTro ENUM('HocSinh', 'GiaoVien') NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Bảng 2: Lớp Học
CREATE TABLE LopHoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenLop VARCHAR(100) NOT NULL,
    maLop VARCHAR(10) NOT NULL UNIQUE,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 3: Thành Viên Lớp
CREATE TABLE ThanhVienLop (
    idHocSinh INT NOT NULL,
    idLop INT NOT NULL,
    ngayThamGia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (idHocSinh, idLop),
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 4: Ngân Hàng Câu Hỏi
CREATE TABLE NganHangCauHoi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    noiDung TEXT NOT NULL,
    loaiCauHoi ENUM('TracNghiem', 'DungSaiNhieuY', 'TraLoiNgan') NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 5: Phương Án
CREATE TABLE PhuongAn (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idCauHoi INT NOT NULL,
    noiDung TEXT NOT NULL,
    laDapAnDung BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 6: Bài Kiểm Tra
CREATE TABLE BaiKiemTra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenBaiKiemTra VARCHAR(255) NOT NULL,
    thongTin TEXT,
    thoiGianLamBai INT NOT NULL, -- tính bằng phút
    matKhau VARCHAR(255) NULL,
    soLanLamBaiToiDa INT NOT NULL DEFAULT 1, -- Số lần làm bài tối đa
    idLop INT NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 7: Chi Tiết Bài Kiểm Tra
CREATE TABLE ChiTietBaiKiemTra (
    idBaiKiemTra INT NOT NULL,
    idCauHoi INT NOT NULL,
    diem FLOAT NOT NULL,
    PRIMARY KEY (idBaiKiemTra, idCauHoi),
    FOREIGN KEY (idBaiKiemTra) REFERENCES BaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 8: Kết Quả Bài Kiểm Tra
CREATE TABLE KetQuaBaiKiemTra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idBaiKiemTra INT NOT NULL,
    idHocSinh INT NOT NULL,
    diemSo FLOAT NOT NULL,
    thoiGianNopBai TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thoiGianBatDau DATETIME NOT NULL,
    FOREIGN KEY (idBaiKiemTra) REFERENCES BaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 9: Chi Tiết Bài Làm
CREATE TABLE ChiTietBaiLam (
    idKetQua INT NOT NULL,
    idCauHoi INT NOT NULL,
    idPhuongAnDaChon INT NULL,
    traLoiNgan TEXT NULL,
    PRIMARY KEY (idKetQua, idCauHoi),
    FOREIGN KEY (idKetQua) REFERENCES KetQuaBaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE,
    FOREIGN KEY (idPhuongAnDaChon) REFERENCES PhuongAn(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Bảng 10: Trò Chơi ĐHBC (Quản lý một trò chơi lớn)
CREATE TABLE TroChoiDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenTroChoi VARCHAR(255) NOT NULL,
    idLop INT NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 11: Câu Hỏi ĐHBC (Lưu từng câu hỏi cho một trò chơi)
CREATE TABLE CauHoiDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idTroChoi INT NOT NULL,
    tenFileAnh VARCHAR(255) NOT NULL, -- Tên file ảnh đã được upload
    dapAn VARCHAR(255) NOT NULL,     -- Đáp án cho hình ảnh
    goiY TEXT NULL,                  -- Gợi ý (nếu có)
    FOREIGN KEY (idTroChoi) REFERENCES TroChoiDHBC(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 12: Kết Quả ĐHBC (Lưu kết quả chơi của học sinh)
CREATE TABLE KetQuaDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idTroChoi INT NOT NULL,
    idHocSinh INT NOT NULL,
    diemSo INT NOT NULL,
    thoiGianHoanThanh INT NULL, -- Thời gian hoàn thành tính bằng giây
    ngayChoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idTroChoi) REFERENCES TroChoiDHBC(id) ON DELETE CASCADE,
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;


ALTER TABLE TroChoiDHBC
ADD COLUMN thoiGianChoi INT NULL AFTER tenTroChoi, -- Thời gian tính bằng phút
ADD COLUMN matKhau VARCHAR(255) NULL AFTER thoiGianChoi;



----------------------------------------------------------------
-----------------------------------------------------------------
-- TẠO CƠ SỞ DỮ LIỆU NẾU CHƯA TỒN TẠI
CREATE DATABASE IF NOT EXISTS trochoi_tracnghiem CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE trochoi_tracnghiem;


-- --- BẮT ĐẦU TẠO CÁC BẢNG ---

-- Bảng 1: Người Dùng (Chung cho Giáo viên và Học sinh)
CREATE TABLE NguoiDung (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hoVaTen VARCHAR(255) NOT NULL,
    tenDangNhap VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    matKhau VARCHAR(255) NOT NULL,
    gioiTinh ENUM('Nam', 'Nữ', 'Khác') NOT NULL,
    vaiTro ENUM('GiaoVien', 'HocSinh') NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Bảng 2: Lớp Học
CREATE TABLE LopHoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenLop VARCHAR(255) NOT NULL,
    maLop VARCHAR(10) NOT NULL UNIQUE,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 3: Học Sinh Trong Lớp (Bảng nối)
CREATE TABLE HocSinhTrongLop (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idLop INT NOT NULL,
    idHocSinh INT NOT NULL,
    ngayThamGia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE,
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE,
    UNIQUE KEY (idLop, idHocSinh)
) ENGINE=InnoDB;

-- Bảng 4: Ngân Hàng Câu Hỏi (Trắc nghiệm & Tự luận)
CREATE TABLE NganHangCauHoi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    noiDung TEXT NOT NULL,
    loaiCauHoi ENUM('TracNghiem', 'DungSaiNhieuY', 'TraLoiNgan') NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 5: Phương Án (Đáp án cho câu hỏi)
CREATE TABLE PhuongAn (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idCauHoi INT NOT NULL,
    noiDung TEXT NOT NULL,
    laDapAnDung BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 6: Bài Kiểm Tra
CREATE TABLE BaiKiemTra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenBaiKiemTra VARCHAR(255) NOT NULL,
    thongTin TEXT,
    thoiGianLamBai INT NOT NULL, -- tính bằng phút
    matKhau VARCHAR(255) NULL,
    soLanLamBaiToiDa INT NOT NULL DEFAULT 1,
    idLop INT NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 7: Chi Tiết Bài Kiểm Tra (Câu hỏi nào trong bài thi nào)
CREATE TABLE ChiTietBaiKiemTra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idBaiKiemTra INT NOT NULL,
    idCauHoi INT NOT NULL,
    diem FLOAT NOT NULL,
    FOREIGN KEY (idBaiKiemTra) REFERENCES BaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 8: Kết Quả Bài Kiểm Tra (Lần làm bài của học sinh)
CREATE TABLE KetQuaBaiKiemTra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idBaiKiemTra INT NOT NULL,
    idHocSinh INT NOT NULL,
    diemSo FLOAT,
    thoiGianBatDau DATETIME NOT NULL,
    thoiGianNopBai TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (idBaiKiemTra) REFERENCES BaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 9: Chi Tiết Kết Quả (Lưu câu trả lời của học sinh)
CREATE TABLE ChiTietKetQua (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idKetQuaBaiKiemTra INT NOT NULL,
    idCauHoi INT NOT NULL,
    idPhuongAnDaChon INT NULL, -- NULL nếu là câu trả lời ngắn
    traLoiNgan TEXT NULL,      -- NULL nếu là câu trắc nghiệm
    FOREIGN KEY (idKetQuaBaiKiemTra) REFERENCES KetQuaBaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE,
    FOREIGN KEY (idPhuongAnDaChon) REFERENCES PhuongAn(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 10: Trò Chơi Đuổi Hình Bắt Chữ (ĐHBC)
CREATE TABLE TroChoiDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenTroChoi VARCHAR(255) NOT NULL,
    thoiGianChoi INT NULL, -- Thời gian tính bằng phút
    matKhau VARCHAR(255) NULL,
    idLop INT NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 11: Câu Hỏi ĐHBC
CREATE TABLE CauHoiDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idTroChoi INT NOT NULL,
    tenFileAnh VARCHAR(255) NOT NULL,
    dapAn VARCHAR(255) NOT NULL,
    goiY TEXT NULL,
    FOREIGN KEY (idTroChoi) REFERENCES TroChoiDHBC(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 12: Kết Quả ĐHBC
CREATE TABLE KetQuaDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idTroChoi INT NOT NULL,
    idHocSinh INT NOT NULL,
    diemSo INT NOT NULL,
    thoiGianHoanThanh INT NULL, -- Thời gian hoàn thành tính bằng giây
    ngayChoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idTroChoi) REFERENCES TroChoiDHBC(id) ON DELETE CASCADE,
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;
--------------------------------------------------------------------------
------------------------------------------------------------------------


CREATE DATABASE IF NOT EXISTS trochoi_tracnghiem CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE trochoi_tracnghiem;

-- Bảng 1: Người Dùng
CREATE TABLE NguoiDung (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hoVaTen VARCHAR(100) NOT NULL,
    tenDangNhap VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    matKhau VARCHAR(255) NOT NULL,
    gioiTinh ENUM('Nam', 'Nu', 'Khac') NOT NULL,
    vaiTro ENUM('HocSinh', 'GiaoVien') NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Bảng 2: Lớp Học
CREATE TABLE LopHoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenLop VARCHAR(100) NOT NULL,
    maLop VARCHAR(10) NOT NULL UNIQUE,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 3: Thành Viên Lớp
CREATE TABLE ThanhVienLop (
    idHocSinh INT NOT NULL,
    idLop INT NOT NULL,
    ngayThamGia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (idHocSinh, idLop),
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 4: Ngân Hàng Câu Hỏi
CREATE TABLE NganHangCauHoi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    noiDung TEXT NOT NULL,
    loaiCauHoi ENUM('TracNghiem', 'DungSaiNhieuY', 'TraLoiNgan') NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 5: Phương Án
CREATE TABLE PhuongAn (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idCauHoi INT NOT NULL,
    noiDung TEXT NOT NULL,
    laDapAnDung BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 6: Bài Kiểm Tra
CREATE TABLE BaiKiemTra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenBaiKiemTra VARCHAR(255) NOT NULL,
    thongTin TEXT,
    thoiGianLamBai INT NOT NULL, -- tính bằng phút
    matKhau VARCHAR(255) NULL,
    soLanLamBaiToiDa INT NOT NULL DEFAULT 1, -- Số lần làm bài tối đa
    idLop INT NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 7: Chi Tiết Bài Kiểm Tra
CREATE TABLE ChiTietBaiKiemTra (
    idBaiKiemTra INT NOT NULL,
    idCauHoi INT NOT NULL,
    diem FLOAT NOT NULL,
    PRIMARY KEY (idBaiKiemTra, idCauHoi),
    FOREIGN KEY (idBaiKiemTra) REFERENCES BaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 8: Kết Quả Bài Kiểm Tra
CREATE TABLE KetQuaBaiKiemTra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idBaiKiemTra INT NOT NULL,
    idHocSinh INT NOT NULL,
    diemSo FLOAT NOT NULL,
    thoiGianNopBai TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thoiGianBatDau DATETIME NOT NULL,
    FOREIGN KEY (idBaiKiemTra) REFERENCES BaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 9: Chi Tiết Bài Làm
CREATE TABLE ChiTietBaiLam (
    idKetQua INT NOT NULL,
    idCauHoi INT NOT NULL,
    idPhuongAnDaChon INT NULL,
    traLoiNgan TEXT NULL,
    PRIMARY KEY (idKetQua, idCauHoi),
    FOREIGN KEY (idKetQua) REFERENCES KetQuaBaiKiemTra(id) ON DELETE CASCADE,
    FOREIGN KEY (idCauHoi) REFERENCES NganHangCauHoi(id) ON DELETE CASCADE,
    FOREIGN KEY (idPhuongAnDaChon) REFERENCES PhuongAn(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Bảng 10: Trò Chơi ĐHBC (Quản lý một trò chơi lớn)
CREATE TABLE TroChoiDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenTroChoi VARCHAR(255) NOT NULL,
    thoiGianChoi INT NULL, -- Thời gian tính bằng phút
    matKhau VARCHAR(255) NULL,
    idLop INT NOT NULL,
    idGiaoVien INT NOT NULL,
    ngayTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idLop) REFERENCES LopHoc(id) ON DELETE CASCADE,
    FOREIGN KEY (idGiaoVien) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 11: Câu Hỏi ĐHBC (Lưu từng câu hỏi cho một trò chơi)
CREATE TABLE CauHoiDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idTroChoi INT NOT NULL,
    tenFileAnh VARCHAR(255) NOT NULL, -- Tên file ảnh đã được upload
    dapAn VARCHAR(255) NOT NULL,      -- Đáp án cho hình ảnh
    goiY TEXT NULL,                   -- Gợi ý (nếu có)
    FOREIGN KEY (idTroChoi) REFERENCES TroChoiDHBC(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bảng 12: Kết Quả ĐHBC (Lưu kết quả chơi của học sinh)
CREATE TABLE KetQuaDHBC (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idTroChoi INT NOT NULL,
    idHocSinh INT NOT NULL,
    diemSo INT NOT NULL,
    thoiGianHoanThanh INT NULL, -- Thời gian hoàn thành tính bằng giây
    ngayChoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idTroChoi) REFERENCES TroChoiDHBC(id) ON DELETE CASCADE,
    FOREIGN KEY (idHocSinh) REFERENCES NguoiDung(id) ON DELETE CASCADE
) ENGINE=InnoDB;