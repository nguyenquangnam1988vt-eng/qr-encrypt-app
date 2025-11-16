import streamlit as st
import qrcode
import json
from cryptography.fernet import Fernet
from hashlib import sha256
import base64
from PIL import Image
from io import BytesIO
import re

# ====== MẬT KHẨU MẶC ĐỊNH CHO CÔNG AN ======
# Được lưu riêng, không hiển thị trong giao diện
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
st.set_page_config(page_title="Hệ Thống QR Code Quản Lý Học Sinh", page_icon="🎓", layout="wide")

st.title("🎓 HỆ THỐNG QUẢN LÝ HỌC SINH THAM GIA GIAO THÔNG")
st.markdown("**Ứng dụng mã QR thông minh cho Công an, Nhà trường và Phụ huynh**")

tab1, tab2 = st.tabs(["📦 TẠO MÃ QR CHO HỌC SINH", "🔓 GIẢI MÃ THÔNG TIN"])

# ---------- TAB 1: TẠO MÃ QR CHO HỌC SINH ----------
with tab1:
    st.subheader("📋 NHẬP THÔNG TIN HỌC SINH ĐỂ TẠO MÃ QR")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Thông tin cá nhân")
        hoten = st.text_input("Họ và tên học sinh *", placeholder="Nguyễn Văn A")
        ngaysinh = st.text_input("Ngày tháng năm sinh *", placeholder="15/07/2008")
        lop = st.text_input("Lớp", placeholder="10A1")
        truong = st.text_input("Trường", placeholder="THPT ABC")
        
    with col2:
        st.markdown("### Thông tin liên hệ")
        hoten_phuhuynh = st.text_input("Họ tên phụ huynh", placeholder="Nguyễn Văn B")
        sdt_phuhuynh = st.text_input("Số điện thoại phụ huynh", placeholder="0912345678")
        diachi = st.text_input("Địa chỉ", placeholder="123 Đường XYZ, Quận 1, TP.HCM")
        bienso_xe = st.text_input("Biển số xe (nếu có)", placeholder="59-A1 123.45")

    if st.button("🎯 TẠO MÃ QR CHO HỌC SINH", type="primary"):
        if not hoten or not ngaysinh:
            st.warning("⚠️ Vui lòng nhập ít nhất Họ tên và Ngày sinh của học sinh!")
        else:
            # Tạo dictionary chứa thông tin
            fields = {
                "hoten": hoten,
                "ngaysinh": ngaysinh,
                "lop": lop,
                "truong": truong,
                "hoten_phuhuynh": hoten_phuhuynh,
                "sdt_phuhuynh": sdt_phuhuynh,
                "diachi": diachi,
                "bienso_xe": bienso_xe,
                "thoigian_taoma": "2025-01-01 00:00:00"
            }
            
            # Loại bỏ các trường rỗng
            fields = {k: v for k, v in fields.items() if v}
            
            data_json = json.dumps(fields, ensure_ascii=False)

            # Mã hóa 2 lớp: 1 với mật khẩu mặc định (Công an), 1 với ngày sinh (Phụ huynh)
            encrypted_default = encrypt_data(data_json, DEFAULT_PASSWORD)  # Cho Công an
            encrypted_birthdate = encrypt_data(data_json, ngaysinh)        # Cho Phụ huynh

            # Gộp cả hai vào một JSON
            combo_data = json.dumps({
                "cong_an": encrypted_default,    # Mã hóa bằng mật khẩu Công an
                "phu_huynh": encrypted_birthdate # Mã hóa bằng ngày sinh
            }, ensure_ascii=False)

            # Tạo QR code
            qr = qrcode.make(combo_data)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            
            # Hiển thị kết quả
            col_success1, col_success2 = st.columns(2)
            
            with col_success1:
                st.image(buf.getvalue(), caption="✅ MÃ QR CÁ NHÂN CHO HỌC SINH", use_column_width=True)
                st.download_button(
                    "⬇️ TẢI MÃ QR VỀ MÁY",
                    buf.getvalue(), 
                    f"QR_{hoten.replace(' ', '_')}.png",
                    "image/png"
                )
            
            with col_success2:
                st.success("🎉 TẠO MÃ QR THÀNH CÔNG!")
                st.info(f"**Họ tên:** {hoten}")
                st.info(f"**Ngày sinh:** {ngaysinh}")
                st.info(f"**Trường:** {truong}")
                st.info(f"**Lớp:** {lop}")
                
                st.markdown("---")
                st.markdown("### 🔑 HƯỚNG DẪN TRUY CẬP:")
                st.markdown("**Phụ huynh:** Dùng ngày sinh của con để giải mã")
                st.markdown("**Công an:** Dùng mật khẩu hệ thống")
                
                st.markdown("---")
                st.markdown("### 📝 HƯỚNG DẪN SỬ DỤNG:")
                st.markdown("""
                1. **In mã QR** lên móc khóa và decal
                2. **Gắn móc khóa** vào chùm chìa xe
                3. **Dán decal** lên xe máy
                4. Khi cần kiểm tra, **quét mã QR** bằng tab GIẢI MÃ
                """)

