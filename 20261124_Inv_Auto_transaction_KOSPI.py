#!/usr/bin/env python
# coding: utf-8

# In[1]:


'''
temp_hr_no_1 = int(20)
temp_hr_no_2 = temp_hr_no_1 + 2

temp_no_0_1 = int(38)
temp_no_0_2 = temp_no_0_1 + 2
temp_no_new_0_3 = temp_no_0_2 + 2
temp_no_0_3 = temp_no_new_0_3 + 2
temp_no_0_4 = temp_no_0_3 + 2
temp_no_0_5 = temp_no_0_4 + 2
temp_no_0_6 = temp_no_0_5 + 2
temp_no_0_7 = temp_no_0_6 + 2
temp_no_0_8 = temp_no_0_7 + 2
temp_no_0_9 = temp_no_0_8 + 2
#temp_no_0_10 = temp_no_0_9 + 2
temp_no_0_10 = temp_no_0_3 + 5
temp_no_0_11 = temp_no_0_10 + 5
temp_no_0_12 = temp_no_0_11 + 2
temp_no_0_13 = temp_no_0_12 + 2
temp_no_0_14 = temp_no_0_13 + 2
temp_no_0_15 = temp_no_0_14 + 2
temp_no_0_16 = temp_no_0_15 + 2
temp_no_0_17 = temp_no_0_16 + 1
'''






#로컬PC와 서버와의 시간차이 보상
#operating_env = "local"
operating_env = "server"

time_conpensation_factor = 0

if (operating_env == "local") :
    time_conpensation_factor = 0
elif (operating_env == "server") :
    time_conpensation_factor = 9


# In[2]:


import os
from pathlib import Path
from dotenv import load_dotenv

# 1. 현재 파이썬 파일(main.py 등)이 위치한 폴더의 절대 경로를 구합니다.
#current_folder = Path(__file__).resolve().parent   # 일반 .py 파일에서 구동시
#current_folder = Path(os.getcwd()).resolve()   # .ipynb(주피터 랩, 주피터 노트북 등) 파일에서 구동시

if "__file__" in locals() or "__file__" in globals():
    current_folder = Path(__file__).resolve().parent
else:
    current_folder = Path(os.getcwd()).resolve()



# 2. 현재 폴더 안에 있는 .env 파일의 정확한 경로를 지정합니다.
env_path = current_folder / ".env"

# 3. 지정한 경로의 .env 파일을 시스템 환경변수로 로드합니다.
load_dotenv(dotenv_path=env_path)


TOSS_CLIENT_ID = os.environ.get("TOSS_API_KEY")
TOSS_CLIENT_SECRET = os.environ.get("TOSS_APP_SECRET")


# In[3]:


import pandas as pd
import datetime  # 유효시간 계산을 위해 상단에 import 필요
from datetime import datetime as d_time
from datetime import timedelta
import requests
import time
import json
import traceback
import statistics

import uuid
from collections import defaultdict



# 판다스 출력 화면이 잘리지 않도록 설정 (콘솔 확인용)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)


# In[4]:


KOSPI_Top_50_code_dictionary = { "005930" : "삼성전자", "000660" : "하이닉스", "005380" : "현대차", "055550" : "신한지주", "373220" : "LG에너지솔루션", "207940" : "삼성바이오로직스",\
                                 "010140" : "삼성중공업", "015760" : "한국전력", "005490" : "포스코홀딩스", "068270" : "셀트리온", "105560" : "KB금융", "336260" : "두산퓨얼셀", \
                                 "012330" : "현대모비스", "456040" : "OCI", "007810" : "코리아써키트", "007660" : "이수페타시스", "034020" : "두산에너빌리티", "000990" : "DB하이텍", \
                                 "042700" : "한미반도체", "298040" : "효성중공업", "010120" : "LS ELECTRIC", "128940" : "한미약품", "066570" : "LG전자", "018260" : "삼성에스디에스", \
                                 "000500" : "가온전선", "042660" : "한화오션", "003160" : "디아이", "010060" : "OCI홀딩스", "278470" : "에이피알", "012450" : "한화에어로스페이스", \
                                 "011200" : "HMM", "103590" : "일진전기", "096770" : "SK이노베이션", "457190" : "이수스페셜티케미컬", "011070" : "LG이노텍", "329180":"HD현대중공업", \
                                 "003230" : "삼양식품", "483650" : "달바글로벌", "267260" : "HD현대일렉트릭", "003670" : "포스코퓨처엠", "066970" : "엘앤에프", \
                                 "036570" : "NC", "051910" : "LG화학", "352820" : "하이브", "000720" : "현대건설", "016360" : "삼성증권", "307950" : "현대오토에버", \
                                 "010130" : "고려아연", "267270" : "HD건설기계", "272210" : "한화시스템" }


DIC_candi_top_semi_company = {"005930" : "삼성전자", "000660" : "하이닉스"}


DIC_candi_general_company = {k: v for k, v in KOSPI_Top_50_code_dictionary.items() if k not in ["005930", "000660"]}

LIST_for_median_top_semi_comp = list(DIC_candi_top_semi_company.keys())
LIST_for_median_general_comp = list(DIC_candi_general_company.keys())

print ("LIST_for_median_general_comp : \n", LIST_for_median_general_comp)



# In[5]:


# 관련 함수 정의


