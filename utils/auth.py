import streamlit as st


def check_admin_password(password: str) -> bool:
    return password == st.secrets["app"]["admin_password"]


def login_form():
    """Render admin login box, return True if authenticated."""
    if st.session_state.get("is_admin"):
        return True

    with st.expander("🔐 Admin Login", expanded=False):
        pwd = st.text_input("Password", type="password", key="admin_pwd_input")
        if st.button("Login", key="admin_login_btn"):
            if check_admin_password(pwd):
                st.session_state["is_admin"] = True
                st.session_state["admin_name"] = "Admin"
                st.success("✅ เข้าสู่ระบบสำเร็จ")
                st.rerun()
            else:
                st.error("❌ Password ไม่ถูกต้อง")
    return st.session_state.get("is_admin", False)


def logout():
    st.session_state["is_admin"] = False
    st.session_state["admin_name"] = ""
