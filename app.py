import streamlit as st
import qrcode
import json
from cryptography.fernet import Fernet
from hashlib import sha256
import base64
from PIL import Image
from io import BytesIO
import re
from datetime import datetime

# ====== MẬT KHẨU MẶC ĐỊNH ======
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

# ====== Hàm xử lý ngày sinh ======
def extract_and_format_birthdate(data_dict):
    """
    Tìm và trích xuất ngày sinh từ dữ liệu, trả về các định dạng có thể dùng làm mật khẩu
    """
    birthdate_formats = []
    
    # Các key có thể chứa ngày sinh
    birth_keys = ['ngaysinh', 'birthdate', 'birthday', 'dob', 'ngay_sinh', 'dateofbirth']
    
    for key, value in data_dict.items():
        # Kiểm tra cả key và value
        search_targets = [str(key).lower(), str(value)]
        
        for target in search_targets:
            # Tìm các định dạng ngày tháng
            patterns = [
                r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',  # dd/mm/yyyy, dd-mm-yyyy
                r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',  # yyyy/mm/dd, yyyy-mm-dd
                r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2})\b',   # dd/mm/yy, dd-mm-yy
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, target)
                for match in matches:
                    if len(match) == 3:
                        if len(match[2]) == 4:  # yyyy
                            day, month, year = match[0], match[1], match[2]
                            # Đảm bảo đúng định dạng dd/mm/yyyy
                            if len(day) == 1: day = '0' + day
                            if len(month) == 1: month = '0' + month
                            birthdate_formats.append(f"{day}/{month}/{year}")
                            birthdate_formats.append(f"{day}-{month}-{year}")
                            birthdate_formats.append(f"{day}{month}{year}")
                        else:  # yy
                            day, month, year = match[0], match[1], match[2]
                            if len(day) == 1: day = '0' + day
                            if len(month) == 1: month = '0' + month
                            # Chuyển yy thành yyyy (giả sử thuộc thế kỷ 20)
                            full_year = '19' + year if int(year) >= 0 and int(year) <= 99 else year
                            birthdate_formats.append(f"{day}/{month}/{full_year}")
    
    # Loại bỏ trùng lặp và trả về
    return list(set(birthdate_formats))

def try_birthdate_passwords(combo_json, birthdate_passwords):
    """
    Thử giải mã với danh sách mật khẩu từ ngày sinh
    """
    for bd_password in birthdate_passwords:
        try:
            decrypted = decrypt_data(combo_json["user"], bd_password)
            return decrypted, bd_password
        except Exception:
            try:
                decrypted = decrypt_data(combo_json["default"], bd_password)
                return decrypted, bd_password
            except Exception:
                continue
    return None, None

# ====== Giao diện web ======
st.title("🔐 Tạo & Giải mã QR có 3 loại mật khẩu (riêng, mặc định & ngày sinh)")

tab1, tab2 = st.tabs(["📦 Tạo mã QR", "🔓 Giải mã QR"])

# ---------- TAB 1: TẠO MÃ ----------
with tab1:
    st.subheader("Nhập thông tin để tạo mã QR")

    password = st.text_input("Nhập mật khẩu riêng để bảo vệ", type="password")
    num_fields = st.number_input("Số lượng trường thông tin", 1, 10, 1)

    fields = {}
    for i in range(num_fields):
        key = st.text_input(f"Tên trường {i+1}", placeholder=f"VD: hoten, ngaysinh...")
        val = st.text_input(f"Giá trị {i+1}", placeholder=f"VD: Nguyen Van A, 15/7/1983...")
        if key:
            fields[key] = val

    if st.button("Tạo mã QR"):
        if not password:
            st.warning("⚠️ Vui lòng nhập mật khẩu riêng!")
        elif not fields:
            st.warning("⚠️ Cần ít nhất 1 trường thông tin!")
        else:
            data_json = json.dumps(fields, ensure_ascii=False)

            # Mã hóa 2 lớp: 1 với mật khẩu riêng, 1 với mật khẩu mặc định
            encrypted_user = encrypt_data(data_json, password)
            encrypted_default = encrypt_data(data_json, DEFAULT_PASSWORD)

            # Gộp cả hai vào một JSON
            combo_data = json.dumps({
                "user": encrypted_user,
                "default": encrypted_default
            }, ensure_ascii=False)

            qr = qrcode.make(combo_data)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="✅ Mã QR được tạo thành công!")
            
            # Hiển thị thông tin về tính năng ngày sinh
            birthdate_passwords = extract_and_format_birthdate(fields)
            if birthdate_passwords:
                st.info(f"🔑 Gợi ý mật khẩu từ ngày sinh: {', '.join(birthdate_passwords)}")
            
            st.download_button("⬇️ Tải mã QR", buf.getvalue(), "ma_hoa_qr.png")

# ---------- TAB 2: GIẢI MÃ ----------
with tab2:
    st.subheader("Tải lên ảnh QR để giải mã")

    uploaded = st.file_uploader("Chọn ảnh QR", type=["png", "jpg", "jpeg"])
    password_dec = st.text_input("Nhập mật khẩu (để trống nếu muốn thử tự động với ngày sinh)", type="password")

    if st.button("Giải mã"):
        if not uploaded:
            st.warning("⚠️ Chưa chọn ảnh QR.")
        else:
            try:
                import cv2, numpy as np
                from pyzbar.pyzbar import decode

                img = Image.open(uploaded)
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                qr_codes = decode(img_cv)

                if not qr_codes:
                    st.error("❌ Không phát hiện được mã QR.")
                else:
                    encrypted_combo = qr_codes[0].data.decode()

                    # Giải mã lớp JSON chứa 2 đoạn mã hóa
                    try:
                        combo_json = json.loads(encrypted_combo)
                    except Exception:
                        st.error("❌ Dữ liệu mã QR không hợp lệ.")
                        st.stop()

                    decrypted = None
                    used_password = None
                    
                    # TRƯỜNG HỢP 1: Có nhập mật khẩu
                    if password_dec:
                        try:
                            decrypted = decrypt_data(combo_json["user"], password_dec)
                            used_password = "Mật khẩu người dùng nhập"
                        except Exception:
                            try:
                                decrypted = decrypt_data(combo_json["default"], password_dec)
                                used_password = "Mật khẩu mặc định"
                            except Exception:
                                pass
                    
                    # TRƯỜNG HỢP 2: Tự động thử với ngày sinh
                    if not decrypted:
                        # Trước tiên thử giải mã với mật khẩu mặc định để lấy thông tin ngày sinh
                        try:
                            temp_decrypted = decrypt_data(combo_json["default"], DEFAULT_PASSWORD)
                            temp_data = json.loads(temp_decrypted)
                            
                            # Trích xuất các định dạng ngày sinh
                            birthdate_passwords = extract_and_format_birthdate(temp_data)
                            
                            if birthdate_passwords:
                                st.info(f"🔍 Đang thử các mật khẩu từ ngày sinh: {', '.join(birthdate_passwords)}")
                                
                                # Thử giải mã với các định dạng ngày sinh
                                decrypted, used_bd_password = try_birthdate_passwords(combo_json, birthdate_passwords)
                                if decrypted:
                                    used_password = f"Ngày sinh: {used_bd_password}"
                        except Exception:
                            pass

                    if decrypted:
                        st.success(f"✅ Giải mã thành công! ({used_password})")
                        data = json.loads(decrypted)
                        st.json(data)
                    else:
                        st.error("❌ Không thể giải mã với mật khẩu đã nhập hoặc ngày sinh tìm thấy.")
                        
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra khi xử lý ảnh QR: {str(e)}")