# ---------- TAB 2: GIẢI MÃ THÔNG TIN ----------
with tab2:
    st.subheader("🔍 QUÉT MÃ QR ĐỂ TRA CỨU THÔNG TIN")
    
    st.markdown("### 📤 TẢI LÊN ẢNH CHỨA MÃ QR")
    uploaded = st.file_uploader("Chọn file ảnh", type=["png", "jpg", "jpeg"])
    
    # Phương án dự phòng: nhập thủ công dữ liệu QR
    st.markdown("---")
    st.markdown("### 🔄 HOẶC NHẬP THỦ CÔNG DỮ LIỆU QR")
    manual_qr_data = st.text_area("Dán dữ liệu từ mã QR vào đây", placeholder='{"cong_an": "encrypted_data", "phu_huynh": "encrypted_data"}', height=100)
    
    st.markdown("---")
    st.markdown("### 👥 CHỌN PHƯƠNG THỨC TRUY CẬP")
    
    option = st.radio(
        "Tôi là:",
        [
            "👨‍👩‍👧‍👦 PHỤ HUYNH (dùng ngày sinh con)", 
            "👮 CÔNG AN (dùng mật khẩu hệ thống)"
        ],
        index=0
    )
    
    # LUÔN PHẢI NHẬP MẬT KHẨU - không có tự động
    password_dec = ""
    if option == "👨‍👩‍👧‍👦 PHỤ HUYNH (dùng ngày sinh con)":
        password_dec = st.text_input("🔒 NHẬP NGÀY SINH CỦA CON", 
                                   placeholder="Nhập ngày sinh (VD: 15/07/2008)",
                                   type="password")
        st.info("💡 Nhập chính xác ngày sinh của con bạn như đã đăng ký")
        
    elif option == "👮 CÔNG AN (dùng mật khẩu hệ thống)":
        password_dec = st.text_input("🔒 NHẬP MẬT KHẨU HỆ THỐNG", 
                                   type="password")
        st.info("💡 Nhập mật khẩu được cấp cho Công an")

    if st.button("🚀 GIẢI MÃ THÔNG TIN", type="primary"):
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
                
                # Thử đọc QR code (đơn giản hóa)
                try:
                    from pyzbar.pyzbar import decode
                    import cv2
                    import numpy as np
                    
                    img_array = np.array(image)
                    if len(img_array.shape) == 3:
                        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    else:
                        img_cv = img_array
                        
                    qr_codes = decode(img_cv)
                    if qr_codes:
                        encrypted_combo = qr_codes[0].data.decode()
                        st.success("✅ ĐÃ ĐỌC THÀNH CÔNG MÃ QR TỪ ẢNH!")
                    else:
                        st.warning("⚠️ KHÔNG THỂ ĐỌC MÃ QR TỰ ĐỘNG. Vui lòng nhập thủ công.")
                        st.stop()
                except ImportError:
                    st.warning("⚠️ KHÔNG THỂ ĐỌC MÃ QR TỰ ĐỘNG. Vui lòng nhập thủ công dữ liệu QR ở trên.")
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
                # Giải mã lớp JSON
                try:
                    combo_json = json.loads(encrypted_combo)
                except Exception:
                    st.error("❌ DỮ LIỆU MÃ QR KHÔNG HỢP LỆ!")
                    st.stop()

                decrypted = None
                used_method = None
                
                # THỬ GIẢI MÃ THEO PHƯƠNG THỨC ĐÃ CHỌN
                if option == "👨‍👩‍👧‍👦 PHỤ HUYNH (dùng ngày sinh con)":
                    try:
                        decrypted = decrypt_data(combo_json["phu_huynh"], password_dec)
                        used_method = "NGÀY SINH"
                    except Exception:
                        st.error("❌ NGÀY SINH KHÔNG CHÍNH XÁC!")
                        
                elif option == "👮 CÔNG AN (dùng mật khẩu hệ thống)":
                    try:
                        decrypted = decrypt_data(combo_json["cong_an"], password_dec)
                        if password_dec == DEFAULT_PASSWORD:
                            used_method = "MẬT KHẨU CÔNG AN"
                        else:
                            used_method = "MẬT KHẨU HỆ THỐNG"
                    except Exception:
                        st.error("❌ MẬT KHẨU KHÔNG CHÍNH XÁC!")

                # HIỂN THỊ KẾT QUẢ
                if decrypted:
                    st.success(f"✅ GIẢI MÃ THÀNH CÔNG! ({used_method})")
                    st.balloons()
                    
                    data = json.loads(decrypted)
                    
                    # Hiển thị thông tin đẹp mắt
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.markdown("### 📊 THÔNG TIN HỌC SINH")
                        st.write(f"**Họ tên:** {data.get('hoten', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh', 'N/A')}")
                        st.write(f"**Trường:** {data.get('truong', 'N/A')}")
                        st.write(f"**Lớp:** {data.get('lop', 'N/A')}")
                    
                    with col_info2:
                        st.markdown("### 📞 THÔNG TIN LIÊN HỆ")
                        st.write(f"**Phụ huynh:** {data.get('hoten_phuhuynh', 'N/A')}")
                        st.write(f"**Điện thoại:** {data.get('sdt_phuhuynh', 'N/A')}")
                        st.write(f"**Địa chỉ:** {data.get('diachi', 'N/A')}")
                        st.write(f"**Biển số xe:** {data.get('bienso_xe', 'N/A')}")
                    
                    # Chức năng đặc biệt cho Công an
                    if option == "👮 CÔNG AN (dùng mật khẩu hệ thống)":
                        st.markdown("---")
                        st.warning("🚨 CHỨC NĂNG BÁO CÁO VI PHẠM")
                        col_report1, col_report2 = st.columns(2)
                        
                        with col_report1:
                            if st.button("📧 GỬI THÔNG BÁO ĐẾN PHỤ HUYNH"):
                                st.success(f"Đã gửi thông báo đến {data.get('hoten_phuhuynh', 'phụ huynh')}!")
                        
                        with col_report2:
                            if st.button("🏫 BÁO CÁO VỚI NHÀ TRƯỜNG"):
                                st.success(f"Đã báo cáo với trường {data.get('truong', 'nhà trường')}!")
                        
            except Exception as e:
                st.error(f"❌ LỖI KHI GIẢI MÃ: {str(e)}")

# ====== FOOTER ======
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎓 <strong>HỆ THỐNG QUẢN LÝ HỌC SINH THAM GIA GIAO THÔNG</strong></p>
    <p>Bản quyền © 2025 - Phát triển cho Cuộc thi Sáng kiến An toàn Giao thông</p>
</div>
""", unsafe_allow_html=True)
