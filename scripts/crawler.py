import pandas as pd
from datetime import date, timedelta
import datetime
import requests
import OpenDartReader
import re
from bs4 import BeautifulSoup
from srim_page.models import Stock
import html5lib

#### KRX(한국거래소) 데이터 - 종목코드, 종목명, 상장주식수


## generate.cmd에서 otp를 가져올 것
otp_url = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
if datetime.date.today().weekday() > 5:
    today = str(datetime.date.today() - timedelta(2))
elif datetime.date.today().weekday() > 4:
    today = str(datetime.date.today() - timedelta(1))
else:
    today = str(datetime.date.today())  # 오늘 날짜를 기입하기 위함, Datetime을 str형태로 변환
today = re.sub('-', '', today)  # 문자 - 를 제거

otp_form_data = {
    'mktId': 'ALL',
    'trdDd': today,
    'share': '1',
    'money': '1',
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT01501'
}

# post방식 활용
otp = requests.post(otp_url, otp_form_data).text

## download.cmd에서 Post방식으로 데이터를 가져올 것(위의 otp 활용)
csv_url = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
csv_form_data = requests.post(csv_url, {'code': otp})

## 데이터 전처리 과정
stock_data = csv_form_data.content.decode('EUC-KR')  # EUC-KR 방식으로 Decoding
stock_data = stock_data.split("\n")  # "\n" 기준으로 나눌 것

# 데이터 프레임 만드는 과정
stock_column = stock_data[0].split(",")  # 칼럼 값 지정, stock_data의 0번째, List 형태로 입력
stock_df = pd.DataFrame(columns=stock_column)  # 컬럼 값만 지정해 놓은 빈 데이터 프레임

# row 값 지정
for row in range(1, len(stock_data)):
    try:
        stock_data[row] = re.sub('"', '', stock_data[row])  # row 값 안의"" 문자열 제거
        stock_row = stock_data[row].split(",")  # 다시 List 형태로 입력
        stock_row_df = pd.DataFrame(data=[stock_row], columns=stock_column)  # 한 줄 형태의 DataFrame 지정
        stock_df = pd.concat([stock_df, stock_row_df])  # 전체 데이터 프레임과 한 줄 형태 데이터 프레임 계속 결합
    except:
        print(row)  # 만일 오류 있을시 row값 출력
        continue

# 종목코드열을 Index로 만듬
stock_df.set_index('종목코드', inplace=True)

# 필요항목(열)만 추출
stock_df = stock_df.loc[:, ['종목명', '시장구분', '종가', '시가총액', '상장주식수']]


#### 종목명, 시장, 종가 가져오는 함수 만들기
# 종목명 가져오는 함수
def stock_name(stock_code):
    stock_name = stock_df.loc[stock_code]['종목명']

    return stock_name


# 코스닥/코스피/코스넥 가져오는 함수
def stock_market(stock_code):
    stock_market = stock_df.loc[stock_code]['시장구분']

    return stock_market


# 종가 가져오는 함수
def stock_price(stock_code):
    stock_price = int(stock_df.loc[stock_code]['종가'])
    # stock_price = format(stock_price, ",")

    return stock_price


#### 한국신용평가 데이터 - 회사채 BBB- 값

## 회사채 BBB-값 구하기
credit_table_url = "https://www.kisrating.com/ratingsStatistics/statics_spread.do" # 한국신용평가 신용등급표 url
req = requests.get(credit_table_url) # get방식으로 불러오기
page_soup = BeautifulSoup(req.text, 'lxml') # BS활용 파싱
credit_table = page_soup.select_one('div.table_ty1') # 테이블 Div, table_ty1 기준으로 가져오기
credit_df = pd.read_html(str(credit_table))[0] # 판다스 read_html 방식으로 표 불러오기, str 방식으로 위의 credit_table 호출
credit_df.set_index('구분', inplace=True) # '구분'열 기준으로 인덱싱
bbb = credit_df.loc['BBB-', '5년'] # 인덱스 BBB-, 컬럼 5년 기준 값 bbb로 지정


#### 네이버금융 데이터 - 자본총계, ROE


## 네이버 재무제표 테이블화
def naver_df(stock_code, report_type):
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

    # 컬럼명 통일시킬것(결산보고일이 다르기 때문에), + 연결/별도에 따라 컬럼명 바꾸기
    columns_ = []
    if report_type == 4:
        columns_ = ['2016(IFRS연결)', '2017(IFRS연결)', '2018(IFRS연결)', '2019(IFRS연결)', '2020(IFRS연결)',
                    '2021(E, IFRS연결)', '2022(E, IFRS연결)', '2023(E, IFRS연결)']
    elif report_type == 3:
        columns_ = ['2016(IFRS별도)', '2017(IFRS별도)', '2018(IFRS별도)', '2019(IFRS별도)', '2020(IFRS별도)',
                    '2021(E, IFRS별도)', '2022(E, IFRS별도)', '2023(E, IFRS별도)']
    df.columns = columns_

    # 필요부분만 추출
    # df = df.transpose() # 행과 열 바꾸기, 열 : 재무정보 / 행 : 발행년도
    df = df.iloc[:, [0, 1, 2, 3, 4]]  # 발행년도 2016~2020만 추출

    return df


