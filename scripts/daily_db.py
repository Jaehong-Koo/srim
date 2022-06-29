import pandas as pd
from datetime import date, timedelta
import datetime
import requests
import re
from bs4 import BeautifulSoup
from srim_page.models import Stock
import html5lib


def run():
    #### 1. Daily 필요한 DB 쌓기 - KRX(한국거래소)

    ### KRX(한국거래소) 데이터 - 종목코드, 종목명, 상장주식수, 섹터(코스피/코스닥)
    ### KRX정보데이터의 종목시세, 산업별구분(코스피/코스닥) 페이지에서 정보를 가져와야 함

    ## (공통) generate.cmd에서 otp를 가져올 것
    otp_url = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
    if datetime.date.today().weekday() > 5:
        today = str(datetime.date.today() - timedelta(2))
    elif datetime.date.today().weekday() > 4:
        today = str(datetime.date.today() - timedelta(1))
    else:
        today = str(datetime.date.today())  # 오늘 날짜를 기입하기 위함, Datetime을 str형태로 변환
    today = re.sub('-', '', today)  # 문자 - 를 제거

    ## 종목시세 페이지의 otp_form_data
    otp_form_data = {
        'mktId': 'ALL',
        'trdDd': today,
        'share': '1',
        'money': '1',
        'csvxls_isNo': 'false',
        'name': 'fileDown',
        'url': 'dbms/MDC/STAT/standard/MDCSTAT01501'
    }

    ## 산업별분류 페이지(코스피) otp_form_data
    otp_form_data_kospi = {
        'mktId': 'STK',
        'trdDd': today,
        'money': '1',
        'csvxls_isNo': 'false',
        'name': 'fileDown',
        'url': 'dbms/MDC/STAT/standard/MDCSTAT03901'
    }

    ## 산업별분류 페이지(코스닥) otp_form_data
    otp_form_data_kosdaq = {
        'mktId': 'KSQ',
        'trdDd': today,
        'money': '1',
        'csvxls_isNo': 'false',
        'name': 'fileDown',
        'url': 'dbms/MDC/STAT/standard/MDCSTAT03901'
    }

    ## 각 otp_form_data에 따른 데이터 프레임 반환 함수
    def krx_df(otp_form_data):
        otp = requests.post(otp_url, otp_form_data).text  # Post방식 활용해서 code값 반환

        # download.cmd에서 Post방식으로 데이터를 가져올 것(위의 otp 활용)
        csv_url = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
        csv_form_data = requests.post(csv_url, {'code': otp})

        # 데이터 전처리 과정
        stock_data = csv_form_data.content.decode('EUC-KR')  # EUC-KR 방식으로 Decoding
        stock_data = stock_data.split("\n")  # "\n" 기준으로 나눌 것(줄나누기)

        # 데이터 프레임 만드는 과정
        stock_column = stock_data[0].split(",")  # 칼럼 값 지정, stock_data의 0번째, List 형태로 입력
        stock_df = pd.DataFrame(columns=stock_column)  # 컬럼 값만 지정해 놓은 빈 데이터 프레임

        # stock_df의 각 row값 지정
        for row in range(1, len(stock_data)):
            try:
                stock_data[row] = re.sub('"', '', stock_data[row])  # row 값 안의"" 문자열 제거
                stock_row = stock_data[row].split(",")  # 다시 List 형태로 입력
                stock_row_df = pd.DataFrame(data=[stock_row], columns=stock_column)  # 한 줄 형태의 DataFrame 지정
                stock_df = pd.concat([stock_df, stock_row_df])  # 전체 데이터 프레임과 한 줄 형태 데이터 프레임 계속 결합
            except:
                pass  # 오류가 있을시에는 넘길 것

        # 종목코드열을 Index로 만듬
        stock_df.set_index('종목코드', inplace=True)

        return stock_df

    ## 각 데이터 프레임 지정

    # 종가, 상장주식수 데이터 프레임
    krx_stock_df = krx_df(otp_form_data)

    # 섹터가 담긴 데이터 프레임(코스피/코스닥)
    krx_sector_df = pd.concat([krx_df(otp_form_data_kospi), krx_df(otp_form_data_kosdaq)])

    # 모두 합칠 것(위 두개)
    stock_df = krx_stock_df.join(krx_sector_df['업종명'], on='종목코드')

    # 필요항목(열)만 추출
    stock_df = stock_df.loc[:, ['종목명', '시장구분', '업종명', '상장주식수']]

    # 결측치 대체
    stock_df = stock_df.fillna('해당없음')

    # stock_df.to_hdf('stock.hdf', key='df')


