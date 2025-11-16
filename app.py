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

tab1, tab2 = st.tabs(["📦 TẠO MÃ QR", "🔓 GIẢI MÃ THÔNG TIN"])

# ---------- TAB 1: TẠO MÃ QR ----------
with tab1:
    st.subheader("📋 NHẬP THÔNG TIN ĐỂ TẠO MÃ QR")
    
    st.markdown("### 🎯 CHỌN LOẠI ĐỐI TƯỢNG SỬ DỤNG")
    loai_doituong = st.radio(
        "Đây là:",
        [
            "🚗 XE CÁ NHÂN CỦA HỌC SINH",
            "🏠 XE GIA ĐÌNH (học sinh sử dụng tạm)"
        ],
        index=0
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👤 THÔNG TIN NGƯỜI SỬ DỤNG")
        hoten_hocsinh = st.text_input("Họ tên học sinh *", placeholder="Nguyễn Văn A")
        ngaysinh_hocsinh = st.text_input("Ngày sinh học sinh *", placeholder="15/07/2008")
        lop = st.text_input("Lớp", placeholder="10A1")
        truong = st.text_input("Trường", placeholder="THPT ABC")
    
    with col2:
        if loai_doituong == "🚗 XE CÁ NHÂN CỦA HỌC SINH":
            st.markdown("### 📄 THÔNG TIN XE CÁ NHÂN")
            bienso_xe = st.text_input("Biển số xe *", placeholder="59-A1 123.45")
            loai_xe = st.text_input("Loại xe", placeholder="Wave Alpha")
            mau_xe = st.text_input("Màu xe", placeholder="Đen")
        else:
            st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE GIA ĐÌNH")
            hoten_chuxe = st.text_input("Họ tên chủ xe *", placeholder="Nguyễn Văn B")
            sdt_chuxe = st.text_input("Số điện thoại chủ xe *", placeholder="0912345678")
            bienso_xe = st.text_input("Biển số xe gia đình *", placeholder="59-A1 123.45")
    
    st.markdown("### 📞 THÔNG TIN LIÊN HỆ (tùy chọn)")
    diachi = st.text_input("Địa chỉ", placeholder="123 Đường XYZ, Quận 1, TP.HCM")

    if st.button("🎯 TẠO MÃ QR", type="primary"):
        # Kiểm tra thông tin bắt buộc
        missing_fields = []
        if not hoten_hocsinh: missing_fields.append("Họ tên học sinh")
        if not ngaysinh_hocsinh: missing_fields.append("Ngày sinh học sinh")
        
        if loai_doituong == "🚗 XE CÁ NHÂN CỦA HỌC SINH":
            if not bienso_xe: missing_fields.append("Biển số xe")
        else:
            if not hoten_chuxe: missing_fields.append("Họ tên chủ xe")
            if not sdt_chuxe: missing_fields.append("Số điện thoại chủ xe")
            if not bienso_xe: missing_fields.append("Biển số xe")
        
        if missing_fields:
            st.error(f"⚠️ Vui lòng nhập các thông tin bắt buộc: {', '.join(missing_fields)}")
        else:
            # Tạo dictionary chứa thông tin
            fields = {
                "loai_doituong": loai_doituong,
                "hoten_hocsinh": hoten_hocsinh,
                "ngaysinh_hocsinh": ngaysinh_hocsinh,
                "lop": lop,
                "truong": truong,
                "diachi": diachi,
                "thoigian_taoma": "2025-01-01 00:00:00"
            }
            
            # Thêm thông tin theo loại đối tượng
            if loai_doituong == "🚗 XE CÁ NHÂN CỦA HỌC SINH":
                fields.update({
                    "bienso_xe": bienso_xe,
                    "loai_xe": loai_xe,
                    "mau_xe": mau_xe,
                    "loai_xe": "XE CÁ NHÂN HỌC SINH"
                })
            else:
                fields.update({
                    "hoten_chuxe": hoten_chuxe,
                    "sdt_chuxe": sdt_chuxe,
                    "bienso_xe": bienso_xe,
                    "loai_xe": "XE GIA ĐÌNH"
                })
            
            # Loại bỏ các trường rỗng
            fields = {k: v for k, v in fields.items() if v}
            
            data_json = json.dumps(fields, ensure_ascii=False)

            # Mã hóa 2 lớp
            encrypted_default = encrypt_data(data_json, DEFAULT_PASSWORD)  # Cho Công an
            encrypted_birthdate = encrypt_data(data_json, ngaysinh_hocsinh) # Cho Phụ huynh

            # Gộp cả hai vào một JSON
            combo_data = json.dumps({
                "cong_an": encrypted_default,
                "phu_huynh": encrypted_birthdate
            }, ensure_ascii=False)

            # Tạo QR code
            qr = qrcode.make(combo_data)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            
            # Hiển thị kết quả
            col_success1, col_success2 = st.columns(2)
            
            with col_success1:
                st.image(buf.getvalue(), caption="✅ MÃ QR ĐÃ TẠO", use_column_width=True)
                st.download_button(
                    "⬇️ TẢI MÃ QR VỀ MÁY",
                    buf.getvalue(), 
                    f"QR_{hoten_hocsinh.replace(' ', '_')}.png",
                    "image/png"
                )
            
            with col_success2:
                st.success("🎉 TẠO MÃ QR THÀNH CÔNG!")
                
                if loai_doituong == "🚗 XE CÁ NHÂN CỦA HỌC SINH":
                    st.info(f"**Loại:** Xe cá nhân học sinh")
                    st.info(f"**Học sinh:** {hoten_hocsinh}")
                    st.info(f"**Biển số:** {bienso_xe}")
                else:
                    st.info(f"**Loại:** Xe gia đình")
                    st.info(f"**Học sinh:** {hoten_hocsinh}")
                    st.info(f"**Chủ xe:** {hoten_chuxe}")
                    st.info(f"**Biển số:** {bienso_xe}")
                
                st.info(f"**Ngày sinh:** {ngaysinh_hocsinh}")
                
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
                combo_json = json.loads(encrypted_combo)
            except Exception:
                st.error("❌ DỮ LIỆU MÃ QR KHÔNG HỢP LỆ!")
                st.stop()

            decrypted = None
            used_method = None
            
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

            if decrypted:
                st.success(f"✅ GIẢI MÃ THÀNH CÔNG! ({used_method})")
                st.balloons()
                
                data = json.loads(decrypted)
                
                # Hiển thị thông tin theo loại đối tượng
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("### 📊 THÔNG TIN HỌC SINH")
                    st.write(f"**Họ tên:** {data.get('hoten_hocsinh', 'N/A')}")
                    st.write(f"**Ngày sinh:** {data.get('ngaysinh_hocsinh', 'N/A')}")
                    st.write(f"**Trường:** {data.get('truong', 'N/A')}")
                    st.write(f"**Lớp:** {data.get('lop', 'N/A')}")
                    st.write(f"**Loại xe:** {data.get('loai_doituong', 'N/A')}")
                
                with col_info2:
                    st.markdown("### 🚗 THÔNG TIN XE")
                    st.write(f"**Biển số:** {data.get('bienso_xe', 'N/A')}")
                    
                    if data.get('loai_doituong') == "🏠 XE GIA ĐÌNH (học sinh sử dụng tạm)":
                        st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
                        st.write(f"**Chủ xe:** {data.get('hoten_chuxe', 'N/A')}")
                        st.write(f"**Điện thoại:** {data.get('sdt_chuxe', 'N/A')}")
                    else:
                        st.write(f"**Loại xe:** {data.get('loai_xe', 'N/A')}")
                        st.write(f"**Màu xe:** {data.get('mau_xe', 'N/A')}")
                    
                    st.write(f"**Địa chỉ:** {data.get('diachi', 'N/A')}")
                
                # Chức năng cho Công an
                if option == "👮 CÔNG AN (dùng mật khẩu hệ thống)":
                    st.markdown("---")
                    st.warning("🚨 CHỨC NĂNG BÁO CÁO VI PHẠM")
                    col_report1, col_report2 = st.columns(2)
                    
                    with col_report1:
                        if st.button("📧 GỬI THÔNG BÁO ĐẾN PHỤ HUYNH"):
                            if data.get('loai_doituong') == "🏠 XE GIA ĐÌNH (học sinh sử dụng tạm)":
                                st.success(f"Đã gửi thông báo đến {data.get('hoten_chuxe', 'chủ xe')}!")
                            else:
                                st.success(f"Đã gửi thông báo đến phụ huynh học sinh!")
                    
                    with col_report2:
                        if st.button("🏫 BÁO CÁO VỚI NHÀ TRƯỜNG"):
                            st.success(f"Đã báo cáo với trường {data.get('truong', 'nhà trường')}!")
                        
# ====== FOOTER ======
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎓 <strong>HỆ THỐNG QUẢN LÝ HỌC SINH THAM GIA GIAO THÔNG</strong></p>
    <p>Bản quyền © 2025 - Phát triển cho Cuộc thi Sáng kiến An toàn Giao thông</p>
</div>
""", unsafe_allow_html=True)
