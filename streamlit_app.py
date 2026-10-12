import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api")

st.set_page_config(
    page_title="Meeting Intelligence AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-completed { background-color: #065f46; color: #a7f3d0; border: 1px solid #059669; }
    .badge-transcribing, .badge-analyzing, .badge-uploaded { background-color: #1e3a8a; color: #bfdbfe; border: 1px solid #2563eb; }
    .badge-failed { background-color: #881337; color: #fecdd3; border: 1px solid #e11d48; }
    
    .priority-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .p-urgent { background: #ffe4e6; color: #9f1239; }
    .p-high { background: #ffedd5; color: #9a3412; }
    .p-medium { background: #fef9c3; color: #854d0e; }
    .p-low { background: #dcfce7; color: #166534; }
    .p-unknown { background: #f3f4f6; color: #374151; }

    .evidence-quote {
        border-left: 3px solid #6366f1;
        background: rgba(99, 102, 241, 0.08);
        padding: 6px 12px;
        margin-top: 6px;
        font-style: italic;
        font-size: 0.85rem;
        border-radius: 0 6px 6px 0;
    }
    
    .segment-box {
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        padding: 8px 0;
    }
    .ts-label {
        font-family: monospace;
        font-size: 0.8rem;
        color: #818cf8;
    }
    .speaker-pill {
        font-size: 0.8rem;
        font-weight: 600;
        color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)


def api_get(endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    try:
        url = f"{API_BASE}{endpoint}"
        resp = httpx.get(url, params=params, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def api_post_file(endpoint: str, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
    url = f"{API_BASE}{endpoint}"
    files = {"file": (filename, file_bytes, content_type or "audio/mpeg")}
    resp = httpx.post(url, files=files, timeout=60.0)
    try:
        data = resp.json()
    except Exception:
        data = {"message": resp.text}
    return {"status_code": resp.status_code, "data": data}


def api_post_json(endpoint: str, payload: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
    url = f"{API_BASE}{endpoint}"
    resp = httpx.post(url, json=payload, timeout=timeout)
    try:
        data = resp.json()
    except Exception:
        data = {"message": resp.text}
    return {"status_code": resp.status_code, "data": data}


def api_delete(endpoint: str) -> bool:
    try:
        url = f"{API_BASE}{endpoint}"
        resp = httpx.delete(url, timeout=10.0)
        return resp.status_code in (200, 204)
    except Exception:
        return False


def format_seconds(seconds: Optional[float]) -> str:
    if seconds is None:
        return "--:--"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def format_bytes(num_bytes: Optional[int]) -> str:
    if not num_bytes:
        return "--"
    mb = num_bytes / (1024 * 1024)
    return f"{mb:.2f} MB"


def format_iso_date(iso_str: Optional[str]) -> str:
    if not iso_str:
        return "--"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return iso_str[:16]


if "selected_meeting_id" not in st.session_state:
    st.session_state["selected_meeting_id"] = None

with st.sidebar:
    st.markdown("### Meeting Intelligence")
    st.caption("Audio Intelligence and Action Tracker")

    health = api_get("/health")
    if health and health.get("status") == "healthy":
        st.success("Backend API Connected")
        whisper_info = health.get("whisper_model", "base")
        gemini_ready = health.get("gemini_configured", False)
        gemini_model = health.get("gemini_model", "gemini")
        st.caption(f"Whisper: `{whisper_info}` | Gemini: `{'Ready (' + gemini_model + ')' if gemini_ready else 'No API Key'}`")
    else:
        st.error("Backend API Offline")
        st.caption(f"Cannot connect to `{API_BASE}`. Please ensure FastAPI is running on port 8000.")

    st.divider()

    st.markdown("#### Upload Recording")
    uploaded_file = st.file_uploader(
        "Choose audio file",
        type=["mp3", "wav", "m4a", "flac", "ogg"],
        help="Upload MP3 or WAV meeting recordings up to 100 MB."
    )

    if uploaded_file is not None:
        st.caption(f"File: **{uploaded_file.name}** ({format_bytes(uploaded_file.size)})")
        if st.button("Process Recording", type="primary", use_container_width=True):
            with st.spinner("Uploading and initiating processing..."):
                file_bytes = uploaded_file.getvalue()
                res = api_post_file(
                    "/meetings/upload",
                    file_bytes=file_bytes,
                    filename=uploaded_file.name,
                    content_type=uploaded_file.type or "audio/mpeg"
                )

                if res["status_code"] == 202:
                    meeting_id = res["data"]["id"]
                    st.session_state["selected_meeting_id"] = meeting_id
                    st.success("Uploaded successfully. Transcription started.")
                    time.sleep(1)
                    st.rerun()
                elif res["status_code"] == 409:
                    dup_id = res["data"].get("existing_id")
                    st.warning(f"Duplicate audio detected. Matching meeting ID: `{dup_id}`")
                    if dup_id and st.button("Open Existing Meeting", key="open_dup"):
                        st.session_state["selected_meeting_id"] = dup_id
                        st.rerun()
                else:
                    detail = res["data"].get("detail") or res["data"].get("message") or "Upload failed"
                    st.error(f"Upload error: {detail}")

    st.divider()

    st.markdown("#### Meetings History")
    col_ref, col_filt = st.columns([1, 2])
    with col_ref:
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    with col_filt:
        status_filter = st.selectbox(
            "Filter status",
            ["All", "completed", "processing", "failed"],
            index=0,
            label_visibility="collapsed"
        )

    search_query = st.text_input("Search meetings", placeholder="Search by name...", label_visibility="collapsed")

    query_params = {"page_size": 50}
    if status_filter != "All":
        query_params["status"] = status_filter
    if search_query:
        query_params["query"] = search_query

    meetings_resp = api_get("/meetings", params=query_params)
    meetings_list = meetings_resp.get("items", []) if meetings_resp else []

    if not meetings_list:
        st.caption("No meetings found.")
    else:
        st.caption(f"Showing {len(meetings_list)} meetings:")
        for m in meetings_list:
            m_id = m["id"]
            status = m.get("status", "unknown")
            badge = "[Done]" if status == "completed" else "[Active]" if status in ("transcribing", "analyzing", "uploaded") else "[Failed]"
            filename = m.get("original_filename", "Audio Recording")
            duration_str = format_seconds(m.get("duration_seconds"))
            date_str = format_iso_date(m.get("created_at"))

            is_selected = (st.session_state["selected_meeting_id"] == m_id)
            btn_label = f"{badge} {filename}\n{duration_str} • {date_str}"

            if st.button(
                btn_label,
                key=f"m_btn_{m_id}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state["selected_meeting_id"] = m_id
                st.rerun()


if not st.session_state.get("selected_meeting_id"):
    st.title("Meeting Intelligence and Action Tracker")
    st.markdown("""
    Welcome to the Meeting Intelligence application.
    
    1. Upload Audio: Select an MP3 or WAV recording in the left sidebar.
    2. Transcription: Local faster-whisper decodes the audio into time-aligned transcript segments.
    3. Structured AI Analysis: Google Gemini extracts executive summaries, decisions, action items, risks, blockers, open questions, and participants.
    4. Grounded Q&A: Ask any question about the meeting. Answers cite strictly from transcript quotes and analysis.
    
    Please select an existing meeting from the sidebar or upload a new audio recording to get started.
    """)
    st.stop()

meeting_id = st.session_state["selected_meeting_id"]
meeting = api_get(f"/meetings/{meeting_id}")

if not meeting:
    st.error(f"Meeting `{meeting_id}` not found or API connection failed.")
    if st.button("Go to Overview"):
        st.session_state["selected_meeting_id"] = None
        st.rerun()
    st.stop()

status = meeting.get("status", "unknown")
filename = meeting.get("original_filename", "audio_meeting")

col_title, col_actions = st.columns([3, 1])
with col_title:
    st.subheader(f"Meeting: {filename}")
    meta_cols = st.columns(4)
    with meta_cols[0]:
        st.caption(f"**Status:** `{status.upper()}`")
    with meta_cols[1]:
        st.caption(f"**Duration:** `{format_seconds(meeting.get('duration_seconds'))}`")
    with meta_cols[2]:
        st.caption(f"**File Size:** `{format_bytes(meeting.get('size_bytes'))}`")
    with meta_cols[3]:
        st.caption(f"**Language:** `{meeting.get('language') or 'Auto-detect'}`")

with col_actions:
    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("Reprocess", help="Re-run transcription and LLM analysis"):
            res = api_post_json(f"/meetings/{meeting_id}/reprocess", {})
            if res["status_code"] in (200, 202):
                st.success("Reprocessing initiated.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to reprocess.")
    with action_cols[1]:
        json_data = json.dumps(meeting, indent=2)
        st.download_button(
            "Export JSON",
            data=json_data,
            file_name=f"{filename}_analysis.json",
            mime="application/json",
            help="Download complete structured analysis JSON"
        )
    with action_cols[2]:
        if st.button("Delete", help="Delete meeting and stored audio"):
            if api_delete(f"/meetings/{meeting_id}"):
                st.success("Meeting deleted.")
                st.session_state["selected_meeting_id"] = None
                time.sleep(1)
                st.rerun()
            else:
                st.error("Could not delete meeting.")

if status in ("uploaded", "transcribing", "analyzing"):
    st.info(f"Processing in progress: Status is `{status}`. Whisper is transcribing or Gemini is extracting intelligence.")
    st.caption("Auto-refreshing in 3 seconds...")
    time.sleep(3)
    st.rerun()

if status == "failed":
    st.error(f"Processing Failed: {meeting.get('error_message') or 'An unknown error occurred during pipeline execution.'}")
    if st.button("Retry Processing Now"):
        api_post_json(f"/meetings/{meeting_id}/reprocess", {})
        st.rerun()

analysis = meeting.get("analysis")
analysis_data = analysis.get("structured_payload", {}) if analysis else {}
segments = meeting.get("segments", [])
queries = meeting.get("queries", [])

tabs = st.tabs([
    "Overview",
    "Action Items",
    "Decisions",
    "Risks and Blockers",
    "Open Questions",
    "Transcript",
    "Ask AI (Q&A)"
])

with tabs[0]:
    st.markdown("### Executive Summary")
    summary = analysis_data.get("summary") or meeting.get("summary") or "Summary not yet available."
    st.write(summary)

    st.markdown("#### Key Topics")
    topics = analysis_data.get("key_topics", [])
    if topics:
        st.write(" ".join([f"`{t}`" for t in topics]))
    else:
        st.caption("No key topics detected.")

    st.markdown("#### Participants Identified")
    participants = analysis_data.get("participants", [])
    if participants:
        for p in participants:
            col_p1, col_p2 = st.columns([1, 3])
            with col_p1:
                st.markdown(f"**{p.get('name', 'Unknown')}**")
                if p.get("role"):
                    st.caption(f"Role: {p.get('role')}")
                if p.get("confidence") is not None:
                    st.caption(f"Confidence: {int(p.get('confidence') * 100)}%")
            with col_p2:
                if p.get("evidence"):
                    st.markdown(f"<div class='evidence-quote'>\"{p.get('evidence')}\"</div>", unsafe_allow_html=True)
            st.divider()
    else:
        st.caption("No participants identified in the conversation.")

with tabs[1]:
    st.markdown("### Action Items")
    action_items = analysis_data.get("action_items", [])
    if action_items:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Tasks", len(action_items))
        col_m2.metric("Urgent / High", len([a for a in action_items if str(a.get("priority")).lower() in ("urgent", "high")]))
        col_m3.metric("Open / In Progress", len([a for a in action_items if str(a.get("status")).lower() in ("open", "in_progress")]))
        col_m4.metric("Completed", len([a for a in action_items if str(a.get("status")).lower() == "completed"]))

        for idx, item in enumerate(action_items):
            with st.container():
                cols = st.columns([4, 2, 2, 2, 2])
                with cols[0]:
                    st.markdown(f"**{idx + 1}. {item.get('task', '')}**")
                    if item.get("evidence"):
                        st.markdown(f"<div class='evidence-quote'>\"{item.get('evidence')}\"</div>", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"**Assignee:** `{item.get('assignee') or 'Unassigned'}`")
                with cols[2]:
                    dl_stated = item.get("deadline_stated") or item.get("deadline") or "None"
                    dl_norm = item.get("deadline_normalized")
                    st.markdown(f"**Deadline:** `{dl_stated}`")
                    if dl_norm:
                        st.caption(f"Norm: {dl_norm}")
                with cols[3]:
                    prio = str(item.get("priority", "medium")).lower()
                    st.markdown(f"**Priority:** `{prio.upper()}`")
                with cols[4]:
                    stat = str(item.get("status", "open")).lower()
                    st.markdown(f"**Status:** `{stat.upper()}`")
                st.divider()
    else:
        st.info("No action items extracted from this meeting.")

with tabs[2]:
    st.markdown("### Confirmed Decisions")
    decisions = analysis_data.get("decisions", [])
    if decisions:
        for idx, d in enumerate(decisions):
            d_status = d.get("status", "confirmed").lower()
            with st.container():
                st.markdown(f"**Decision {idx + 1}:** {d.get('decision', '')}")
                col_d1, col_d2 = st.columns([1, 3])
                with col_d1:
                    st.caption(f"Status: `{d_status.upper()}`")
                    if d.get("confidence") is not None:
                        st.caption(f"Confidence: {int(d.get('confidence') * 100)}%")
                    if d.get("timestamp"):
                        st.caption(f"Timestamp: {d.get('timestamp')}")
                with col_d2:
                    if d.get("evidence"):
                        st.markdown(f"<div class='evidence-quote'>\"{d.get('evidence')}\"</div>", unsafe_allow_html=True)
                st.divider()
    else:
        st.info("No confirmed decisions recorded for this meeting.")

with tabs[3]:
    col_risk, col_block = st.columns(2)
    with col_risk:
        st.markdown("### Identified Risks")
        risks = analysis_data.get("risks", [])
        if risks:
            for r in risks:
                st.markdown(f"- **{r.get('description', '')}**")
                if r.get("impact"):
                    st.caption(f"Impact: {r.get('impact')}")
                if r.get("evidence"):
                    st.markdown(f"<div class='evidence-quote'>\"{r.get('evidence')}\"</div>", unsafe_allow_html=True)
                st.divider()
        else:
            st.caption("No risks identified.")

    with col_block:
        st.markdown("### Blockers and Dependencies")
        blockers = analysis_data.get("blockers", [])
        if blockers:
            for b in blockers:
                st.markdown(f"- **{b.get('description', '')}**")
                if b.get("owner"):
                    st.caption(f"Owner: `{b.get('owner')}`")
                if b.get("dependency"):
                    st.caption(f"Dependency: `{b.get('dependency')}`")
                if b.get("evidence"):
                    st.markdown(f"<div class='evidence-quote'>\"{b.get('evidence')}\"</div>", unsafe_allow_html=True)
                st.divider()
        else:
            st.caption("No blockers identified.")

with tabs[4]:
    st.markdown("### Unresolved Items and Open Questions")
    unresolved = analysis_data.get("unresolved_items", [])
    if unresolved:
        for idx, u in enumerate(unresolved):
            st.markdown(f"**{idx + 1}. {u.get('question') or u.get('description', '')}**")
            col_u1, col_u2 = st.columns([1, 3])
            with col_u1:
                if u.get("owner"):
                    st.caption(f"Owner: `{u.get('owner')}`")
                if u.get("confidence") is not None:
                    st.caption(f"Confidence: {int(u.get('confidence') * 100)}%")
            with col_u2:
                if u.get("evidence"):
                    st.markdown(f"<div class='evidence-quote'>\"{u.get('evidence')}\"</div>", unsafe_allow_html=True)
            st.divider()
    else:
        st.info("No unresolved questions or open items.")

with tabs[5]:
    st.markdown("### Full Transcript")
    if segments:
        col_t_search, col_t_copy = st.columns([3, 1])
        with col_t_search:
            t_search = st.text_input("Filter transcript text", placeholder="Type keyword...", label_visibility="collapsed")
        with col_t_copy:
            full_text = "\n".join([f"[{format_seconds(s.get('start_seconds'))} - {format_seconds(s.get('end_seconds'))}] {s.get('speaker') or 'Speaker'}: {s.get('text')}" for s in segments])
            st.download_button(
                "Download Transcript",
                data=full_text,
                file_name=f"{filename}_transcript.txt",
                mime="text/plain",
                use_container_width=True
            )

        filtered_segments = [s for s in segments if not t_search or t_search.lower() in s.get("text", "").lower()]
        st.caption(f"Displaying {len(filtered_segments)} of {len(segments)} segments:")

        for s in filtered_segments:
            st_time = format_seconds(s.get("start_seconds"))
            end_time = format_seconds(s.get("end_seconds"))
            speaker = s.get("speaker") or "Speaker"
            st.markdown(
                f"<div class='segment-box'>"
                f"<span class='ts-label'>[{st_time} - {end_time}]</span> "
                f"<span class='speaker-pill'>{speaker}:</span> {s.get('text', '')}"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.caption("No transcript segments available.")

with tabs[6]:
    st.markdown("### Ask AI About This Meeting")
    st.caption("Answers are strictly grounded in this meeting transcript and verified analysis. If evidence is absent, the AI will explicitly state so.")

    q_form = st.form("query_meeting_form", clear_on_submit=True)
    with q_form:
        user_question = st.text_input(
            "Your Question:",
            placeholder="e.g., What did Rahul agree to do by 10 September? What is blocking the payment gateway?",
            label_visibility="collapsed"
        )
        submit_q = st.form_submit_button("Ask Question", type="primary")

    if submit_q and user_question.strip():
        with st.spinner("Generating grounded answer from transcript..."):
            res = api_post_json(f"/meetings/{meeting_id}/query", {"question": user_question.strip()})
            if res["status_code"] == 200:
                st.success("Answer received.")
                st.rerun()
            else:
                err_detail = res["data"].get("detail") or res["data"].get("message") or "Query failed"
                st.error(f"Error answering query: {err_detail}")

    if queries:
        st.markdown("#### Conversation History")
        for q in reversed(queries):
            with st.container():
                st.markdown(f"**Question:** {q.get('question')}")
                st.markdown(f"**Answer:** {q.get('answer')}")
                evidence_list = q.get("evidence", [])
                if evidence_list:
                    st.caption("Supporting Evidence:")
                    for ev in evidence_list:
                        st.markdown(f"<div class='evidence-quote'>\"{ev}\"</div>", unsafe_allow_html=True)
                st.caption(f"Model: `{q.get('model', 'gemini')}` • Time: `{format_iso_date(q.get('created_at'))}`")
                st.divider()
    else:
        st.caption("No questions have been asked yet.")