# # 현재 가격, 네이버금융에서 크롤링하는 함수
# def stock_price(stock_code):
#     url = 'https://finance.naver.com/item/main.nhn?code={}'.format(stock_code)
#     r = requests.get(url)
#     bs = BeautifulSoup(r.text, "html.parser")
#     result = bs.find("p", {"class": "no_today"}).find("span", {"class": "blind"}).text
#     result = result.replace(',', '')
#     result = int(result)
#
#     return result

    # 현재 가격, 네이버금융에서 크롤링하는 함수
    def stock_price(stock_code):
        url = 'https://finance.naver.com/item/main.nhn?code={}'.format(stock_code)
        r = requests.get(url)
        bs = BeautifulSoup(r.text, "html.parser")
        result = bs.find("p", {"class": "no_today"}).find("span", {"class": "blind"}).text
        result = result.replace(',', '')
        result = int(result)

        return result



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


    naver_report = pd.DataFrame()
    fnguide_df = pd.DataFrame()
    for cnt in range(0, len(stock_df)):  # len(stock_df)
        stock_code = stock_df.iloc[cnt].name
        try:
            naver_report = pd.concat([naver_report, naver_total(stock_code)])
            fnguide_df = pd.concat([fnguide_df, mystock_count_df(stock_code)])
            print(cnt, "done")
        except:
            print(stock_code)
            pass

    naver_report = naver_report.fillna(0)




    #### 3. 위의 DB를 활용해서 뽑아내는 함수

    ## KRX

    # 종목명 가져오는 함수
    def stock_name(stock_code):
        stock_name = stock_df.loc[stock_code]['종목명']

        return stock_name

    # 코스닥/코스피/코스넥 가져오는 함수
    def stock_market(stock_code):
        stock_market = stock_df.loc[stock_code]['시장구분']

        return stock_market

    # 섹터 가져오는 함수
    def stock_sector(stock_code):
        stock_sector = stock_df.loc[stock_code]['업종명']

        return stock_sector

    ## 한국신용평가

    # 회사채 BBB-값 반환 함수
    def bbb():
        credit_table_url = "https://www.kisrating.com/ratingsStatistics/statics_spread.do"  # 한국신용평가 신용등급표 url
        req = requests.get(credit_table_url)  # get방식으로 불러오기
        page_soup = BeautifulSoup(req.text, 'lxml')  # BS활용 파싱
        credit_table = page_soup.select_one('div.table_ty1')  # 테이블 Div, table_ty1 기준으로 가져오기
        credit_df = pd.read_html(str(credit_table))[0]  # 판다스 read_html 방식으로 표 불러오기, str 방식으로 위의 credit_table 호출
        credit_df.set_index('구분', inplace=True)  # '구분'열 기준으로 인덱싱
        bbb_value = credit_df.loc['BBB-', '5년']  # 인덱스 BBB-, 컬럼 5년 기준 값 bbb로 지정

        return bbb_value

    ## 네이버금융

    # 종목코드별 재무제표 반환 함수
    def naver_df(stock_code):
        df = naver_report[naver_report['종목코드'] == stock_code]

        return df

    # 자기자본총계(지배주주지분) 출력함수
    def naver_equity(stock_code):
        if naver_df(stock_code)['자본총계(지배)']['2021(IFRS연결)'] != 0:
            equity = naver_df(stock_code)['자본총계(지배)']['2021(IFRS연결)']  # 컬럼 : 자본총계(지배), 인덱스 : 2021/12 연결 값 출력

        else:
            equity = naver_df(stock_code)['자본총계(지배)']['2021(IFRS별도)']  # 컬럼 : 자본총계(지배), 인덱스 : 2021/12 별도 값 출력

        equity = equity * 100000000  # 억 단위 변환

        return equity

    # roe 구하는 함수
    def roe(stock_code, year):
        if naver_df(stock_code)['ROE(%)'][year + '(IFRS연결)'] != 0:
            roe_result = naver_df(stock_code)['ROE(%)'][year + '(IFRS연결)']

        else:
            roe_result = naver_df(stock_code)['ROE(%)'][year + '(IFRS별도)']

        return roe_result

    # 3년 가중평균 roe 값 구하는 함수
    def roe_3(stock_code):
        roe_1st = roe(stock_code, '2021')
        roe_2nd = roe(stock_code, '2020')
        roe_3rd = roe(stock_code, '2019')

        # 가중평균 중 나누기 값을 구하기 위함, 만약 3년전 roe 값 0이라면 가중치를 0으로 둬야하기 때문
        roe_list = [roe_1st, roe_2nd, roe_3rd]
        count_list = []
        for count in [0, 1, 2]:
            if roe_list[count] != 0:
                count_list.append(-(count - 3))
            else:
                count_list.append(0)
        try:
            roe_average = ((roe_1st * 3) + (roe_2nd * 2) + (roe_3rd * 1)) / (
                    count_list[0] + count_list[1] + count_list[2])
        except:
            roe_average = 0

        return roe_average

    ## 상장폐지 4가지 요건
    # 매출액 : 50억미만, 2년 (별도)
    # 법인세비용차감전계속사업손실 : 법인세비용차감전손실 > 자기자본(지배지분)/2, 3년간 2회 (연결)
    # 장기간영업손실 : 최근 4년동안 적자 (별도)
    # 자본잠식 : 자본금/자본총계 > 50%

    def risk_revenue(stock_code):
        revenue_2021 = naver_df(stock_code)['매출액']['2021(IFRS별도)']
        revenue_2020 = naver_df(stock_code)['매출액']['2020(IFRS별도)']

        if revenue_2021 < 50 or revenue_2020 < 50:
            result = 'risky'
        else:
            result = 'okay'

        return result

    def risk_profit(stock_code):
        profit_2021 = naver_df(stock_code)['영업이익']['2021(IFRS별도)']
        profit_2020 = naver_df(stock_code)['영업이익']['2020(IFRS별도)']
        profit_2019 = naver_df(stock_code)['영업이익']['2019(IFRS별도)']
        profit_2018 = naver_df(stock_code)['영업이익']['2018(IFRS별도)']

        if profit_2021 < 0 or profit_2020 < 0 or profit_2019 < 0 or profit_2018 < 0:
            result = 'risky'
        else:
            result = 'okay'

        return result

    def risk_ebitda(stock_code):
        if naver_df(stock_code)['세전계속사업이익']['2021(IFRS연결)'] != 0:
            ebitda_2021 = naver_df(stock_code)['세전계속사업이익']['2021(IFRS연결)']
            equity_2021 = naver_df(stock_code)['자본총계(지배)']['2021(IFRS연결)']
            ebitda_2020 = naver_df(stock_code)['세전계속사업이익']['2020(IFRS연결)']
            equity_2020 = naver_df(stock_code)['자본총계(지배)']['2020(IFRS연결)']
            ebitda_2019 = naver_df(stock_code)['세전계속사업이익']['2019(IFRS연결)']
            equity_2019 = naver_df(stock_code)['자본총계(지배)']['2019(IFRS연결)']
        else:
            ebitda_2021 = naver_df(stock_code)['세전계속사업이익']['2021(IFRS별도)']
            equity_2021 = naver_df(stock_code)['자본총계(지배)']['2021(IFRS별도)']
            ebitda_2020 = naver_df(stock_code)['세전계속사업이익']['2020(IFRS별도)']
            equity_2020 = naver_df(stock_code)['자본총계(지배)']['2020(IFRS별도)']
            ebitda_2019 = naver_df(stock_code)['세전계속사업이익']['2019(IFRS별도)']
            equity_2019 = naver_df(stock_code)['자본총계(지배)']['2019(IFRS별도)']

        if ebitda_2021 > equity_2021 / 2 or ebitda_2020 > equity_2020 / 2 or ebitda_2019 > equity_2019 / 2:
            result = 'risky'
        else:
            result = 'okay'

        return result

    def risk_capital(stock_code):
        if naver_df(stock_code)['자본총계']['2021(IFRS연결)'] != 0:
            total_equity_2021 = naver_df(stock_code)['자본총계']['2021(IFRS연결)']
            capital_2021 = naver_df(stock_code)['자본금']['2021(IFRS연결)']
            total_equity_2020 = naver_df(stock_code)['자본총계']['2020(IFRS연결)']
            capital_2020 = naver_df(stock_code)['자본금']['2020(IFRS연결)']
        else:
            total_equity_2021 = naver_df(stock_code)['자본총계']['2021(IFRS별도)']
            capital_2021 = naver_df(stock_code)['자본금']['2021(IFRS별도)']
            total_equity_2020 = naver_df(stock_code)['자본총계']['2020(IFRS별도)']
            capital_2020 = naver_df(stock_code)['자본금']['2020(IFRS별도)']

        if capital_2021 / total_equity_2021 >= 0.5 or capital_2020 / total_equity_2020 >= 0.5:
            result = 'risky'
        else:
            result = 'okay'

        return result

    ##에프앤가이드

    # 유통주식수 가져오는 함수
    def stock_count(stock_code):
        stock_count = int(stock_df['상장주식수'][stock_code]) - int(fnguide_df['자사주'][stock_code])

        return stock_count

    #### 4. 위의 재료를 활용해서 계산하는 함수(Daily)
    #### - Risk구분(4가지 요건), 유통주식수

    ### 기업가치 = 자기자본 + (초과이익/할인율)
    ### 초과이익 = 자기자본 * (3년가중평균 ROE - BBB-할인율)
    ### 적정주가 = 기업가치 / 유통주식수

    ## s-rim 적정가치 구하는 함수
    def srim(stock_code, w):
        equity = naver_equity(stock_code)  # 자기자본(지배주주지분)
        roe = roe_3(stock_code)  # 3년 가중평균 ROE
        k = bbb()  # 할인율

        excess_profit = equity * ((roe - k) / 100)  # 초과이익 = 자기자본 * (ROE-할인율), 100분율 고려
        company_value = equity + excess_profit * w / (1 + (k / 100) - w)  # 시가총액 = 자기자본 + 초과이익 * 이익계수 /(1+할인율-이익계수)

        srim = company_value / stock_count(stock_code)  # 적정주가 = 시가총액/유통주식수

        srim = int(srim.round())  # 반올림 + 정수형(int)
        # srim = format(srim, ",")

        return srim

    ## 괴리율 구하는 함수
    def gap_(stock_code):
        gap = (((stock_price(stock_code) - srim(stock_code, 1)) / srim(stock_code, 1)) * 100)
        # gap = round(gap, 2) # 2번째자리 반올림

        return gap

    ## 상장폐지 요건 구하는 함수
    def risk(stock_code):
        if risk_revenue(stock_code) == 'risky' or risk_profit(stock_code) == 'risky' or risk_ebitda(
                stock_code) == 'risky' or risk_capital(stock_code) == 'risky':
            result = 'risky'
        else:
            result = 'okay'

        return result

    for row in range(0, len(stock_df)):  # len(stock_df)
        try:
            stock_code = stock_df.index[row]
            name = stock_name(stock_code)
            sector = stock_sector(stock_code)
            current_price = stock_price(stock_code)

            srim_price = srim(stock_code, 1)
            srim10_price = srim(stock_code, 0.9)
            srim20_price = srim(stock_code, 0.8)

            roe_average = float(round(roe_3(stock_code), 2))
            roe_2021 = float(round(roe(stock_code, '2021'), 2))
            roe_2020 = float(round(roe(stock_code, '2020'), 2))
            roe_2019 = float(round(roe(stock_code, '2019'), 2))
            bbb_rate = float(bbb())

            gap = float(round(gap_(stock_code), 2))
            risky = risk(stock_code)
            risky_revenue = risk_revenue(stock_code)
            risky_profit = risk_profit(stock_code)
            risky_ebitda = risk_ebitda(stock_code)
            risky_capital = risk_capital(stock_code)

            updated_at = datetime.datetime.now()

            if Stock.objects.filter(code=stock_code).count() == 0:
                Stock(code=stock_code, name=name, sector=sector, current_price=current_price, srim_price=srim_price,
                      srim10_price=srim10_price, srim20_price=srim20_price, roe_average=roe_average,
                      roe_2021=roe_2021, roe_2020=roe_2020, roe_2019=roe_2019, bbb_rate=bbb_rate,
                      gap=gap, risky=risky, risky_revenue=risky_revenue, risky_profit=risky_profit,
                      risky_ebitda=risky_ebitda, risky_capital=risky_capital).save()
            else:
                queryset = Stock.objects.filter(code=stock_code)
                queryset.update(current_price=current_price, srim_price=srim_price, srim10_price=srim10_price,
                                srim20_price=srim20_price, bbb_rate=bbb_rate, gap=gap, updated_at=updated_at)

        except:
            pass
