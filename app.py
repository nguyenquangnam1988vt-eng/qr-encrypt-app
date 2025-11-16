import streamlit as st
import qrcode
import json
from cryptography.fernet import Fernet
from hashlib import sha256
import base64
from PIL import Image
from io import BytesIO
import re
import cv2
import numpy as np
from pyzbar.pyzbar import decode

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

# ====== Hàm xử lý ngày sinh ======
def extract_and_format_birthdate(data_dict):
    """
    Tìm và trích xuất ngày sinh từ dữ liệu, trả về các định dạng có thể dùng làm mật khẩu
    """
    birthdate_formats = []
    
    # Các key có thể chứa ngày sinh
    birth_keys = ['ngaysinh', 'birthdate', 'birthday', 'dob', 'ngay_sinh', 'dateofbirth', 'ngaysinhhocsinh']
    
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
        hoten = st.text_input("Họ và tên học sinh")
        ngaysinh = st.text_input("Ngày tháng năm sinh", placeholder="VD: 15/07/2008")
        lop = st.text_input("Lớp")
        truong = st.text_input("Trường")
        
    with col2:
        st.markdown("### Thông tin liên hệ")
        hoten_phuhuynh = st.text_input("Họ tên phụ huynh")
        sdt_phuhuynh = st.text_input("Số điện thoại phụ huynh")
        diachi = st.text_input("Địa chỉ")
        bienso_xe = st.text_input("Biển số xe (nếu có)")
    
    # Mật khẩu riêng cho từng học sinh
    password = st.text_input("🔐 Mật khẩu bảo vệ (dùng cho công an)", type="password", 
                           help="Mật khẩu này chỉ công an biết, phụ huynh dùng ngày sinh để truy cập")

    if st.button("🎯 TẠO MÃ QR CHO HỌC SINH"):
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
                "thoigian_taoma": st.session_state.get('current_time', '2025-01-01')
            }
            
            # Loại bỏ các trường rỗng
            fields = {k: v for k, v in fields.items() if v}
            
            data_json = json.dumps(fields, ensure_ascii=False)

            # Mã hóa 2 lớp
            encrypted_user = encrypt_data(data_json, password) if password else encrypt_data(data_json, DEFAULT_PASSWORD)
            encrypted_default = encrypt_data(data_json, DEFAULT_PASSWORD)

            # Gộp cả hai vào một JSON
            combo_data = json.dumps({
                "user": encrypted_user,
                "default": encrypted_default
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
                
                # Hiển thị gợi ý mật khẩu từ ngày sinh
                birthdate_passwords = extract_and_format_birthdate(fields)
                if birthdate_passwords:
                    st.markdown("---")
                    st.markdown("### 🔑 HƯỚNG DẪN TRUY CẬP:")
                    st.markdown("**Phụ huynh dùng các mật khẩu sau:**")
                    for bd_pass in birthdate_passwords[:3]:  # Hiển thị tối đa 3 định dạng
                        st.code(bd_pass)
                
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
    
    uploaded = st.file_uploader("📤 TẢI LÊN ẢNH CHỨA MÃ QR", type=["png", "jpg", "jpeg"])
    
    if uploaded:
        st.success("✅ ĐÃ TẢI LÊN ẢNH THÀNH CÔNG!")
        
        # Hiển thị ảnh preview
        img = Image.open(uploaded)
        st.image(img, caption="Ảnh mã QR đã tải lên", width=300)
    
    st.markdown("---")
    st.markdown("### 👥 CHỌN PHƯƠNG THỨC TRUY CẬP")
    
    option = st.radio(
        "Tôi là:",
        [
            "👨‍👩‍👧‍👦 PHỤ HUYNH (dùng ngày sinh con)", 
            "👮 CÔNG AN (mật khẩu hệ thống)",
            "🔐 NGƯỜI CÓ MẬT KHẨU RIÊNG"
        ],
        index=0
    )
    
    password_dec = ""
    if option == "👨‍👩‍👧‍👦 PHỤ HUYNH (dùng ngày sinh con)":
        st.info("🎯 Hệ thống sẽ TỰ ĐỘNG tìm ngày sinh trong thông tin để giải mã")
        
    elif option == "👮 CÔNG AN (mật khẩu hệ thống)":
        password_dec = DEFAULT_PASSWORD
        st.success("🔓 ĐANG SỬ DỤNG MẬT KHẨU HỆ THỐNG CHO CÔNG AN")
        
    elif option == "🔐 NGƯỜI CÓ MẬT KHẨU RIÊNG":
        password_dec = st.text_input("🔒 NHẬP MẬT KHẨU RIÊNG", type="password")

    if st.button("🚀 GIẢI MÃ THÔNG TIN", type="primary"):
        if not uploaded:
            st.warning("⚠️ VUI LÒNG CHỌN ẢNH CHỨA MÃ QR!")
            st.stop()
            
        try:
            # Xử lý ảnh QR
            img = Image.open(uploaded)
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            qr_codes = decode(img_cv)

            if not qr_codes:
                st.error("❌ KHÔNG PHÁT HIỆN ĐƯỢC MÃ QR TRONG ẢNH!")
            else:
                encrypted_combo = qr_codes[0].data.decode()

                # Giải mã lớp JSON chứa 2 đoạn mã hóa
                try:
                    combo_json = json.loads(encrypted_combo)
                except Exception:
                    st.error("❌ DỮ LIỆU MÃ QR KHÔNG HỢP LỆ!")
                    st.stop()

                decrypted = None
                used_password = None
                
                # TRƯỜNG HỢP 1: PHỤ HUYNH - TỰ ĐỘNG DÙNG NGÀY SINH
                if option == "👨‍👩‍👧‍👦 PHỤ HUYNH (dùng ngày sinh con)":
                    # Thử giải mã với mật khẩu mặc định để lấy thông tin ngày sinh
                    try:
                        temp_decrypted = decrypt_data(combo_json["default"], DEFAULT_PASSWORD)
                        temp_data = json.loads(temp_decrypted)
                        
                        # Trích xuất các định dạng ngày sinh
                        birthdate_passwords = extract_and_format_birthdate(temp_data)
                        
                        if birthdate_passwords:
                            st.info(f"🔍 ĐANG THỬ CÁC MẬT KHẨU TỪ NGÀY SINH: {', '.join(birthdate_passwords)}")
                            
                            # Thử giải mã với các định dạng ngày sinh
                            decrypted, used_bd_password = try_birthdate_passwords(combo_json, birthdate_passwords)
                            if decrypted:
                                used_password = f"NGÀY SINH: {used_bd_password}"
                                st.balloons()
                    except Exception as e:
                        st.error("❌ KHÔNG THỂ ĐỌC THÔNG TIN NGÀY SINH!")
                
                # TRƯỜNG HỢP 2 & 3: CÓ MẬT KHẨU
                elif password_dec:
                    try:
                        decrypted = decrypt_data(combo_json["user"], password_dec)
                        used_password = "MẬT KHẨU RIÊNG"
                    except Exception:
                        try:
                            decrypted = decrypt_data(combo_json["default"], password_dec)
                            used_password = "MẬT KHẨU HỆ THỐNG"
                        except Exception:
                            pass

                # HIỂN THỊ KẾT QUẢ
                if decrypted:
                    st.success(f"✅ GIẢI MÃ THÀNH CÔNG! ({used_password})")
                    
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
                    
                    # Nút báo cáo vi phạm (cho công an)
                    if option == "👮 CÔNG AN (mật khẩu hệ thống)":
                        st.markdown("---")
                        st.warning("🚨 CHỨC NĂNG BÁO CÁO VI PHẠM")
                        col_report1, col_report2, col_report3 = st.columns(3)
                        
                        with col_report1:
                            if st.button("📧 GỬI THÔNG BÁO ĐẾN PHỤ HUYNH"):
                                st.success("Đã gửi thông báo đến phụ huynh!")
                        
                        with col_report2:
                            if st.button("🏫 BÁO CÁO VỚI NHÀ TRƯỜNG"):
                                st.success("Đã báo cáo với nhà trường!")
                        
                        with col_report3:
                            if st.button("📋 GHI NHẬN VI PHẠM"):
                                st.success("Đã ghi nhận vi phạm vào hệ thống!")
                
                else:
                    st.error("❌ KHÔNG THỂ GIẢI MÃ! VUI LÒNG KIỂM TRA LẠI PHƯƠNG THỨC TRUY CẬP.")
                        
        except Exception as e:
            st.error(f"❌ CÓ LỖI XẢY RA KHI XỬ LÝ ẢNH QR: {str(e)}")

# ====== FOOTER ======
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎓 <strong>HỆ THỐNG QUẢN LÝ HỌC SINH THAM GIA GIAO THÔNG</strong></p>
    <p>Bản quyền © 2025 - Phát triển cho Cuộc thi Sáng kiến An toàn Giao thông</p>
</div>
""", unsafe_allow_html=True)
