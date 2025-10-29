import streamlit as st
import qrcode
import json
from cryptography.fernet import Fernet
from hashlib import sha256
import base64
from PIL import Image
from io import BytesIO

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

# ====== Giao diện web ======
st.title("🔐 Tạo & Giải mã QR có mật khẩu")

tab1, tab2 = st.tabs(["📦 Tạo mã QR", "🔓 Giải mã QR"])

# ---------- TAB 1: TẠO MÃ ----------
with tab1:
    st.subheader("Nhập thông tin để tạo mã QR")

    password = st.text_input("Nhập mật khẩu bảo vệ", type="password")
    num_fields = st.number_input("Số lượng trường thông tin", 1, 10, 1)

    fields = {}
    for i in range(num_fields):
        key = st.text_input(f"Tên trường {i+1}")
        val = st.text_input(f"Giá trị {i+1}")
        if key:
            fields[key] = val

    if st.button("Tạo mã QR"):
        if not password:
            st.warning("⚠️ Vui lòng nhập mật khẩu!")
        elif not fields:
            st.warning("⚠️ Cần ít nhất 1 trường thông tin!")
        else:
            data_json = json.dumps(fields, ensure_ascii=False)
            encrypted = encrypt_data(data_json, password)
            qr = qrcode.make(encrypted)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Mã QR được tạo")
            st.download_button("Tải mã QR", buf.getvalue(), "ma_hoa_qr.png")

# ---------- TAB 2: GIẢI MÃ ----------
with tab2:
    st.subheader("Tải lên ảnh QR để giải mã")

    uploaded = st.file_uploader("Chọn ảnh QR", type=["png", "jpg", "jpeg"])
    password_dec = st.text_input("Nhập mật khẩu", type="password")

    if st.button("Giải mã"):
        if not uploaded:
            st.warning("⚠️ Chưa chọn ảnh QR.")
        elif not password_dec:
            st.warning("⚠️ Chưa nhập mật khẩu.")
        else:
            try:
                img = Image.open(uploaded)
                import cv2, numpy as np
                from pyzbar.pyzbar import decode

                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                qr_codes = decode(img_cv)
                if not qr_codes:
                    st.error("❌ Không phát hiện được mã QR.")
                else:
                    encrypted_data = qr_codes[0].data.decode()
                    decrypted = decrypt_data(encrypted_data, password_dec)
                    st.success("✅ Giải mã thành công!")
                    data = json.loads(decrypted)
                    st.json(data)
            except Exception as e:
                st.error("❌ Mật khẩu sai hoặc mã QR không hợp lệ.")
