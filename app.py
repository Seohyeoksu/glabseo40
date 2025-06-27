import streamlit as st
import datetime
from datetime import datetime, timedelta
import hashlib
import os
import html
from supabase import create_client, Client

# 페이지 설정 (가장 먼저 실행되어야 함)
st.set_page_config(
    page_title="2025 AI(새)로고침! 우리 교실 앱 공모전",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Supabase 설정
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_ANON_KEY", "")

# Supabase 클라이언트 초기화
@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# Supabase 데이터 로드 함수
@st.cache_data(ttl=5)  # 5초 캐시 (실시간성 향상)
def load_posts_from_supabase():
    """Supabase에서 게시물 데이터를 로드합니다."""
    if not supabase:
        return []
    
    try:
        response = supabase.table('post').select('id, name, category, text, created_at').order('created_at', desc=True).execute()
        
        # 데이터 형식 변환
        posts = []
        for post in response.data:
            # 답글 로드
            replies = load_replies_from_supabase(post['id'])
            
            posts.append({
                'id': post['id'],  # 실제 DB의 ID 사용
                'db_id': post['id'],  # 삭제용 DB ID 저장
                'name': post['name'],
                'type': post['category'],  # category -> type으로 매핑
                'text': post['text'],
                'time': datetime.fromisoformat(post['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M'),
                'replies': replies,  # Supabase에서 로드한 답변들
                'status': 'answered' if replies else ('waiting' if post['category'] == '질문' else 'none')
            })
        return posts
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return []

# Supabase에 게시물 저장 함수
def save_post_to_supabase(name, category, text):
    """Supabase에 새 게시물을 저장합니다."""
    if not supabase:
        return False
    
    try:
        data = {
            'name': name,
            'category': category,  # type -> category로 매핑
            'text': text,
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('post').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"게시물 저장 중 오류가 발생했습니다: {e}")
        return False

# Supabase에서 게시물 삭제 함수
def delete_post_from_supabase(post_id):
    """Supabase에서 게시물을 삭제합니다."""
    if not supabase:
        return False
    
    try:
        response = supabase.table('post').delete().eq('id', post_id).execute()
        return True
    except Exception as e:
        st.error(f"게시물 삭제 중 오류가 발생했습니다: {e}")
        return False

# 시간 차이 계산 함수
def get_time_ago(created_at):
    """시간 차이를 계산하여 '?분전', '?시간전', '?일전' 형식으로 반환합니다."""
    try:
        # ISO 형식의 시간을 datetime 객체로 변환
        if isinstance(created_at, str):
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            created_time = created_at
        
        now = datetime.now(created_time.tzinfo) if created_time.tzinfo else datetime.now()
        diff = now - created_time
        
        if diff.days > 0:
            return f"{diff.days}일전"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}시간전"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes}분전"
        else:
            return "방금전"
    except Exception as e:
        return "시간 정보 없음"

# Supabase에서 답글 로드 함수
def load_replies_from_supabase(post_id):
    """특정 게시물의 답글들을 Supabase에서 로드합니다."""
    if not supabase:
        return []
    
    try:
        response = supabase.table('reply').select('reply, created_at').eq('id', post_id).order('created_at', desc=False).execute()
        
        replies = []
        for reply_data in response.data:
            replies.append({
                'text': reply_data['reply'],
                'time': datetime.fromisoformat(reply_data['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            })
        return replies
    except Exception as e:
        st.error(f"답글 로드 중 오류가 발생했습니다: {e}")
        return []

# Supabase에 답글 저장 함수
def save_reply_to_supabase(post_id, reply_text):
    """Supabase에 새 답글을 저장합니다."""
    if not supabase:
        return False
    
    try:
        data = {
            'id': post_id,  # 외래키로 post id 참조
            'reply': reply_text,
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('reply').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"답글 저장 중 오류가 발생했습니다: {e}")
        return False

# CSS 스타일
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .info-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid #667eea;
    }
    .prize-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
        border: 2px solid #f0f2f6;
    }
    .deadline-alert {
        background-color: #ff6b6b;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .success-box {
        background-color: #51cf66;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        text-align: center;
    }
    
    /* 사이드바 스타일링 */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    

    
    /* 라디오 버튼 스타일링 */
    .stRadio > div[role="radiogroup"] > label {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 12px 16px;
        margin: 5px 0;
        border-radius: 10px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: block !important;
        width: 100%;
    }
    
    .stRadio > div[role="radiogroup"] > label:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
    }
    
    .stRadio > div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* 라디오 버튼 원형 아이콘 숨기기 (더 안전한 방법) */
    .stRadio > div[role="radiogroup"] > label > div:first-child {
        width: 0px !important;
        height: 0px !important;
        min-width: 0px !important;
        margin-right: 0px !important;
        visibility: hidden !important;
    }
    
    /* 사이드바 제목 스타일 */
    .sidebar-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 1rem;
    }
    
    /* 통계 카드 스타일 */
    .stats-container {
        display: flex;
        gap: 15px;
        margin: 20px 0;
        flex-wrap: wrap;
    }
    
    .stat-card {
        flex: 1;
        min-width: 150px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stat-number {
        font-size: 2em;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .stat-label {
        font-size: 0.9em;
        opacity: 0.9;
    }
    
    /* 게시물 카드 스타일 */
    .post-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #f0f2f6;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .post-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .post-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #f8f9fa;
        min-height: 40px;
    }
    
    .post-author {
        font-weight: bold;
        color: #2c3e50;
        font-size: 1.1em;
    }
    
    .post-time {
        color: #6c757d;
        font-size: 0.9em;
        margin-top: 2px;
    }
    
    .post-header-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 8px;
    }
    
    .post-category {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 500;
        margin-bottom: 10px;
    }
    
    .category-question {
        background: linear-gradient(135deg, #ff6b6b, #ffa726);
        color: white;
    }
    
    .category-info {
        background: linear-gradient(135deg, #4ecdc4, #44a08d);
        color: white;
    }
    
    .category-idea {
        background: linear-gradient(135deg, #a8edea, #fed6e3);
        color: #2c3e50;
    }
    
    .category-other {
        background: linear-gradient(135deg, #d299c2, #fef9d7);
        color: #2c3e50;
    }
    
    .post-content {
        color: #2c3e50;
        line-height: 1.6;
        font-size: 1em;
        margin: 15px 0;
    }
    
    .post-status {
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
        white-space: nowrap;
    }
    
    .status-waiting {
        background: #ffeaa7;
        color: #e17055;
    }
    
    .status-answered {
        background: #00b894;
        color: white;
    }
    
    .admin-reply {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
        border-left: 4px solid #4834d4;
        position: relative;
    }
    
    .admin-reply::before {
        content: "👨‍💼";
        position: absolute;
        top: -5px;
        left: 15px;
        background: white;
        padding: 5px;
        border-radius: 50%;
        font-size: 1.2em;
    }
    
    .reply-time {
        font-size: 0.8em;
        opacity: 0.8;
        margin-top: 10px;
    }
    

</style>
""",
    unsafe_allow_html=True,
)

# 헤더
st.markdown(
    """
<div class="main-header">
    <h1>🔄 2025 AI(새)로고침! 우리 교실 앱 공모전</h1>
    <h3>AI 활용 교육용 앱 개발 공모전</h3>
    <p>주최: 경상북도교육청</p>
</div>
""",
    unsafe_allow_html=True,
)

# 사이드바
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-title">
            🔍 AI로고침! 우리 교실 앱 공모전
        </div>
        """, 
        unsafe_allow_html=True
    )
    

    
    # 라디오 버튼으로 메뉴 선택 (스타일링된 상태)
    menu = st.radio(
        "메뉴를 선택하세요",
        [
            "📋 공모전 개요",
            "💰 상금 및 시상",
            "📅 일정 및 마감",
            "💡 공모 주제",
            "📝 제출 방법",
            "⚖️ 심사 기준",
            "❓ 자주 묻는 질문",
            "💬 커뮤니티",
            "📧 문의하기",
        ],
        key="sidebar_menu",
        label_visibility="collapsed"
    )
    
    st.markdown("---")  # 구분선 추가
    
    # 빠른 정보 카드
    st.markdown("### 🚀 빠른 정보")
    
    # 마감일 카운트다운 (사이드바용)
    deadline = datetime(2025, 7, 18)
    today = datetime.now()
    days_left = (deadline - today).days
    
    if days_left > 0:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
                color: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                margin: 10px 0;
                box-shadow: 0 3px 10px rgba(255, 107, 107, 0.3);
            ">
                ⏰ <strong>마감까지</strong><br>
                <span style="font-size: 1.5em; font-weight: bold;">{days_left}일</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="
                background: #6c757d;
                color: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                margin: 10px 0;
            ">
                ⏰ <strong>접수 마감</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    

    
    # 공모전 정보 요약
    with st.expander("📊 공모전 요약", expanded=False):
        st.markdown("""
        **🎯 주최:** 경상북도교육청  
        **💰 최대상금:** 100만원  
        **👥 대상:** 교직원, 예비교사  
        **🤖 필수:** AI 기술 활용  
        **📅 마감:** 2025.07.18
        """)
    
    # 도움말
    st.markdown("---")
    st.markdown("### 💡 도움말")
    st.info("메뉴를 클릭하여 원하는 정보를 확인하세요. 궁금한 점이 있으시면 '문의하기'를 이용해주세요!")

# 메인 컨텐츠
if menu == "📋 공모전 개요":
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🎯 공모전 목적")
        st.info(
            """
        - **AI 기술을 활용한 교육용 앱 개발**을 통한 교실 수업 혁신
        - 교직원과 예비교사가 참여하는 **현장 중심** 교육 실천 문화 조성
        - 공공성과 실용성을 갖춘 앱으로 **AI 교육 생태계** 기반 마련
        """
        )

        st.markdown("### 👥 참가 자격")
        st.success(
            """
        ✅ 전국 초·중·고·특수학교 **교직원**  
        ✅ **교육전문직원**  
        ✅ 교육대학교 및 사범대학 **재학생(예비교사)**  
        
        ⚠️ **개인 단위로만 참가 가능** (팀 참가 불가)
        """
        )

    with col2:
        # 마감일 계산
        deadline = datetime(2025, 7, 18)
        today = datetime.now()
        days_left = (deadline - today).days

        if days_left > 0:
            st.markdown(
                f"""
            <div class="deadline-alert">
                📅 마감까지<br>
                <h2>{days_left}일</h2>
                남았습니다!
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div class="deadline-alert">
                ⏰ 접수 마감
            </div>
            """,
                unsafe_allow_html=True,
            )

elif menu == "💰 상금 및 시상":
    st.markdown("### 🏆 시상 내역")

    prizes = [
        {"상급": "대상", "인원": "1명", "상금": "100만원", "icon": "🥇"},
        {"상급": "금상", "인원": "2명", "상금": "50만원", "icon": "🥈"},
        {"상급": "은상", "인원": "3명", "상금": "30만원", "icon": "🥉"},
        {"상급": "동상", "인원": "5명", "상금": "10만원", "icon": "🏅"},
        {"상급": "장려상", "인원": "10명 내외", "상금": "소정의 상품", "icon": "🎖️"},
    ]

    for prize in prizes:
        st.markdown(
            f"""
        <div class="prize-card">
            <h4>{prize['icon']} {prize['상급']}</h4>
            <p>인원: {prize['인원']} | 부상: 경상북도교육감상 및 상금 {prize['상금']}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.warning("💡 상금은 제세공과금 공제 후 지급됩니다.")

elif menu == "📅 일정 및 마감":
    st.markdown("### 📅 공모전 일정")

    timeline = {
        "공고 및 접수 시작": "2025년 6월 25일(수)",
        "접수 마감": "2025년 7월 18일(금)",
        "심사 기간": "2025년 7월 21일(월) ~ 7월 25일(금)",
        "결과 발표": "2025년 7월 30일(수)",
    }

    for event, date in timeline.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{event}**")
        with col2:
            st.markdown(f"📌 {date}")
        st.divider()

elif menu == "💡 공모 주제":
    st.markdown("### 🎯 공모 주제 (AI 요소 필수 포함)")

    topics = {
        "① 수업 및 학습 지원": [
            "개별 맞춤형 학습 경로 추천",
            "AI를 활용한 질의응답, 요약, 퀴즈 생성",
            "학생의 학습 패턴 분석 및 피드백 제공",
        ],
        "② 생활·정서 지원": [
            "AI 기반 자기성찰, 감정일기, 스트레스 진단",
            "생활 습관 관리, 학습 동기 유발 도우미",
            "교실 속 SEL(Social Emotional Learning) 도구",
        ],
        "③ 평가 및 피드백": [
            "서술형/논술형 문항 채점 보조",
            "학습 진단 및 성취 피드백 자동화",
            "교사용 평가 보조 앱",
        ],
        "④ 교육행정 및 업무 경감": [
            "가정통신문 자동 작성, 학급 일정 자동 정리",
            "수업 계획서/자료 추천, 보고서 초안 생성",
            "상담 기록 자동 정리 및 요약",
        ],
        "⑤ 기타 AI 기술 기반의 창의적 교육활용": [
            "교실 속 생성형 AI 도구",
            "AI 윤리교육을 위한 시뮬레이션 앱",
            "지역/학교 맥락에 맞춘 문제 해결형 앱",
        ],
    }

    for topic, details in topics.items():
        with st.expander(topic):
            for detail in details:
                st.write(f"• {detail}")

    st.info(
        "💡 위 범주를 참고하여 교육현장의 실제 필요에 기반한 앱을 자유롭게 기획·개발하세요!"
    )

elif menu == "📝 제출 방법":
    st.markdown("### 📤 제출 방법")

    st.markdown("#### 1️⃣ 제출 서류")
    requirements = {
        "필수 제출": [
            "✅ 앱 실행 파일 또는 웹앱 접속 링크",
            "✅ 앱 소개서 1부 (PDF, 5쪽 이내)",
            "✅ 소스코드 전체 (zip 압축 파일)",
            "✅ 개인정보 수집 및 이용 동의서 1부",
        ],
        "선택 제출": ["📹 시연 영상 (3분 이내)"],
    }

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**필수 제출 서류**")
        for item in requirements["필수 제출"]:
            st.write(item)

    with col2:
        st.markdown("**선택 제출 서류**")
        for item in requirements["선택 제출"]:
            st.write(item)

    st.markdown("#### 2️⃣ 제출 방법")
    st.markdown(
        """
    <div class="info-card">
        <h4>📧 이메일 접수</h4>
        <p><strong>접수 이메일:</strong> chs0601@gbe.kr</p>
        <p><strong>접수 기간:</strong> 2025. 6. 25.(수) ~ 7. 18.(금)</p>
        <p>💡 파일 용량이 클 경우 클라우드 링크(Google Drive, OneDrive 등) 첨부</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

elif menu == "⚖️ 심사 기준":
    st.markdown("### ⚖️ 심사 기준")

    # 각 항목을 개별적으로 표시
    st.markdown("#### 📊 평가 항목 및 배점")

    # 창의성
    with st.container():
        col1, col2, col3 = st.columns([2, 5, 1])
        with col1:
            st.markdown("**창의성**")
        with col2:
            st.write("기존과 차별화된 문제 해결 방식인가")
        with col3:
            st.markdown("**25점**")

    # 교육 효과성
    with st.container():
        col1, col2, col3 = st.columns([2, 5, 1])
        with col1:
            st.markdown("**교육 효과성**")
        with col2:
            st.write("수업, 생활, 행정 등 교육현장 활용 가능성")
        with col3:
            st.markdown("**25점**")

    # 실현 가능성
    with st.container():
        col1, col2, col3 = st.columns([2, 5, 1])
        with col1:
            st.markdown("**실현 가능성**")
        with col2:
            st.write("기술적 완성도와 사용 안정성")
        with col3:
            st.markdown("**20점**")

    # AI 활용성
    with st.container():
        col1, col2, col3 = st.columns([2, 5, 1])
        with col1:
            st.markdown("**AI 활용성**")
        with col2:
            st.write("AI 기술 적용의 적절성과 기능적 의미")
        with col3:
            st.markdown("**20점**")

    # 완성도
    with st.container():
        col1, col2, col3 = st.columns([2, 5, 1])
        with col1:
            st.markdown("**완성도**")
        with col2:
            st.write("앱 구성의 논리성, 디자인, 사용자 편의성")
        with col3:
            st.markdown("**10점**")

    st.markdown("---")

    # 합계
    col1, col2, col3 = st.columns([2, 5, 1])
    with col1:
        st.markdown("### 합계")
    with col3:
        st.markdown("### 100점")

    st.info("※ 필요 시 심사위원 협의에 따라 평가 항목 및 배점은 일부 조정될 수 있음")

elif menu == "❓ 자주 묻는 질문":
    st.markdown("### ❓ 자주 묻는 질문")

    faqs = {
        "팀으로 참가할 수 있나요?": "아니요. 개인 단위로만 참가 가능하며, 팀 단위 접수는 불가합니다.",
        "예비교사도 참가할 수 있나요?": "네! 교육대학교 및 사범대학 재학생이라면 참가 가능합니다.",
        "AI 기술을 꼭 사용해야 하나요?": "네, 모든 응모작은 AI 요소를 반드시 포함해야 합니다. AI 모델은 자유롭게 선택할 수 있습니다.",
        "오픈소스를 활용해도 되나요?": "네, 가능합니다. 단, 라이선스 확인 및 출처 명시는 필수입니다.",
        "제출한 앱의 저작권은 어떻게 되나요?": "출품작의 저작재산권은 경상북도교육청에 귀속되며, 향후 비영리적 교육 목적으로 활용됩니다.",
        "파일 용량이 너무 큰데 어떻게 제출하나요?": "Google Drive, OneDrive 등 클라우드 링크를 이메일에 첨부하여 제출하시면 됩니다.",
    }

    for q, a in faqs.items():
        with st.expander(f"Q. {q}"):
            st.write(f"A. {a}")

elif menu == "💬 커뮤니티":
    st.markdown("### 💬 참가자 커뮤니티")

    # 관리자 로그인 상태 초기화
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "show_admin_login" not in st.session_state:
        st.session_state.show_admin_login = False

    # 관리자 로그인 버튼 (우측 상단)
    col1, col2 = st.columns([5, 1])
    with col2:
        if not st.session_state.is_admin:
            if st.button("🔐 관리자", use_container_width=True, key="admin_login_btn"):
                st.session_state.show_admin_login = (
                    not st.session_state.show_admin_login
                )
        else:
            st.success("관리자")
            if st.button("로그아웃", use_container_width=True, key="admin_logout_btn"):
                st.session_state.is_admin = False
                st.session_state.show_admin_login = False
                st.rerun()

    # 관리자 로그인 폼
    if st.session_state.show_admin_login and not st.session_state.is_admin:
        with st.container():
            st.markdown("---")
            with st.form("admin_login"):
                st.markdown("#### 🔐 관리자 로그인")
                password = st.text_input("비밀번호", type="password")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("로그인", use_container_width=True):
                        # 환경변수에서 관리자 비밀번호 불러오기
                        admin_password = st.secrets.get("ADMIN_PASSWORD", "")
                        if admin_password and (
                            hashlib.sha256(password.encode()).hexdigest()
                            == hashlib.sha256(admin_password.encode()).hexdigest()
                        ):
                            st.session_state.is_admin = True
                            st.session_state.show_admin_login = False
                            st.success("관리자로 로그인되었습니다!")
                            st.rerun()
                        else:
                            st.error("비밀번호가 틀렸습니다.")
                with col2:
                    if st.form_submit_button("취소", use_container_width=True):
                        st.session_state.show_admin_login = False
                        st.rerun()
            st.markdown("---")

    # 데이터 초기화
    if "comments" not in st.session_state:
        st.session_state.comments = []
    if "notices" not in st.session_state:
        st.session_state.notices = []
    if "blocked_users" not in st.session_state:
        st.session_state.blocked_users = []

    # 관리자 모드
    if st.session_state.is_admin:
        st.info("🔐 관리자 모드로 접속 중입니다.")

        # 관리자 모드에서도 Supabase 데이터 로드
        if supabase:
            posts_data = load_posts_from_supabase()
            if posts_data:
                st.session_state.comments = posts_data

        admin_menu = st.tabs(
            ["📝 게시물 관리", "📢 공지사항", "🚫 차단 관리", "📊 통계"]
        )

        with admin_menu[0]:  # 게시물 관리
            st.markdown("#### 📝 게시물 관리")

            if st.session_state.comments:
                for i, comment in enumerate(st.session_state.comments):
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            # 질문 상태 표시
                            status_icon = ""
                            if comment["type"] == "질문":
                                if comment.get("status") == "answered":
                                    status_icon = "✅ "
                                else:
                                    status_icon = "⏳ "

                            st.markdown(
                                f"{status_icon}**{comment['name']}** ({comment['type']}) - {comment['time']}"
                            )
                            st.write(comment["text"])

                            # 답변 표시
                            if comment.get("replies"):
                                for reply in comment["replies"]:
                                    st.success(f"↳ **관리자 답변**: {reply['text']}")
                                    st.caption(f"{reply['time']}")

                            # 관리자 답변 작성
                            if (
                                comment["type"] == "질문"
                                and comment.get("status") != "answered"
                            ):
                                with st.expander("답변 작성"):
                                    reply_text = st.text_area(
                                        "답변", key=f"reply_{comment['id']}"
                                    )
                                    if st.button(
                                        "답변 등록", key=f"reply_btn_{comment['id']}"
                                    ):
                                        if reply_text:
                                            # Supabase에 답글 저장 시도
                                            if supabase and comment.get("db_id"):
                                                success = save_reply_to_supabase(comment["db_id"], reply_text)
                                                if success:
                                                    # 로컬 상태도 업데이트
                                                    comment["replies"].append(
                                                        {
                                                            "text": reply_text,
                                                            "time": datetime.now().strftime('%Y-%m-%d %H:%M')
                                                        }
                                                    )
                                                    comment["status"] = "answered"
                                                    st.success("✅ 답변이 성공적으로 등록되었습니다!")
                                                    # 캐시 초기화로 새 데이터 반영
                                                    st.cache_data.clear()
                                                    st.rerun()
                                                else:
                                                    st.error("답변 저장 중 오류가 발생했습니다.")
                                            else:
                                                # 로컬 저장 (fallback)
                                                comment["replies"].append(
                                                    {
                                                        "text": reply_text,
                                                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                                    }
                                                )
                                                comment["status"] = "answered"
                                                st.success("답변이 등록되었습니다!")
                                                st.rerun()

                        with col2:
                            if st.button("🗑️ 삭제", key=f"admin_del_{i}"):
                                # Supabase에서 삭제 시도
                                if supabase and comment.get("db_id"):
                                    success = delete_post_from_supabase(comment["db_id"])
                                    if success:
                                        st.session_state.comments.remove(comment)
                                        st.success("✅ 게시물이 성공적으로 삭제되었습니다!")
                                        # 캐시 초기화로 새 데이터 반영
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("게시물 삭제 중 오류가 발생했습니다.")
                                else:
                                    # 로컬 삭제 (fallback)
                                    st.session_state.comments.remove(comment)
                                    st.rerun()
                            if comment["name"] not in [
                                u["name"] for u in st.session_state.blocked_users
                            ]:
                                if st.button("🚫 차단", key=f"block_{i}"):
                                    st.session_state.blocked_users.append(
                                        {
                                            "name": comment["name"],
                                            "date": datetime.now().strftime("%Y-%m-%d"),
                                        }
                                    )
                                    st.success(f"{comment['name']}님을 차단했습니다.")
                        st.divider()
            else:
                st.info("아직 게시물이 없습니다.")

        with admin_menu[1]:  # 공지사항
            st.markdown("#### 📢 공지사항 작성")
            with st.form("notice_form"):
                notice_type = st.selectbox("공지 유형", ["일반", "중요", "긴급"])
                notice_content = st.text_area("공지 내용")
                if st.form_submit_button("공지 등록"):
                    if notice_content:
                        st.session_state.notices.append(
                            {
                                "type": notice_type,
                                "content": notice_content,
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            }
                        )
                        st.success("공지사항이 등록되었습니다!")
                        st.rerun()

            # 공지사항 목록
            if st.session_state.notices:
                st.markdown("#### 등록된 공지사항")
                for notice in st.session_state.notices:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if notice["type"] == "긴급":
                            st.error(f"[{notice['type']}] {notice['content']}")
                        elif notice["type"] == "중요":
                            st.warning(f"[{notice['type']}] {notice['content']}")
                        else:
                            st.info(f"[{notice['type']}] {notice['content']}")
                        st.caption(notice["time"])
                    with col2:
                        if st.button("삭제", key=f"del_notice_{notice['time']}"):
                            st.session_state.notices.remove(notice)
                            st.rerun()

        with admin_menu[2]:  # 차단 관리
            st.markdown("#### 🚫 차단된 사용자")
            if st.session_state.blocked_users:
                for user in st.session_state.blocked_users:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{user['name']}** - 차단일: {user['date']}")
                    with col2:
                        if st.button("차단 해제", key=f"unblock_{user['name']}"):
                            st.session_state.blocked_users.remove(user)
                            st.rerun()
                    st.divider()
            else:
                st.info("차단된 사용자가 없습니다.")

        with admin_menu[3]:  # 통계
            st.markdown("#### 📊 커뮤니티 통계")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("전체 게시물", len(st.session_state.comments))
            with col2:
                st.metric("차단된 사용자", len(st.session_state.blocked_users))
            with col3:
                st.metric("공지사항", len(st.session_state.notices))

            # 게시물 유형별 통계
            if st.session_state.comments:
                st.markdown("##### 게시물 유형별 현황")
                type_counts = {}
                for comment in st.session_state.comments:
                    type_counts[comment["type"]] = (
                        type_counts.get(comment["type"], 0) + 1
                    )

                for type_name, count in type_counts.items():
                    st.write(f"- {type_name}: {count}개")

    # 일반 사용자 모드
    else:
        # 공지사항 표시
        if st.session_state.notices:
            for notice in st.session_state.notices:
                if notice["type"] == "긴급":
                    st.error(f"📢 [{notice['type']}] {notice['content']}")
                elif notice["type"] == "중요":
                    st.warning(f"📢 [{notice['type']}] {notice['content']}")
                else:
                    st.info(f"📢 {notice['content']}")

        st.info("공모전 관련 질문, 아이디어 공유, 네트워킹을 위한 공간입니다.")

        # Supabase 연결 상태 확인
        if not supabase:
            st.warning("⚠️ 데이터베이스 연결을 확인해주세요. Supabase 설정이 필요합니다.")
            st.info("현재는 로컬 저장 방식으로 작동합니다.")

        # 댓글 작성 폼
        with st.form("community_form", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                comment_name = st.text_input("이름 또는 닉네임")
            with col2:
                comment_type = st.selectbox(
                    "구분", ["질문", "정보공유", "아이디어", "기타"]
                )

            comment_text = st.text_area("내용을 입력하세요", height=100)

            if st.form_submit_button("✏️ 작성하기", use_container_width=True):
                if comment_name and comment_text:
                    # 차단된 사용자 확인
                    if comment_name in [
                        u["name"] for u in st.session_state.blocked_users
                    ]:
                        st.error("차단된 사용자입니다. 관리자에게 문의하세요.")
                    else:
                        # Supabase에 저장 시도
                        if supabase:
                            success = save_post_to_supabase(comment_name, comment_type, comment_text)
                            if success:
                                st.success("✅ 게시물이 성공적으로 등록되었습니다!")
                                st.balloons()
                                # 캐시 초기화로 새 데이터 반영
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("게시물 저장 중 오류가 발생했습니다.")
                        else:
                            # 로컬 저장 (fallback)
                            st.session_state.comments.append(
                                {
                                    "id": len(st.session_state.comments) + 1,
                                    "name": comment_name,
                                    "type": comment_type,
                                    "text": comment_text,
                                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "replies": [],  # 답변 저장용
                                    "status": (
                                        "waiting" if comment_type == "질문" else "none"
                                    ),
                                }
                            )
                            st.success("✅ 작성되었습니다!")
                            st.balloons()
                else:
                    st.error("이름과 내용을 모두 입력해주세요.")

        # 게시물 데이터 로드 (Supabase 또는 로컬)
        if supabase:
            # Supabase에서 데이터 로드
            posts_data = load_posts_from_supabase()
            if posts_data:
                st.session_state.comments = posts_data
        
        # 댓글 통계
        questions = len([c for c in st.session_state.comments if c["type"] == "질문"])
        info_posts = len([c for c in st.session_state.comments if c["type"] == "정보공유"])
        ideas = len([c for c in st.session_state.comments if c["type"] == "아이디어"])
        
        stats_html = f"""
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.comments)}</div>
                <div class="stat-label">📝 전체 글</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{questions}</div>
                <div class="stat-label">❓ 질문</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{ideas}</div>
                <div class="stat-label">💡 아이디어</div>
            </div>
        </div>
        """
        
        st.markdown(stats_html, unsafe_allow_html=True)

        st.divider()

        # 댓글 표시
        if st.session_state.comments:
            # 최신 글부터 표시
            displayed_comments = list(reversed(st.session_state.comments)) if not supabase else st.session_state.comments
            
            for i, comment in enumerate(displayed_comments):
                # 카테고리 스타일 설정
                category_class = {
                    "질문": "category-question",
                    "정보공유": "category-info", 
                    "아이디어": "category-idea",
                    "기타": "category-other"
                }.get(comment["type"], "category-other")
                
                # 상태 스타일 설정
                status_html = ""
                if comment["type"] == "질문":
                    if comment.get("status") == "answered":
                        status_html = '<div class="post-status status-answered">답변완료</div>'
                    else:
                        status_html = '<div class="post-status status-waiting">답변대기</div>'
                
                                # 게시물 내용도 HTML 안전하게 처리
                safe_name = html.escape(comment['name'])
                safe_time = html.escape(comment['time'])
                safe_type = html.escape(comment['type'])
                safe_text = html.escape(comment['text']).replace('\n', '<br>')
                
                # 게시물 카드 HTML (답글 제외)
                post_html = f"""
                <div class="post-card">
                    <div class="post-header">
                        <div>
                            <div class="post-author">{safe_name}</div>
                            <div class="post-time">{safe_time}</div>
                        </div>
                        <div class="post-header-right">
                            {status_html}
                        </div>
                    </div>
                    <div class="post-category {category_class}">
                        {safe_type}
                    </div>
                    <div class="post-content">
                        {safe_text}
                    </div>
                </div>
                """
                
                # 게시물 카드 표시
                st.markdown(post_html, unsafe_allow_html=True)
                
                # 관리자 답변을 Streamlit 컴포넌트로 표시 (화살표 아이콘과 들여쓰기)
                if comment.get("replies"):
                    for reply in comment["replies"]:
                        with st.container():
                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: flex-start; margin: 10px 0;">
                                    <div style="
                                        color: #667eea;
                                        font-size: 1.5em;
                                        margin-right: 10px;
                                        margin-top: 5px;
                                        font-weight: bold;
                                    ">
                                        ↳
                                    </div>
                                    <div style="
                                        background: linear-gradient(135deg, #667eea, #764ba2);
                                        color: white;
                                        padding: 15px;
                                        border-radius: 10px;
                                        border-left: 4px solid #4834d4;
                                        flex: 1;
                                    ">
                                        <strong>👨‍💼 관리자 답변</strong><br><br>
                                        {reply['text']}<br>
                                        <small style="opacity: 0.8;">{reply['time']}</small>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
        else:
            st.markdown(
                """
                <div style="
                    text-align: center; 
                    padding: 60px 40px; 
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 20px;
                    margin: 30px 0;
                    border: 2px dashed #dee2e6;
                ">
                    <div style="font-size: 3em; margin-bottom: 20px;">📝</div>
                    <h3 style="color: #495057; margin-bottom: 15px;">아직 작성된 글이 없습니다</h3>
                    <p style="color: #6c757d; font-size: 1.1em;">첫 번째 글을 작성하여 커뮤니티를 활성화해보세요!</p>
                    <div style="margin-top: 20px;">
                        <span style="
                            background: linear-gradient(135deg, #667eea, #764ba2);
                            color: white;
                            padding: 8px 20px;
                            border-radius: 25px;
                            font-size: 0.9em;
                            display: inline-block;
                        ">💡 질문, 아이디어, 정보공유 모두 환영합니다!</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )



elif menu == "📧 문의하기":
    st.markdown("### 📞 문의처")

    st.markdown(
        """
    <div class="info-card">
        <h4>경상북도교육청 기획예산관</h4>
        <p>📧 이메일: chs0601@gbe.kr</p>
        <p>👤 담당자: 공모전 담당자</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# 푸터
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: gray;">
    <p>2025 AI(새)로고침! 우리 교실 앱 공모전 | 경상북도교육청</p>
</div>
""",
    unsafe_allow_html=True,
)
