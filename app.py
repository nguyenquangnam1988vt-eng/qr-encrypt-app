import streamlit as st
import qrcode
import json
from cryptography.fernet import Fernet
from hashlib import sha256
import base64
from PIL import Image
from io import BytesIO
import re
import datetime

# ====== THƯ VIỆN ĐỌC QR CODE ======
try:
    from pyzbar.pyzbar import decode
    import cv2
    import numpy as np
    QR_READER_AVAILABLE = True
except ImportError:
    QR_READER_AVAILABLE = False

# ====== MẬT KHẨU MẶC ĐỊNH CHO CÔNG AN ======
DEFAULT_PASSWORD = "CA@123123"

# ====== Hàm mã hóa / giải mã ======
def generate_key(password: str) -> bytes:
    key = sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key[:32])

def encrypt_data(data: str, password: str) -> str:
    key = generate_key(password)
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(token: str, password: str) -> str:
    key = generate_key(password)
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()

# ====== Hàm tạo QR code chuẩn ======
def create_proper_qr_code(data):
    """Tạo QR code với cấu hình chuẩn"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# ====== Hàm tạo QR trắng ======
def create_blank_qr():
    """Tạo QR trắng với cấu trúc dữ liệu rỗng"""
    blank_data = {
        "status": "blank",
        "created_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "note": "QR trắng - chưa có thông tin"
    }
    
    # Mã hóa với mật khẩu mặc định
    encrypted_default = encrypt_data(json.dumps(blank_data), DEFAULT_PASSWORD)
    
    # Tạo mật khẩu tạm thời cho QR trắng
    temp_password = "TEMP@123"
    encrypted_temp = encrypt_data(json.dumps(blank_data), temp_password)
    
    # Tạo cấu trúc combo giống QR thật
    combo_data = json.dumps({
        "cong_an": encrypted_default,
        "ngay_sinh": encrypted_temp,  # Sẽ được thay thế sau
        "custom": encrypted_temp,     # Sẽ được thay thế sau
        "is_blank": True
    }, ensure_ascii=False)
    
    return combo_data, temp_password

# ====== Hàm cập nhật QR trắng ======
def update_blank_qr(blank_qr_data, new_data, custom_password, birthdate_password):
    """Cập nhật QR trắng với thông tin mới"""
    try:
        # Parse dữ liệu QR trắng
        qr_json = json.loads(blank_qr_data)
        
        # Mã hóa thông tin mới với các mật khẩu
        data_json = json.dumps(new_data, ensure_ascii=False)
        
        encrypted_default = encrypt_data(data_json, DEFAULT_PASSWORD)
        encrypted_birthdate = encrypt_data(data_json, birthdate_password)
        encrypted_custom = encrypt_data(data_json, custom_password)
        
        # Tạo combo mới
        updated_combo = json.dumps({
            "cong_an": encrypted_default,
            "ngay_sinh": encrypted_birthdate,
            "custom": encrypted_custom,
            "is_blank": False,
            "updated_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, ensure_ascii=False)
        
        return updated_combo
        
    except Exception as e:
        st.error(f"Lỗi khi cập nhật QR trắng: {str(e)}")
        return None

# ====== Giao diện web ======
st.set_page_config(page_title="Hệ Thống QR Code Quản Lý Học Sinh", page_icon="🎓", layout="wide")

st.title("🎓 HỆ THỐNG QUẢN LÝ HỌC SINH THAM GIA GIAO THÔNG")
st.markdown("**Ứng dụng mã QR thông minh cho Công an, Nhà trường và Phụ huynh**")

tab1, tab2, tab3 = st.tabs(["📦 TẠO MÃ QR", "🔓 GIẢI MÃ THÔNG TIN", "⚪ TẠO & CẬP NHẬT QR TRẮNG"])

# ---------- TAB 1: TẠO MÃ QR ----------
with tab1:
    st.subheader("📋 NHẬP THÔNG TIN ĐỂ TẠO MÃ QR")
    
    st.markdown("### 🎯 CHỌN LOẠI ĐỐI TƯỢNG")
    loai_doituong = st.radio(
        "Loại xe:",
        [
            "🚗 XE CÁ NHÂN HỌC SINH",
            "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM", 
            "🏠 XE GIA ĐÌNH (chỉ thông tin chủ xe)"
        ],
        index=0
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if loai_doituong in ["🚗 XE CÁ NHÂN HỌC SINH", "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM"]:
            st.markdown("### 👤 THÔNG TIN HỌC SINH")
            hoten_hocsinh = st.text_input("Họ tên học sinh *", placeholder="Nguyễn Văn A", key="hs1")
            ngaysinh_hocsinh = st.text_input("Ngày sinh học sinh *", placeholder="15/07/2008", key="ns1")
            lop = st.text_input("Lớp", placeholder="10A1", key="lop1")
            truong = st.text_input("Trường", placeholder="THPT ABC", key="truong1")
        else:
            st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
            hoten_chuxe = st.text_input("Họ tên chủ xe *", placeholder="Nguyễn Văn B", key="cx1")
            ngaysinh_chuxe = st.text_input("Ngày sinh chủ xe *", placeholder="20/05/1975", key="nscx1")
            sdt_chuxe = st.text_input("Số điện thoại chủ xe *", placeholder="0912345678", key="sdt1")
    
    with col2:
        st.markdown("### 🚗 THÔNG TIN XE")
        bienso_xe = st.text_input("Biển số xe *", placeholder="59-A1 123.45", key="bs1")
        
        if loai_doituong == "🚗 XE CÁ NHÂN HỌC SINH":
            loai_xe = st.text_input("Loại xe", placeholder="Wave Alpha", key="lx1")
            mau_xe = st.text_input("Màu xe", placeholder="Đen", key="mx1")
            
        elif loai_doituong == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
            st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
            hoten_chuxe = st.text_input("Họ tên chủ xe *", placeholder="Nguyễn Văn B", key="cx2")
            ngaysinh_chuxe = st.text_input("Ngày sinh chủ xe *", placeholder="20/05/1975", key="nscx2")
            sdt_chuxe = st.text_input("Số điện thoại chủ xe *", placeholder="0912345678", key="sdt2")
            quanhe_voihocsinh = st.selectbox("Quan hệ với học sinh", 
                                           ["Bố", "Mẹ", "Ông", "Bà", "Anh", "Chị", "Khác"], key="qh1")
            
        else:  # XE GIA ĐÌNH
            loai_xe = st.text_input("Loại xe", placeholder="Vision", key="lx2")
            mau_xe = st.text_input("Màu xe", placeholder="Trắng", key="mx2")
    
    st.markdown("### 🔑 THIẾT LẬP MẬT KHẨU")
    col_pass1, col_pass2 = st.columns(2)
    
    with col_pass1:
        custom_password = st.text_input(
            "Mật khẩu tùy chỉnh *", 
            placeholder="Nhập mật khẩu để mở QR sau này",
            type="password",
            key="cp1"
        )
        
    with col_pass2:
        confirm_password = st.text_input(
            "Xác nhận mật khẩu *", 
            placeholder="Nhập lại mật khẩu",
            type="password",
            key="cf1"
        )
    
    st.markdown("### 📞 THÔNG TIN LIÊN HỆ (tùy chọn)")
    diachi = st.text_input("Địa chỉ", placeholder="123 Đường XYZ, Quận 1, TP.HCM", key="dc1")

    if st.button("🎯 TẠO MÃ QR", type="primary", key="btn1"):
        # Kiểm tra thông tin bắt buộc
        missing_fields = []
        
        if loai_doituong == "🚗 XE CÁ NHÂN HỌC SINH":
            if not hoten_hocsinh: missing_fields.append("Họ tên học sinh")
            if not ngaysinh_hocsinh: missing_fields.append("Ngày sinh học sinh")
            
        elif loai_doituong == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
            if not hoten_hocsinh: missing_fields.append("Họ tên học sinh")
            if not ngaysinh_hocsinh: missing_fields.append("Ngày sinh học sinh")
            if not hoten_chuxe: missing_fields.append("Họ tên chủ xe")
            if not ngaysinh_chuxe: missing_fields.append("Ngày sinh chủ xe")
            if not sdt_chuxe: missing_fields.append("Số điện thoại chủ xe")
            
        else:  # XE GIA ĐÌNH
            if not hoten_chuxe: missing_fields.append("Họ tên chủ xe")
            if not ngaysinh_chuxe: missing_fields.append("Ngày sinh chủ xe")
            if not sdt_chuxe: missing_fields.append("Số điện thoại chủ xe")
        
        if not bienso_xe: missing_fields.append("Biển số xe")
        if not custom_password: missing_fields.append("Mật khẩu tùy chỉnh")
        if not confirm_password: missing_fields.append("Xác nhận mật khẩu")
        
        if custom_password != confirm_password:
            st.error("⚠️ MẬT KHẨU XÁC NHẬN KHÔNG KHỚP!")
        elif missing_fields:
            st.error(f"⚠️ Vui lòng nhập các thông tin bắt buộc: {', '.join(missing_fields)}")
        else:
            # Tạo dictionary chứa thông tin
            fields = {
                "loai_xe": loai_doituong,
                "bienso_xe": bienso_xe,
                "diachi": diachi,
                "thoigian_taoma": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Thêm thông tin theo loại xe
            if loai_doituong == "🚗 XE CÁ NHÂN HỌC SINH":
                fields.update({
                    "hoten_hocsinh": hoten_hocsinh,
                    "ngaysinh_hocsinh": ngaysinh_hocsinh,
                    "lop": lop,
                    "truong": truong,
                    "loai_xe_chi_tiet": loai_xe,
                    "mau_xe": mau_xe
                })
                ngaysinh_mo_qr = ngaysinh_hocsinh
                
            elif loai_doituong == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
                fields.update({
                    "hoten_hocsinh": hoten_hocsinh,
                    "ngaysinh_hocsinh": ngaysinh_hocsinh,
                    "lop": lop,
                    "truong": truong,
                    "hoten_chuxe": hoten_chuxe,
                    "ngaysinh_chuxe": ngaysinh_chuxe,
                    "sdt_chuxe": sdt_chuxe,
                    "quanhe_voihocsinh": quanhe_voihocsinh
                })
                ngaysinh_mo_qr = ngaysinh_hocsinh
                
            else:  # XE GIA ĐÌNH
                fields.update({
                    "hoten_chuxe": hoten_chuxe,
                    "ngaysinh_chuxe": ngaysinh_chuxe,
                    "sdt_chuxe": sdt_chuxe,
                    "loai_xe_chi_tiet": loai_xe,
                    "mau_xe": mau_xe
                })
                ngaysinh_mo_qr = ngaysinh_chuxe
            
            # Loại bỏ các trường rỗng
            fields = {k: v for k, v in fields.items() if v}

            data_json = json.dumps(fields, ensure_ascii=False)

            # Mã hóa 3 lớp với các mật khẩu khác nhau
            encrypted_default = encrypt_data(data_json, DEFAULT_PASSWORD)
            encrypted_birthdate = encrypt_data(data_json, ngaysinh_mo_qr)
            encrypted_custom = encrypt_data(data_json, custom_password)

            # Gộp cả ba vào một JSON
            combo_data = json.dumps({
                "cong_an": encrypted_default,
                "ngay_sinh": encrypted_birthdate,
                "custom": encrypted_custom
            }, ensure_ascii=False)

            # TẠO QR CODE
            qr_img = create_proper_qr_code(combo_data)
            
            # Tạo buffer RIÊNG cho hiển thị
            display_buf = BytesIO()
            qr_img.save(display_buf, format="PNG", optimize=True)
            display_buf.seek(0)

            # Tạo buffer RIÊNG cho download PNG
            download_buf_png = BytesIO()
            qr_img.save(download_buf_png, format="PNG", optimize=True)
            download_buf_png.seek(0)

            # Tạo buffer RIÊNG cho download JPG (dự phòng)
            download_buf_jpg = BytesIO()
            qr_img.convert('RGB').save(download_buf_jpg, format="JPEG", quality=95)
            download_buf_jpg.seek(0)
            
            # Hiển thị kết quả
            col_success1, col_success2 = st.columns(2)
            
            with col_success1:
                st.image(display_buf.getvalue(), caption="✅ MÃ QR ĐÃ TẠO", use_column_width=True)
                
                # Nút download PNG
                st.download_button(
                    "⬇️ TẢI MÃ QR (PNG)",
                    download_buf_png.getvalue(), 
                    f"QR_{bienso_xe.replace(' ', '_')}.png",
                    "image/png"
                )
                
                # Nút download JPG (dự phòng)
                st.download_button(
                    "⬇️ TẢI MÃ QR (JPG)",
                    download_buf_jpg.getvalue(), 
                    f"QR_{bienso_xe.replace(' ', '_')}.jpg",
                    "image/jpeg"
                )
            
            with col_success2:
                st.success("🎉 TẠO MÃ QR THÀNH CÔNG!")
                
                # Hiển thị dữ liệu QR để copy
                st.markdown("### 📋 DỮ LIỆU QR ĐỂ SAO CHÉP:")
                st.code(combo_data, language="json")
                st.info("💡 **SAO CHÉP ĐOẠN CODE TRÊN để dán vào phần giải mã**")
                
                if loai_doituong == "🚗 XE CÁ NHÂN HỌC SINH":
                    st.info(f"**Loại:** Xe cá nhân học sinh")
                    st.info(f"**Học sinh:** {hoten_hocsinh}")
                    st.info(f"**Biển số:** {bienso_xe}")
                    
                elif loai_doituong == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
                    st.info(f"**Loại:** Xe gia đình - học sinh sử dụng tạm")
                    st.info(f"**Học sinh:** {hoten_hocsinh}")
                    st.info(f"**Chủ xe:** {hoten_chuxe} ({quanhe_voihocsinh})")
                    st.info(f"**Biển số:** {bienso_xe}")
                    
                else:
                    st.info(f"**Loại:** Xe gia đình")
                    st.info(f"**Chủ xe:** {hoten_chuxe}")
                    st.info(f"**Biển số:** {bienso_xe}")
                
                st.markdown("---")
                st.markdown("### 🔑 THÔNG TIN MẬT KHẨU:")
                st.success(f"**Mật khẩu tùy chỉnh:** {custom_password}")
                st.info(f"**Ngày sinh để mở QR:** {ngaysinh_mo_qr}")
                st.info("**Mật khẩu Công an:** Hệ thống")

# ---------- TAB 2: GIẢI MÃ THÔNG TIN ----------
with tab2:
    st.subheader("🔍 QUÉT MÃ QR ĐỂ TRA CỨU THÔNG TIN")
    
    st.markdown("### 📤 TẢI LÊN ẢNH CHỨA MÃ QR")
    uploaded = st.file_uploader("Chọn file ảnh", type=["png", "jpg", "jpeg"], key="up2")
    
    st.markdown("---")
    st.markdown("### 📋 HOẶC NHẬP DỮ LIỆU QR THỦ CÔNG")
    manual_qr_data = st.text_area("Dán dữ liệu từ mã QR vào đây", 
                                 placeholder='{"cong_an": "encrypted_data...", "ngay_sinh": "encrypted_data...", "custom": "encrypted_data..."}', 
                                 height=150, key="man2")
    
    st.markdown("---")
    st.markdown("### 🔑 CHỌN PHƯƠNG THỨC MỞ KHÓA")
    
    option = st.radio(
        "Chọn cách mở QR:",
        [
            "🔐 MẬT KHẨU TÙY CHỈNH", 
            "🎂 NGÀY SINH",
            "👮 MẬT KHẨU CÔNG AN"
        ],
        index=0,
        key="opt2"
    )
    
    password_dec = ""
    password_field_key = ""
    
    if option == "🔐 MẬT KHẨU TÙY CHỈNH":
        password_dec = st.text_input("🔒 NHẬP MẬT KHẨU TÙY CHỈNH", 
                                   placeholder="Nhập mật khẩu bạn đã đặt khi tạo QR",
                                   type="password",
                                   key="pass2")
        password_field_key = "custom"
        st.info("💡 Nhập mật khẩu tùy chỉnh đã đặt khi tạo mã QR")
        
    elif option == "🎂 NGÀY SINH":
        password_dec = st.text_input("🔒 NHẬP NGÀY SINH", 
                                   placeholder="Nhập ngày sinh học sinh/chủ xe",
                                   help="Định dạng: dd/mm/yyyy hoặc dd-mm-yyyy",
                                   key="bd2")
        password_field_key = "ngay_sinh"
        st.info("💡 Nhập ngày sinh của học sinh (xe cá nhân) hoặc chủ xe (xe gia đình)")
        
    elif option == "👮 MẬT KHẨU CÔNG AN":
        password_dec = st.text_input("🔒 NHẬP MẬT KHẨU HỆ THỐNG", 
                                   type="password",
                                   key="ca2")
        password_field_key = "cong_an"
        st.info("💡 Nhập mật khẩu được cấp cho Công an")

    if st.button("🚀 GIẢI MÃ THÔNG TIN", type="primary", key="btn2"):
        if not password_dec:
            st.warning("⚠️ VUI LÒNG NHẬP MẬT KHẨU!")
            st.stop()
            
        encrypted_combo = None
        
        # Ưu tiên dữ liệu nhập thủ công
        if manual_qr_data and manual_qr_data.strip():
            try:
                encrypted_combo = manual_qr_data.strip()
                st.success("✅ ĐÃ NHẬN DỮ LIỆU QR THỦ CÔNG")
            except:
                st.error("❌ DỮ LIỆU QR KHÔNG HỢP LỆ!")
        
        # Nếu không có dữ liệu thủ công, thử đọc từ ảnh
        elif uploaded:
            try:
                image = Image.open(uploaded)
                st.image(image, caption="Ảnh đã tải lên", width=300)
                
                if QR_READER_AVAILABLE:
                    try:
                        img_array = np.array(image)
                        if len(img_array.shape) == 3:
                            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                        else:
                            img_cv = img_array
                            
                        qr_codes = decode(img_cv)
                        if qr_codes:
                            encrypted_combo = qr_codes[0].data.decode()
                            st.success("✅ ĐÃ ĐỌC THÀNH CÔNG MÃ QR TỰ ẢNH!")
                        else:
                            st.warning("⚠️ KHÔNG TÌM THẤY MÃ QR TRONG ẢNH. Vui lòng nhập thủ công dữ liệu QR.")
                            st.stop()
                    except Exception as e:
                        st.error(f"❌ LỖI KHI ĐỌC MÃ QR: {str(e)}")
                        st.stop()
                else:
                    st.warning("⚠️ THƯ VIỆN ĐỌC QR CHƯA ĐƯỢC CÀI ĐẶT. Vui lòng nhập thủ công dữ liệu QR.")
                    st.info("💡 Chạy lệnh: pip install pyzbar")
                    st.stop()
                    
            except Exception as e:
                st.error(f"❌ LỖI KHI XỬ LÝ ẢNH: {str(e)}")
                st.stop()
        else:
            st.warning("⚠️ VUI LÒNG TẢI LÊN ẢNH HOẶC NHẬP DỮ LIỆU QR!")
            st.stop()

        # Xử lý giải mã
        if encrypted_combo:
            try:
                combo_json = json.loads(encrypted_combo)
            except Exception:
                st.error("❌ DỮ LIỆU MÃ QR KHÔNG HỢP LỆ!")
                st.stop()

            # Kiểm tra xem có phải QR trắng không
            is_blank_qr = combo_json.get('is_blank', False)
            
            if is_blank_qr:
                st.warning("⚠️ ĐÂY LÀ MÃ QR TRẮNG - CHƯA CÓ THÔNG TIN")
                st.info("💡 Vui lòng sử dụng tab 'TẠO & CẬP NHẬT QR TRẮNG' để thêm thông tin")
                st.stop()

            decrypted = None
            used_method = ""
            
            try:
                decrypted = decrypt_data(combo_json[password_field_key], password_dec)
                
                if option == "🔐 MẬT KHẨU TÙY CHỈNH":
                    used_method = "MẬT KHẨU TÙY CHỈNH"
                elif option == "🎂 NGÀY SINH":
                    used_method = "NGÀY SINH"
                elif option == "👮 MẬT KHẨU CÔNG AN":
                    if password_dec == DEFAULT_PASSWORD:
                        used_method = "MẬT KHẨU CÔNG AN"
                    else:
                        used_method = "MẬT KHẨU HỆ THỐNG"
                        
            except Exception:
                st.error("❌ MẬT KHẨU KHÔNG CHÍNH XÁC!")
                st.stop()

            if decrypted:
                st.success(f"✅ GIẢI MÃ THÀNH CÔNG! ({used_method})")
                st.balloons()
                
                data = json.loads(decrypted)
                
                # Hiển thị thông tin theo loại xe
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("### 📊 THÔNG TIN CHUNG")
                    st.write(f"**Loại xe:** {data.get('loai_xe', 'N/A')}")
                    st.write(f"**Biển số:** {data.get('bienso_xe', 'N/A')}")
                    st.write(f"**Địa chỉ:** {data.get('diachi', 'N/A')}")
                    st.write(f"**Thời gian tạo:** {data.get('thoigian_taoma', 'N/A')}")
                
                with col_info2:
                    if data.get('loai_xe') == "🚗 XE CÁ NHÂN HỌC SINH":
                        st.markdown("### 👤 THÔNG TIN HỌC SINH")
                        st.write(f"**Họ tên:** {data.get('hoten_hocsinh', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh_hocsinh', 'N/A')}")
                        st.write(f"**Trường:** {data.get('truong', 'N/A')}")
                        st.write(f"**Lớp:** {data.get('lop', 'N/A')}")
                        if data.get('loai_xe_chi_tiet'):
                            st.write(f"**Loại xe:** {data.get('loai_xe_chi_tiet', 'N/A')}")
                        if data.get('mau_xe'):
                            st.write(f"**Màu xe:** {data.get('mau_xe', 'N/A')}")
                        
                    elif data.get('loai_xe') == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
                        st.markdown("### 👤 THÔNG TIN HỌC SINH")
                        st.write(f"**Họ tên:** {data.get('hoten_hocsinh', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh_hocsinh', 'N/A')}")
                        st.write(f"**Trường:** {data.get('truong', 'N/A')}")
                        st.write(f"**Lớp:** {data.get('lop', 'N/A')}")
                        st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
                        st.write(f"**Chủ xe:** {data.get('hoten_chuxe', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh_chuxe', 'N/A')}")
                        st.write(f"**Quan hệ:** {data.get('quanhe_voihocsinh', 'N/A')}")
                        st.write(f"**Điện thoại:** {data.get('sdt_chuxe', 'N/A')}")
                        
                    else:  # XE GIA ĐÌNH
                        st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
                        st.write(f"**Chủ xe:** {data.get('hoten_chuxe', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh_chuxe', 'N/A')}")
                        st.write(f"**Điện thoại:** {data.get('sdt_chuxe', 'N/A')}")
                        if data.get('loai_xe_chi_tiet'):
                            st.write(f"**Loại xe:** {data.get('loai_xe_chi_tiet', 'N/A')}")
                        if data.get('mau_xe'):
                            st.write(f"**Màu xe:** {data.get('mau_xe', 'N/A')}")

# ---------- TAB 3: TẠO & CẬP NHẬT QR TRẮNG ----------
with tab3:
    st.subheader("⚪ TẠO & CẬP NHẬT QR TRẮNG")
    
    st.markdown("""
    ### 💡 CHẾ ĐỘ QR TRẮNG LÀ GÌ?
    - **QR trắng**: Tạo mã QR trước khi có thông tin, in sẵn để sử dụng sau
    - **Cập nhật sau**: Khi có thông tin học sinh/xe, quét QR trắng và thêm thông tin
    - **Bảo mật**: Vẫn có đầy đủ 3 lớp mật khẩu (Công an, ngày sinh, tùy chỉnh)
    """)
    
    tab3_1, tab3_2 = st.tabs(["🆕 TẠO QR TRẮNG", "📝 CẬP NHẬT QR TRẮNG"])
    
    # ---- TAB 3.1: TẠO QR TRẮNG ----
    with tab3_1:
        st.markdown("### 🆕 TẠO MÃ QR TRẮNG MỚI")
        
        st.info("""
        **ƯU ĐIỂM CỦA QR TRẮNG:**
        - In hàng loạt trước khi có thông tin
        - Tiết kiệm thời gian khi cần cấp phát nhanh
        - Dễ dàng quản lý kho QR code
        """)
        
        if st.button("⚪ TẠO QR TRẮNG", type="primary", key="btn_blank"):
            with st.spinner("Đang tạo QR trắng..."):
                combo_data, temp_password = create_blank_qr()
                
                # Tạo QR code từ dữ liệu
                qr_img = create_proper_qr_code(combo_data)
                
                # Tạo buffer cho hiển thị và download
                display_buf = BytesIO()
                qr_img.save(display_buf, format="PNG", optimize=True)
                display_buf.seek(0)
                
                download_buf = BytesIO()
                qr_img.save(download_buf, format="PNG", optimize=True)
                download_buf.seek(0)
                
                # Hiển thị kết quả
                col1, col2 = st.columns(2)
                
                with col1:
                    st.image(display_buf.getvalue(), caption="✅ QR TRẮNG ĐÃ TẠO", use_column_width=True)
                    
                    st.download_button(
                        "⬇️ TẢI QR TRẮNG (PNG)",
                        download_buf.getvalue(),
                        "QR_TRANG.png",
                        "image/png"
                    )
                
                with col2:
                    st.success("🎉 TẠO QR TRẮNG THÀNH CÔNG!")
                    
                    st.markdown("### 📋 DỮ LIỆU QR TRẮNG:")
                    st.code(combo_data, language="json")
                    
                    st.markdown("### 🔐 THÔNG TIN TẠM THỜI:")
                    st.warning(f"**Mật khẩu tạm thời:** {temp_password}")
                    st.info("💡 **Mật khẩu này sẽ được thay thế khi cập nhật thông tin**")
                    
                    st.markdown("### 📝 HƯỚNG DẪN SỬ DỤNG:")
                    st.write("1. **In QR code** này và dán lên xe")
                    st.write("2. **Khi có thông tin**, quét QR này trong tab 'CẬP NHẬT QR TRẮNG'")
                    st.write("3. **Nhập thông tin** và mật khẩu mới")
                    st.write("4. **QR sẽ được cập nhật** với thông tin đầy đủ")
    
    # ---- TAB 3.2: CẬP NHẬT QR TRẮNG ----
    with tab3_2:
        st.markdown("### 📝 CẬP NHẬT THÔNG TIN CHO QR TRẮNG")
        
        st.markdown("### 📤 TẢI LÊN QR TRẮNG HOẶC NHẬP DỮ LIỆU")
        uploaded_blank = st.file_uploader("Chọn file ảnh QR trắng", type=["png", "jpg", "jpeg"], key="up_blank")
        
        manual_blank_data = st.text_area("Hoặc dán dữ liệu QR trắng", 
                                       placeholder='{"cong_an": "encrypted_data...", "ngay_sinh": "encrypted_data...", "custom": "encrypted_data...", "is_blank": true}',
                                       height=100, key="man_blank")
        
        st.markdown("### 🔑 XÁC THỰC QR TRẮNG")
        temp_password = st.text_input("Nhập mật khẩu tạm thời của QR trắng", 
                                    type="password", 
                                    placeholder="Nhập mật khẩu tạm thời",
                                    key="temp_pass")
        
        st.markdown("---")
        st.markdown("### 📝 NHẬP THÔNG TIN MỚI")
        
        # Form nhập thông tin mới (giống tab 1 nhưng đơn giản hơn)
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.markdown("### 👤 THÔNG TIN CÁ NHÂN")
            loai_doituong_update = st.radio(
                "Loại đối tượng:",
                ["🚗 XE CÁ NHÂN HỌC SINH", "🏠 XE GIA ĐÌNH"],
                key="update_type"
            )
            
            if loai_doituong_update == "🚗 XE CÁ NHÂN HỌC SINH":
                hoten_update = st.text_input("Họ tên học sinh *", key="hs_update")
                ngaysinh_update = st.text_input("Ngày sinh học sinh *", key="ns_update")
                lop_update = st.text_input("Lớp", key="lop_update")
                truong_update = st.text_input("Trường", key="truong_update")
            else:
                hoten_update = st.text_input("Họ tên chủ xe *", key="cx_update")
                ngaysinh_update = st.text_input("Ngày sinh chủ xe *", key="nscx_update")
                sdt_update = st.text_input("Số điện thoại *", key="sdt_update")
        
        with col_info2:
            st.markdown("### 🚗 THÔNG TIN XE")
            bienso_update = st.text_input("Biển số xe *", key="bs_update")
            loai_xe_update = st.text_input("Loại xe", key="lx_update")
            mau_xe_update = st.text_input("Màu xe", key="mx_update")
            diachi_update = st.text_input("Địa chỉ", key="dc_update")
        
        st.markdown("### 🔑 THIẾT LẬP MẬT KHẨU MỚI")
        col_pass1, col_pass2 = st.columns(2)
        
        with col_pass1:
            new_custom_password = st.text_input("Mật khẩu tùy chỉnh mới *", 
                                              type="password", 
                                              key="new_pass")
        
        with col_pass2:
            confirm_new_password = st.text_input("Xác nhận mật khẩu mới *", 
                                               type="password", 
                                               key="conf_new_pass")
        
        if st.button("🔄 CẬP NHẬT QR TRẮNG", type="primary", key="btn_update"):
            # Kiểm tra dữ liệu đầu vào
            if not temp_password:
                st.error("⚠️ Vui lòng nhập mật khẩu tạm thời!")
                st.stop()
            
            # Lấy dữ liệu QR trắng
            blank_qr_data = None
            if manual_blank_data and manual_blank_data.strip():
                blank_qr_data = manual_blank_data.strip()
                st.success("✅ ĐÃ NHẬN DỮ LIỆU QR TRẮNG")
            elif uploaded_blank:
                try:
                    image = Image.open(uploaded_blank)
                    if QR_READER_AVAILABLE:
                        img_array = np.array(image)
                        if len(img_array.shape) == 3:
                            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                        else:
                            img_cv = img_array
                            
                        qr_codes = decode(img_cv)
                        if qr_codes:
                            blank_qr_data = qr_codes[0].data.decode()
                            st.success("✅ ĐÃ ĐỌC THÀNH CÔNG QR TRẮNG!")
                        else:
                            st.error("❌ KHÔNG TÌM THẤY MÃ QR TRONG ẢNH!")
                            st.stop()
                    else:
                        st.error("❌ THƯ VIỆN ĐỌC QR CHƯA ĐƯỢC CÀI ĐẶT!")
                        st.stop()
                except Exception as e:
                    st.error(f"❌ LỖI KHI ĐỌC QR TRẮNG: {str(e)}")
                    st.stop()
            else:
                st.error("⚠️ Vui lòng tải lên ảnh QR trắng hoặc nhập dữ liệu!")
                st.stop()
            
            # Kiểm tra xem có phải QR trắng không
            try:
                qr_json = json.loads(blank_qr_data)
                if not qr_json.get('is_blank', False):
                    st.error("❌ ĐÂY KHÔNG PHẢI LÀ QR TRẮNG!")
                    st.stop()
            except:
                st.error("❌ DỮ LIỆU QR KHÔNG HỢP LỆ!")
                st.stop()
            
            # Kiểm tra mật khẩu tạm thời
            try:
                # Thử giải mã với mật khẩu tạm thời
                temp_data = decrypt_data(qr_json['custom'], temp_password)
                st.success("✅ XÁC THỰC QR TRẮNG THÀNH CÔNG!")
            except:
                st.error("❌ MẬT KHẨU TẠM THỜI KHÔNG CHÍNH XÁC!")
                st.stop()
            
            # Kiểm tra thông tin mới
            missing_fields = []
            if not hoten_update: missing_fields.append("Họ tên")
            if not ngaysinh_update: missing_fields.append("Ngày sinh")
            if not bienso_update: missing_fields.append("Biển số xe")
            if not new_custom_password: missing_fields.append("Mật khẩu tùy chỉnh mới")
            if not confirm_new_password: missing_fields.append("Xác nhận mật khẩu mới")
            
            if new_custom_password != confirm_new_password:
                st.error("⚠️ MẬT KHẨU XÁC NHẬN KHÔNG KHỚP!")
            elif missing_fields:
                st.error(f"⚠️ Vui lòng nhập các thông tin bắt buộc: {', '.join(missing_fields)}")
            else:
                # Tạo dữ liệu mới
                new_data = {
                    "loai_xe": loai_doituong_update,
                    "bienso_xe": bienso_update,
                    "diachi": diachi_update,
                    "thoigian_taoma": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "thoigian_capnhat": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if loai_doituong_update == "🚗 XE CÁ NHÂN HỌC SINH":
                    new_data.update({
                        "hoten_hocsinh": hoten_update,
                        "ngaysinh_hocsinh": ngaysinh_update,
                        "lop": lop_update,
                        "truong": truong_update,
                        "loai_xe_chi_tiet": loai_xe_update,
                        "mau_xe": mau_xe_update
                    })
                    birthdate_password = ngaysinh_update
                else:
                    new_data.update({
                        "hoten_chuxe": hoten_update,
                        "ngaysinh_chuxe": ngaysinh_update,
                        "sdt_chuxe": sdt_update,
                        "loai_xe_chi_tiet": loai_xe_update,
                        "mau_xe": mau_xe_update
                    })
                    birthdate_password = ngaysinh_update
                
                # Loại bỏ trường rỗng
                new_data = {k: v for k, v in new_data.items() if v}
                
                # Cập nhật QR trắng
                updated_qr_data = update_blank_qr(
                    blank_qr_data, 
                    new_data, 
                    new_custom_password, 
                    birthdate_password
                )
                
                if updated_qr_data:
                    # Tạo QR code mới
                    updated_qr_img = create_proper_qr_code(updated_qr_data)
                    
                    # Tạo buffer
                    display_buf = BytesIO()
                    updated_qr_img.save(display_buf, format="PNG", optimize=True)
                    display_buf.seek(0)
                    
                    download_buf = BytesIO()
                    updated_qr_img.save(download_buf, format="PNG", optimize=True)
                    download_buf.seek(0)
                    
                    # Hiển thị kết quả
                    col_success1, col_success2 = st.columns(2)
                    
                    with col_success1:
                        st.image(display_buf.getvalue(), caption="✅ QR ĐÃ ĐƯỢC CẬP NHẬT", use_column_width=True)
                        
                        st.download_button(
                            "⬇️ TẢI QR ĐÃ CẬP NHẬT",
                            download_buf.getvalue(),
                            f"QR_{bienso_update.replace(' ', '_')}.png",
                            "image/png"
                        )
                    
                    with col_success2:
                        st.success("🎉 CẬP NHẬT QR TRẮNG THÀNH CÔNG!")
                        
                        st.markdown("### 📋 DỮ LIỆU QR MỚI:")
                        st.code(updated_qr_data, language="json")
                        
                        st.markdown("### 🔑 THÔNG TIN MẬT KHẨU MỚI:")
                        st.success(f"**Mật khẩu tùy chỉnh:** {new_custom_password}")
                        st.info(f"**Ngày sinh để mở QR:** {birthdate_password}")
                        st.info("**Mật khẩu Công an:** Hệ thống")
                        
                        st.balloons()

# ====== FOOTER ======
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎓 <strong>HỆ THỐNG QUẢN LÝ HỌC SINH THAM GIA GIAO THÔNG</strong></p>
    <p>Bản quyền © 2025 - Phát triển cho Cuộc thi Sáng kiến An toàn Giao thông</p>
</div>
""", unsafe_allow_html=True)
