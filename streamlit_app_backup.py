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

def get_naver_related_keywords(keyword):
    """네이버 쇼핑 검색 결과에서 광범위한 연관키워드를 추출합니다."""
    try:
        encText = urllib.parse.quote(keyword)
        word_frequency = {}
        all_words = set()
        
        # 여러 페이지에서 데이터 수집 (1~500개 상품)
        for start in range(1, 501, 100):  # 5페이지까지 검색
            shop_url = f"https://openapi.naver.com/v1/search/shop.json?query={encText}&display=100&start={start}"
            shop_request = urllib.request.Request(shop_url)
            shop_request.add_header("X-Naver-Client-Id", client_id)
            shop_request.add_header("X-Naver-Client-Secret", client_secret)
            
            try:
                response = urllib.request.urlopen(shop_request)
                result = json.loads(response.read())
                
                for item in result.get("items", []):
                    title = re.sub(r"<.*?>", "", item["title"])
                    
                    # 다양한 패턴으로 키워드 추출
                    # 1. 한글 키워드 (2-10글자)
                    korean_words = re.findall(r'[가-힣]{2,10}', title)
                    # 2. 영어 키워드 (2-15글자)
                    english_words = re.findall(r'[a-zA-Z]{2,15}', title)
                    # 3. 한글+영어+숫자 조합 키워드
                    mixed_words = re.findall(r'[가-힣a-zA-Z0-9]{2,15}', title)
                    # 4. 특수 패턴 (예: iPhone12, 갤럭시S21 등)
                    special_patterns = re.findall(r'[가-힣a-zA-Z]+[0-9]+[가-힣a-zA-Z]*|[가-힣a-zA-Z]*[0-9]+[가-힣a-zA-Z]+', title)
                    
                    # 모든 추출된 단어들을 통합
                    all_extracted_words = korean_words + english_words + mixed_words + special_patterns
                    
                    for word in all_extracted_words:
                        word_clean = word.strip().lower()
                        original_word = word.strip()
                        
                        # 필터링 조건
                        if (len(word_clean) >= 2 and 
                            len(word_clean) <= 20 and
                            word_clean != keyword.lower() and
                            not word_clean.isdigit() and
                            word_clean not in ['상품', '제품', '브랜드', '공식', '정품', '무료배송', '당일발송']):
                            
                            # 원본 대소문자 형태로 저장
                            all_words.add(original_word)
                            word_frequency[original_word] = word_frequency.get(original_word, 0) + 1
                
                time.sleep(0.1)  # API 요청 간격 조절
                
            except Exception as page_error:
                print(f"페이지 {start} 검색 오류: {page_error}")
                continue
        
        # 빈도수 기반 정렬
        sorted_words = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)
        
        # 카테고리별 키워드 분류
        primary_keywords = []      # 기본 키워드와 직접 관련
        secondary_keywords = []    # 일반 연관키워드
        brand_keywords = []        # 브랜드 관련
        tech_keywords = []         # 기술/사양 관련
        
        # 브랜드명 패턴
        brand_patterns = ['삼성', '애플', 'Apple', '엘지', 'LG', '소니', 'Sony', '나이키', 'Nike', 
                         '아디다스', 'Adidas', '로지텍', 'Logitech', '레이저', 'Razer', 'iPhone', 'Galaxy']
        
        # 기술 사양 패턴
        tech_patterns = ['프로', 'Pro', '플러스', 'Plus', '맥스', 'Max', '미니', 'Mini', 
                        '무선', '유선', 'USB', 'Type-C', 'Bluetooth', '블루투스']
        
        for word, freq in sorted_words:
            if freq >= 2:  # 2번 이상 등장한 키워드만 선택
                word_lower = word.lower()
                keyword_lower = keyword.lower()
                
                # 카테고리별 분류
                if (keyword_lower in word_lower or word_lower in keyword_lower):
                    primary_keywords.append(word)
                elif any(brand in word for brand in brand_patterns):
                    brand_keywords.append(word)
                elif any(tech in word for tech in tech_patterns):
                    tech_keywords.append(word)
                else:
                    secondary_keywords.append(word)
        
        # 최종 연관키워드 구성 (우선순위에 따라)
        final_keywords = []
        
        # 1순위: 기본 키워드 관련 (최대 20개)
        final_keywords.extend(primary_keywords[:20])
        
        # 2순위: 브랜드 키워드 (최대 15개)
        final_keywords.extend(brand_keywords[:15])
        
        # 3순위: 기술 사양 키워드 (최대 15개)
        final_keywords.extend(tech_keywords[:15])
        
        # 4순위: 일반 연관키워드 (최대 20개)
        final_keywords.extend(secondary_keywords[:20])
        
        # 중복 제거하면서 순서 유지
        seen = set()
        unique_keywords = []
        for word in final_keywords:
            if word.lower() not in seen:
                seen.add(word.lower())
                unique_keywords.append(word)
        
        # 최대 50개 연관키워드 반환
        return unique_keywords[:50] if unique_keywords else []
        
    except Exception as e:
        st.error(f"연관키워드 검색 오류: {e}")
        return []

