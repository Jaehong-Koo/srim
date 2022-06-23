from scripts.daily_db import *

#### 2. Quarterly 필요한 DB쌓기 - 네이버금융, 에프앤가이드

## 네이버 재무제표 db구축 함수 함수, 초안(연결보고서/별도보고서)
def naver_first(stock_code, report_type):
    url_tmp = "https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=005930"
    r_tmp = requests.get(url_tmp)
    pattern_enc = re.compile("encparam: '(.+)'", re.IGNORECASE)
    pattern_id = re.compile("id: '(.+?)'", re.IGNORECASE)
    target_text = r_tmp.text
    encparam = pattern_enc.search(target_text).groups()[0]
    id_ = pattern_id.search(target_text).groups()[0]

    payload = {}  # 빈 리스트 만들어주기
    payload['cmp_cd'] = stock_code  # 종목코드 넣어주기
    payload['fin_typ'] = report_type  # 4 : 연결보고서 / 3: 별도보고서
    payload['freq_typ'] = 'Y'  # 연간보고서
    payload['encparam'] = encparam
    payload['id'] = id_

    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'Referer': "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?",
        'X-Requested-With': 'XMLHttpRequest'}
    financial_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?"

    r = requests.get(financial_url, params=payload, headers=head)

    df = pd.read_html(r.text)[1]

    df.columns = df.columns.droplevel(0)  # 다중인덱스 -> 단일 인덱스화
    df.set_index('주요재무정보', inplace=True)  # 주요재무정보칼럼 => 인덱스(row)
    df = df.fillna(0)  # 결측값 Nan은 0으로 치환

    # 행과 열 바꾸기, 열 : 재무정보 / 행 : 발행년도
    df = df.transpose()

    return df


## 네이버 재무제표 db구축 함수, 완성본
def naver_total(stock_code):
    df_connect = naver_first(stock_code, 4)
    df_individual = naver_first(stock_code, 3)

    df = pd.concat([df_connect, df_individual], join='inner')

    # 인덱스 이름 재정리(2017~2024)
    index_dict = ['2017(IFRS연결)', '2018(IFRS연결)', '2019(IFRS연결)', '2020(IFRS연결)', '2021(IFRS연결)', '2022(IFRS연결)',
                  '2023(IFRS연결)', '2024(IFRS연결)',
                  '2017(IFRS별도)', '2018(IFRS별도)', '2019(IFRS별도)', '2020(IFRS별도)', '2021(IFRS별도)', '2022(IFRS별도)',
                  '2023(IFRS별도)', '2024(IFRS별도)']
    df.index = index_dict

    # 발행년도 2017~2021만 추출
    df = df.loc[['2017(IFRS연결)', '2018(IFRS연결)', '2019(IFRS연결)', '2020(IFRS연결)', '2021(IFRS연결)',
                 '2017(IFRS별도)', '2018(IFRS별도)', '2019(IFRS별도)', '2020(IFRS별도)', '2021(IFRS별도)']]

    # stock_code 열 추가
    df['종목코드'] = stock_code

    # 컬럼 정리(필요항목만)
    df = df[['종목코드', '매출액', '영업이익', '세전계속사업이익', '자본총계(지배)', '자본총계', '자본금', 'ROE(%)']]

    return df


### 에프앤가이드 데이터 - 자사주

## 자사주 가져오는 함수
def mystock_count_df(stock_code):
    ##### 스냅샷 홈페이지 : 'http://comp.fnguide.com/SVO2/asp/SVD_Main.asp?pGB=1&gicode=A005930&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701'
    ##### gicode = A다음자리가 종목코드
    ##### get 방식으로 부르기
    url = 'http://comp.fnguide.com/SVO2/asp/SVD_Main.asp?pGB=1&gicode=A{}&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701'.format(
        stock_code)
    r = requests.get(url)
    df_1 = pd.read_html(r.text)  # 텍스트를 데이터프레임화
    df_2 = df_1[4]  # 4번째 값이 찾고자 하는 자사주란이 있음
    df_3 = df_2.loc[4]  # 4번째 행 값이 자사주 행

    mystock_count = df_3[2]  # 3번째 열 값이 찾고자 하는 값

    # 자사주가 없는 경우, 0값으로 치환
    if str(mystock_count) == 'nan':
        mystock_count = 0
    # 아닌 경우는 그대로(타입만 int형으로 변경)
    else:
        mystock_count == int(mystock_count)

    df = pd.DataFrame({'자사주': [mystock_count]}, index=[stock_code])

    return df

## DB쌓기
def run():
    stock_df = pd.read_hdf('stock.hdf', key='df')

    naver_report = pd.DataFrame()
    fnguide_df = pd.DataFrame()
    for cnt in range(0, len(stock_df)):  # len(stock_df)
        stock_code = stock_df.iloc[cnt].name
        try:
            naver_report = pd.concat([naver_report, naver_total(stock_code)])
            fnguide_df = pd.concat([fnguide_df, mystock_count_df(stock_code)])
            # print("done")
        except:
            # print(stock_code)
            pass

    naver_report = naver_report.fillna(0)

    fnguide_df.to_hdf('fnguide.hdf', key='df')
    naver_report.to_hdf('naver.hdf', key='df')




