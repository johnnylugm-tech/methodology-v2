#!/usr/bin/env python3
"""
ApprovalFlow Web UI - 人類審批界面

使用方法：
    streamlit run approval_ui.py
    或
    python approval_ui.py
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from approval_flow import ApprovalFlow, ApprovalLevel, ApprovalStatus


def init_session_state():
    """初始化 session state"""
    if 'approval_flow' not in st.session_state:
        st.session_state.approval_flow = ApprovalFlow()
    if 'refresh_key' not in st.session_state:
        st.session_state.refresh_key = 0


def render_pending_list(flow: ApprovalFlow):
    """渲染待審批列表"""
    st.subheader("📋 待審批任務")
    
    pending = flow.get_pending()
    
    if not pending:
        st.success("✅ 目前沒有待審批的任務")
        return None
    
    # 構建選擇列表
    options = [f"{p['id']} - {p['name']} ({p['approval_type']})" for p in pending]
    selected = st.selectbox("選擇任務", options, key=f"pending_select_{st.session_state.refresh_key}")
    
    if selected:
        request_id = selected.split(" - ")[0]
        return request_id
    return None


def render_task_detail(flow: ApprovalFlow, request_id: str):
    """渲染任務詳情"""
    request = flow.get_request(request_id)
    
    if not request:
        st.error(f"找不到任務: {request_id}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {request.name}")
        st.markdown(f"**ID:** `{request.id}`")
        st.markdown(f"**類型:** {request.approval_type}")
        st.markdown(f"**申請人:** {request.requester_name or request.requester}")
    
    with col2:
        status_color = {
            ApprovalStatus.PENDING: "🟡",
            ApprovalStatus.APPROVED: "🟢",
            ApprovalStatus.REJECTED: "🔴",
            ApprovalStatus.EXPIRED: "⚪",
        }.get(request.status, "")
        
        st.markdown(f"**狀態:** {status_color} {request.status.value}")
        st.markdown(f"**創建時間:** {request.created_at.strftime('%Y-%m-%d %H:%M')}")
        st.markdown(f"**當前步驟:** {request.current_step_index + 1} / {len(request.steps)}")
    
    st.markdown("---")
    st.markdown(f"**描述:**\n\n{request.description}")
    
    st.markdown("### 審批步驟")
    
    for i, step in enumerate(request.steps):
        is_current = i == request.current_step_index
        marker = "👉" if is_current else ("✅" if step.status != ApprovalStatus.PENDING else "⬜")
        
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 2])
            
            with col1:
                st.markdown(f"### {marker}")
            
            with col2:
                st.markdown(f"**[{step.level.value.upper()}]** {step.approver}")
                if step.deadline:
                    st.caption(f"截止: {step.deadline.strftime('%Y-%m-%d %H:%M')}")
            
            with col3:
                if step.status == ApprovalStatus.PENDING:
                    st.write(f"**狀態:** ⏳ 等待審批")
                elif step.status == ApprovalStatus.APPROVED:
                    st.write(f"**狀態:** ✅ 已批准")
                else:
                    st.write(f"**狀態:** ❌ 已拒絕")
            
            # 顯示審批記錄
            if step.approvals:
                for approval in step.approvals:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;↳ `{approval['approver']}`: {approval['status'].value} {approval.get('comment', '')}")
            
            st.markdown("---")
    
    return request


def render_action_buttons(flow: ApprovalFlow, request_id: str):
    """渲染操作按鈕"""
    request = flow.get_request(request_id)
    
    if not request or request.status != ApprovalStatus.PENDING:
        return
    
    current_step = request.steps[request.current_step_index]
    
    st.markdown("### 🎬 操作")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ 批准")
        approver = st.text_input("審批人", value="user", key=f"approver_{request_id}")
        comment = st.text_area("備註 (可選)", key=f"comment_approve_{request_id}")
        
        if st.button("確認批准", type="primary", key=f"btn_approve_{request_id}"):
            result = flow.approve(request_id, approver, comment=comment)
            if result:
                st.success(f"✅ 已批准: {request_id}")
                st.session_state.refresh_key += 1
                st.rerun()
            else:
                st.error("❌ 批准失敗")
    
    with col2:
        st.markdown("#### ❌ 駁回")
        reject_approver = st.text_input("審批人", value="user", key=f"rejecter_{request_id}")
        reject_comment = st.text_area("駁回原因", key=f"comment_reject_{request_id}")
        
        if st.button("確認駁回", type="secondary", key=f"btn_reject_{request_id}"):
            result = flow.reject(request_id, reject_approver, comment=reject_comment)
            if result:
                st.success(f"❌ 已駁回: {request_id}")
                st.session_state.refresh_key += 1
                st.rerun()
            else:
                st.error("❌ 駁回失敗")


def render_create_form(flow: ApprovalFlow):
    """渲染創建表單"""
    st.subheader("➕ 創建審批請求")
    
    with st.form("create_form"):
        name = st.text_input("任務名稱 *", placeholder="例如：代碼審查 - 登入模塊")
        description = st.text_area("描述", placeholder="請描述需要審批的內容...")
        approval_type = st.selectbox("審批類型", 
                                     ["general", "code_review", "deployment", "budget"],
                                     format_func=lambda x: {
                                         "general": "一般審批",
                                         "code_review": "代碼審查",
                                         "deployment": "部署審批",
                                         "budget": "預算審批"
                                     }.get(x, x))
        requester = st.text_input("申請人", value="user")
        requester_name = st.text_input("申請人名稱", value="User")
        
        submitted = st.form_submit_button("創建審批請求")
        
        if submitted:
            if not name:
                st.error("請輸入任務名稱")
            else:
                req_id = flow.create_request(
                    name=name,
                    description=description,
                    requester=requester,
                    requester_name=requester_name,
                    approval_type=approval_type,
                )
                st.success(f"✅ 已創建審批請求: {req_id}")
                st.session_state.refresh_key += 1
                st.rerun()


def render_statistics(flow: ApprovalFlow):
    """渲染統計信息"""
    stats = flow.get_statistics()
    
    st.sidebar.markdown("### 📊 統計")
    
    col1, col2 = st.sidebar.columns(2)
    col1.metric("總請求", stats['total_requests'])
    col2.metric("待審批", stats['pending'])
    
    col3, col4 = st.sidebar.columns(2)
    col3.metric("已批准", stats['approved'])
    col4.metric("已拒絕", stats['rejected'])
    
    st.sidebar.markdown(f"**規則數:** {stats['rules_count']}")


def render_rules(flow: ApprovalFlow):
    """渲染審批規則"""
    st.sidebar.markdown("### 📋 審批規則")
    
    for rule_id, rule in flow.rules.items():
        with st.sidebar.expander(f"{rule.name}"):
            st.markdown(f"**審批級別:** {' → '.join([l.value.upper() for l in rule.levels])}")
            st.markdown(f"**描述:** {rule.description}")
            st.markdown(f"**超時:** {rule.timeout_hours}h")


def main():
    st.set_page_config(
        page_title="任務審批",
        page_icon="✅",
        layout="wide"
    )
    
    init_session_state()
    flow = st.session_state.approval_flow
    
    st.title("✅ 人類審批 UI")
    st.markdown("---")
    
    # Tab layout
    tab1, tab2, tab3 = st.tabs(["📋 待審批", "➕ 創建請求", "📊 統計"])
    
    with tab1:
        request_id = render_pending_list(flow)
        
        if request_id:
            request = render_task_detail(flow, request_id)
            
            if request and request.status == ApprovalStatus.PENDING:
                render_action_buttons(flow, request_id)
    
    with tab2:
        render_create_form(flow)
    
    with tab3:
        render_statistics(flow)
        render_rules(flow)
        
        st.markdown("### 📝 完整報告")
        if st.button("生成 Markdown 報告"):
            report = flow.generate_report()
            st.markdown(report)

    # Auto-refresh hint
    st.markdown("---")
    st.caption("💡 如需刷新，請切換標籤頁或重新選擇任務")


if __name__ == "__main__":
    # 嘗試使用 streamlit 運行
    try:
        import streamlit as st
        main()
    except SystemExit:
        # streamlit 命令行
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
