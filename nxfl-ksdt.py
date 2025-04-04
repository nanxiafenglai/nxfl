'''
Description: 
Author: 南下风来
Date: 2024-12-27 20:43:24
LastEditTime: 2025-03-19 22:59:37
LastEditors: 南下风来
'''
import requests
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import json
from pathlib import Path

# 创建一个全局锁用于同步输出
print_lock = threading.Lock()

def print_banner():
    RED = '\033[91m'
    RESET = '\033[0m'
    banner = f'''{RED}
    N   N  X   X  FFFFF  L      
    NN  N   X X   F      L      
    N N N    X    FFF    L      
    N  NN   X X   F      L      
    N   N  X   X  F      L      
    N   N  X   X  F      LLLLL
    {RESET}'''
    print(banner)

headers = {
  'user-agent':'Mozilla/5.0 (Linux; Android 15; 23046PNC9C Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.770 (rel) Mobile Safari/537.36 Yoda/3.2.11-rc1 ksNebula/13.2.21.9647 OS_PRO_BIT/64 MAX_PHY_MEM/11446 KDT/PHONE AZPREFIX/az3 ICFO/0 StatusHT/37 TitleHT/44 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn SHP/2400 SWP/1080 SD/2.75 CT/0 ISLM/0'
}

def user(ck, log_collector, activity_token=None):
    url = "https://ppg.viviv.com/rest/doodle/block/activity/auth/user"
    local_headers = headers.copy()
    local_headers['cookie'] = ck
    body = {
        "source": "KUAISHOU",
        "activityToken": activity_token or "dxbCnfff"
    }
    try:
        res = requests.post(url, headers=local_headers, json=body, timeout=10).json()
        return [res["data"]["userName"],res["data"]["userId"]] if res["data"]["login"] else None
    except Exception as e:
        log_collector(f"请求失败: {str(e)}")
        return None

def chance(ck, log_collector, answer_token):
    url = "https://ppg.viviv.com/rest/doodle/activity/answer/online/barrier/query-chance"
    local_headers = headers.copy()
    local_headers['cookie'] = ck
    body = {"answerActivityToken": answer_token}
    try:
        res = requests.post(url, headers=local_headers, data=body, timeout=10).json()
        return int(res["data"]["chance"])
    except Exception as e:
        log_collector(f"请求失败: {str(e)}")
        return 0

def answers(ck, answer_token):
    url = 'https://ppg.viviv.com/rest/doodle/activity/answer/online/barrier/begin-answer'
    local_headers = headers.copy()
    local_headers['cookie'] = ck
    body = {"answerActivityToken": answer_token}
    try:
        res = requests.post(url, headers=local_headers, data=body, timeout=10).json()
        examId = res["data"]["examId"]
        result = [{
            "id": question["id"],
            "题目": question["content"]["text"],
            "选项": [{"id": str(idx+1), "text": opt["text"], "original_id": opt["id"]} 
                    for idx, opt in enumerate(question["options"])]
        } for question in res["data"]["examQuestions"]]
        return result, examId
    except Exception as e:
        return f"请求失败: {str(e)}", None

def ai(msg):
    url = 'https://aliyun.zaiwen.top/admin/chatbot'
    body = {"message": [{"role": "user", "content": msg}], "mode": "deepseekv3"}
    try:
        res = requests.post(url, json=body).text
        match = re.search(r'[1-4]', res)
        return match.group(0) if match else "1"
    except:
        return "1"

