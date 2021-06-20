import pandas as pd
from datetime import date, timedelta
import datetime
import requests
import re
from bs4 import BeautifulSoup
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

    stock_df.to_hdf('stock.hdf', key='df')


# 현재 가격, 네이버금융에서 크롤링하는 함수
def stock_price(stock_code):
    url = 'https://finance.naver.com/item/main.nhn?code={}'.format(stock_code)
    r = requests.get(url)
    bs = BeautifulSoup(r.text, "html.parser")
    result = bs.find("p", {"class": "no_today"}).find("span", {"class": "blind"}).text
    result = result.replace(',', '')
    result = int(result)

    return result
