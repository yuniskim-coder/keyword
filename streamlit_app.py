"""
본 프로그램 'RankChecker by 아로미작업실'는 아로미작업실에 의해 개발된 소프트웨어입니다.
해당 소스코드 및 실행 파일의 무단 복제, 배포, 역컴파일, 수정은
저작권법 및 컴퓨터프로그램 보호법에 따라 엄격히 금지됩니다.

무단 유포 및 상업적 이용 시 민형사상 법적 책임을 물을 수 있습니다.

Copyright ⓒ 2025 아로미작업실. All rights reserved.
Unauthorized reproduction or redistribution is strictly prohibited. 
"""

import streamlit as st
import os
import json
import urllib.request
import urllib.parse
import re
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client_id = os.getenv("NAVER_CLIENT_ID", "tp2ypJeFL98lJyTSWLy5")
client_secret = os.getenv("NAVER_CLIENT_SECRET", "QeYFNiR0k7")

def get_top_ranked_product_by_mall(keyword, mall_name, progress_bar=None, status_text=None):
    """네이버 쇼핑에서 특정 쇼핑몰의 최고 순위 상품을 검색합니다."""
    encText = urllib.parse.quote(keyword)
    seen_titles = set()
    best_product = None
    
    for page_num, start in enumerate(range(1, 1001, 100), 1):
        if progress_bar and status_text:
            progress = min(page_num / 10, 1.0)  # 10페이지까지 검색
            progress_bar.progress(progress)
            status_text.text(f"'{keyword}' 검색 중... ({page_num}/10 페이지)")
        
        url = f"https://openapi.naver.com/v1/search/shop.json?query={encText}&display=100&start={start}"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            response = urllib.request.urlopen(request)
            result = json.loads(response.read())
            
            for idx, item in enumerate(result.get("items", []), start=1):
                if item.get("mallName") and mall_name in item["mallName"]:
                    title_clean = re.sub(r"<.*?>", "", item["title"])
                    if title_clean in seen_titles:
                        continue
                    seen_titles.add(title_clean)
                    rank = start + idx - 1
                    product = {
                        "rank": rank,
                        "title": title_clean,
                        "price": item["lprice"],
                        "link": item["link"],
                        "mallName": item["mallName"]
                    }
                    if not best_product or rank < best_product["rank"]:
                        best_product = product
        except Exception as e:
            st.error(f"API 요청 오류: {e}")
            break
        
        time.sleep(0.1)  # API 요청 간격 조절
    
    return best_product

