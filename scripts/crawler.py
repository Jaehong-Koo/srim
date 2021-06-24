from srim_page.models import Stock
from scripts.quarterly_db import *


def run():
    naver_report = pd.read_hdf('naver.hdf', key='df')
    fnguide_df = pd.read_hdf('fnguide.hdf', key='df')
    stock_df = pd.read_hdf('stock.hdf', key='df')

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
        if naver_df(stock_code)['자본총계(지배)']['2020(IFRS연결)'] != 0:
            equity = naver_df(stock_code)['자본총계(지배)']['2020(IFRS연결)']  # 컬럼 : 자본총계(지배), 인덱스 : 2020/12 연결 값 출력

        else:
            equity = naver_df(stock_code)['자본총계(지배)']['2020(IFRS별도)']  # 컬럼 : 자본총계(지배), 인덱스 : 2020/12 별도 값 출력

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
        roe_1st = roe(stock_code, '2020')
        roe_2nd = roe(stock_code, '2019')
        roe_3rd = roe(stock_code, '2018')

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
        revenue_2020 = naver_df(stock_code)['매출액']['2020(IFRS별도)']
        revenue_2019 = naver_df(stock_code)['매출액']['2019(IFRS별도)']

        if revenue_2020 < 50 or revenue_2019 < 50:
            result = 'risky'
        else:
            result = 'okay'

        return result

    def risk_profit(stock_code):
        profit_2020 = naver_df(stock_code)['영업이익']['2020(IFRS별도)']
        profit_2019 = naver_df(stock_code)['영업이익']['2019(IFRS별도)']
        profit_2018 = naver_df(stock_code)['영업이익']['2018(IFRS별도)']
        profit_2017 = naver_df(stock_code)['영업이익']['2017(IFRS별도)']

        if profit_2020 < 0 or profit_2019 < 0 or profit_2018 < 0 or profit_2017 < 0:
            result = 'risky'
        else:
            result = 'okay'

        return result

    def risk_ebitda(stock_code):
        if naver_df(stock_code)['세전계속사업이익']['2020(IFRS연결)'] != 0:
            ebitda_2020 = naver_df(stock_code)['세전계속사업이익']['2020(IFRS연결)']
            equity_2020 = naver_df(stock_code)['자본총계(지배)']['2020(IFRS연결)']
            ebitda_2019 = naver_df(stock_code)['세전계속사업이익']['2019(IFRS연결)']
            equity_2019 = naver_df(stock_code)['자본총계(지배)']['2019(IFRS연결)']
            ebitda_2018 = naver_df(stock_code)['세전계속사업이익']['2018(IFRS연결)']
            equity_2018 = naver_df(stock_code)['자본총계(지배)']['2018(IFRS연결)']
        else:
            ebitda_2020 = naver_df(stock_code)['세전계속사업이익']['2020(IFRS별도)']
            equity_2020 = naver_df(stock_code)['자본총계(지배)']['2020(IFRS별도)']
            ebitda_2019 = naver_df(stock_code)['세전계속사업이익']['2019(IFRS별도)']
            equity_2019 = naver_df(stock_code)['자본총계(지배)']['2019(IFRS별도)']
            ebitda_2018 = naver_df(stock_code)['세전계속사업이익']['2018(IFRS별도)']
            equity_2018 = naver_df(stock_code)['자본총계(지배)']['2018(IFRS별도)']

        if ebitda_2020 > equity_2020 / 2 or ebitda_2019 > equity_2019 / 2 or ebitda_2018 > equity_2018 / 2:
            result = 'risky'
        else:
            result = 'okay'

        return result

    def risk_capital(stock_code):
        if naver_df(stock_code)['자본총계']['2020(IFRS연결)'] != 0:
            total_equity_2020 = naver_df(stock_code)['자본총계']['2020(IFRS연결)']
            capital_2020 = naver_df(stock_code)['자본금']['2020(IFRS연결)']
            total_equity_2019 = naver_df(stock_code)['자본총계']['2019(IFRS연결)']
            capital_2019 = naver_df(stock_code)['자본금']['2019(IFRS연결)']
        else:
            total_equity_2020 = naver_df(stock_code)['자본총계']['2020(IFRS별도)']
            capital_2020 = naver_df(stock_code)['자본금']['2020(IFRS별도)']
            total_equity_2019 = naver_df(stock_code)['자본총계']['2019(IFRS별도)']
            capital_2019 = naver_df(stock_code)['자본금']['2019(IFRS별도)']

        if capital_2020 / total_equity_2020 >= 0.5 or capital_2019 / total_equity_2019 >= 0.5:
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


    for row in range(0, 50):  # len(stock_df)
        try:
            stock_code = stock_df.index[row]
            name = stock_name(stock_code)
            sector = stock_sector(stock_code)
            current_price = stock_price(stock_code)

            srim_price = srim(stock_code, 1)
            srim10_price = srim(stock_code, 0.9)
            srim20_price = srim(stock_code, 0.8)

            roe_average = float(round(roe_3(stock_code), 2))
            roe_2020 = float(round(roe(stock_code, '2020'), 2))
            roe_2019 = float(round(roe(stock_code, '2019'), 2))
            roe_2018 = float(round(roe(stock_code, '2018'), 2))
            bbb_rate = float(bbb())

            gap = float(round(gap_(stock_code), 2))
            risky = risk(stock_code)
            risky_revenue = risk_revenue(stock_code)
            risky_profit = risk_profit(stock_code)
            risky_ebitda = risk_ebitda(stock_code)
            risky_capital = risk_capital(stock_code)

            if Stock.objects.filter(code=stock_code).count() == 0:
                Stock(code=stock_code, name=name, sector=sector, current_price=current_price, srim_price=srim_price,
                      srim10_price=srim10_price, srim20_price=srim20_price, roe_average=roe_average,
                      roe_2020=roe_2020, roe_2019=roe_2019, roe_2018=roe_2018, bbb_rate=bbb_rate,
                      gap=gap, risky=risky, risky_revenue=risky_revenue, risky_profit=risky_profit,
                      risky_ebitda=risky_ebitda, risky_capital=risky_capital).save()
            else:
                queryset = Stock.objects.filter(code=stock_code)
                queryset.update(current_price=current_price, srim_price=srim_price, srim10_price=srim10_price,
                                srim20_price=srim20_price, bbb_rate=bbb_rate, gap=gap)

        except:
            pass