def get_related_keywords(keyword):
    """기존 함수 호환성을 위한 래퍼 함수"""
    return get_naver_related_keywords(keyword)

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
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 순위 검색", "🔗 연관키워드 찾기", "📊 연관키워드 순위", "🏆 통합 랭킹"])
    
    # 탭 1: 순위 검색
    with tab1:
        # 사이드바 정보
        with st.sidebar:
            st.header("📋 순위 검색 사용 방법")
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
    
    # 탭 2: 연관키워드 찾기
    with tab2:
        # 사이드바 정보
        with st.sidebar:
            st.header("📋 연관키워드 찾기 사용 방법")
            st.markdown("""
            1. **기본 키워드 입력**: 연관키워드를 찾고 싶은 기본 키워드 입력
            2. **연관키워드 검색**: '연관키워드 찾기' 버튼 클릭
            3. **결과 확인**: 찾은 연관키워드 목록 확인
            4. **순위 탭 이동**: 다음 탭에서 선택한 키워드들의 순위 확인
            """)
            
            st.markdown("---")
            st.markdown("**📌 참고사항**")
            st.markdown("- 네이버 쇼핑 검색 결과 500개 상품을 분석합니다")
            st.markdown("- 브랜드, 기술사양, 관련 키워드를 종합 추출합니다")
            st.markdown("- 최대 50개의 다양한 연관키워드를 제공합니다")
            st.markdown("- 빈도수와 관련성을 기준으로 우선순위를 매깁니다")
        
        st.subheader("🔗 연관키워드 검색")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 기본 키워드 입력
            base_keyword = st.text_input(
                "기본 키워드",
                placeholder="예: 키보드",
                help="연관키워드를 찾고 싶은 기본 키워드를 입력하세요",
                key="base_keyword_input"
            )
            
            # 연관키워드 검색 버튼
            related_search_button = st.button("🔗 연관키워드 찾기", type="primary", use_container_width=True)
        
        with col2:
            if base_keyword:
                st.success(f"✅ 기본 키워드: {base_keyword}")
            else:
                st.info("기본 키워드를 입력하세요")
        
        # 연관키워드 검색 실행
        if related_search_button and base_keyword:
            # 검색 진행률 표시
            search_progress = st.progress(0)
            search_status = st.empty()
            
            search_status.text("🔍 네이버 쇼핑에서 500개 상품 분석 중...")
            search_progress.progress(0.2)
            
            with st.spinner(f"'{base_keyword}' 연관키워드 대규모 검색 중..."):
                related_keywords = get_related_keywords(base_keyword)
            
            search_progress.progress(1.0)
            search_status.text("✅ 연관키워드 검색 완료!")
            
            if related_keywords:
                st.success(f"🎉 총 {len(related_keywords)}개의 연관키워드를 발견했습니다!")
                
                # 세션 상태에 연관키워드 저장
                st.session_state.found_related_keywords = related_keywords
                st.session_state.base_keyword_name = base_keyword
                
                st.subheader("📋 연관키워드 목록")
                
                # 탭으로 카테고리별 분류 표시
                tab_all, tab_primary, tab_brand, tab_tech = st.tabs(["🌟 전체", "🎯 핵심", "🏷️ 브랜드", "⚙️ 기술"])
                
                # 키워드 분류
                brand_patterns = ['삼성', '애플', 'Apple', '엘지', 'LG', '소니', 'Sony', '나이키', 'Nike', 
                                '아디다스', 'Adidas', '로지텍', 'Logitech', '레이저', 'Razer', 'iPhone', 'Galaxy']
                tech_patterns = ['프로', 'Pro', '플러스', 'Plus', '맥스', 'Max', '미니', 'Mini', 
                               '무선', '유선', 'USB', 'Type-C', 'Bluetooth', '블루투스']
                
                primary_keywords = []
                brand_keywords = []
                tech_keywords = []
                other_keywords = []
                
                for keyword in related_keywords:
                    keyword_lower = keyword.lower()
                    base_lower = base_keyword.lower()
                    
                    if base_lower in keyword_lower or keyword_lower in base_lower:
                        primary_keywords.append(keyword)
                    elif any(brand in keyword for brand in brand_patterns):
                        brand_keywords.append(keyword)
                    elif any(tech in keyword for tech in tech_patterns):
                        tech_keywords.append(keyword)
                    else:
                        other_keywords.append(keyword)
                
                with tab_all:
                    st.info(f"📊 전체 {len(related_keywords)}개 연관키워드")
                    # 5열로 표시
                    cols = st.columns(5)
                    for i, keyword in enumerate(related_keywords):
                        with cols[i % 5]:
                            st.markdown(f"**{i+1}.** 🔸 {keyword}")
                
                with tab_primary:
                    st.info(f"🎯 핵심 연관키워드 {len(primary_keywords)}개")
                    if primary_keywords:
                        cols = st.columns(4)
                        for i, keyword in enumerate(primary_keywords):
                            with cols[i % 4]:
                                st.markdown(f"**{i+1}.** 🎯 {keyword}")
                    else:
                        st.warning("핵심 연관키워드가 없습니다.")
                
                with tab_brand:
                    st.info(f"🏷️ 브랜드 키워드 {len(brand_keywords)}개")
                    if brand_keywords:
                        cols = st.columns(4)
                        for i, keyword in enumerate(brand_keywords):
                            with cols[i % 4]:
                                st.markdown(f"**{i+1}.** 🏷️ {keyword}")
                    else:
                        st.warning("브랜드 키워드가 없습니다.")
                
                with tab_tech:
                    st.info(f"⚙️ 기술/사양 키워드 {len(tech_keywords)}개")
                    if tech_keywords:
                        cols = st.columns(4)
                        for i, keyword in enumerate(tech_keywords):
                            with cols[i % 4]:
                                st.markdown(f"**{i+1}.** ⚙️ {keyword}")
                    else:
                        st.warning("기술/사양 키워드가 없습니다.")
                
                # 통계 정보
                st.markdown("---")
                col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                
                with col_stats1:
                    st.metric("전체 키워드", len(related_keywords))
                
                with col_stats2:
                    st.metric("핵심 키워드", len(primary_keywords))
                
                with col_stats3:
                    st.metric("브랜드 키워드", len(brand_keywords))
                
                with col_stats4:
                    st.metric("기술 키워드", len(tech_keywords))
                
                st.success("💡 이제 '📊 연관키워드 순위' 탭으로 이동하여 원하는 키워드들의 순위를 확인하세요!")
                st.info("🚀 또는 '🏆 순위 랭킹' 탭에서 모든 키워드를 한 번에 검색할 수 있습니다!")
            
            else:
                st.error(f"❌ '{base_keyword}'에 대한 연관키워드를 찾을 수 없습니다.")
        
        elif related_search_button and not base_keyword:
            st.error("🚫 기본 키워드를 입력해주세요.")
    
    # 탭 3: 연관키워드 순위 확인
    with tab3:
        # 사이드바 정보
        with st.sidebar:
            st.header("📊 연관키워드 순위 사용 방법")
            st.markdown("""
            1. **키워드 선택**: 이전 탭에서 찾은 연관키워드 중 선택
            2. **판매처명 입력**: 순위를 확인할 쇼핑몰명 입력
            3. **순위 검색**: '순위 확인' 버튼 클릭
            4. **순위별 리스트 확인**: 1위부터 순서대로 정렬된 결과 확인
            """)
            
            st.markdown("---")
            st.markdown("**📌 주의사항**")
            st.markdown("- 먼저 '연관키워드 찾기' 탭에서 키워드를 검색하세요")
            st.markdown("- 최대 50개 연관키워드 중 원하는 것을 선택하세요")
            st.markdown("- 선택한 키워드들이 1위부터 순위별로 정렬됩니다")
            st.markdown("- 대량 선택 시 검색 시간이 오래 걸릴 수 있습니다")
        
        st.subheader("📊 연관키워드 순위 확인")
        
        # 세션 상태에서 연관키워드 확인
        if 'found_related_keywords' in st.session_state and st.session_state.found_related_keywords:
            base_name = st.session_state.get('base_keyword_name', '기본 키워드')
            st.info(f"🔗 '{base_name}'의 연관키워드들 중에서 선택하세요")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**🔸 연관키워드 선택**")
                
                # 전체 선택/해제 버튼
                col_select1, col_select2, col_select3 = st.columns(3)
                with col_select1:
                    select_all = st.button("✅ 전체 선택", use_container_width=True, key="select_all")
                with col_select2:
                    select_none = st.button("❌ 전체 해제", use_container_width=True, key="select_none")
                with col_select3:
                    select_top10 = st.button("🔟 상위 10개", use_container_width=True, key="select_top10")
                
                st.markdown("---")
                
                # 세션 상태로 선택 상태 관리
                if 'selected_related_keywords' not in st.session_state:
                    st.session_state.selected_related_keywords = []
                
                # 버튼 동작 처리
                if select_all:
                    st.session_state.selected_related_keywords = st.session_state.found_related_keywords.copy()
                elif select_none:
                    st.session_state.selected_related_keywords = []
                elif select_top10:
                    st.session_state.selected_related_keywords = st.session_state.found_related_keywords[:10]
                
                # 연관키워드를 체크박스로 표시 (4열 구조로 더 많이 표시)
                st.markdown(f"**📋 연관키워드 목록 ({len(st.session_state.found_related_keywords)}개)**")
                
                # 페이지네이션 (20개씩 표시)
                keywords_per_page = 20
                total_pages = (len(st.session_state.found_related_keywords) + keywords_per_page - 1) // keywords_per_page
                
                if total_pages > 1:
                    page = st.selectbox(f"페이지 선택 (총 {total_pages}페이지)", 
                                      range(1, total_pages + 1), key="keyword_page")
                    start_idx = (page - 1) * keywords_per_page
                    end_idx = start_idx + keywords_per_page
                    display_keywords = st.session_state.found_related_keywords[start_idx:end_idx]
                else:
                    display_keywords = st.session_state.found_related_keywords
                
                # 체크박스 표시
                cols = st.columns(4)
                selected_keywords = []
                
                for i, keyword in enumerate(display_keywords):
                    with cols[i % 4]:
                        # 기존 선택 상태 확인
                        is_selected = keyword in st.session_state.selected_related_keywords
                        
                        if st.checkbox(f"{keyword}", 
                                     value=is_selected,
                                     key=f"rank_related_{keyword}_{page if total_pages > 1 else 1}"):
                            if keyword not in st.session_state.selected_related_keywords:
                                st.session_state.selected_related_keywords.append(keyword)
                        else:
                            if keyword in st.session_state.selected_related_keywords:
                                st.session_state.selected_related_keywords.remove(keyword)
                
                selected_keywords = st.session_state.selected_related_keywords
                
                # 판매처명 입력
                st.markdown("---")
                mall_name_rank = st.text_input(
                    "판매처명",
                    placeholder="예: OO스토어",
                    help="순위를 확인할 쇼핑몰명을 입력하세요",
                    key="mall_name_rank"
                )
                
                # 순위 검색 버튼
                rank_search_button = st.button(
                    f"🎯 순위 확인 ({len(selected_keywords)}개 키워드)",
                    type="primary",
                    use_container_width=True,
                    disabled=len(selected_keywords) == 0 or not mall_name_rank,
                    key="rank_search_button"
                )
            
            with col2:
                st.markdown("**📈 선택 현황**")
                st.metric("선택된 키워드", len(selected_keywords))
                
                if selected_keywords:
                    st.success("✅ 키워드 선택됨")
                    for keyword in selected_keywords[:5]:  # 최대 5개까지 표시
                        st.markdown(f"• {keyword}")
                    if len(selected_keywords) > 5:
                        st.markdown(f"• ... 외 {len(selected_keywords) - 5}개")
                else:
                    st.info("키워드를 선택하세요")
                
                if mall_name_rank:
                    st.success(f"✅ 판매처: {mall_name_rank}")
                else:
                    st.info("판매처명을 입력하세요")
            
            # 순위 검색 실행
            if rank_search_button and selected_keywords and mall_name_rank:
                st.markdown("---")
                st.subheader("🏆 연관키워드 순위 검색 결과")
                
                # 전체 진행률 표시
                overall_progress = st.progress(0)
                overall_status = st.empty()
                
                results_with_rank = []
                no_results = []
                total_keywords = len(selected_keywords)
                
                # 각 키워드별 검색
                for i, keyword in enumerate(selected_keywords):
                    overall_progress.progress((i + 1) / total_keywords)
                    overall_status.text(f"순위 검색 진행률: {i + 1}/{total_keywords} - 현재: '{keyword}'")
                    
                    result = get_top_ranked_product_by_mall(keyword, mall_name_rank)
                    
                    if result:
                        results_with_rank.append({
                            'keyword': keyword,
                            'rank': result['rank'],
                            'title': result['title'],
                            'price': int(result['price']),
                            'link': result['link'],
                            'mallName': result['mallName'],
                            'result_data': result
                        })
                    else:
                        no_results.append(keyword)
                    
                    time.sleep(0.1)  # API 요청 간격 조절
                
                # 검색 완료
                overall_progress.progress(1.0)
                overall_status.text("🎉 모든 순위 검색이 완료되었습니다!")
                
                # 순위별로 정렬 (1위부터)
                results_with_rank.sort(key=lambda x: x['rank'])
                
                # 결과 요약
                st.markdown("---")
                col_summary1, col_summary2, col_summary3 = st.columns(3)
                
                with col_summary1:
                    st.metric("검색한 키워드", total_keywords)
                
                with col_summary2:
                    st.metric("순위 발견", len(results_with_rank))
                
                with col_summary3:
                    st.metric("검색 실패", len(no_results))
                
                # 순위별 결과 표시 (1위부터 리스트 형태)
                if results_with_rank:
                    st.subheader("🥇 순위별 결과 (1위부터)")
                    
                    for i, result in enumerate(results_with_rank, 1):
                        # 순위에 따른 메달 이모지
                        if result['rank'] <= 3:
                            medal = "🥇" if result['rank'] == 1 else "🥈" if result['rank'] == 2 else "🥉"
                        else:
                            medal = "🏅"
                        
                        # 순위 카드 형태로 표시
                        with st.container():
                            st.markdown(f"""
                            <div style='padding: 15px; border-radius: 10px; border: 2px solid #e0e0e0; margin: 10px 0; background-color: #f8f9fa;'>
                                <h4>{medal} {result['rank']}위 - {result['keyword']}</h4>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col_rank1, col_rank2 = st.columns([1, 2])
                            
                            with col_rank1:
                                st.markdown(f"**순위:** {result['rank']}위")
                                st.markdown(f"**가격:** {result['price']:,}원")
                                st.markdown(f"**쇼핑몰:** {result['mallName']}")
                            
                            with col_rank2:
                                st.markdown(f"**상품명:** {result['title']}")
                                st.markdown(f"**링크:** [상품 보기]({result['link']})")
                            
                            st.markdown("---")
                    
                    # 순위 요약 표
                    st.subheader("📋 순위 요약표")
                    summary_data = []
                    for result in results_with_rank:
                        summary_data.append({
                            "순위": f"{result['rank']}위",
                            "키워드": result['keyword'],
                            "상품명": result['title'][:40] + "..." if len(result['title']) > 40 else result['title'],
                            "가격": f"{result['price']:,}원",
                            "쇼핑몰": result['mallName']
                        })
                    
                    st.dataframe(summary_data, use_container_width=True)
                
                # 검색 실패한 키워드들
                if no_results:
                    st.subheader("❌ 순위를 찾을 수 없는 키워드")
                    for keyword in no_results:
                        st.error(f"🚫 {keyword} - 해당 쇼핑몰에서 검색 결과를 찾을 수 없습니다.")
            
            elif rank_search_button:
                st.error("🚫 키워드를 선택하고 판매처명을 입력해주세요.")
        
        else:
            st.warning("⚠️ 먼저 '🔗 연관키워드 찾기' 탭에서 연관키워드를 검색하세요.")
            st.info("💡 이전 탭으로 이동하여 기본 키워드를 입력하고 연관키워드를 찾아보세요!")
    
    # 탭 4: 통합 랭킹 (모든 결과를 1위부터 통합 표시)
    with tab4:
        # 사이드바 정보
        with st.sidebar:
            st.header("🏆 통합 랭킹 사용 방법")
            st.markdown("""
            1. **키워드 일괄 입력**: 여러 키워드를 한 번에 입력
            2. **판매처명 입력**: 순위를 확인할 쇼핑몰명 입력
            3. **일괄 순위 검색**: 모든 키워드의 순위를 한 번에 검색
            4. **통합 랭킹 확인**: 1위부터 순위별로 정렬된 통합 결과
            """)
            
            st.markdown("---")
            st.markdown("**🎯 특징**")
            st.markdown("- 모든 키워드 결과를 1위부터 통합 표시")
            st.markdown("- 순위별 색상 구분 및 메달 표시")
            st.markdown("- 실시간 검색 진행률 표시")
            st.markdown("- 상세 분석 및 비교 기능")
        
        st.subheader("🏆 통합 순위 랭킹 검색")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 키워드 일괄 입력
            ranking_keywords_input = st.text_area(
                "키워드 일괄 입력 (쉼표로 구분)",
                placeholder="예: 키보드, 마우스, 모니터, 헤드셋, 스피커",
                height=120,
                help="순위를 확인하고 싶은 모든 키워드를 쉼표로 구분하여 입력하세요",
                key="ranking_keywords_input"
            )
            
            # 판매처명 입력
            ranking_mall_name = st.text_input(
                "판매처명",
                placeholder="예: OO스토어",
                help="순위를 확인할 쇼핑몰명을 입력하세요",
                key="ranking_mall_name"
            )
            
            # 연관키워드 포함 옵션
            include_related = st.checkbox(
                "🔗 연관키워드도 함께 검색",
                help="입력한 키워드들의 연관키워드도 자동으로 찾아서 함께 검색합니다",
                key="include_related"
            )
            
            # 일괄 검색 버튼
            ranking_search_button = st.button(
                "🚀 통합 순위 검색 시작",
                type="primary",
                use_container_width=True,
                key="ranking_search_button"
            )
        
        with col2:
            st.markdown("**📊 검색 설정 현황**")
            
            if ranking_keywords_input:
                ranking_keywords = [k.strip() for k in ranking_keywords_input.split(",") if k.strip()]
                st.metric("입력된 키워드", len(ranking_keywords))
                
                if include_related:
                    estimated_total = len(ranking_keywords) * 3  # 연관키워드 포함 예상
                    st.info(f"📈 연관키워드 포함 예상: 약 {estimated_total}개")
                
                for keyword in ranking_keywords[:5]:  # 최대 5개까지 미리보기
                    st.markdown(f"• {keyword}")
                if len(ranking_keywords) > 5:
                    st.markdown(f"• ... 외 {len(ranking_keywords) - 5}개")
            else:
                st.metric("입력된 키워드", 0)
            
            if ranking_mall_name:
                st.success(f"✅ 판매처: {ranking_mall_name}")
            else:
                st.info("판매처명을 입력하세요")
        
        # 통합 순위 검색 실행
        if ranking_search_button and ranking_keywords_input and ranking_mall_name:
            ranking_keywords = [k.strip() for k in ranking_keywords_input.split(",") if k.strip()]
            
            st.markdown("---")
            st.subheader("🔍 통합 순위 검색 진행")
            
            # 전체 키워드 수집
            all_search_keywords = ranking_keywords.copy()
            
            # 연관키워드 포함 옵션이 체크된 경우
            if include_related:
                st.info("🔗 대량 연관키워드 검색 중...")
                related_progress = st.progress(0)
                related_status = st.empty()
                
                for i, keyword in enumerate(ranking_keywords):
                    related_progress.progress((i + 1) / len(ranking_keywords))
                    related_status.text(f"'{keyword}' 연관키워드 분석 중... ({i + 1}/{len(ranking_keywords)})")
                    
                    related_keywords = get_naver_related_keywords(keyword)
                    # 각 키워드당 상위 10개 연관키워드 추가 (더 많은 키워드 포함)
                    all_search_keywords.extend(related_keywords[:10])
                    time.sleep(0.2)  # API 요청 간격 조절
                
                related_progress.progress(1.0)
                related_status.text("✅ 연관키워드 검색 완료!")
                st.success(f"🎉 총 {len(all_search_keywords)}개 키워드로 대규모 검색을 시작합니다!")
            
            # 중복 제거
            all_search_keywords = list(dict.fromkeys(all_search_keywords))  # 순서 유지하면서 중복 제거
            
            st.markdown("---")
            st.subheader("🏃‍♂️ 순위 검색 진행")
            
            # 전체 진행률 표시
            main_progress = st.progress(0)
            main_status = st.empty()
            
            all_results = []
            total_search_keywords = len(all_search_keywords)
            
            # 모든 키워드 검색
            for i, keyword in enumerate(all_search_keywords):
                main_progress.progress((i + 1) / total_search_keywords)
                main_status.text(f"검색 진행: {i + 1}/{total_search_keywords} - '{keyword}'")
                
                result = get_top_ranked_product_by_mall(keyword, ranking_mall_name)
                
                if result:
                    all_results.append({
                        'keyword': keyword,
                        'rank': result['rank'],
                        'title': result['title'],
                        'price': int(result['price']),
                        'link': result['link'],
                        'mallName': result['mallName'],
                        'is_original': keyword in ranking_keywords,  # 원본 키워드인지 구분
                        'result_data': result
                    })
                
                time.sleep(0.1)  # API 요청 간격 조절
            
            # 검색 완료
            main_progress.progress(1.0)
            main_status.text("🎉 모든 키워드 검색 완료!")
            
            # 순위별로 정렬 (1위부터)
            all_results.sort(key=lambda x: x['rank'])
            
            st.markdown("---")
            st.subheader("📊 검색 결과 통계")
            
            # 결과 통계
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("검색 키워드", total_search_keywords)
            
            with col_stat2:
                st.metric("순위 발견", len(all_results))
            
            with col_stat3:
                original_found = sum(1 for r in all_results if r['is_original'])
                st.metric("원본 키워드 발견", original_found)
                
            with col_stat4:
                related_found = sum(1 for r in all_results if not r['is_original'])
                st.metric("연관키워드 발견", related_found)
            
            # 통합 순위 랭킹 표시
            if all_results:
                st.markdown("---")
                st.subheader("🏆 통합 순위 랭킹 (1위부터)")
                
                # 상위 랭킹 필터
                rank_filter = st.selectbox(
                    "표시할 순위 범위",
                    ["전체 순위", "1-10위", "1-20위", "1-50위", "1-100위"],
                    key="rank_filter"
                )
                
                # 필터 적용
                if rank_filter == "1-10위":
                    filtered_results = [r for r in all_results if r['rank'] <= 10]
                elif rank_filter == "1-20위":
                    filtered_results = [r for r in all_results if r['rank'] <= 20]
                elif rank_filter == "1-50위":
                    filtered_results = [r for r in all_results if r['rank'] <= 50]
                elif rank_filter == "1-100위":
                    filtered_results = [r for r in all_results if r['rank'] <= 100]
                else:
                    filtered_results = all_results
                
                st.info(f"📋 {len(filtered_results)}개 결과를 표시합니다")
                
                # 순위별 결과 카드 표시
                for i, result in enumerate(filtered_results, 1):
                    # 순위별 메달과 색상
                    if result['rank'] == 1:
                        medal = "🥇"
                        bg_color = "#FFD700"  # 금색
                    elif result['rank'] == 2:
                        medal = "🥈"
                        bg_color = "#C0C0C0"  # 은색
                    elif result['rank'] == 3:
                        medal = "🥉"
                        bg_color = "#CD7F32"  # 동색
                    elif result['rank'] <= 10:
                        medal = "🏅"
                        bg_color = "#E6F3FF"  # 연한 파란색
                    else:
                        medal = "🔸"
                        bg_color = "#F8F9FA"  # 연한 회색
                    
                    # 키워드 타입 표시
                    keyword_type = "🎯 원본" if result['is_original'] else "🔗 연관"
                    
                    # 순위 카드
                    with st.container():
                        st.markdown(f"""
                        <div style='padding: 15px; border-radius: 10px; border: 2px solid #e0e0e0; 
                                    margin: 10px 0; background: linear-gradient(135deg, {bg_color}20, #ffffff);'>
                            <h4>{medal} {result['rank']}위 - {result['keyword']} {keyword_type}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_detail1, col_detail2 = st.columns([1, 2])
                        
                        with col_detail1:
                            st.markdown(f"**🏆 순위:** {result['rank']}위")
                            st.markdown(f"**💰 가격:** {result['price']:,}원")
                            st.markdown(f"**🏪 쇼핑몰:** {result['mallName']}")
                            st.markdown(f"**📂 타입:** {keyword_type}")
                        
                        with col_detail2:
                            st.markdown(f"**📦 상품명:** {result['title']}")
                            st.markdown(f"**🔗 링크:** [상품 보기]({result['link']})")
                        
                        st.markdown("---")
                
                # 순위 요약 테이블
                st.subheader("📋 순위 요약 테이블")
                
                summary_data = []
                for result in filtered_results:
                    keyword_type_text = "원본" if result['is_original'] else "연관"
                    summary_data.append({
                        "순위": result['rank'],
                        "키워드": result['keyword'],
                        "타입": keyword_type_text,
                        "상품명": result['title'][:30] + "..." if len(result['title']) > 30 else result['title'],
                        "가격": f"{result['price']:,}원",
                        "쇼핑몰": result['mallName']
                    })
                
                # 데이터프레임으로 표시 (순위별 색상 적용)
                df = st.dataframe(
                    summary_data, 
                    use_container_width=True,
                    hide_index=True
                )
                
                # 순위 분석 차트
                if len(all_results) > 1:
                    st.subheader("📈 순위 분석")
                    
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        # 원본 vs 연관키워드 순위 분포
                        original_ranks = [r['rank'] for r in all_results if r['is_original']]
                        related_ranks = [r['rank'] for r in all_results if not r['is_original']]
                        
                        st.markdown("**🎯 키워드 타입별 평균 순위**")
                        if original_ranks:
                            avg_original = sum(original_ranks) / len(original_ranks)
                            st.metric("원본 키워드 평균 순위", f"{avg_original:.1f}위")
                        
                        if related_ranks:
                            avg_related = sum(related_ranks) / len(related_ranks)
                            st.metric("연관키워드 평균 순위", f"{avg_related:.1f}위")
                    
                    with col_chart2:
                        # 순위 구간별 분포
                        rank_ranges = {
                            "1-10위": len([r for r in all_results if 1 <= r['rank'] <= 10]),
                            "11-50위": len([r for r in all_results if 11 <= r['rank'] <= 50]),
                            "51-100위": len([r for r in all_results if 51 <= r['rank'] <= 100]),
                            "100위 초과": len([r for r in all_results if r['rank'] > 100])
                        }
                        
                        st.markdown("**📊 순위 구간별 분포**")
                        for range_name, count in rank_ranges.items():
                            if count > 0:
                                st.markdown(f"• {range_name}: {count}개")
            
            else:
                st.error("❌ 검색된 순위 결과가 없습니다.")
                st.info("💡 다른 판매처명을 시도해보시거나 키워드를 조정해보세요.")
        
        elif ranking_search_button:
            st.error("🚫 키워드와 판매처명을 모두 입력해주세요.")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**🔸 연관키워드 선택**")
                
                # 전체 선택/해제 버튼
                col_select1, col_select2, col_select3 = st.columns(3)
                with col_select1:
                    select_all = st.button("✅ 전체 선택", use_container_width=True, key="select_all")
                with col_select2:
                    select_none = st.button("❌ 전체 해제", use_container_width=True, key="select_none")
                with col_select3:
                    select_top10 = st.button("🔟 상위 10개", use_container_width=True, key="select_top10")
                
                st.markdown("---")
                
                # 세션 상태로 선택 상태 관리
                if 'selected_related_keywords' not in st.session_state:
                    st.session_state.selected_related_keywords = []
                
                # 버튼 동작 처리
                if select_all:
                    st.session_state.selected_related_keywords = st.session_state.found_related_keywords.copy()
                elif select_none:
                    st.session_state.selected_related_keywords = []
                elif select_top10:
                    st.session_state.selected_related_keywords = st.session_state.found_related_keywords[:10]
                
                # 연관키워드를 체크박스로 표시 (4열 구조로 더 많이 표시)
                st.markdown(f"**📋 연관키워드 목록 ({len(st.session_state.found_related_keywords)}개)**")
                
                # 페이지네이션 (20개씩 표시)
                keywords_per_page = 20
                total_pages = (len(st.session_state.found_related_keywords) + keywords_per_page - 1) // keywords_per_page
                
                if total_pages > 1:
                    page = st.selectbox(f"페이지 선택 (총 {total_pages}페이지)", 
                                      range(1, total_pages + 1), key="keyword_page")
                    start_idx = (page - 1) * keywords_per_page
                    end_idx = start_idx + keywords_per_page
                    display_keywords = st.session_state.found_related_keywords[start_idx:end_idx]
                else:
                    display_keywords = st.session_state.found_related_keywords
                
                # 체크박스 표시
                cols = st.columns(4)
                selected_keywords = []
                
                for i, keyword in enumerate(display_keywords):
                    with cols[i % 4]:
                        # 기존 선택 상태 확인
                        is_selected = keyword in st.session_state.selected_related_keywords
                        
                        if st.checkbox(f"{keyword}", 
                                     value=is_selected,
                                     key=f"rank_related_{keyword}_{page if total_pages > 1 else 1}"):
                            if keyword not in st.session_state.selected_related_keywords:
                                st.session_state.selected_related_keywords.append(keyword)
                        else:
                            if keyword in st.session_state.selected_related_keywords:
                                st.session_state.selected_related_keywords.remove(keyword)
                
                selected_keywords = st.session_state.selected_related_keywords
                
                # 판매처명 입력
                st.markdown("---")
                mall_name_rank = st.text_input(
                    "판매처명",
                    placeholder="예: OO스토어",
                    help="순위를 확인할 쇼핑몰명을 입력하세요",
                    key="mall_name_rank"
                )
                
                # 순위 검색 버튼
                rank_search_button = st.button(
                    f"🎯 순위 확인 ({len(selected_keywords)}개 키워드)",
                    type="primary",
                    use_container_width=True,
                    disabled=len(selected_keywords) == 0 or not mall_name_rank,
                    key="rank_search_button"
                )
            
            with col2:
                st.markdown("**📈 선택 현황**")
                st.metric("선택된 키워드", len(selected_keywords))
                
                if selected_keywords:
                    st.success("✅ 키워드 선택됨")
                    for keyword in selected_keywords:
                        st.markdown(f"• {keyword}")
                else:
                    st.info("키워드를 선택하세요")
                
                if mall_name_rank:
                    st.success(f"✅ 판매처: {mall_name_rank}")
                else:
                    st.info("판매처명을 입력하세요")
            
            # 순위 검색 실행
            if rank_search_button and selected_keywords and mall_name_rank:
                st.markdown("---")
                st.subheader("🏆 순위 검색 결과")
                
                # 전체 진행률 표시
                overall_progress = st.progress(0)
                overall_status = st.empty()
                
                results_with_rank = []
                no_results = []
                total_keywords = len(selected_keywords)
                
                # 각 키워드별 검색
                for i, keyword in enumerate(selected_keywords):
                    overall_progress.progress((i + 1) / total_keywords)
                    overall_status.text(f"순위 검색 진행률: {i + 1}/{total_keywords} - 현재: '{keyword}'")
                    
                    result = get_top_ranked_product_by_mall(keyword, mall_name_rank)
                    
                    if result:
                        results_with_rank.append({
                            'keyword': keyword,
                            'rank': result['rank'],
                            'title': result['title'],
                            'price': int(result['price']),
                            'link': result['link'],
                            'mallName': result['mallName'],
                            'result_data': result
                        })
                    else:
                        no_results.append(keyword)
                    
                    time.sleep(0.1)  # API 요청 간격 조절
                
                # 검색 완료
                overall_progress.progress(1.0)
                overall_status.text("🎉 모든 순위 검색이 완료되었습니다!")
                
                # 순위별로 정렬 (1위부터)
                results_with_rank.sort(key=lambda x: x['rank'])
                
                # 결과 요약
                st.markdown("---")
                col_summary1, col_summary2, col_summary3 = st.columns(3)
                
                with col_summary1:
                    st.metric("검색한 키워드", total_keywords)
                
                with col_summary2:
                    st.metric("순위 발견", len(results_with_rank))
                
                with col_summary3:
                    st.metric("검색 실패", len(no_results))
                
                # 순위별 결과 표시 (1위부터 리스트 형태)
                if results_with_rank:
                    st.subheader("🥇 순위별 결과 (1위부터)")
                    
                    for i, result in enumerate(results_with_rank, 1):
                        # 순위에 따른 메달 이모지
                        if result['rank'] <= 3:
                            medal = "🥇" if result['rank'] == 1 else "🥈" if result['rank'] == 2 else "🥉"
                        else:
                            medal = "🏅"
                        
                        # 순위 카드 형태로 표시
                        with st.container():
                            st.markdown(f"""
                            <div style='padding: 15px; border-radius: 10px; border: 2px solid #e0e0e0; margin: 10px 0; background-color: #f8f9fa;'>
                                <h4>{medal} {result['rank']}위 - {result['keyword']}</h4>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col_rank1, col_rank2 = st.columns([1, 2])
                            
                            with col_rank1:
                                st.markdown(f"**순위:** {result['rank']}위")
                                st.markdown(f"**가격:** {result['price']:,}원")
                                st.markdown(f"**쇼핑몰:** {result['mallName']}")
                            
                            with col_rank2:
                                st.markdown(f"**상품명:** {result['title']}")
                                st.markdown(f"**링크:** [상품 보기]({result['link']})")
                            
                            st.markdown("---")
                    
                    # 순위 요약 표
                    st.subheader("📋 순위 요약표")
                    summary_data = []
                    for result in results_with_rank:
                        summary_data.append({
                            "순위": f"{result['rank']}위",
                            "키워드": result['keyword'],
                            "상품명": result['title'][:40] + "..." if len(result['title']) > 40 else result['title'],
                            "가격": f"{result['price']:,}원",
                            "쇼핑몰": result['mallName']
                        })
                    
                    st.dataframe(summary_data, use_container_width=True)
                
                # 검색 실패한 키워드들
                if no_results:
                    st.subheader("❌ 순위를 찾을 수 없는 키워드")
                    for keyword in no_results:
                        st.error(f"🚫 {keyword} - 해당 쇼핑몰에서 검색 결과를 찾을 수 없습니다.")
            
            elif rank_search_button:
                st.error("� 키워드를 선택하고 판매처명을 입력해주세요.")
        
        else:
            st.warning("⚠️ 먼저 '🔗 연관키워드 찾기' 탭에서 연관키워드를 검색하세요.")
            st.info("💡 이전 탭으로 이동하여 기본 키워드를 입력하고 연관키워드를 찾아보세요!")
    

        # 사이드바 정보
        with st.sidebar:
            st.header("🏆 순위 랭킹 사용 방법")
            st.markdown("""
            1. **키워드 일괄 입력**: 여러 키워드를 한 번에 입력
            2. **판매처명 입력**: 순위를 확인할 쇼핑몰명 입력
            3. **일괄 순위 검색**: 모든 키워드의 순위를 한 번에 검색
            4. **통합 랭킹 확인**: 1위부터 순위별로 정렬된 통합 결과
            """)
            
            st.markdown("---")
            st.markdown("**🎯 특징**")
            st.markdown("- 모든 키워드 결과를 1위부터 통합 표시")
            st.markdown("- 순위별 색상 구분 및 메달 표시")
            st.markdown("- 실시간 검색 진행률 표시")
            st.markdown("- 상세 분석 및 비교 기능")
        
        st.subheader("🏆 통합 순위 랭킹 검색")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 키워드 일괄 입력
            ranking_keywords_input = st.text_area(
                "키워드 일괄 입력 (쉼표로 구분)",
                placeholder="예: 키보드, 마우스, 모니터, 헤드셋, 스피커",
                height=120,
                help="순위를 확인하고 싶은 모든 키워드를 쉼표로 구분하여 입력하세요",
                key="ranking_keywords_input"
            )
            
            # 판매처명 입력
            ranking_mall_name = st.text_input(
                "판매처명",
                placeholder="예: OO스토어",
                help="순위를 확인할 쇼핑몰명을 입력하세요",
                key="ranking_mall_name"
            )
            
            # 연관키워드 포함 옵션
            include_related = st.checkbox(
                "🔗 연관키워드도 함께 검색",
                help="입력한 키워드들의 연관키워드도 자동으로 찾아서 함께 검색합니다",
                key="include_related"
            )
            
            # 일괄 검색 버튼
            ranking_search_button = st.button(
                "🚀 통합 순위 검색 시작",
                type="primary",
                use_container_width=True,
                key="ranking_search_button"
            )
        
        with col2:
            st.markdown("**📊 검색 설정 현황**")
            
            if ranking_keywords_input:
                ranking_keywords = [k.strip() for k in ranking_keywords_input.split(",") if k.strip()]
                st.metric("입력된 키워드", len(ranking_keywords))
                
                if include_related:
                    estimated_total = len(ranking_keywords) * 3  # 연관키워드 포함 예상
                    st.info(f"📈 연관키워드 포함 예상: 약 {estimated_total}개")
                
                for keyword in ranking_keywords[:5]:  # 최대 5개까지 미리보기
                    st.markdown(f"• {keyword}")
                if len(ranking_keywords) > 5:
                    st.markdown(f"• ... 외 {len(ranking_keywords) - 5}개")
            else:
                st.metric("입력된 키워드", 0)
            
            if ranking_mall_name:
                st.success(f"✅ 판매처: {ranking_mall_name}")
            else:
                st.info("판매처명을 입력하세요")
        
        # 통합 순위 검색 실행
        if ranking_search_button and ranking_keywords_input and ranking_mall_name:
            ranking_keywords = [k.strip() for k in ranking_keywords_input.split(",") if k.strip()]
            
            st.markdown("---")
            st.subheader("🔍 통합 순위 검색 진행")
            
            # 전체 키워드 수집
            all_search_keywords = ranking_keywords.copy()
            
            # 연관키워드 포함 옵션이 체크된 경우
            if include_related:
                st.info("🔗 대량 연관키워드 검색 중...")
                related_progress = st.progress(0)
                related_status = st.empty()
                
                for i, keyword in enumerate(ranking_keywords):
                    related_progress.progress((i + 1) / len(ranking_keywords))
                    related_status.text(f"'{keyword}' 연관키워드 분석 중... ({i + 1}/{len(ranking_keywords)})")
                    
                    related_keywords = get_naver_related_keywords(keyword)
                    # 각 키워드당 상위 10개 연관키워드 추가 (더 많은 키워드 포함)
                    all_search_keywords.extend(related_keywords[:10])
                    time.sleep(0.2)  # API 요청 간격 조절
                
                related_progress.progress(1.0)
                related_status.text("✅ 연관키워드 검색 완료!")
                st.success(f"🎉 총 {len(all_search_keywords)}개 키워드로 대규모 검색을 시작합니다!")
            
            # 중복 제거
            all_search_keywords = list(dict.fromkeys(all_search_keywords))  # 순서 유지하면서 중복 제거
            
            st.markdown("---")
            st.subheader("🏃‍♂️ 순위 검색 진행")
            
            # 전체 진행률 표시
            main_progress = st.progress(0)
            main_status = st.empty()
            
            all_results = []
            total_search_keywords = len(all_search_keywords)
            
            # 모든 키워드 검색
            for i, keyword in enumerate(all_search_keywords):
                main_progress.progress((i + 1) / total_search_keywords)
                main_status.text(f"검색 진행: {i + 1}/{total_search_keywords} - '{keyword}'")
                
                result = get_top_ranked_product_by_mall(keyword, ranking_mall_name)
                
                if result:
                    all_results.append({
                        'keyword': keyword,
                        'rank': result['rank'],
                        'title': result['title'],
                        'price': int(result['price']),
                        'link': result['link'],
                        'mallName': result['mallName'],
                        'is_original': keyword in ranking_keywords,  # 원본 키워드인지 구분
                        'result_data': result
                    })
                
                time.sleep(0.1)  # API 요청 간격 조절
            
            # 검색 완료
            main_progress.progress(1.0)
            main_status.text("🎉 모든 키워드 검색 완료!")
            
            # 순위별로 정렬 (1위부터)
            all_results.sort(key=lambda x: x['rank'])
            
            st.markdown("---")
            st.subheader("📊 검색 결과 통계")
            
            # 결과 통계
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("검색 키워드", total_search_keywords)
            
            with col_stat2:
                st.metric("순위 발견", len(all_results))
            
            with col_stat3:
                original_found = sum(1 for r in all_results if r['is_original'])
                st.metric("원본 키워드 발견", original_found)
                
            with col_stat4:
                related_found = sum(1 for r in all_results if not r['is_original'])
                st.metric("연관키워드 발견", related_found)
            
            # 통합 순위 랭킹 표시
            if all_results:
                st.markdown("---")
                st.subheader("🏆 통합 순위 랭킹 (1위부터)")
                
                # 상위 랭킹 필터
                rank_filter = st.selectbox(
                    "표시할 순위 범위",
                    ["전체 순위", "1-10위", "1-20위", "1-50위", "1-100위"],
                    key="rank_filter"
                )
                
                # 필터 적용
                if rank_filter == "1-10위":
                    filtered_results = [r for r in all_results if r['rank'] <= 10]
                elif rank_filter == "1-20위":
                    filtered_results = [r for r in all_results if r['rank'] <= 20]
                elif rank_filter == "1-50위":
                    filtered_results = [r for r in all_results if r['rank'] <= 50]
                elif rank_filter == "1-100위":
                    filtered_results = [r for r in all_results if r['rank'] <= 100]
                else:
                    filtered_results = all_results
                
                st.info(f"📋 {len(filtered_results)}개 결과를 표시합니다")
                
                # 순위별 결과 카드 표시
                for i, result in enumerate(filtered_results, 1):
                    # 순위별 메달과 색상
                    if result['rank'] == 1:
                        medal = "🥇"
                        bg_color = "#FFD700"  # 금색
                    elif result['rank'] == 2:
                        medal = "🥈"
                        bg_color = "#C0C0C0"  # 은색
                    elif result['rank'] == 3:
                        medal = "🥉"
                        bg_color = "#CD7F32"  # 동색
                    elif result['rank'] <= 10:
                        medal = "🏅"
                        bg_color = "#E6F3FF"  # 연한 파란색
                    else:
                        medal = "🔸"
                        bg_color = "#F8F9FA"  # 연한 회색
                    
                    # 키워드 타입 표시
                    keyword_type = "🎯 원본" if result['is_original'] else "🔗 연관"
                    
                    # 순위 카드
                    with st.container():
                        st.markdown(f"""
                        <div style='padding: 15px; border-radius: 10px; border: 2px solid #e0e0e0; 
                                    margin: 10px 0; background: linear-gradient(135deg, {bg_color}20, #ffffff);'>
                            <h4>{medal} {result['rank']}위 - {result['keyword']} {keyword_type}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_detail1, col_detail2 = st.columns([1, 2])
                        
                        with col_detail1:
                            st.markdown(f"**🏆 순위:** {result['rank']}위")
                            st.markdown(f"**💰 가격:** {result['price']:,}원")
                            st.markdown(f"**🏪 쇼핑몰:** {result['mallName']}")
                            st.markdown(f"**📂 타입:** {keyword_type}")
                        
                        with col_detail2:
                            st.markdown(f"**📦 상품명:** {result['title']}")
                            st.markdown(f"**🔗 링크:** [상품 보기]({result['link']})")
                        
                        st.markdown("---")
                
                # 순위 요약 테이블
                st.subheader("📋 순위 요약 테이블")
                
                summary_data = []
                for result in filtered_results:
                    keyword_type_text = "원본" if result['is_original'] else "연관"
                    summary_data.append({
                        "순위": result['rank'],
                        "키워드": result['keyword'],
                        "타입": keyword_type_text,
                        "상품명": result['title'][:30] + "..." if len(result['title']) > 30 else result['title'],
                        "가격": f"{result['price']:,}원",
                        "쇼핑몰": result['mallName']
                    })
                
                # 데이터프레임으로 표시 (순위별 색상 적용)
                df = st.dataframe(
                    summary_data, 
                    use_container_width=True,
                    hide_index=True
                )
                
                # 순위 분석 차트
                if len(all_results) > 1:
                    st.subheader("📈 순위 분석")
                    
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        # 원본 vs 연관키워드 순위 분포
                        original_ranks = [r['rank'] for r in all_results if r['is_original']]
                        related_ranks = [r['rank'] for r in all_results if not r['is_original']]
                        
                        st.markdown("**🎯 키워드 타입별 평균 순위**")
                        if original_ranks:
                            avg_original = sum(original_ranks) / len(original_ranks)
                            st.metric("원본 키워드 평균 순위", f"{avg_original:.1f}위")
                        
                        if related_ranks:
                            avg_related = sum(related_ranks) / len(related_ranks)
                            st.metric("연관키워드 평균 순위", f"{avg_related:.1f}위")
                    
                    with col_chart2:
                        # 순위 구간별 분포
                        rank_ranges = {
                            "1-10위": len([r for r in all_results if 1 <= r['rank'] <= 10]),
                            "11-50위": len([r for r in all_results if 11 <= r['rank'] <= 50]),
                            "51-100위": len([r for r in all_results if 51 <= r['rank'] <= 100]),
                            "100위 초과": len([r for r in all_results if r['rank'] > 100])
                        }
                        
                        st.markdown("**📊 순위 구간별 분포**")
                        for range_name, count in rank_ranges.items():
                            if count > 0:
                                st.markdown(f"• {range_name}: {count}개")
            
            else:
                st.error("❌ 검색된 순위 결과가 없습니다.")
                st.info("💡 다른 판매처명을 시도해보시거나 키워드를 조정해보세요.")
        
        elif ranking_search_button:
            st.error("🚫 키워드와 판매처명을 모두 입력해주세요.")
    
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