## 자기자본총계 지배주주지분 출력함수
def naver_equity(stock_code):
    if naver_df(stock_code, 4).loc['자본총계(지배)', '2020(IFRS연결)'] != 0:
        df = naver_df(stock_code, 4)
        equity = df.loc['자본총계(지배)', '2020(IFRS연결)']  # loc 메소드 활용, row 자본총계(지배) column 2020/12 연결 값 출력

    else:
        df = naver_df(stock_code, 3)
        equity = df.loc['자본총계(지배)', '2020(IFRS별도)']  # loc 메소드 활용, row 자본총계(지배) column 2020/12 별도 값 출력

    equity = equity * 100000000  # 억 단위 변환

    return equity


## 3년 가중평균 roe 값 구하는 함수
def roe_3(stock_code):
    if naver_df(stock_code, 4).loc['ROE(%)', '2020(IFRS연결)'] != 0:
        df = naver_df(stock_code, 4)
        roe_1st = df.loc['ROE(%)', '2020(IFRS연결)']
        roe_2nd = df.loc['ROE(%)', '2019(IFRS연결)']
        roe_3rd = df.loc['ROE(%)', '2018(IFRS연결)']

    else:
        df = naver_df(stock_code, 3)
        roe_1st = df.loc['ROE(%)', '2020(IFRS별도)']
        roe_2nd = df.loc['ROE(%)', '2019(IFRS별도)']
        roe_3rd = df.loc['ROE(%)', '2018(IFRS별도)']

    # 가중평균 중 나누기 값을 구하기 위함, 만약 3년전 roe 값 0이라면 가중치를 0으로 둬야하기 때문
    roe_list = [roe_1st, roe_2nd, roe_3rd]
    count_list = []
    for count in [0, 1, 2]:
        if roe_list[count] != 0:
            count_list.append(-(count - 3))
        else:
            count_list.append(0)

    roe_average = ((roe_1st * 3) + (roe_2nd * 2) + (roe_3rd * 1)) / (count_list[0] + count_list[1] + count_list[2])

    return roe_average


#### 에프앤가이드 데이터 - 자사주

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

    return mystock_count


## 유통주식수 가져오는 함수
def stock_count(stock_code):
    stock_count = int(stock_df.loc[stock_code]['상장주식수']) - int(mystock_count_df(stock_code))

    return stock_count


#### 기업가치 = 자기자본 + (초과이익/할인율)
#### 초과이익 = 자기자본 * (3년가중평균 ROE - BBB-할인율)
#### 적정주가 = 기업가치 / 유통주식수

## s-rim 적정가치 구하는 함수
def srim(stock_code, w):
    equity = naver_equity(stock_code)  # 자기자본(지배주주지분)
    roe = roe_3(stock_code)  # 3년 가중평균 ROE
    k = bbb  # 할인율

    excess_profit = equity * ((roe - k) / 100)  # 초과이익 = 자기자본 * (ROE-할인율), 100분율 고려
    company_value = equity + excess_profit * w / (1 + (k / 100) - w)  # 시가총액 = 자기자본 + 초과이익 * 이익계수 /(1+할인율-이익계수)

    srim = company_value / stock_count(stock_code)  # 적정주가 = 시가총액/유통주식수

    srim = int(srim.round())  # 반올림 + 정수형(int)
    # srim = format(srim, ",")

    return srim


## 괴리율 구하는 함수
def gap_(stock_code):
    gap = (((stock_price(stock_code) - srim(stock_code, 1)) / srim(stock_code, 1)) * 100)
    gap = round(gap, 2)  # 2번째자리 반올림

    return gap


# 매출액 : 50억미만, 2년 (별도)
# 법인세비용차감전계속사업손실 : 법인세비용차감전손실 > 자기자본(지배지분)/2, 3년간 2회 (연결)
# 장기간영업손실 : 최근 4년동안 적자 (별도)
# 자본잠식 : 자본금/자본총계 > 50%


def risk_revenue(stock_code):
    revenue_2020 = naver_df(stock_code, 3).loc['매출액', '2020(IFRS별도)']
    revenue_2019 = naver_df(stock_code, 3).loc['매출액', '2019(IFRS별도)']

    if revenue_2020 < 50 or revenue_2019 < 50:
        result = 'risk'
    else:
        result = 'okay'

    return result


