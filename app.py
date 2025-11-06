import streamlit as st
import qrcode
import json
from cryptography.fernet import Fernet
from hashlib import sha256
import base64
from PIL import Image
from io import BytesIO

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

# ====== Giao diện web ======
st.title("🔐 Tạo & Giải mã QR có 2 loại mật khẩu (riêng & mặc định)")

tab1, tab2 = st.tabs(["📦 Tạo mã QR", "🔓 Giải mã QR"])

# ---------- TAB 1: TẠO MÃ ----------
with tab1:
    st.subheader("Nhập thông tin để tạo mã QR")

    password = st.text_input("Nhập mật khẩu riêng để bảo vệ", type="password")
    num_fields = st.number_input("Số lượng trường thông tin", 1, 10, 1)

    fields = {}
    for i in range(num_fields):
        key = st.text_input(f"Tên trường {i+1}")
        val = st.text_input(f"Giá trị {i+1}")
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
            st.download_button("⬇️ Tải mã QR", buf.getvalue(), "ma_hoa_qr.png")

# ---------- TAB 2: GIẢI MÃ ----------
with tab2:
    st.subheader("Tải lên ảnh QR để giải mã")

    uploaded = st.file_uploader("Chọn ảnh QR", type=["png", "jpg", "jpeg"])
    password_dec = st.text_input("Nhập mật khẩu (mặc định hoặc riêng)", type="password")

    if st.button("Giải mã"):
        if not uploaded:
            st.warning("⚠️ Chưa chọn ảnh QR.")
        elif not password_dec:
            st.warning("⚠️ Chưa nhập mật khẩu.")
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
                    try:
                        # Thử với mật khẩu người dùng nhập
                        decrypted = decrypt_data(combo_json["user"], password_dec)
                    except Exception:
                        try:
                            # Nếu thất bại, thử với mật khẩu mặc định
                            decrypted = decrypt_data(combo_json["default"], password_dec)
                        except Exception:
                            pass

                    if decrypted:
                        st.success("✅ Giải mã thành công!")
                        data = json.loads(decrypted)
                        st.json(data)
                    else:
                        st.error("❌ Mật khẩu sai hoặc mã QR không hợp lệ.")
            except Exception as e:
                st.error("❌ Có lỗi xảy ra khi xử lý ảnh QR.")