class QuestionBank:
    def __init__(self):
        self.bank_file = Path("question_bank.json")
        self.bank = self._load_bank()
        
    def _load_bank(self):
        if self.bank_file.exists():
            try:
                with open(self.bank_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def _save_bank(self):
        with open(self.bank_file, 'w', encoding='utf-8') as f:
            json.dump(self.bank, f, ensure_ascii=False, indent=2)
            
    def add_question(self, question_id, question_text, options, correct_answer):
        self.bank[question_id] = {
            "text": question_text,
            "options": options,
            "answer": correct_answer,
            "update_time": time.time()
        }
        self._save_bank()
        
    def get_answer(self, question_id):
        return self.bank.get(question_id, {}).get("answer")

question_bank = QuestionBank()

def tiku(id):
    answer = question_bank.get_answer(id)
    return answer if answer else None

def answer(ck, id, answer_id, examId, answer_token, log_collector):
    url = "https://ppg.viviv.com/rest/doodle/activity/answer/online/barrier/answer"
    local_headers = headers.copy()
    local_headers['cookie'] = ck
    body = {
        "answerActivityToken": answer_token,
        "examId": examId,
        "answerInfo": {"questionId": id, "answerOptionIds": [answer_id]}
    }
    try:
        res = requests.post(url, headers=local_headers, json=body, timeout=10).json()
        if not res['data']['waitForReward']:
            questions, _ = answers(ck, answer_token)
            for q in questions:
                if q["id"] == id:
                    question_bank.add_question(
                        id,
                        q["题目"],
                        [opt["text"] for opt in q["选项"]],
                        answer_id
                    )
                    break
            return True
        return False
    except Exception as e:
        return False

def renwu(id, account):
    log_buffer = []
    def log_collector(message):
        log_buffer.append(f"[线程ID:{threading.get_ident()}] {message}")

    try:
        if not account or '#' not in account:
            log_collector("账号格式错误")
            return "格式错误"
            
        ck, remark = account.split('#', 1) if '#' in account else (account, "未命名")
        log_collector(f"\n==== 账号[{id+1}] {remark} ====")
        
        tokens = ["AN_h824VX7W","AN_p6fY6Ug1","AN_UN50YKLC","AN_v3qACQVs","AN_pwtdY14H","AN_uRJMkM17","AN_z0LJte4f","AN_T8JEs6G2","AN_tSPfKNJ1","AN_qD4BkMvE","AN_FFFrEdNV","AN_l5Z1xKW2","AN_oivAKfWg","AN_gZl5fnCI","AN_4KKXM1in","AN_wa3lr9Lr","AN_N87Vgiq9"]
        activityTokens = ["vJAAzNly","VeZrhfmm","oDDwxCPd","YjdsrGKP","chUxzEzk","ffRykfgF","sxIKdxJF","uUbmuNKs","pZqbkloO","aMKwstkY","aIZlZycv","dxbCnfff","SbfKgNmx","NhzQNKth","egredzTV","SGvaKzCU","EMMekLUf"]
        
        if not user(ck, log_collector):
            log_collector("Cookie失效")
            return "未登录"
            
        username, userid = user(ck, log_collector)
        log_collector(f"用户: {username} (ID:{userid})")
        
        total_answered = 0
        for token_idx in range(len(tokens)):
            answer_token = tokens[token_idx]
            activity_token = activityTokens[token_idx]
            
            log_collector(f"尝试token对 [{token_idx+1}/{len(tokens)}]: {answer_token}")
            
            if not user(ck, log_collector, activity_token):
                log_collector(f"Token {answer_token} 无效，跳过")
                continue
                
            while True:
                remain = chance(ck, log_collector, answer_token)
                if remain <= 0:
                    log_collector(f"Token {answer_token} 答题次数已用尽")
                    break
                    
                log_collector(f"Token {answer_token} 剩余次数: {remain}")
                
                answer_data = answers(ck, answer_token)
                if not isinstance(answer_data, tuple) or len(answer_data) != 2:
                    log_collector("获取题目失败，等待重试...")
                    time.sleep(2)
                    continue
                    
                questions, exam_id = answer_data
                
                error_flag = False
                for q in questions:
                    if error_flag: break
                    
                    log_collector(f"题目: {q['题目'][:20]}...")
                    options = "\n".join([f"{opt['id']}. {opt['text'][:10]}" for opt in q['选项']])
                    log_collector(f"选项:\n{options}")
                    
                    ans_id = tiku(q["id"]) or ai(f"{q['题目']}\n选项：{options}")
                    log_collector(f"选择答案: {ans_id}")
                    
                    if answer(ck, q["id"], ans_id, exam_id, answer_token, log_collector):
                        log_collector("✓ 回答正确")
                        total_answered += 1
                    else:
                        log_collector("× 回答错误")
                        error_flag = True
                        
                time.sleep(1)
            
        with print_lock:
            print('\n'.join(log_buffer))
            
        return f"{remark} 任务完成，共完成{total_answered}次答题"
    except Exception as e:
        log_collector(f"异常: {str(e)}")
        return "执行失败"

def main():
    print_banner()
    accounts='kpn=NEBULA;kpf=ANDROID_PHONE;userId=2948931818;did=ANDROID_19694067756c6939;c=XIAOMI;ver=13.2;appver=13.2.21.9647;language=zh-cn;countryCode=CN;sys=ANDROID_15;mod=Xiaomi%284AC144AE4042DB1A6A10%29;net=NOTFOUND;deviceName=Xiaomi%284AC144AE4042DB1A6A10%29;earphoneMode=1;isp=CTCC;ud=2948931818;did_tag=0;egid=DFP83A2F3EB0720DCA08ACC6DAC7B21440300CCB79D721D4E0A173277244F2B4;thermal=10000;kcv=1598;app=0;bottom_navigation=true;android_os=0;oDid=ANDROID_64214b1f26109c11;boardPlatform=mt6895;newOc=XIAOMI;androidApiLevel=35;slh=0;country_code=cn;nbh=0;hotfix_ver=;did_gt=1742163948506;keyconfig_state=2;cdid_tag=2;lkvr=;max_memory=256;sid=a5e98d3a-8110-4492-9079-e36d8985dd14;cold_launch_time_ms=1742164364090;oc=XIAOMI;sh=2400;deviceBit=0;browseType=3;ddpi=440;socName=MediaTek+MT6895;is_background=0;sw=1080;ftt=bd-T-T;apptype=22;abi=arm64;cl=0;userRecoBit=0;device_abi=arm64;ll_client_time=0;icaver=1;totalMemory=11446;grant_browse_type=AUTHORIZED;iuid=;rdid=ANDROID_9269fa5f4d04c0ac;sbh=102;darkMode=false;kuaishou.api_st=Cg9rdWFpc2hvdS5hcGkuc3QSoAFpR5lHwxGSdPNXremRMxMdy0dWD3flkxPqF121xbQb01niyIW8nMwm-epv86KeFCEeeG_qG7mfTGrWgh1IoxoeUl2OVvsFylLx3j92eNF1WUKCfHE30psyat1rwnjoV95lIO2VUBmS6OXFB2-eden-K_fFV7xzQz_daVJ0IpP5fl5eywsERawyZvooh9X3uJkf6vih83fDt_pILwLe1_2vGhJQViwWWuREjLU9a7lIv7onMn4iILeQLUV8oib5ZgXli5jGRSh-ofzBdMs14tcpR79mKRi2KAUwAQ;__NSWJ=;client_key=2ac2a76d;kuaishou.h5_st=Cg5rdWFpc2hvdS5oNS5zdBKgARgDl7Q1dMdxfhXC4aF2pit-w-77eB3QbprzCf2TeWlHVFoNi_JYvFqUTslgZUQc50rvMDsRZU0F7ZrKPUi7O_u_VWAg-xhIndPqFujeANPOHXX87nUe5fdO-f00G0Icv2n2F0hfC4ZGoI_CNVde6jrBvvuWGftRZytlP5rgLJmjLZrayJwDcRS2D70IzFlIc232Lz0kuBaEZHTVYGfr17waEi0FTenUzzyakcPnzsVR98aTkSIgN_UsygMLuQCCvbl58l9M2jOMY9JZaavaFw2y9sKJR0koBTAB;token=#小号'.split('&')
    valid_accounts = [acc.strip() for acc in accounts if acc.strip()]
    if not valid_accounts:
        print("未找到有效账号")
        return
    
    print(f'找到{len(valid_accounts)}个账号，开始答题...')
    
    start = time.time()
    success = fail = 0
    
    with ThreadPoolExecutor(max_workers=min(10, len(valid_accounts))) as executor:
        futures = [executor.submit(renwu, idx, acc) for idx, acc in enumerate(valid_accounts)]
        for future in as_completed(futures):
            result = future.result()
            success += 1 if "失败" not in result else 0
            fail += 1 if "失败" in result else 0
    
    print(f"\n总耗时: {time.time()-start:.1f}s | 成功: {success} | 失败: {fail}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"运行错误: {e}")
    print("程序退出")