def risk_profit(stock_code):
    profit_2020 = naver_df(stock_code, 3).loc['영업이익', '2020(IFRS별도)']
    profit_2019 = naver_df(stock_code, 3).loc['영업이익', '2019(IFRS별도)']
    profit_2018 = naver_df(stock_code, 3).loc['영업이익', '2018(IFRS별도)']
    profit_2017 = naver_df(stock_code, 3).loc['영업이익', '2017(IFRS별도)']

    if profit_2020 < 0 or profit_2019 < 0 or profit_2018 < 0 or profit_2017 < 0:
        result = 'risk'
    else:
        result = 'okay'

    return result


def risk_ebitda(stock_code):
    if naver_df(stock_code, 4).loc['세전계속사업이익', '2020(IFRS연결)'] != 0:
        ebitda_2020 = naver_df(stock_code, 4).loc['세전계속사업이익', '2020(IFRS연결)']
        equity_2020 = naver_df(stock_code, 4).loc['자본총계(지배)', '2020(IFRS연결)']
        ebitda_2019 = naver_df(stock_code, 4).loc['세전계속사업이익', '2019(IFRS연결)']
        equity_2019 = naver_df(stock_code, 4).loc['자본총계(지배)', '2019(IFRS연결)']
        ebitda_2018 = naver_df(stock_code, 4).loc['세전계속사업이익', '2018(IFRS연결)']
        equity_2018 = naver_df(stock_code, 4).loc['자본총계(지배)', '2018(IFRS연결)']
    else:
        ebitda_2020 = naver_df(stock_code, 3).loc['세전계속사업이익', '2020(IFRS별도)']
        equity_2020 = naver_df(stock_code, 3).loc['자본총계(지배)', '2020(IFRS별도)']
        ebitda_2019 = naver_df(stock_code, 3).loc['세전계속사업이익', '2019(IFRS별도)']
        equity_2019 = naver_df(stock_code, 3).loc['자본총계(지배)', '2019(IFRS별도)']
        ebitda_2018 = naver_df(stock_code, 3).loc['세전계속사업이익', '2018(IFRS별도)']
        equity_2018 = naver_df(stock_code, 3).loc['자본총계(지배)', '2018(IFRS별도)']

    if ebitda_2020 > equity_2020 / 2 or ebitda_2019 > equity_2019 / 2 or ebitda_2018 > equity_2018 / 2:
        result = 'risk'
    else:
        result = 'okay'

    return result


def risk_capital(stock_code):
    if naver_df(stock_code, 4).loc['자본총계', '2020(IFRS연결)'] != 0:
        total_equity_2020 = naver_df(stock_code, 4).loc['자본총계', '2020(IFRS연결)']
        capital_2020 = naver_df(stock_code, 4).loc['자본금', '2020(IFRS연결)']
        total_equity_2019 = naver_df(stock_code, 4).loc['자본총계', '2019(IFRS연결)']
        capital_2019 = naver_df(stock_code, 4).loc['자본금', '2019(IFRS연결)']
    else:
        total_equity_2020 = naver_df(stock_code, 3).loc['자본총계', '2020(IFRS별도)']
        capital_2020 = naver_df(stock_code, 3).loc['자본금', '2020(IFRS별도)']
        total_equity_2019 = naver_df(stock_code, 3).loc['자본총계', '2019(IFRS별도)']
        capital_2019 = naver_df(stock_code, 3).loc['자본금', '2019(IFRS별도)']

    if capital_2020 / total_equity_2020 >= 0.5 or capital_2019 / total_equity_2019 >= 0.5:
        result = 'risk'
    else:
        result = 'okay'

    return result


def risk(stock_code):
    if risk_revenue(stock_code) == 'risk' or risk_profit(stock_code) == 'risk' or risk_ebitda(
            stock_code) == 'risk' or risk_capital(stock_code) == 'risk':
        result = 'risky'
    else:
        result = 'okay'

    return result


# 실행하는 함수
def run():
    x, _ = Stock.objects.filter(created_at__lte=datetime.date.today() - timedelta(days=1)).delete()
    print(x, 'stock deleted')

    for row in range(0, 15): #len(stock_df)
        try:
            stock_code = stock_df.index[row]
            name = stock_name(stock_code)
            current_price = format(stock_price(stock_code), ",") # 3자리수 콤마
            srim_price = format(srim(stock_code, 1), ",")
            srim10_price = format(srim(stock_code, 0.9), ",")
            srim20_price = format(srim(stock_code, 0.8), ",")
            roe = roe_3(stock_code).round(2)
            gap = gap_(stock_code)
            risky = risk(stock_code)

            if Stock.objects.filter(code=stock_code).count() == 0:
                Stock(code=stock_code, name=name, current_price=current_price, srim_price=srim_price,
                      srim10_price=srim10_price, srim20_price=srim20_price, roe=roe, gap=gap, risky=risky).save()

        except Exception as e:
            print(e)
            continue