# OAuth2 토큰 발급
def get_access_token(TOSS_CLIENT_ID_insert, TOSS_CLIENT_SECRET_insert):

    token_BASE_URL = "https://openapi.tossinvest.com"
    
    """OAuth2 토큰 발급"""
    url = f"{token_BASE_URL}/oauth2/token"
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_payload = {
        "grant_type": "client_credentials",
        "client_id": TOSS_CLIENT_ID_insert,
        "client_secret": TOSS_CLIENT_SECRET_insert,
    }
    response = requests.post(url, headers = token_headers, data = token_payload)
    
    token_request = response.json().get("access_token") or response.json().get("access_token")
    # access_token = response.json().get("access_token") or response.json().get("("accessToken")")

    expires_in = response.json().get("expires_in")


    issued_at = datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))  # 클라우드 서버와 한국과의 시간차이 보정 (9시간)
    expires_at = issued_at + datetime.timedelta(seconds=int(expires_in))
            
    print(f"토큰 유효 기간: {expires_in}초 (약 {int(expires_in)/3600:.1f}시간)")
    print(f"토큰 만료 일시: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

    
    return token_request

    

# 현재 보유중인 자산 확인 (현금, 종목, 수익율 등)
def asset_check (access_token_this_time) :

    # =====================================================================
    # 2. 계좌 잔고 조회 설정 정보
    # =====================================================================
    MY_ACCOUNT_NUMBER = "1"  # 본인의 토스증권 계좌번호 입력
    holdings_url = "https://openapi.tossinvest.com/api/v1/holdings"
    
    # =====================================================================
    # 3. HTTP Request Headers 및 Params 설정
    # =====================================================================
    headers = {
        "X-Tossinvest-Account": MY_ACCOUNT_NUMBER,  # 대소문자 정확히 일치
        "Authorization": f"Bearer {access_token_this_time}"
    }
    
    # 전체 보유 주식 및 예수금을 확인하려면 대개 params를 비우거나 
    # 가이드 문서의 다른 잔고 조회용 엔드포인트(예: /balances)가 있는지 확인이 필요할 수 있습니다.
    # 우선 가이드에 나온 기본 형태로 전체 조회를 시도합니다.
    params = {} 
    
    print("현재 계좌의 보유 자산 및 주식 상태를 조회합니다...")
    print(f"요청 URL: {holdings_url}\n")
    
    try:

        # -----------------------------------------------------------------
        # 1. 포맷팅 헬퍼 함수 정의 (문자열을 숫자 변환 후 천단위 콤마 및 % 적용)
        # -----------------------------------------------------------------
        def fmt_amt(val):
            """금액 포맷팅: 숫자로 변환 후 1,000 단위 콤마 추가"""
            if val is None or val == "": return "-"
            try:
                return f"{int(float(val)):,}"
            except ValueError:
                return val
    
        def fmt_rate(val):
            """수익률 포맷팅: 소수점 문자열을 % 단위로 변환 (예: -0.3744 -> -37.44%)"""
            if val is None or val == "": return "-"
            try:
                return f"{float(val) * 100:.2f}%"
            except ValueError:
                return val

        
        # GET 메서드를 사용하여 보유 현황 조회
        response = requests.get(holdings_url, headers=headers, params=params)

        # 4. 응답 결과 처리
        if response.status_code == 200:
            print("계좌 정보 조회가 완료되었습니다.")
            
            holdings_result = response.json()
            # 가독성 좋게 정렬된 JSON 데이터 출력
            print(json.dumps(holdings_result, indent=4, ensure_ascii=False))
            print("holdings_result : ", holdings_result)
            
            # [참고] 만약 특정 주식(예: 삼성전자)만 콕 집어서 확인하고 싶다면 아래와 같이 활용 가능합니다.
            # response_single = requests.get(holdings_url, headers=headers, params={"symbol": "005930"})

            result_data = holdings_result.get("result", {})

            print("result_data : ", result_data)
            
            # -----------------------------------------------------------------
            # 2. 계좌 요약 데이터프레임 생성
            # -----------------------------------------------------------------
            summary_data = {
                "항목": ["총 매수금액", "총 평가금액", "총 평가금액(제비용후)", "총 평가손익", "총 평가손익(제비용후)", "총 수익률", "총 수익률(제비용후)", "당일 평가손익", "당일 수익률"],
                "금액/비율": [
                    fmt_amt(result_data.get("totalPurchaseAmount", {}).get("krw")),
                    fmt_amt(result_data.get("marketValue", {}).get("amount", {}).get("krw")),
                    fmt_amt(result_data.get("marketValue", {}).get("amountAfterCost", {}).get("krw")),
                    fmt_amt(result_data.get("profitLoss", {}).get("amount", {}).get("krw")),
                    fmt_amt(result_data.get("profitLoss", {}).get("amountAfterCost", {}).get("krw")),
                    fmt_rate(result_data.get("profitLoss", {}).get("rate")),
                    fmt_rate(result_data.get("profitLoss", {}).get("rateAfterCost")),
                    fmt_amt(result_data.get("dailyProfitLoss", {}).get("amount", {}).get("krw")),
                    fmt_rate(result_data.get("dailyProfitLoss", {}).get("rate"))
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            
            print("[계좌 자산 요약]")
            print(df_summary.to_string(index=False))
            print("-" * 50)
        
            # -----------------------------------------------------------------
            # 3. 개별 보유 주식 데이터프레임 생성
            # -----------------------------------------------------------------
            items = result_data.get("items", [])
            if items:
                item_list = []
                for item in items:
                    item_list.append({
                        "종목명": item.get("name"),
                        "종목코드": item.get("symbol"),
                        "보유수량": fmt_amt(item.get("quantity")),
                        "매입단가": fmt_amt(item.get("averagePurchasePrice")),
                        "현재가": fmt_amt(item.get("lastPrice")),
                        "총매수금액": fmt_amt(item.get("marketValue", {}).get("purchaseAmount")),
                        "평가금액": fmt_amt(item.get("marketValue", {}).get("amount")),
                        "평가손익": fmt_amt(item.get("profitLoss", {}).get("amount")),
                        "수익률": fmt_rate(item.get("profitLoss", {}).get("rate")),
                        "당일손익": fmt_amt(item.get("dailyProfitLoss", {}).get("amount")),
                        "수수료": fmt_amt(item.get("cost", {}).get("commission")),
                        "제세금": fmt_amt(item.get("cost", {}).get("tax"))
                    })
                    
                df_items = pd.DataFrame(item_list)
                
                print("[보유 주식 상세 현황]")
                print(df_items.to_string(index=False))   

                
            else:
                print("현재 보유 중인 주식이 없습니다.")

                

            return holdings_result
    
            
        else:
            print(f"[조회 실패] 토스증권 API 서버에서 에러를 반환했습니다.")
            print(f"상태 코드 (Status Code): {response.status_code}")
            print(f"에러 내용: {response.text}")
    
    except Exception as e:
        print(f"[통신 에러] 요청 중 예기치 못한 오류가 발생했습니다: {e}")









def get_toss_cash_buyable(access_token_this_time):
    # 1. API 엔드포인트 URL 설정
    url = "https://openapi.tossinvest.com/api/v1/buying-power"

    # 2. 사용자 인증 정보 설정 (실제 본인의 값으로 변경하세요)
    # 보안을 위해 환경 변수나 설정 파일에서 가져오는 것을 권장합니다.
    TOSS_ACCOUNT_ID = "1"  # 가이드에 명시된 X-Tossinvest-Account 값
    SECRET_TOKEN = access_token_this_time  # 발급받은 API 비밀 토큰

    # 3. 요청 헤더 및 파라미터 구성
    headers = {
        "X-Tossinvest-Account": TOSS_ACCOUNT_ID,
        "Authorization": f"Bearer {SECRET_TOKEN}",
        "Accept": "application/json",  # JSON 응답을 명시적으로 요청
    }

    params = {
        "currency": "KRW",  # 대한민국 원화 기준 조회
    }

    try:
        # 4. API 서버에 GET 요청 보냄
        response = requests.get(url, headers=headers, params=params)

        # 5. HTTP 상태 코드 확인 (200이 아니면 예외 발생)
        response.raise_for_status()

        # 6. JSON 데이터 파싱 및 결과 출력
        data = response.json()
        
        # 'result' 안에서 'cashBuyingPower' 값을 가져옵니다.
        # 값이 없을 경우를 대비해 기본값 '0'을 설정합니다.
        buying_power_str = data.get('result', {}).get('cashBuyingPower', '0')
        
        # 문자로 된 금액을 숫자(정수)로 변환합니다 (예: '99999' -> 99999)
        buying_power_int = int(buying_power_str)
        
        print("\n[토스증권 API] 거래가능 금액 조회 성공")
        # : , 를 넣으면 3자리마다 쉼표가 찍힙니다 (예: 99,999원)
        #print(f"거래가능 금액: {buying_power_int:,} 원") 
        
        return buying_power_int
        

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 에러가 발생했습니다: {http_err}")
        print(f"서버 응답 내용: {response.text}")
    except requests.exceptions.RequestException as err:
        print(f"요청 중 에러가 발생했습니다: {err}")
    except ValueError:
        print("응답 데이터를 JSON으로 파싱하는 데 실패했습니다.")






def fetch_batch_prices(access_token, ticker_list, chunk_size = 25):
    """
    여러 종목 코드를 콤마로 묶어 일괄(Batch) 조회
    응답 필드: symbol, timestamp, lastPrice, currency
    """
    url = f"https://openapi.tossinvest.com/api/v1/prices"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    all_results = []

    for i in range(0, len(ticker_list), chunk_size):
        chunk = ticker_list[i : i + chunk_size]
        params = {"symbols": ",".join(chunk)}

        try:
            response = requests.get(url, headers=headers, params=params, timeout = 10)
            if response.status_code != 200:
                print(
                    f"조회 실패 (구간 {i} ~ {i + len(chunk)}): "
                    f"코드 {response.status_code} - {response.text}"
                )
                continue

            data = response.json()
            items = data.get("result", data) if isinstance(data, dict) else data
            if not isinstance(items, list):
                items = [items]

            for item in items:
                if not isinstance(item, dict):
                    continue

                ticker = str(item.get("symbol") or "")
                raw_price = item.get("lastPrice")

                # lastPrice 문자열을 숫자로 변환 (실패 시 None)
                try:
                    price_val = int(raw_price) if raw_price is not None else None
                except (ValueError, TypeError):
                    try:
                        price_val = float(raw_price)
                    except (ValueError, TypeError):
                        price_val = None

                all_results.append(
                    {
                        "ticker": ticker,
                        #"name": TICKER_NAMES.get(ticker, ""),
                        "last_price": price_val,
                        "currency": item.get("currency", "KRW"),
                        "timestamp": item.get("timestamp"),
                    }
                )

        except Exception as e:
            print(f"요청 중 에러 발생: {e}")

        time.sleep(0.05)

    return pd.DataFrame(all_results)







def get_1m_1d_candles(access_token_this_time, candle_type, symbol, No_candle, No_size):

    candle_BASE_URL = "https://openapi.tossinvest.com"
    
    url = f"{candle_BASE_URL}/api/v1/candles"
    headers = {"Authorization": f"Bearer {access_token_this_time}"}

    # 현재 시간 기준 ISO 8601 형식 설정
    current_before = (d_time.now() + timedelta(hours = time_conpensation_factor)).strftime("%Y-%m-%dT%H:%M:%S+09:00")

    all_candles = []
    total_needed = No_candle  # 5일치 1분봉 데이터 분량 (하루 약 390분 * 5일)
    chunk_size = No_size  # 토스증권 API 1회 최대 호출 제한량

    print(f"토스증권으로부터 1분봉 데이터 수집 시작 (목표: {total_needed}개)...")

    while len(all_candles) < total_needed:
        params = {
            "symbol": symbol,
            "interval": candle_type,  # 1분봉 요청
            "count": str(chunk_size),
            "before": current_before,
            "adjusted": "true",
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"데이터 수집 중 에러 발생: {response.status_code}")
            break

        raw_data = response.json()
        result_node = raw_data.get("result", {})
        candles_chunk = result_node.get("candles", [])

        if not candles_chunk:
            print("종료: 더 이상 가져올 과거 데이터가 없습니다.")
            break

        all_candles.extend(candles_chunk)
        print(f"  -> 현재 {len(all_candles)}개 수집 완료...")

        # 다음 과거 데이터를 위해 before 시간 갱신
        last_candle_time = candles_chunk[-1].get("timestamp")
        if last_candle_time:
            current_before = last_candle_time
        else:
            break

        time.sleep(0.2)  # 연속 호출 제한 방지

    if not all_candles:
        print("수집된 데이터가 없습니다.")
        return None

    # 1. Pandas DataFrame 변환
    df = pd.DataFrame(all_candles)

    # 시간 컬럼 처리 및 인덱스 지정
    df["standard_time"] = pd.to_datetime(df["timestamp"])
    df.set_index("standard_time", inplace=True)

    # 중복 제거 및 과거 -> 현재 순 정렬
    df = df[~df.index.duplicated(keep="first")]
    df = df.sort_index()

    # 데이터 타입 숫자형으로 변환
    target_columns = ["openPrice", "highPrice", "lowPrice", "closePrice", "volume"]
    for col in target_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 필요한 컬럼만 추출하고 한글 이름으로 변경
    df_clean = df[target_columns].copy()
    df_clean.columns = ["시가", "고가", "저가", "종가", "거래량"]

    return df_clean


# In[6]:


# 판매할 수 있는 물량 확인
def get_sellable_quantity(api_token, item_code) :
    """토스증권 API를 통해 보유 중인 종목의 판매 가능 수량을 조회합니다.

    :param api_token: 토스증권 API Secret Token (Bearer 토큰)
    :param account_id: 계좌 번호/식별자 (기본값: "1")
    :return: 판매 가능 수량 (정수)
    """
    url = "https://openapi.tossinvest.com/api/v1/sellable-quantity"

    headers = {
        "X-Tossinvest-Account": "1",
        "Authorization": f"Bearer {api_token}",
    }

    # 삼성전자 종목코드: 005930
    params = {"symbol": str(item_code)}

    try:
        response = requests.get(url, headers=headers, params=params)
        # HTTP 에러 발생 시 예외 호출 (4xx, 5xx)
        response.raise_for_status()

        data = response.json()

        # JSON 응답에서 sellableQuantity 추출 및 정수형(int) 변환
        sellable_qty_str = data.get("result", {}).get("sellableQuantity", "0")
        return int(sellable_qty_str)

    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 네트워크/HTTP 에러 발생: {e}")
        raise
    except (KeyError, ValueError) as e:
        print(f"응답 데이터 파싱 실패: {e}")
        raise






# 매수 함수 정의

def run_toss_stock_buyer_seller(access_token_this_time, transaction_company, transaction_side, price_type, transaction_quantity, transaction_price, company_dict = None):
    """
    토스증권 API를 이용한 지정가/시장가 매수/매도 주문 통합 함수
    """
    MY_ACCOUNT_SEQ = "1"
    order_url = "https://openapi.tossinvest.com/api/v1/orders"

    # HTTP 헤더 설정
    order_headers = {
        "X-Tossinvest-Account": MY_ACCOUNT_SEQ,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token_this_time}"
    }

    # clientOrderId 중복(422 idempotency-key-conflict) 방지를 위해 UUID4 사용
    #unique_client_order_id = f"order-{uuid.uuid4().hex}"
    unique_client_order_id = f"order-{uuid.uuid4().hex[:16]}"

    # 주문 페이로드 구성
    order_payload = {
        "clientOrderId": unique_client_order_id,
        "symbol": str(transaction_company),
        "side": transaction_side.upper(),      # 'BUY' 또는 'SELL'
        "orderType": price_type,               # 'LIMIT' 또는 'MARKET'
        "quantity": str(transaction_quantity),
        "price": str(transaction_price),
    }

    # 종목명 출력용 (사전에 전달받지 못한 경우 종목코드 그대로 표시)
    company_name = company_dict.get(transaction_company, transaction_company) if company_dict else transaction_company
    side_name = "매수" if transaction_side.upper() == "BUY" else "매도"

    print(f"\n[{side_name} 주문 요청 중] {company_name}_{transaction_quantity}주_{transaction_price}원 (clientOrderId: {unique_client_order_id})")

    try:
        # API 요청 전송
        order_response = requests.post(order_url, headers=order_headers, json=order_payload, timeout=10)
        
        # JSON 응답 파싱 (파싱 에러 방지)
        try:
            response_json = order_response.json()
        except ValueError:
            response_json = {}

        print(f"[{side_name} 주문 접수 상태 확인]")

        # 성공 처리 (200 OK 또는 201 Created)
        if order_response.ok:  # status_code가 200~299 사이일 때 True
            print(f"{side_name} 주문 접수 성공!")
            
            # 응답 데이터 구조에 안전하게 접근
            toss_order_id = response_json.get("result", {}).get("orderId") or response_json.get("orderId", "UNKNOWN")
            print(f"order_result_data : {response_json}")
            print(f"toss_order_id : {toss_order_id}\n")
            
            return 1, toss_order_id

        # 실패 처리 (4xx, 5xx 에러)
        else:
            print(f"{side_name} 주문 실패 (상태 코드: {order_response.status_code})")
            print(f"응답 본문: {order_response.text}")
            
            # 에러 발생 시에도 혹시 모를 orderId 또는 error 정보 추출
            toss_order_id = response_json.get("result", {}).get("orderId", None)
            return 0, toss_order_id

    except requests.exceptions.RequestException as e:
        # 네트워크 에러, 타임아웃 등 요청 자체가 실패한 경우
        print(f"[{side_name} 주문 중 통신 예외 발생]: {e}")
        return 0, None










def get_orderbook(access_token_this_time, symbol_this_time):
    """
    특정 종목의 매수/매도 호가 및 잔량을 조회하는 함수
    
    :param symbol: 종목 심볼 (예: '005930', 'AAPL')
    :param access_token: 인증용 Bearer 토큰 (YOUR_SECRET_TOKEN)
    :return: 매도호가(asks) 목록과 매수호가(bids) 목록을 담은 딕셔너리
    """
    url = "https://openapi.tossinvest.com/api/v1/orderbook"
    
    headers = {
        "Authorization": f"Bearer {access_token_this_time}"
    }
    
    params = {
        "symbol": symbol_this_time
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        # 요청 실패 시 예외 발생 (4xx, 5xx 에러)
        response.raise_for_status()
        
        data = response.json()
        result = data.get("result", {})
        
        # 매도 호가(asks)와 매수 호가(bids) 추출
        asks = result.get("asks", [])  # 매도 호가 (팔고자 하는 가격)
        bids = result.get("bids", [])  # 매수 호가 (사고자 하는 가격)
        
        return {
            "timestamp": result.get("timestamp"),
            "currency": result.get("currency"),
            "asks": asks,
            "bids": bids
        }

    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류가 발생했습니다: {e}")
        return None









def transaction_result_check (token_this_time, order_id) :

    MY_ACCOUNT_SEQ = "1"
    
    # ==========================================
    # [단계] 토스 서버가 준 ID로 체결 상태 조회
    # ==========================================
    check_url = f"https://openapi.tossinvest.com/api/v1/orders/{order_id}"

    order_headers = {
        "X-Tossinvest-Account": MY_ACCOUNT_SEQ,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_this_time}"
        }

    print(f"\n토스 주문 ID로 체결 상태를 확인합니다...")

    # 조회 API는 GET 방식을 사용하며, 주문할 때와 헤더가 동일합니다.
    check_response = requests.get(check_url, headers = order_headers)

    if check_response.status_code == 200:
        order_status_data = check_response.json()
        print("[조회 성공] 최종 주문 상태 결과:")
        print(json.dumps(order_status_data, indent=4, ensure_ascii=False))
        
        # 조회 데이터 역시 'result' 키 내부에 포장되어 오므로 안전하게 방어 코드를 작성합니다.
        status_info = order_status_data.get("result") if "result" in order_status_data else order_status_data
        
        status = status_info.get("status")
        
        # [버그 수정]: 'execution' 딕셔너리가 존재하면 그 안에서 진짜 체결 수량(filledQuantity)을 꺼내옵니다.
        execution_info = status_info.get("execution", {})
        if execution_info:
            filled_qty = execution_info.get("filledQuantity", "0")
        else:
            # 아직 체결 정보가 생기기 전(대기 상태 등)일 경우의 방어 코드
            filled_qty = status_info.get("filledQuantity", "0")

        
        print(f"\n현재 주문 상태: {status}")
        print(f"체결된 수량: {filled_qty}주")

        status_return = 0
        
        if status == "FILLED":
            print("주문의 체결이 완료되었습니다! 계좌를 확인해보세요.")
            status_return = 1
            return status_return
            
        elif status == "REJECTED":
            print("주문이 거부되었습니다. (이유: 예수금 부족, 주문 가능 시간 아님 등)")
            status_return = 5
            return status_return
            
        else:
            print("아직 주문이 체결되지 않고 호가창에 접수되어 대기 중입니다.")
            status_return = 0
            return status_return
            
    else:
        print(f"주문 상태 조회 실패 (상태 코드: {check_response.status_code})")
        print(check_response.text)


# In[7]:


# 체결이 되지 않은 상태의 주문에 대해 취소하는 처리

def cancel_toss_stock_order(access_token_this_time, order_id):
    """토스증권 API를 이용한 기존 주문 취소 함수

    :param access_token_this_time: 현재 유효한 OAuth Access Token (문자열)
    :param order_id: 취소할 주문의 식별자 (서버에서 발급받은 opaque token 문자열)
    """
    MY_ACCOUNT_SEQ = (
        "1"  # 계좌 조회 결과에 따른 순번(Sequence) 값 "1"을 지정합니다.
    )

    # URL 경로에 입력받은 order_id를 동적으로 삽입합니다.
    cancel_url = f"https://openapi.tossinvest.com/api/v1/orders/{order_id}/cancel"

    # HTTP 헤더 설정 (매수 함수와 동일한 규격)
    cancel_headers = {
        "X-Tossinvest-Account": MY_ACCOUNT_SEQ,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token_this_time}",
    }

    print(f"\n[취소 요청] 주문 ID ({order_id}) 취소 진행 중...")

    # 공식 가이드에 따라 POST 요청을 보내며, 빈 json 객체({})를 전달합니다.
    try:
        response = requests.post(
            cancel_url, headers=cancel_headers, json={}
        )

        # 200(성공) 또는 201(생성됨) 상태 코드가 아니면 실패 처리
        if response.status_code not in [200, 201]:
            print(
                f"주문 취소 요청 실패 (상태 코드: {response.status_code})"
            )
            print(f"상세 에러 내용: {response.text}")
            return False

        # 성공 시 응답 데이터 파싱
        cancel_result = response.json()
        print("주문 취소 접수 성공!")
        return cancel_result

    except Exception as e:
        print(f"네트워크 또는 기타 에러 발생: {e}")
        return False










def get_stock_quantity(data, target_symbol) :
    # 2. 데이터 구조에 맞춰 'items' 리스트를 가져옵니다.
    items = data.get("result", {}).get("items", [])

    # 3. items 안의 주식들을 하나씩 꺼내며 검사합니다.
    for item in items:
        # 4. 찾고자 하는 종목번호(symbol)와 일치하는지 확인합니다.
        if item.get("symbol") == target_symbol:
            # 토스증권은 수량(quantity)을 문자열('100')로 주기 때문에 숫자로 변환합니다.
            quantity = int(item.get("quantity", 0))
            name = item.get("name")
            print(f"종목 검색 성공! [{name} / {target_symbol}]")
            print(f"현재 보유 수량: {quantity} 주")
            return quantity

    # 만약 리스트를 다 돌았는데도 찾지 못했다면 보유하지 않은 주식입니다.
    print(f"해당 종목번호({target_symbol})는 보유 중이 아닙니다.")
    return 0


# In[8]:


# 매수가격 호가 단위 반영 조정 함수 정의

def buyable_price_volume_with_unit (buy_intermediate_price, budget_for_buy_a_item) :
    
    buy_unit = 0
    
    if buy_intermediate_price < 2000 :
        buy_unit = 1
    elif (2000 <= buy_intermediate_price < 5000) :
        buy_unit = 5
    elif (5000 <= buy_intermediate_price < 20000) :
        buy_unit = 10
    elif (20000 <= buy_intermediate_price < 50000) :
        buy_unit = 50
    elif (50000 <= buy_intermediate_price < 200000) :
        buy_unit = 100
    elif (200000 <= buy_intermediate_price < 500000) :
        buy_unit = 500
    elif (500000 <= buy_intermediate_price) :
        buy_unit = 1000

    compensation_share = buy_intermediate_price // buy_unit
    buy_price = int(buy_unit * compensation_share)
    buy_volume = int(budget_for_buy_a_item // buy_price)

    return buy_price, buy_volume


'''

# 복수 종목 현재가격 한번에 추출 테스트
print("1. 토스증권 API 인증 토큰 발급 중...")
test_token = get_access_token(TOSS_CLIENT_ID, TOSS_CLIENT_SECRET)

print(f"2. 총 {len(LIST_for_median_general_comp)}개 general company 종목 현재가 일괄 조회 시작...")
start_time = time.time()

DF_multi_items_last_price = fetch_batch_prices(test_token, LIST_for_median_general_comp, chunk_size = 25)

end_time = time.time()
print(f"3. 데이터 수집 완료 (소요 시간: {end_time - start_time:.2f}초)")

print("복수 종목 현재 가격 \n", DF_multi_items_last_price['last_price'])
print("\n\n복수 종목 현재 가격 median : ", DF_multi_items_last_price['last_price'].median())



print(f"Fetch {len(LIST_for_median_general_comp)} general companies current price at a time...")
DF_multi_items_last_price = fetch_batch_prices(test_token, LIST_for_median_general_comp, chunk_size = 25)
print("\ncurrent price : ", DF_multi_items_last_price['last_price'].median())
'''

# 거래 로직



print ("Program Begins\n")


transaction_money_criteria = 50000000
#ratio_buy_block_S_H_median = 0.97
ratio_buy_general_median_diff_cri_1 = -0.012
ratio_buy_general_median_diff_cri_2 = -0.005
ratio_buy_0800_start_lower = 0.02

ratio_buy_block_S_H_and_general_median = -0.05
ratio_buy_block_by_yesterday_variance = 0.2

sell_duration_1 = 5
sell_duration_2 = 3
sell_duration_3 = 8
sell_duration_4 = 15
ratio_sell_after_duration_1 = 0.014
ratio_sell_after_duration_2 = 0.007
ratio_sell_after_duration_3 = 0




cycle_period = 30

token_get = "temp"

value_fall_criteria = -50.0
value_fall_criteria_this_time = -50.0




total_cash_buyable_today = 0
money_for_a_item_divider_for_top_semi_comp = 2
money_for_a_item_divider_for_general_comp = 100

ratio_lowest_buyable_price_and_yesterday_end_price = 99.0
difference_lowest_buyable_price_and_general_comp_median = 0.0

money_for_buy_a_top_semi_comp = 0
total_cash_buyable_residual = 0
total_cash_buyable_residual_s = 0

median_ratio_general_comp_this_time_yesterday = 0.0
aver_price = 0.0

DIC_candi_general_company_buy_blocked_check = {}
 
DIC_candi_top_semi_company_yesterday_end_price = {}
DIC_candi_general_company_yesterday_end_price = {}

DIC_candi_top_semi_company_0800_start_price = {}
DIC_candi_general_company_0800_start_price = {}

DIC_candi_top_semi_company_this_time_start_price = {}
DIC_candi_general_company_this_time_start_price = {}

DIC_candi_top_semi_company_0801_start_price = {}
DIC_candi_general_company_0801_start_price = {}

DIC_candi_top_semi_company_0802_start_price = {}
DIC_candi_general_company_0802_start_price = {}

DIC_candi_company_ratio_top_semi_comp_0800_to_yesterday = {}
DIC_candi_company_ratio_general_comp_0800_to_yesterday = {}

DIC_candi_company_ratio_top_semi_comp_this_time_to_yesterday = {}
DIC_candi_company_ratio_general_comp_this_time_to_yesterday = {}

DIC_candi_company_ratio_top_semi_comp_0802_to_yesterday = {}
DIC_candi_company_ratio_general_comp_0802_to_yesterday = {}

DIC_candi_company_ratio_top_semi_comp_0801_to_0800 = {}
DIC_candi_company_ratio_general_comp_0801_to_0800 = {}

DIC_candi_company_ratio_top_semi_comp_0802_to_0801 = {}
DIC_candi_company_ratio_general_comp_0802_to_0801 = {}

median_ratio_top_semi_comp_0800_yesterday = 0
median_ratio_general_comp_0800_yesterday = 0

DIC_transaction_top_semi_comp_buy_target_quantity = {}
DIC_transaction_general_comp_buy_target_quantity = {}

DIC_candi_top_semi_company_transaction_money_0800_0801 = {}
DIC_candi_general_company_transaction_money_0800_0801 = {}

DIC_candi_top_semi_company_transaction_money_0800_0802 = {}
DIC_candi_general_company_transaction_money_0800_0802 = {}

DIC_transaction_top_semi_comp_buy_target_with_orderID = {}
DIC_transaction_general_comp_buy_target_with_orderID = {}

DIC_transaction_top_semi_comp_buy_time_minute = {}
DIC_transaction_general_comp_buy_time_minute = {}

DIC_transaction_top_semi_comp_SELL_target_with_orderID = {}
DIC_transaction_general_comp_SELL_target_with_orderID = {}

DIC_top_semi_comp_bought_average_price = {}
DIC_general_comp_bought_average_price = {}

DIC_top_semi_comp_bought_quantity = {}
DIC_general_comp_bought_quantity = {}

total_bought_quantity = 0

market_condition = 99

#buy_state = 0

#bought_quantity_of_0 = 0
#bought_quantity_of_1 = 0

intermediate_price = 0

order_response = 0



'''
DIC_transaction_buy_target_with_company_name = {}
DIC_transaction_buy_target_with_price = {}
DIC_transaction_buy_target_with_quantity = {}


DIC_transaction_sell_target_with_volume = {}
DIC_transaction_sell_target_with_orderID = {}

DIC_candi_company_ratio_today_0801_to_0800 = {}
DIC_candi_company_buyable_price = {}
'''



while True:
    
    try:

        now = datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))  # 클라우드 서버와 한국과의 시간차이 보정 (9시간)

        print ("now : ", now)

        # 7시에 토근 발행, 8시부터 거래 시작
        
        if ((7 <= now.hour < 8) and (40 <= now.minute < 41) and (0 <= now.second < (cycle_period + 29))) :   # (original values) ((7 <= now.hour < 8) and (40 <= now.minute < 41) and (0 <= now.second < (cycle_period + 29))) :       (for test) ((temp_hr_no_1 <= now.hour < temp_hr_no_2) and (temp_no_0_1 <= now.minute < temp_no_0_2) and (0 <= now.second < (cycle_period + 29))) :
            print ("[ Get transaction TOKEN ]\n")
            token_get = get_access_token(TOSS_CLIENT_ID, TOSS_CLIENT_SECRET)
            time.sleep(1)


            # ==========================================
            # [단계] 발급받은 진짜 토큰으로 계좌 조회하기
            # ==========================================

            print ("[ Current_ACCOUNT check ]")
            account_url = "https://openapi.tossinvest.com/api/v1/accounts"
            account_headers = {
                "Authorization": f"Bearer {token_get}"
                }

            account_response = requests.get(account_url, headers = account_headers)
            print(json.dumps(account_response.json(), indent=4, ensure_ascii=False))

            print ("\n[ Current Asset check ]\n")
            get_asset_check = asset_check(token_get)
            print ("\nget_asset_check :\n", get_asset_check)
            #print ("Currnt time : ", now)

            total_cash_buyable_today = get_toss_cash_buyable (token_get)
            #money_for_buy_a_item = total_cash_buyable_today // money_for_a_item_divider
            print("total_cash_buyable : {0:,} won".format (total_cash_buyable_today))

            cycle_in_transation_mode = 0.5
            hour_check = (datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))).hour
            

            while ((datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))).hour <= (hour_check + 1)) :
                
                now_in_mode = datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))  # 클라우드 서버와 한국과의 시간차이 보정 (9시간)
                print ("[ Begin transaction mode at ] ", now_in_mode)



                if ((7 <= now_in_mode.hour < 8) and (50 <= now_in_mode.minute < 51) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 1))) :   # (original)  ((7 <= now_in_mode.hour < 8) and (50 <= now_in_mode.minute < 51) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 1))) :     (for test) ((temp_hr_no_1 <= now_in_mode.hour < temp_hr_no_2) and (temp_no_0_2 <= now_in_mode.minute < temp_no_new_0_3) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 1))) :
                    print ("\n[ Check general item variance level of previous day at ] ", datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600)))

                    LIST_buy_block = []
                    for i_check_yesterday_general in DIC_candi_general_company.keys() :
                        print ("\n[ Get_1d_stat_general_company ] {0} : {1}".format(i_check_yesterday_general, DIC_candi_general_company[i_check_yesterday_general]))
                        DF_1d_stat_yesterday_general = get_1m_1d_candles(token_get, "1d", i_check_yesterday_general, 1, 1)
                        print (DF_1d_stat_yesterday_general)
                        variance_yesterday_lowest_maximum = abs((DF_1d_stat_yesterday_general['고가'].iloc[-1] - DF_1d_stat_yesterday_general['저가'].iloc[-1]) / DF_1d_stat_yesterday_general['저가'].iloc[-1])
                        if (variance_yesterday_lowest_maximum >= ratio_buy_block_by_yesterday_variance) :
                            DIC_candi_general_company_buy_blocked_check[i_check_yesterday_general] = int(1)
                            LIST_buy_block.append(i_check_yesterday_general)
                            print ("This company is blocked for today's buy transaction")
                        else :
                            DIC_candi_general_company_buy_blocked_check[i_check_yesterday_general] = int(0)
                            print ("This company is included for today's buy transaction")
                        time.sleep(0.5)

                    print("\ntoday's buy transaction blocked list")
                    for i_blocked in range (0, len(LIST_buy_block), 1) :
                        print ("{0} _ {1}".format(LIST_buy_block[i_blocked], DIC_candi_general_company[LIST_buy_block[i_blocked]]))

                    print("\ntoday's buy transaction cadidate list\n", DIC_candi_general_company_buy_blocked_check)



                               
                if ((7 <= now_in_mode.hour < 8) and (55 <= now_in_mode.minute < 56) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 1))) :   # (original)  ((7 <= now_in_mode.hour < 8) and (55 <= now_in_mode.minute < 56) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 1))) :     (for test) ((temp_hr_no_1 <= now_in_mode.hour < temp_hr_no_2) and (temp_no_new_0_3 <= now_in_mode.minute < temp_no_0_3) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 1))) :
                    print ("\n[ Get information YESTERDAY ending price at ] ", datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600)))

                    for i_stat_yesterday_ts in DIC_candi_top_semi_company.keys() :
                        print ("\n[ Get_1m_stat_Top_semi_company ] {0} : {1}".format(i_stat_yesterday_ts, DIC_candi_top_semi_company[i_stat_yesterday_ts]))
                        DF_1m_stat_yesterday_top_semi = get_1m_1d_candles(token_get, "1m", i_stat_yesterday_ts, 350, 200)
                        DF_1m_stat_yesterday_top_semi.index = DF_1m_stat_yesterday_top_semi.index.tz_localize(None)   # 타임존(+9:00) 제거
                        print (DF_1m_stat_yesterday_top_semi)
                        #DF_1m_stat_yesterday.to_excel("stat_1m_{0}.xlsx".format(DIC_candi_company[list(DIC_candi_company.keys())[i_stat_yesterday]]))
                        yesterday_end_value = DF_1m_stat_yesterday_top_semi.loc[DF_1m_stat_yesterday_top_semi.index.astype(str).str.contains("15:31:00"), "종가"].iloc[0]
                        print ("  Yesterday_end_price : {0} ".format(yesterday_end_value))
                        DIC_candi_top_semi_company_yesterday_end_price[i_stat_yesterday_ts] = int(yesterday_end_value)
                        time.sleep(0.5)

                    print ("\nDIC_candi_top_semi_company_yesterday_end_price :\n", DIC_candi_top_semi_company_yesterday_end_price)

                    

                    for i_stat_yesterday_general in DIC_candi_general_company.keys() :
                        print ("\n[ Get_1m_stat_general_company ] {0} : {1}".format(i_stat_yesterday_general, DIC_candi_general_company[i_stat_yesterday_general]))
                        DF_1m_stat_yesterday_general = get_1m_1d_candles(token_get, "1m", i_stat_yesterday_general, 350, 200)
                        DF_1m_stat_yesterday_general.index = DF_1m_stat_yesterday_general.index.tz_localize(None)   # 타임존(+9:00) 제거
                        print (DF_1m_stat_yesterday_general)
                        #DF_1m_stat_yesterday.to_excel("stat_1m_{0}.xlsx".format(DIC_candi_company[list(DIC_candi_company.keys())[i_stat_yesterday]]))
                        yesterday_end_value_general = DF_1m_stat_yesterday_general.loc[DF_1m_stat_yesterday_general.index.astype(str).str.contains("15:31:00"), "종가"].iloc[0]
                        print ("  Yesterday_end_price : {0} ".format(yesterday_end_value_general))
                        DIC_candi_general_company_yesterday_end_price[i_stat_yesterday_general] = int(yesterday_end_value_general)
                        time.sleep(0.5)

                    print ("\nDIC_candi_general_company_yesterday_end_price :\n", DIC_candi_general_company_yesterday_end_price)
                    print ("[ FINISH Getting information of YESTERDAY ending price at ]", datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600)))

                    
                    print ("\n\n\ntotal budget for buy transaction : {0:,}".format(total_cash_buyable_today))
                    budget_for_each_company = total_cash_buyable_today / money_for_a_item_divider_for_general_comp
                    print ("budget_for_each_company ", budget_for_each_company)
                    
                    for i_buy_target_quantity in DIC_candi_general_company.keys() :
                        buyable_quantity_of_this_company = int(budget_for_each_company // DIC_candi_general_company_yesterday_end_price[i_buy_target_quantity])
                        print ("\n [Get Buy target quantity of company {0}_{1} ___ {2:,}".format(i_buy_target_quantity, DIC_candi_general_company[i_buy_target_quantity], buyable_quantity_of_this_company))
                        DIC_transaction_general_comp_buy_target_quantity[i_buy_target_quantity] = int(buyable_quantity_of_this_company)
                        time.sleep(0.5)

                    print ("\nDIC_transaction_general_comp_buy_target_quantity\n", DIC_transaction_general_comp_buy_target_quantity)                       
 

                elif (8 <= now_in_mode.hour < 9) and (0 <= now_in_mode.minute < 10) :   # (original) (8 <= now_in_mode.hour < 9) and (0 <= now_in_mode.minute < 10) :     (for test) (temp_hr_no_1 <= now_in_mode.hour < temp_hr_no_2) and (temp_no_0_3 <= now_in_mode.minute < temp_no_0_10) :
                    today_now = datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))
                    today = str(today_now.strftime("%Y-%m-%d"))
                    #today = "2026-07-24"
                    #print ("today is : ", today)
                    print ("Now is : ", today_now)

                    if (today_now.minute == 0) :    # (original) (today_now.minute == 0) :    # (for test) (today_now.minute == temp_no_0_3) :
                        if (0.3 < today_now.second) :
                            print(f"Fetch {len(LIST_for_median_top_semi_comp)} Top semi companies current price at a time...")
                            DF_top_semi_multi_items_last_price = fetch_batch_prices(token_get, LIST_for_median_top_semi_comp, chunk_size = 25)
                            #median_general_comp = DF_multi_items_last_price['last_price'].median()
                            print ("current price list \n :", DF_top_semi_multi_items_last_price['last_price'])

                            print(f"Fetch {len(LIST_for_median_general_comp)} general companies current price at a time...")
                            DF_multi_items_last_price = fetch_batch_prices(token_get, LIST_for_median_general_comp, chunk_size = 25)
                            #median_general_comp = DF_multi_items_last_price['last_price'].median()
                            print ("current price list \n :", DF_multi_items_last_price['last_price'])

                            i_median_top_semi = 0
                            print ("\n[ Get information Top_semi_company TODAY an starting price ]")
                            for i_stat_today_start in DIC_candi_top_semi_company.keys() :
                                print ("\n[ Get_1d_stat_Top_semi ] {0} : {1}".format(i_stat_today_start, DIC_candi_top_semi_company[i_stat_today_start]))
                                today_start_value_top_semi = int(DF_top_semi_multi_items_last_price['last_price'][i_median_top_semi])
                                i_median_top_semi = i_median_top_semi + 1
                                print ("  Today_start_value : {0:,}".format(today_start_value_top_semi))
                                DIC_candi_top_semi_company_0800_start_price[i_stat_today_start] = today_start_value_top_semi

                                ratio_today_yesterday = today_start_value_top_semi / DIC_candi_top_semi_company_yesterday_end_price[i_stat_today_start]
                                print ("  ratio TODAY_start_price to YESTERDAY_end_price : ", ratio_today_yesterday)
                                DIC_candi_company_ratio_top_semi_comp_0800_to_yesterday[i_stat_today_start] = ratio_today_yesterday

                            print ("\nratio TOP_Semi_company_TODAY_start_price to YESTERDAY_end_price\n", DIC_candi_company_ratio_top_semi_comp_0800_to_yesterday)

                            median_ratio_top_semi_comp_0800_yesterday = statistics.median(list(DIC_candi_company_ratio_top_semi_comp_0800_to_yesterday.values()))
                            print ("  [median_ratio]_of_TOP_semi_candidate_companies : ", median_ratio_top_semi_comp_0800_yesterday)



                            i_median_general = 0
                            print ("\n[ Get information GENERAL_company TODAY an starting price ]")
                            for i_stat_today_start_general in DIC_candi_general_company.keys() :
                                print ("\n[ Get_stat info_General_company ] {0} : {1}".format(i_stat_today_start_general, DIC_candi_general_company[i_stat_today_start_general]))
                                today_start_value_general = int(DF_multi_items_last_price['last_price'][i_median_general])
                                i_median_general = i_median_general + 1
                                print ("  Today_start_value : {0:,}".format(today_start_value_general))
                                DIC_candi_general_company_0800_start_price[i_stat_today_start_general] = today_start_value_general

                                ratio_today_yesterday_general = today_start_value_general / DIC_candi_general_company_yesterday_end_price[i_stat_today_start_general]
                                print ("  ratio TODAY_start_price to YESTERDAY_end_price : ", ratio_today_yesterday_general)
                                DIC_candi_company_ratio_general_comp_0800_to_yesterday[i_stat_today_start_general] = ratio_today_yesterday_general

                            print ("\nratio GENERAL_company_TODAY_start_price to YESTERDAY_end_price\n", DIC_candi_company_ratio_general_comp_0800_to_yesterday)

                            median_ratio_general_comp_0800_yesterday = statistics.median(list(DIC_candi_company_ratio_general_comp_0800_to_yesterday.values()))
                            print ("  [median_ratio]_of_GENERAL_companies : ", median_ratio_general_comp_0800_yesterday)

                            transaction_restrict_check_median = (median_ratio_top_semi_comp_0800_yesterday - 1) + (median_ratio_general_comp_0800_yesterday - 1)
                            print ("\n transaction_restrict_check_median_0800 :", transaction_restrict_check_median)



                            if (median_ratio_top_semi_comp_0800_yesterday >= 1) and (median_ratio_general_comp_0800_yesterday >= 1) :
                                value_fall_criteria = ratio_buy_general_median_diff_cri_1
                                print ("value_fall_criteria : ", value_fall_criteria)

                            elif (median_ratio_top_semi_comp_0800_yesterday < 1) and (median_ratio_general_comp_0800_yesterday >= 1) :
                                value_fall_criteria = ratio_buy_general_median_diff_cri_1 + ratio_buy_general_median_diff_cri_2
                                print ("value_fall_criteria : ", value_fall_criteria)

                            elif (median_ratio_top_semi_comp_0800_yesterday >= 1) and (median_ratio_general_comp_0800_yesterday < 1) :
                                value_fall_criteria = (ratio_buy_general_median_diff_cri_1 + ratio_buy_general_median_diff_cri_2) + (median_ratio_general_comp_0800_yesterday - 1)
                                print ("value_fall_criteria : ", value_fall_criteria)

                            elif (median_ratio_top_semi_comp_0800_yesterday < 1) and (median_ratio_general_comp_0800_yesterday < 1) :
                                value_fall_criteria = (ratio_buy_general_median_diff_cri_1 + ratio_buy_general_median_diff_cri_2) + (median_ratio_general_comp_0800_yesterday - 1)
                                print ("value_fall_criteria : ", value_fall_criteria)

                            print("value_fall_criteria calculation is done at ", (datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))))


                            print ("\nBegin transaction mode during 0800_0801")
                            for i_screening_buy_item_0800_0801 in DIC_candi_general_company.keys() :
                                print ("\n[ Get_info_stat_General_company ] {0} : {1}".format(i_screening_buy_item_0800_0801, DIC_candi_general_company[i_screening_buy_item_0800_0801]))

                                if (transaction_restrict_check_median >= ratio_buy_block_S_H_and_general_median) and (DIC_candi_company_ratio_general_comp_0800_to_yesterday[i_screening_buy_item_0800_0801] < (1 + value_fall_criteria)) :
                                    print ("check buy transaction condition")
                                    DF_1d_stat_today_start_general_0800_0801 = get_1m_1d_candles(token_get, "1d", i_screening_buy_item_0800_0801, 1, 2)
                                    DF_1d_stat_today_start_general_0800_0801.index = DF_1d_stat_today_start_general_0800_0801.index.tz_localize(None)   # 타임존(+9:00) 제거
                                    print (DF_1d_stat_today_start_general_0800_0801)

                                    real_today_start_price = int(DF_1d_stat_today_start_general_0800_0801.loc[DF_1d_stat_today_start_general_0800_0801.index.astype(str).str.contains(today), "시가"].iloc[0])
                                    ratio_real_today_start_price_and_yesterday = real_today_start_price / DIC_candi_general_company_yesterday_end_price[i_screening_buy_item_0800_0801]

                                    transaction_money_general_0800_0801 = int(DF_1d_stat_today_start_general_0800_0801.loc[DF_1d_stat_today_start_general_0800_0801.index.astype(str).str.contains(today), "시가"].iloc[0] * DF_1d_stat_today_start_general_0800_0801.loc[DF_1d_stat_today_start_general_0800_0801.index.astype(str).str.contains(today), "거래량"].iloc[0])
                                    time.sleep(0.2)

                                    bought_quantity_0800_general_comp_after_transaction = int(get_sellable_quantity(token_get, i_screening_buy_item_0800_0801))
                                    print("  check whether belong to buy blocked list by yesterday variance : {0}".format (DIC_candi_general_company_buy_blocked_check[i_screening_buy_item_0800_0801]))
                                    print("  transaction_money_during_0800_to_until : [condition] more than {0:,} ___ [current value] {1:,}".format(transaction_money_criteria, transaction_money_general_0800_0801))
                                    print("  target buy quantity : [base target] {0:,} ___ [current value] {1:,}".format(DIC_transaction_general_comp_buy_target_quantity[i_screening_buy_item_0800_0801], bought_quantity_0800_general_comp_after_transaction))
                                    time.sleep(0.2)

                                    if (DIC_candi_general_company_buy_blocked_check[i_screening_buy_item_0800_0801] != 1) and (transaction_money_general_0800_0801 >= transaction_money_criteria) and \
                                        (bought_quantity_0800_general_comp_after_transaction <= (2 * DIC_transaction_general_comp_buy_target_quantity[i_screening_buy_item_0800_0801])) :
                                        get_callable_ask_bid_price_info_general_0800_0801 = get_orderbook(token_get, i_screening_buy_item_0800_0801) # 해당 주식의 매도/매수 호가 및 연관 물량 조회

                                        # 1. result 내부의 asks 배열 안전하게 접근
                                        asks_list_general_0800_0801 = get_callable_ask_bid_price_info_general_0800_0801.get("asks", [])
                                        print("asks price information : ", asks_list_general_0800_0801)

                                        # 2. 데이터 유무 확인 후 min()으로 최저가 추출
                                        if asks_list_general_0800_0801 :
                                            callable_ask_price_0_general_0800_0801 = min(int(ask["price"]) for ask in asks_list_general_0800_0801)
                                        else :
                                            callable_ask_price_0_general_0800_0801 = None
                                            print("매도 호가 데이터가 존재하지 않습니다.")

                                        ratio_lowest_buyable_price_and_yesterday_end_price = callable_ask_price_0_general_0800_0801 / DIC_candi_general_company_yesterday_end_price[i_screening_buy_item_0800_0801]
                                        difference_lowest_buyable_price_and_general_comp_median = ratio_lowest_buyable_price_and_yesterday_end_price - median_ratio_general_comp_0800_yesterday

                                        print("buyable_basic_ratio_cri : {0} and buyable_additional_lower_ratio : {1}".format(value_fall_criteria, ratio_buy_0800_start_lower))
                                        print("ratio_difference_lowest buyable price and general_median : {0}".format(difference_lowest_buyable_price_and_general_comp_median))
                                        print("different ratio between real today start value and lowest buyable price : ", (ratio_real_today_start_price_and_yesterday - ratio_lowest_buyable_price_and_yesterday_end_price))
                                        if (DIC_transaction_general_comp_buy_target_quantity[i_screening_buy_item_0800_0801] >= 1) and (transaction_money_general_0800_0801 >= transaction_money_criteria) and \
                                        (difference_lowest_buyable_price_and_general_comp_median < (value_fall_criteria)) and ((ratio_real_today_start_price_and_yesterday - ratio_lowest_buyable_price_and_yesterday_end_price) >= ratio_buy_0800_start_lower):

                                            order_response_general_0800, orderID_buy_general_0800 = run_toss_stock_buyer_seller (token_get, str(i_screening_buy_item_0800_0801), "BUY", "LIMIT", DIC_transaction_general_comp_buy_target_quantity[i_screening_buy_item_0800_0801], callable_ask_price_0_general_0800_0801)

                                            if (order_response_general_0800 == 1) :
                                                DIC_transaction_general_comp_buy_target_with_orderID[i_screening_buy_item_0800_0801] = orderID_buy_general_0800

                                            # 매수 안된 주문은 취소하기
                                            time.sleep(0.5)
                                            print ("\n{0}_{1} transaction result check".format(i_screening_buy_item_0800_0801, DIC_candi_general_company[i_screening_buy_item_0800_0801]))
                                            check_result_0800_general_comp = transaction_result_check (token_get, DIC_transaction_general_comp_buy_target_with_orderID[i_screening_buy_item_0800_0801])

                                            if (check_result_0800_general_comp != 1) :
                                                print("All or partial {0}_{1} buy transaction order will be canceled".format (i_screening_buy_item_0800_0801, DIC_candi_general_company[i_screening_buy_item_0800_0801]))
                                                cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_buy_target_with_orderID[i_screening_buy_item_0800_0801])
                                                DIC_transaction_general_comp_buy_target_with_orderID.pop(i_screening_buy_item_0800_0801, None)   # 취소한 orderID는 삭제

                                            time.sleep(0.2)
    
                                        # 매수가 된 주문은, 매수 시점을 기준으로 매도 시도 시점을 딕셔너리내 리스트로 저장 ([1차 매도 시도 시점, 2차 매도 시도 시점, 3차 매도 시도 시점])
    
                                        bought_quantity_0800_general_comp_after_transaction = get_sellable_quantity(token_get, i_screening_buy_item_0800_0801)

                                        current_time_0800 = datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))
                                        DIC_transaction_general_comp_buy_time_minute[i_screening_buy_item_0800_0801] = int(current_time_0800.minute)
                                        time.sleep(0.2)
                                        

                                time.sleep(0.05)

                    elif (original) (1 <= today_now.minute < 10) :   # (original) (1 <= today_now.minute < 10) :         (for test) (temp_no_0_4 <= today_now.minute < temp_no_0_10) :
                        print("Begin after 0801 transaction at :", (datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))))

                        print(f"Fetch {len(LIST_for_median_top_semi_comp)} Top semi companies current price at a time...")
                        DF_top_semi_multi_items_last_price_0801 = fetch_batch_prices(token_get, LIST_for_median_top_semi_comp, chunk_size = 25)
                        #median_general_comp = DF_top_semi_multi_items_last_price_0801['last_price'].median()
                        print ("current price list \n :", DF_top_semi_multi_items_last_price_0801['last_price'])

                        print(f"Fetch {len(LIST_for_median_general_comp)} general companies current price at a time...")
                        DF_multi_items_last_price_0801 = fetch_batch_prices(token_get, LIST_for_median_general_comp, chunk_size = 25)
                        #median_general_comp = DF_multi_items_last_price_0801['last_price'].median()
                        print ("current price list \n :", DF_multi_items_last_price_0801['last_price'])

                        i_median_top_semi_0801 = 0
                        print ("\n[ Get information Top_semi_company current price ]")
                        for i_stat_today_start_0801 in DIC_candi_top_semi_company.keys() :
                            print ("\n[ Get_info_Top_semi ] {0} : {1}".format(i_stat_today_start_0801, DIC_candi_top_semi_company[i_stat_today_start_0801]))
                            current_value_top_semi = int(DF_top_semi_multi_items_last_price_0801['last_price'][i_median_top_semi_0801])
                            i_median_top_semi_0801 = i_median_top_semi_0801 + 1
                            print ("  current_price : {0:,}".format(current_value_top_semi))
                            DIC_candi_top_semi_company_this_time_start_price[i_stat_today_start_0801] = current_value_top_semi

                            ratio_current_yesterday = current_value_top_semi / DIC_candi_top_semi_company_yesterday_end_price[i_stat_today_start_0801]
                            print ("  ratio current_price to YESTERDAY_end_price : ", ratio_current_yesterday)
                            DIC_candi_company_ratio_top_semi_comp_this_time_to_yesterday[i_stat_today_start_0801] = ratio_current_yesterday

                        print ("\nratio TOP_Semi_company_current_price to YESTERDAY_end_price\n", DIC_candi_company_ratio_top_semi_comp_this_time_to_yesterday)

                        median_ratio_top_semi_comp_this_time_yesterday = statistics.median(list(DIC_candi_company_ratio_top_semi_comp_this_time_to_yesterday.values()))
                        print ("\n [median_ratio]_of_TOP_semi_candidate_companies : ", median_ratio_top_semi_comp_this_time_yesterday)



                        i_median_general_0801 = 0
                        print ("\n[ Get information GENERAL_company current price ]")
                        for i_stat_today_start_general_0801 in DIC_candi_general_company.keys() :
                            print ("\n[ Get_info_General_company ] {0} : {1}".format(i_stat_today_start_general_0801, DIC_candi_general_company[i_stat_today_start_general_0801]))
                            current_value_general = int(DF_multi_items_last_price_0801['last_price'][i_median_general_0801])
                            i_median_general_0801 = i_median_general_0801 + 1
                            print ("  Current_price : {0:,}".format(current_value_general))
                            DIC_candi_general_company_this_time_start_price[i_stat_today_start_general_0801] = current_value_general

                            ratio_current_yesterday_general = current_value_general / DIC_candi_general_company_yesterday_end_price[i_stat_today_start_general_0801]
                            print ("  ratio current_price to YESTERDAY_end_price : ", ratio_current_yesterday_general)
                            DIC_candi_company_ratio_general_comp_this_time_to_yesterday[i_stat_today_start_general_0801] = ratio_current_yesterday_general

                        print ("\nratio GENERAL_company_current_price to YESTERDAY_end_price\n", DIC_candi_company_ratio_general_comp_this_time_to_yesterday)

                        median_ratio_general_comp_this_time_yesterday = statistics.median(list(DIC_candi_company_ratio_general_comp_this_time_to_yesterday.values()))
                        print ("\n [median_ratio]_of_GENERAL_companies : ", median_ratio_general_comp_this_time_yesterday)

                        transaction_restrict_check_median_this_time = (median_ratio_top_semi_comp_this_time_yesterday - 1) + (median_ratio_general_comp_this_time_yesterday - 1)
                        print ("\n transaction_restrict_check_median_this_time :", transaction_restrict_check_median_this_time)


                        if (median_ratio_top_semi_comp_this_time_yesterday >= 1) and (median_ratio_general_comp_this_time_yesterday >= 1) :
                            value_fall_criteria_this_time = ratio_buy_general_median_diff_cri_1
                            print ("value_fall_criteria : ", value_fall_criteria_this_time)

                        elif (median_ratio_top_semi_comp_this_time_yesterday < 1) and (median_ratio_general_comp_this_time_yesterday >= 1) :
                            value_fall_criteria = ratio_buy_general_median_diff_cri_1 + ratio_buy_general_median_diff_cri_2
                            print ("value_fall_criteria : ", value_fall_criteria_this_time)

                        elif (median_ratio_top_semi_comp_this_time_yesterday >= 1) and (median_ratio_general_comp_this_time_yesterday < 1) :
                            value_fall_criteria = (ratio_buy_general_median_diff_cri_1 + ratio_buy_general_median_diff_cri_2) + (median_ratio_general_comp_this_time_yesterday - 1)
                            print ("value_fall_criteria : ", value_fall_criteria_this_time)

                        elif (median_ratio_top_semi_comp_this_time_yesterday < 1) and (median_ratio_general_comp_this_time_yesterday < 1) :
                            value_fall_criteria = (ratio_buy_general_median_diff_cri_1 + ratio_buy_general_median_diff_cri_2) + (median_ratio_general_comp_this_time_yesterday - 1)
                            print ("value_fall_criteria : ", value_fall_criteria_this_time)

                        print("value_fall_criteria calculation is done at ", (datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))))


                        print ("\nBegin transaction mode during 0801_0810")
                        for i_screening_buy_item_0801_0810 in DIC_candi_general_company.keys() :
                            print ("\n[ Get_info_General_company ] {0} : {1}".format(i_screening_buy_item_0801_0810, DIC_candi_general_company[i_screening_buy_item_0801_0810]))

                            if (transaction_restrict_check_median_this_time >= ratio_buy_block_S_H_and_general_median) and (DIC_candi_company_ratio_general_comp_this_time_to_yesterday[i_screening_buy_item_0801_0810] < (1 + value_fall_criteria_this_time)) :
                                print ("check buy transaction condition")
                                DF_stat_today_this_time_general = get_1m_1d_candles(token_get, "1m", i_screening_buy_item_0801_0810, 1, 2)
                                DF_stat_today_this_time_general.index = DF_stat_today_this_time_general.index.tz_localize(None)   # 타임존(+9:00) 제거
                                print (DF_stat_today_this_time_general)

                                #real_today_start_price = int(DF_stat_today_this_time_general_0800_0801.loc[DF_stat_today_this_time_general_0800_0801.index.astype(str).str.contains(today), "시가"].iloc[0])
                                #ratio_real_today_start_price_and_yesterday = real_today_start_price / DIC_candi_general_company_yesterday_end_price[i_screening_buy_item_0801_0810]

                                transaction_money_general_this_time = (DF_stat_today_this_time_general.iloc[0]["시가"] *  DF_stat_today_this_time_general.iloc[0]["거래량"])
                                time.sleep(0.2)

                                bought_quantity_this_time_general_comp_after_transaction = int(get_sellable_quantity(token_get, i_screening_buy_item_0801_0810))
                                print("  check whether belong to buy blocked list by yesterday variance : {0}".format (DIC_candi_general_company_buy_blocked_check[i_screening_buy_item_0801_0810]))
                                print("  transaction_money_during_prior_minute_duration : [condition] more than {0:,} ___ [current value] {1:,}".format(transaction_money_criteria, transaction_money_general_this_time))
                                print("  target buy quantity : [base target] {0:,} ___ [current value] {1:,}".format(DIC_transaction_general_comp_buy_target_quantity[i_screening_buy_item_0801_0810], bought_quantity_this_time_general_comp_after_transaction))
                                time.sleep(0.2)

                                if DIC_candi_general_company_buy_blocked_check[i_screening_buy_item_0801_0810] and (transaction_money_general_this_time >= transaction_money_criteria) and \
                                    (bought_quantity_this_time_general_comp_after_transaction <= (2 * DIC_transaction_general_comp_buy_target_quantity[i_screening_buy_item_0801_0810])) :
                                    get_callable_ask_bid_price_info_general_0801_0810 = get_orderbook(token_get, i_screening_buy_item_0801_0810) # 해당 주식의 매도/매수 호가 및 연관 물량 조회

                                    # 1. result 내부의 asks 배열 안전하게 접근
                                    asks_list_general_0801_0810 = get_callable_ask_bid_price_info_general_0801_0810.get("asks", [])
                                    print("asks price information : ", asks_list_general_0801_0810)

                                    # 2. 데이터 유무 확인 후 min()으로 최저가 추출
                                    if asks_list_general_0801_0810 :
                                        callable_ask_price_0_general_0801_0810 = min(int(ask["price"]) for ask in asks_list_general_0801_0810)
                                    else :
                                        callable_ask_price_0_general_0801_0810 = None
                                        print("매도 호가 데이터가 존재하지 않습니다.")

                                    ratio_lowest_buyable_price_and_yesterday_end_price = callable_ask_price_0_general_0801_0810 / DIC_candi_general_company_yesterday_end_price[i_screening_buy_item_0801_0810]
                                    difference_lowest_buyable_price_and_general_comp_median = ratio_lowest_buyable_price_and_yesterday_end_price - median_ratio_general_comp_this_time_yesterday

                                    print("buyable_basic_ratio_cri : {0}".format(value_fall_criteria_this_time))
                                    print("ratio_difference_lowest buyable price and general_median : {0}".format(difference_lowest_buyable_price_and_general_comp_median))
                                    if (DIC_transaction_general_comp_buy_target_quantity[i_screening_buy_item_0801_0810] >= 1) and (transaction_money_general_this_time >= transaction_money_criteria) and \
                                    (difference_lowest_buyable_price_and_general_comp_median < (value_fall_criteria_this_time)) :

                                        order_response_general_this_time, orderID_buy_general_this_time = run_toss_stock_buyer_seller (token_get, str(i_screening_buy_item_0801_0810), "BUY", "LIMIT", DIC_transaction_general_comp_buy_target_quantity[i_screening_buy_item_0801_0810], callable_ask_price_0_general_0801_0810)

                                        if (order_response_general_this_time == 1) :
                                            DIC_transaction_general_comp_buy_target_with_orderID[i_screening_buy_item_0801_0810] = orderID_buy_general_this_time

                                        # 매수 안된 주문은 취소하기
                                        time.sleep(0.5)
                                        print ("\n{0}_{1} transaction result check".format(i_screening_buy_item_0801_0810, DIC_candi_general_company[i_screening_buy_item_0801_0810]))
                                        check_result_this_time_general_comp = transaction_result_check (token_get, DIC_transaction_general_comp_buy_target_with_orderID[i_screening_buy_item_0801_0810])

                                        if (check_result_this_time_general_comp != 1) :
                                            print("All or partial {0}_{1} buy transaction order will be canceled".format (i_screening_buy_item_0801_0810, DIC_candi_general_company[i_screening_buy_item_0801_0810]))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_buy_target_with_orderID[i_screening_buy_item_0801_0810])
                                            DIC_transaction_general_comp_buy_target_with_orderID.pop(i_screening_buy_item_0801_0810, None)   # 취소한 orderID는 삭제

                                        time.sleep(0.2)

                                    # 매수가 된 주문은, 매수 시점을 기준으로 매도 시도 시점을 딕셔너리내 리스트로 저장 ([1차 매도 시도 시점, 2차 매도 시도 시점, 3차 매도 시도 시점])

                                    bought_quantity_this_time_general_comp_after_transaction = get_sellable_quantity(token_get, i_screening_buy_item_0801_0810)

                                    current_time_0800 = datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))
                                    DIC_transaction_general_comp_buy_time_minute[i_screening_buy_item_0801_0810] = int(current_time_0800.minute)
                                    time.sleep(0.2)


                            time.sleep(0.05)


                        # 매수했던 종목들의 매도 검토
                        print ("\nBegin SELL transaction mode at ", datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600)))

                        asset_current = asset_check (token_get)
                        print ("current asset : \n ", asset_current)

                        for i_sell_check_early in DIC_transaction_general_comp_buy_time_minute.keys() :
                            print ("\n\n{0}_{1} SELL transaction check".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early]))

                            # 1. 평균 매수가
                            items = asset_current.get("result", {}).get("items", [])
                            target_item = next((item for item in items if str(item.get("symbol")) == i_sell_check_early), None)

                            if target_item :
                                aver_price = target_item.get("averagePurchasePrice")
                                print("{0}_{1} : 평균매수가 {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], float(aver_price)))

                            else :
                                print("해당 symbol을 찾을 수 없습니다.")
                            time.sleep(0.2)

                            sellable_quantity_current_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                            time.sleep(0.2)

                            get_callable_ask_bid_price_info_sell_early = get_orderbook(token_get, str(i_sell_check_early)) # 해당 주식의 매도/매수 호가 및 연관 물량 조회

                            # 2. result 내부의 bids 배열 안전하게 접근
                            bids_list_early = get_callable_ask_bid_price_info_sell_early.get("bids", [])
                            print("bids price information : ", bids_list_early)

                            # 3. 데이터 유무 확인 후 max()으로 최고가 추출
                            if bids_list_early :
                                callable_bid_price_0_early = max(int(bid["price"]) for bid in bids_list_early)
                            else :
                                callable_bid_price_0_early = None
                                print("매수 호가 데이터가 존재하지 않습니다.")
                                #callable_bid_price_0 = int(get_callable_ask_bid_price_info_sell["bids"][0]["price"])   # 현재 첫번째로 높은 매수 호가 (현재 해당 주식을 어떤 사람이 사겠다고 제안한 가격)

                            time_sell_check = datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))
                            if (sellable_quantity_current_early >= 1) and (callable_bid_price_0_early is not None) :
                                if (time_sell_check.minute >= (DIC_transaction_general_comp_buy_time_minute[i_sell_check_early] + sell_duration_1 + sell_duration_2 + sell_duration_3 + sell_duration_4)) :

                                    order_response_sell_early, orderID_sell_early = run_toss_stock_buyer_seller(token_get, str(i_sell_check_early), "SELL", "LIMIT", sellable_quantity_current_early, callable_bid_price_0_early)
                                    time.sleep(0.5)
                                    sellable_quantity_after_order_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                                    print ("\n{0}_{1} bought quantity after sell order is {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], int(sellable_quantity_after_order_early)))

                                    if (order_response_sell_early == 1) :
                                        DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early] = orderID_sell_early
                                        print ("orderID_sell_early : ", orderID_sell_early)
                                        time.sleep(0.2)
                                        print("DIC_transaction_general_comp_SELL_target_with_orderID :\n", DIC_transaction_general_comp_SELL_target_with_orderID)

                                        sellable_quantity_current_early_confirm = get_sellable_quantity(token_get, str(i_sell_check_early_confirm))

                                        if (sellable_quantity_current_early_confirm >= 1) :
                                            print("\n\nUnSold quantity order is cenceled of {0}_{1} with quantity {2:,}".format(i_sell_check_early_confirm, DIC_candi_general_company[i_sell_check_early_confirm], int(sellable_quantity_current_early)))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early_confirm])
                                            DIC_transaction_general_comp_SELL_target_with_orderID.pop(i_sell_check_early_confirm, None)   # 취소한 orderID는 삭제
                                            time.sleep(0.2)


                                elif (time_sell_check.minute >= (DIC_transaction_general_comp_buy_time_minute[i_sell_check_early] + sell_duration_1 + sell_duration_2 + sell_duration_3)) and (callable_bid_price_0_early >= (aver_price * (1 + ratio_sell_after_duration_3))) :

                                    order_response_sell_early, orderID_sell_early = run_toss_stock_buyer_seller(token_get, str(i_sell_check_early), "SELL", "LIMIT", sellable_quantity_current_early, callable_bid_price_0_early)
                                    time.sleep(0.5)
                                    sellable_quantity_after_order_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                                    print ("\n{0}_{1} bought quantity after sell order is {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], int(sellable_quantity_after_order_early)))

                                    if (order_response_sell_early == 1) :
                                        DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early] = orderID_sell_early
                                        print ("orderID_sell_early : ", orderID_sell_early)
                                        time.sleep(0.2)
                                        print("DIC_transaction_general_comp_SELL_target_with_orderID :\n", DIC_transaction_general_comp_SELL_target_with_orderID)

                                        sellable_quantity_current_early_confirm = get_sellable_quantity(token_get, str(i_sell_check_early_confirm))

                                        if (sellable_quantity_current_early_confirm >= 1) :
                                            print("\n\nUnSold quantity order is cenceled of {0}_{1} with quantity {2:,}".format(i_sell_check_early_confirm, DIC_candi_general_company[i_sell_check_early_confirm], int(sellable_quantity_current_early)))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early_confirm])
                                            DIC_transaction_general_comp_SELL_target_with_orderID.pop(i_sell_check_early_confirm, None)   # 취소한 orderID는 삭제
                                            time.sleep(0.2)


                                elif (time_sell_check.minute >= (DIC_transaction_general_comp_buy_time_minute[i_sell_check_early] + sell_duration_1 + sell_duration_2)) and (callable_bid_price_0_early >= (aver_price * (1 + ratio_sell_after_duration_2))) :

                                    order_response_sell_early, orderID_sell_early = run_toss_stock_buyer_seller(token_get, str(i_sell_check_early), "SELL", "LIMIT", sellable_quantity_current_early, callable_bid_price_0_early)
                                    time.sleep(0.5)
                                    sellable_quantity_after_order_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                                    print ("\n{0}_{1} bought quantity after sell order is {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], int(sellable_quantity_after_order_early)))

                                    if (order_response_sell_early == 1) :
                                        DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early] = orderID_sell_early
                                        print ("orderID_sell_early : ", orderID_sell_early)
                                        time.sleep(0.2)
                                        print("DIC_transaction_general_comp_SELL_target_with_orderID :\n", DIC_transaction_general_comp_SELL_target_with_orderID)

                                        sellable_quantity_current_early_confirm = get_sellable_quantity(token_get, str(i_sell_check_early_confirm))

                                        if (sellable_quantity_current_early_confirm >= 1) :
                                            print("\n\nUnSold quantity order is cenceled of {0}_{1} with quantity {2:,}".format(i_sell_check_early_confirm, DIC_candi_general_company[i_sell_check_early_confirm], int(sellable_quantity_current_early)))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early_confirm])
                                            DIC_transaction_general_comp_SELL_target_with_orderID.pop(i_sell_check_early_confirm, None)   # 취소한 orderID는 삭제
                                            time.sleep(0.2)


                                elif (time_sell_check.minute >= (DIC_transaction_general_comp_buy_time_minute[i_sell_check_early] + sell_duration_1)) and (callable_bid_price_0_early >= (aver_price * (1 + ratio_sell_after_duration_1))) :

                                    order_response_sell_early, orderID_sell_early = run_toss_stock_buyer_seller(token_get, str(i_sell_check_early), "SELL", "LIMIT", sellable_quantity_current_early, callable_bid_price_0_early)
                                    time.sleep(0.5)
                                    sellable_quantity_after_order_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                                    print ("\n{0}_{1} bought quantity after sell order is {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], int(sellable_quantity_after_order_early)))

                                    if (order_response_sell_early == 1) :
                                        DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early] = orderID_sell_early
                                        print ("orderID_sell_early : ", orderID_sell_early)
                                        time.sleep(0.2)
                                        print("DIC_transaction_general_comp_SELL_target_with_orderID :\n", DIC_transaction_general_comp_SELL_target_with_orderID)

                                        sellable_quantity_current_early_confirm = get_sellable_quantity(token_get, str(i_sell_check_early_confirm))

                                        if (sellable_quantity_current_early_confirm >= 1) :
                                            print("\n\nUnSold quantity order is cenceled of {0}_{1} with quantity {2:,}".format(i_sell_check_early_confirm, DIC_candi_general_company[i_sell_check_early_confirm], int(sellable_quantity_current_early)))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early_confirm])
                                            DIC_transaction_general_comp_SELL_target_with_orderID.pop(i_sell_check_early_confirm, None)   # 취소한 orderID는 삭제
                                            time.sleep(0.2)

                            time.sleep(0.2)



                    elif (10 <= today_now.minute <= 50) :   # (original) (10 <= today_now.minute <= 50) :    (for test) (temp_no_0_10 <= today_now.minute <= temp_no_0_11) :

                        asset_current = asset_check (token_get)
                        print ("current asset : \n ", asset_current)
                        
                        for i_sell_check_early in DIC_transaction_general_comp_buy_time_minute.keys() :
                            print ("Now : ", datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600)))
                            print ("\n\n{0}_{1} SELL transaction check_after_0810".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early]))

                            # 1. 평균 매수가
                            items = asset_current.get("result", {}).get("items", [])
                            target_item = next((item for item in items if str(item.get("symbol")) == i_sell_check_early), None)

                            if target_item:
                                aver_price = target_item.get("averagePurchasePrice")
                                print("{0}_{1} : 평균매수가 {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], float(aver_price)))
    
                            else:
                                print("해당 symbol을 찾을 수 없습니다.")
                            time.sleep(0.2)
                            
                            sellable_quantity_current_early = get_sellable_quantity(token_get, str(i_sell_check_early))

                            get_callable_ask_bid_price_info_sell_early = get_orderbook(token_get, str(i_sell_check_early)) # 해당 주식의 매도/매수 호가 및 연관 물량 조회

                            # 2. result 내부의 bids 배열 안전하게 접근
                            bids_list_early = get_callable_ask_bid_price_info_sell_early.get("bids", [])
                            print("bids price information : ", bids_list_early)

                            # 3. 데이터 유무 확인 후 max()으로 최고가 추출
                            if bids_list_early :
                                callable_bid_price_0_early = max(int(bid["price"]) for bid in bids_list_early)
                            else :
                                callable_bid_price_0_early = None
                                print("매수 호가 데이터가 존재하지 않습니다.")                       
                                #callable_bid_price_0 = int(get_callable_ask_bid_price_info_sell["bids"][0]["price"])   # 현재 첫번째로 높은 매수 호가 (현재 해당 주식을 어떤 사람이 사겠다고 제안한 가격)

                            time_sell_check = datetime.datetime.now() + datetime.timedelta(seconds=(time_conpensation_factor * 3600))
                            if (sellable_quantity_current_early >= 1) and (callable_bid_price_0_early is not None) :
                                if (time_sell_check.minute >= (DIC_transaction_general_comp_buy_time_minute[i_sell_check_early] + sell_duration_1 + sell_duration_2 + sell_duration_3 + sell_duration_4)) :
                                    
                                    order_response_sell_early, orderID_sell_early = run_toss_stock_buyer_seller(token_get, str(i_sell_check_early), "SELL", "LIMIT", sellable_quantity_current_early, callable_bid_price_0_early)
                                    time.sleep(0.5)
                                    sellable_quantity_after_order_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                                    print ("\n{0}_{1} bought quantity after sell order is {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], int(sellable_quantity_after_order_early)))
                                    
                                    if (order_response_sell_early == 1) :
                                        DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early] = orderID_sell_early
                                        print ("orderID_sell_early : ", orderID_sell_early)
                                        time.sleep(0.2)
                                        print("DIC_transaction_general_comp_SELL_target_with_orderID :\n", DIC_transaction_general_comp_SELL_target_with_orderID)

                                        sellable_quantity_current_early_confirm = get_sellable_quantity(token_get, str(i_sell_check_early_confirm))

                                        if (sellable_quantity_current_early_confirm >= 1) :
                                            print("\n\nUnSold quantity order is cenceled of {0}_{1} with quantity {2:,}".format(i_sell_check_early_confirm, DIC_candi_general_company[i_sell_check_early_confirm], int(sellable_quantity_current_early)))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early_confirm])
                                            DIC_transaction_general_comp_SELL_target_with_orderID.pop(i_sell_check_early_confirm, None)   # 취소한 orderID는 삭제
                                            time.sleep(0.2)
                                            

                                elif (time_sell_check.minute >= (DIC_transaction_general_comp_buy_time_minute[i_sell_check_early] + sell_duration_1 + sell_duration_2 + sell_duration_3)) and (callable_bid_price_0_early >= (aver_price * (1 + ratio_sell_after_duration_3))) :
                                    
                                    order_response_sell_early, orderID_sell_early = run_toss_stock_buyer_seller(token_get, str(i_sell_check_early), "SELL", "LIMIT", sellable_quantity_current_early, callable_bid_price_0_early)
                                    time.sleep(0.5)
                                    sellable_quantity_after_order_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                                    print ("\n{0}_{1} bought quantity after sell order is {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], int(sellable_quantity_after_order_early)))
                                    
                                    if (order_response_sell_early == 1) :
                                        DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early] = orderID_sell_early
                                        print ("orderID_sell_early : ", orderID_sell_early)
                                        time.sleep(0.2)
                                        print("DIC_transaction_general_comp_SELL_target_with_orderID :\n", DIC_transaction_general_comp_SELL_target_with_orderID)

                                        sellable_quantity_current_early_confirm = get_sellable_quantity(token_get, str(i_sell_check_early_confirm))

                                        if (sellable_quantity_current_early_confirm >= 1) :
                                            print("\n\nUnSold quantity order is cenceled of {0}_{1} with quantity {2:,}".format(i_sell_check_early_confirm, DIC_candi_general_company[i_sell_check_early_confirm], int(sellable_quantity_current_early)))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early_confirm])
                                            DIC_transaction_general_comp_SELL_target_with_orderID.pop(i_sell_check_early_confirm, None)   # 취소한 orderID는 삭제
                                            time.sleep(0.2)
                                            

                                elif (time_sell_check.minute >= (DIC_transaction_general_comp_buy_time_minute[i_sell_check_early] + sell_duration_1 + sell_duration_2)) and (callable_bid_price_0_early >= (aver_price * (1 + ratio_sell_after_duration_2))) :
                                    
                                    order_response_sell_early, orderID_sell_early = run_toss_stock_buyer_seller(token_get, str(i_sell_check_early), "SELL", "LIMIT", sellable_quantity_current_early, callable_bid_price_0_early)
                                    time.sleep(0.5)
                                    sellable_quantity_after_order_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                                    print ("\n{0}_{1} bought quantity after sell order is {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], int(sellable_quantity_after_order_early)))
                                    
                                    if (order_response_sell_early == 1) :
                                        DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early] = orderID_sell_early
                                        print ("orderID_sell_early : ", orderID_sell_early)
                                        time.sleep(0.2)
                                        print("DIC_transaction_general_comp_SELL_target_with_orderID :\n", DIC_transaction_general_comp_SELL_target_with_orderID)

                                        sellable_quantity_current_early_confirm = get_sellable_quantity(token_get, str(i_sell_check_early_confirm))

                                        if (sellable_quantity_current_early_confirm >= 1) :
                                            print("\n\nUnSold quantity order is cenceled of {0}_{1} with quantity {2:,}".format(i_sell_check_early_confirm, DIC_candi_general_company[i_sell_check_early_confirm], int(sellable_quantity_current_early)))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early_confirm])
                                            DIC_transaction_general_comp_SELL_target_with_orderID.pop(i_sell_check_early_confirm, None)   # 취소한 orderID는 삭제
                                            time.sleep(0.2)
                                            

                                elif (time_sell_check.minute >= (DIC_transaction_general_comp_buy_time_minute[i_sell_check_early] + sell_duration_1)) and (callable_bid_price_0_early >= (aver_price * (1 + ratio_sell_after_duration_1))) :
                                    
                                    order_response_sell_early, orderID_sell_early = run_toss_stock_buyer_seller(token_get, str(i_sell_check_early), "SELL", "LIMIT", sellable_quantity_current_early, callable_bid_price_0_early)
                                    time.sleep(0.5)
                                    sellable_quantity_after_order_early = get_sellable_quantity(token_get, str(i_sell_check_early))
                                    print ("\n{0}_{1} bought quantity after sell order is {2:,}".format(i_sell_check_early, DIC_candi_general_company[i_sell_check_early], int(sellable_quantity_after_order_early)))
                                    
                                    if (order_response_sell_early == 1) :
                                        DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early] = orderID_sell_early
                                        print ("orderID_sell_early : ", orderID_sell_early)
                                        time.sleep(0.2)
                                        print("DIC_transaction_general_comp_SELL_target_with_orderID :\n", DIC_transaction_general_comp_SELL_target_with_orderID)

                                        sellable_quantity_current_early_confirm = get_sellable_quantity(token_get, str(i_sell_check_early_confirm))

                                        if (sellable_quantity_current_early_confirm >= 1) :
                                            print("\n\nUnSold quantity order is cenceled of {0}_{1} with quantity {2:,}".format(i_sell_check_early_confirm, DIC_candi_general_company[i_sell_check_early_confirm], int(sellable_quantity_current_early)))
                                            cancel_order = cancel_toss_stock_order(token_get, DIC_transaction_general_comp_SELL_target_with_orderID[i_sell_check_early_confirm])
                                            DIC_transaction_general_comp_SELL_target_with_orderID.pop(i_sell_check_early_confirm, None)   # 취소한 orderID는 삭제
                                            time.sleep(0.2)
            
                            time.sleep(0.2)

                

                
                
                elif ((8 <= now_in_mode.hour < 9) and (55 <= now_in_mode.minute < 56) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 3))) :   # (original) ((8 <= now_in_mode.hour < 9) and (55 <= now_in_mode.minute < 56) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 3))) :     (for test) ((temp_hr_no_1 <= now_in_mode.hour < temp_hr_no_2) and (temp_no_0_11 <= now_in_mode.minute < temp_no_0_12) and (0 <= now_in_mode.second < (cycle_in_transation_mode + 3))) :
                    print ("setting initial condition again")
                    token_get = "temp"

                    value_fall_criteria = -50.0
                    value_fall_criteria_this_time = -50.0




                    total_cash_buyable_today = 0
                    money_for_a_item_divider_for_top_semi_comp = 2
                    money_for_a_item_divider_for_general_comp = 100

                    ratio_lowest_buyable_price_and_yesterday_end_price = 99.0
                    difference_lowest_buyable_price_and_general_comp_median = 0.0

                    money_for_buy_a_top_semi_comp = 0
                    total_cash_buyable_residual = 0
                    total_cash_buyable_residual_s = 0

                    median_ratio_general_comp_this_time_yesterday = 0.0
                    aver_price = 0.0

                    DIC_candi_general_company_buy_blocked_check = {}

                    DIC_candi_top_semi_company_yesterday_end_price = {}
                    DIC_candi_general_company_yesterday_end_price = {}

                    DIC_candi_top_semi_company_0800_start_price = {}
                    DIC_candi_general_company_0800_start_price = {}

                    DIC_candi_top_semi_company_this_time_start_price = {}
                    DIC_candi_general_company_this_time_start_price = {}

                    DIC_candi_top_semi_company_0801_start_price = {}
                    DIC_candi_general_company_0801_start_price = {}

                    DIC_candi_top_semi_company_0802_start_price = {}
                    DIC_candi_general_company_0802_start_price = {}

                    DIC_candi_company_ratio_top_semi_comp_0800_to_yesterday = {}
                    DIC_candi_company_ratio_general_comp_0800_to_yesterday = {}

                    DIC_candi_company_ratio_top_semi_comp_this_time_to_yesterday = {}
                    DIC_candi_company_ratio_general_comp_this_time_to_yesterday = {}

                    DIC_candi_company_ratio_top_semi_comp_0802_to_yesterday = {}
                    DIC_candi_company_ratio_general_comp_0802_to_yesterday = {}

                    DIC_candi_company_ratio_top_semi_comp_0801_to_0800 = {}
                    DIC_candi_company_ratio_general_comp_0801_to_0800 = {}

                    DIC_candi_company_ratio_top_semi_comp_0802_to_0801 = {}
                    DIC_candi_company_ratio_general_comp_0802_to_0801 = {}

                    median_ratio_top_semi_comp_0800_yesterday = 0
                    median_ratio_general_comp_0800_yesterday = 0

                    DIC_transaction_top_semi_comp_buy_target_quantity = {}
                    DIC_transaction_general_comp_buy_target_quantity = {}

                    DIC_candi_top_semi_company_transaction_money_0800_0801 = {}
                    DIC_candi_general_company_transaction_money_0800_0801 = {}

                    DIC_candi_top_semi_company_transaction_money_0800_0802 = {}
                    DIC_candi_general_company_transaction_money_0800_0802 = {}

                    DIC_transaction_top_semi_comp_buy_target_with_orderID = {}
                    DIC_transaction_general_comp_buy_target_with_orderID = {}

                    DIC_transaction_top_semi_comp_buy_time_minute = {}
                    DIC_transaction_general_comp_buy_time_minute = {}

                    DIC_transaction_top_semi_comp_SELL_target_with_orderID = {}
                    DIC_transaction_general_comp_SELL_target_with_orderID = {}

                    DIC_top_semi_comp_bought_average_price = {}
                    DIC_general_comp_bought_average_price = {}

                    DIC_top_semi_comp_bought_quantity = {}
                    DIC_general_comp_bought_quantity = {}

                    total_bought_quantity = 0

                    market_condition = 99

                    #buy_state = 0

                    #bought_quantity_of_0 = 0
                    #bought_quantity_of_1 = 0

                    intermediate_price = 0

                    order_response = 0



                time.sleep(cycle_in_transation_mode)
                #time_check = time_check + 1

        time.sleep(cycle_period)

    except :
        
        print ('\n\nError has occured!!!')
        err_msg = traceback.format_exc()
        print(err_msg)
        time.sleep(10)


# In[ ]:


#test_asset_check = asset_check(token_get)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