def main():
    # 페이지 설정
    st.set_page_config(
        page_title="네이버 순위 확인기 by 아로미작업실",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 헤더
    st.title("🔍 네이버 순위 확인기")
    st.markdown("**by 아로미작업실**")
    st.markdown("---")
    
    # 사이드바 정보
    with st.sidebar:
        st.header("📋 사용 방법")
        st.markdown("""
        1. **검색어 입력**: 확인하고 싶은 키워드들을 쉼표로 구분하여 입력
        2. **판매처명 입력**: 순위를 확인하고 싶은 쇼핑몰명 입력
        3. **검색 시작**: '순위 확인' 버튼 클릭
        4. **결과 확인**: 각 키워드별 순위와 상품 정보 확인
        """)
        
        st.markdown("---")
        st.markdown("**📌 주의사항**")
        st.markdown("- 최대 10개의 키워드까지 입력 가능")
        st.markdown("- 검색은 네이버 쇼핑 기준입니다")
        st.markdown("- 정확한 쇼핑몰명을 입력해주세요")
    
    # 메인 입력 폼
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔎 검색 설정")
        
        # 검색어 입력
        keywords_input = st.text_area(
            "검색어 입력 (쉼표로 구분, 최대 10개)",
            placeholder="예: 키보드, 마우스, 충전기",
            height=100,
            help="확인하고 싶은 키워드들을 쉼표(,)로 구분하여 입력하세요"
        )
        
        # 판매처명 입력
        mall_name = st.text_input(
            "판매처명",
            placeholder="예: OO스토어",
            help="순위를 확인하고 싶은 쇼핑몰명을 입력하세요"
        )
        
        # 검색 버튼
        search_button = st.button("🔍 순위 확인", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("📊 검색 현황")
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
            st.metric("입력된 키워드 수", len(keywords))
            if len(keywords) > 10:
                st.error("⚠️ 키워드는 최대 10개까지만 입력 가능합니다.")
        else:
            st.metric("입력된 키워드 수", 0)
        
        if mall_name:
            st.success(f"✅ 판매처: {mall_name}")
        else:
            st.info("판매처명을 입력하세요")
    
    # 검색 실행
    if search_button:
        if not keywords_input or not mall_name:
            st.error("🚫 검색어와 판매처명을 모두 입력해주세요.")
            return
        
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        
        if len(keywords) > 10:
            st.error("🚫 키워드는 최대 10개까지만 입력 가능합니다.")
            return
        
        st.markdown("---")
        st.subheader("📈 검색 결과")
        
        # 전체 진행률 표시
        overall_progress = st.progress(0)
        overall_status = st.empty()
        
        results = {}
        total_keywords = len(keywords)
        
        # 각 키워드별 검색
        for i, keyword in enumerate(keywords):
            overall_progress.progress((i + 1) / total_keywords)
            overall_status.text(f"전체 진행률: {i + 1}/{total_keywords} - 현재 검색: '{keyword}'")
            
            # 개별 키워드 진행률
            with st.container():
                col_result1, col_result2 = st.columns([1, 3])
                
                with col_result1:
                    st.write(f"**🔍 {keyword}**")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                with col_result2:
                    result = get_top_ranked_product_by_mall(keyword, mall_name, progress_bar, status_text)
                    
                    if result:
                        results[keyword] = result
                        st.success(f"✅ 순위 발견: {result['rank']}위")
                        
                        # 결과 상세 정보 표시
                        with st.expander(f"📋 '{keyword}' 상세 정보", expanded=True):
                            col_info1, col_info2 = st.columns([1, 1])
                            
                            with col_info1:
                                st.write(f"**순위:** {result['rank']}위")
                                st.write(f"**가격:** {int(result['price']):,}원")
                                st.write(f"**쇼핑몰:** {result['mallName']}")
                            
                            with col_info2:
                                st.write(f"**상품명:** {result['title']}")
                                st.markdown(f"**링크:** [상품 보기]({result['link']})")
                    else:
                        results[keyword] = None
                        st.error(f"❌ '{keyword}' - 해당 쇼핑몰에서 검색 결과를 찾을 수 없습니다.")
                    
                    progress_bar.progress(1.0)
                    status_text.text("검색 완료!")
            
            st.markdown("---")
        
        # 검색 완료
        overall_progress.progress(1.0)
        overall_status.text("🎉 모든 검색이 완료되었습니다!")
        
        # 결과 요약
        st.subheader("📊 검색 결과 요약")
        
        success_count = sum(1 for result in results.values() if result is not None)
        fail_count = total_keywords - success_count
        
        col_summary1, col_summary2, col_summary3 = st.columns(3)
        
        with col_summary1:
            st.metric("전체 키워드", total_keywords)
        
        with col_summary2:
            st.metric("순위 발견", success_count, delta=None if success_count == 0 else "성공")
        
        with col_summary3:
            st.metric("검색 실패", fail_count, delta=None if fail_count == 0 else "실패")
        
        # 성공한 결과들을 표로 정리
        if success_count > 0:
            st.subheader("🏆 순위 발견 결과")
            
            table_data = []
            for keyword, result in results.items():
                if result:
                    table_data.append({
                        "키워드": keyword,
                        "순위": f"{result['rank']}위",
                        "상품명": result['title'][:50] + "..." if len(result['title']) > 50 else result['title'],
                        "가격": f"{int(result['price']):,}원",
                        "쇼핑몰": result['mallName'],
                        "링크": result['link']
                    })
            
            if table_data:
                st.dataframe(table_data, use_container_width=True)
    
    # 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 12px;'>
        ⓒ 2025 아로미작업실. 무단 복제 및 배포 금지. All rights reserved.
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()