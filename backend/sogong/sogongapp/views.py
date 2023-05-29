from django.http import JsonResponse
from .models import User
from .models import EthicsProblem
from .models import CodingProblem
from .models import SolvedEthics
from .models import SolvedCoding
from .models import CodingSubmission
from .models import CodingTestCase
import json
import hashlib
import openai
import sogongapp.gpt_prompts as gpt_prompts
from .API_KEY import OPENAI_API_KEY  

openai.api_key = OPENAI_API_KEY

def gpt_inference( method,problem_content=None,  testcases=None, answer=None):
    messages = []
    if method == 'feedback':
        prompt = getattr(gpt_prompts, 'GPT_CODE_FEEDBACK')
        prompt = '문제: \n' + problem_content + '\n' + '답변 CODE: \n'+ answer + '\n' + prompt
        messages.append({'role': 'user', 'content': prompt})
    elif method == 'testcase':
        prompt = 'Code: \n' + answer
        tmp_message= ''
        for i in range(4):
            try:
                tmp_message = f'case_input{i+1}: \n' + getattr(testcases, f'case_input{i+1}') + '\n' 
                tmp_message += f'case_output{i+1} : \n' + getattr(testcases, f'case_output{i+1}') +'\n'
            except:
                print(f'{i+1}번째 input case는 존재하지 않습니다.')
        prompt += tmp_message
        prompt += getattr(gpt_prompts, 'GPT_CODE_CHECK')
        messages.append({'role': 'user', 'content': prompt})
    wait = 1
    while True:
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                temperature=1.0,
                messages=messages
            )
            content = [response['choices'][i]['message']['content'] for i in range(1)]
            return content
        except openai.error.RateLimitError:
            print('openai.error.RateLimitError')
            import time
            time.sleep(min(wait, 60))
        except openai.error.ServiceUnavailableError:
            print('openai.error.ServiceUnavailableError')
            import time
            time.sleep(min(wait, 60))
        except openai.error.InvalidRequestError:
            print('openai.error.InvalidRequestError')
            import time
            time.sleep(min(wait, 60))
        except openai.error.APIError:
            print('openai.error.APIError')
            import time
            time.sleep(min(wait, 60))
        except openai.error.APIConnectionError:
            print('openai.error.APIConnectionError')
            import time
            time.sleep(min(wait, 60))    

def check_password(user, input_word): # 비밀번호 확인
    password = user.password

    if input_word == password:
        return True
    else:
        return False
    
#GPT로 부터 답변을 얻어오는 함수
def get_gpt_answer(problem_text, problem_input, problem_output):
    #!---GPT에게 넘겨주어야 할 것은 문제 텍스트, 문제의 입력값 예시, 문제의 출력값 예시---!
    #!---GPT로 부터 받아온 코드를 answer에 넣고 answer를 반환
    answer = 'text'
    return answer

#답이 유효한지 확인하는 함수
def answer_validation(answer, testcases):
    #!---GPT에게 넘겨주어야 코드와, 일련의 테스트 케이스 집합---!
    response = gpt_inference('testcase', testcases=testcases, answer = answer)
    input_1 = testcases.case_input1
    input_2 = testcases.case_input2
    input_3 = testcases.case_input3
    input_4 = testcases.case_input4
    output_1 = testcases.case_output1
    output_2 = testcases.case_output2
    output_3 = testcases.case_output3
    output_4 = testcases.case_output4

    #!---정상적으로 통과했으면 True를, 통과하지 못했으면 False를 반환
    return True

#사용자의 답의 피드백을 받는 함수
def get_feedback(problem_content, user_submission):
    #!---피드백을 지피티로부터 받아서 피드백을 리턴---!
    response = gpt_inference('feedback',problem_content, answer= user_submission)
    feedback = response
    return feedback


def register_view(request):
    if request.method == "POST": # 회원가입
        body = json.loads(request.body)
        id = body.get("id")
        email = body.get("email")
        pw = body.get("pw")
        user = User(username=id, email=email, password=pw) # id, email, password
        if User.objects.filter(username=id).exists():
            response_data = {
            "message": "이미 존재하는 회원입니다.",
            "id" : id,
            "email" : email,
            "pw" : pw
        } # 이미 회원 정보가 존재하는 경우
        else:
            user.save()   
            response_data = {
            "message": "회원가입이 완료되었습니다.",
            "id" : id,
            "email" : email,
            "pw" : pw
        } # 새로 만든 경우
    
        
        return JsonResponse(response_data)
    
    else:
        id = request.GET.get('id')
        pw = request.GET.get('pw')
        user = User.objects.get(username=id)
        print()
        if user and check_password(user,pw): # db와 비교 
            # 로그인 성공
            hash_object = hashlib.md5(id.encode())
            hash_value = hash_object.hexdigest()
            
            response_data = {
            "message" : "로그인이 완료되었습니다.",
            "id" : id,
            "pw" : pw,
            "cookie" : hash_value,
        }
            return JsonResponse(response_data)
        else:
            # 로그인 실패
            response_data = {
            "message" : "로그인이 실패했습니다"
        }
            return JsonResponse(response_data)
    
def userinfo_view(request):
    username = request.GET.get('username')
    solvedEthics_count = SolvedEthics.objects.filter(username=username).count() #해결 한 윤리 문제의 수
    solvedCoding_count = SolvedCoding.objects.filter(username=username).count() #해결 한 코딩 문제의 수
    ethicsProblem_count = EthicsProblem.objects.all().count() #전체 윤리 문제의 수
    codingProblem_count = CodingProblem.objects.all().count() #전체 코딩 문제의 수
    ethics_progress_rate = solvedEthics_count / ethicsProblem_count * 100 #윤리 문제 진행도 계산
    coding_progress_rate = solvedCoding_count / codingProblem_count * 100 #코딩 문제 진행도 계산
    response_data = {
        "message" : "사용자의 진척도 입니다.",
        "ethics_progress_rate" : ethics_progress_rate,
        "coding_progress_rate" : coding_progress_rate,
    }
    return JsonResponse(response_data)

def ethics_view(request):
    username = request.GET.get('username')
    ethicsProblems = EthicsProblem.objects.all() #전체 윤리 문제를 불러와서 저장
    solvedEthics = SolvedEthics.objects.filter(username=username).all() #해결한 윤리 문제를 불러와서 저장
    response_data = []
    for ethicsProblem in ethicsProblems: #전체 문제 리스트 순회
        solved_ethics = solvedEthics.filter(problem=ethicsProblem.title).first() #지금 선택한 문제 제목이 solvedEthics에 존재 하는지 확인
        if solved_ethics is not None:
            response_data.append({
                "title": ethicsProblem.title,
                "content": ethicsProblem.content,
                "optionA": ethicsProblem.optionA,
                "optionB": ethicsProblem.optionB,
                "submissionA": ethicsProblem.submissionA,
                "submissionB": ethicsProblem.submissionB,
                "solved": True,
            }) #존재시 해결한 문제임을 전송
        else:
            response_data.append({
                "title": ethicsProblem.title,
                "content": ethicsProblem.content,
                "optionA": ethicsProblem.optionA,
                "optionB": ethicsProblem.optionB,
                "submissionA": ethicsProblem.submissionA,
                "submissionB": ethicsProblem.submissionB,
                "solved": False,
            }) #부재시 해결한 적 없는 문제임을 전송
    
    return JsonResponse(response_data)

def codings_view(request):
    username = request.GET.get('username')
    codingsProblems = CodingProblem.objects.all() #전체 코딩 문제를 불러와서 저장
    solvedCodings = SolvedCoding.objects.filter(username=username).all() #해결한 코딩 문제를 불러와서 저장
    response_data = []
    for codingproblem in codingsProblems: #전체 문제 리스트 순회
        solved_coding = solvedCodings.filter(problem=codingproblem.title).first() #지금 선택한 문제 제목이 solvedCodings에 존재하는 지 확인
        if solved_coding is not None:
            response_data.append({
                "title": codingproblem.title,
                "level": codingproblem.level,
                "content": codingproblem.content_problem,
                "input": codingproblem.content_input,
                "output": codingproblem.content_output,
                "solved": True,
            }) #존재시 해결한 문제임을 전송
        else:
            response_data.append({
                "title": codingproblem.title,
                "level": codingproblem.level,
                "content": codingproblem.content_problem,
                "input": codingproblem.content_input,
                "output": codingproblem.content_output,
                "solved": False,
            }) #부재시 해결한 적 없는 문제임을 전송
    
    return JsonResponse(response_data)


def coding_answer(request):
    username = request.GET.get('username')
    pid = request.GET.get('pid')
    problem_info = CodingProblem.objects.get(id=pid) #pid를 통해 전체 문제를 불러온다
    problem_title = problem_info.title
    problem_text = problem_info.content_problem
    problem_input = problem_info.content_input
    problem_output = problem_info.content_output
    gpt_answer = problem_info.content_output  #gpt 답안을 받을 변수 선언

    #이미 해결한 적 있는 경우 저장되어 있을 것이므로 CodingSubmission을 찾아서 gpt_answer를 반환
    try:  
        codingSubmission = CodingSubmission.objects.get(user=username, problem=problem_title)
        gpt_answer = codingSubmission.gpt_answer
    #해결한 적 없는 경우 GPT에게 요청
    except CodingSubmission.DoesNotExist:
        gpt_answer = get_gpt_answer(problem_text, problem_input, problem_output) #GPT답을 받아오는 함수(구현요망)
        testcases = CodingTestCase.objects.get(problem = problem_title) #해당 문제의 테스트 케이스를 가져옴

        # 테스트 케이스를 통과하지 못하면 GPT의 답변에 문제가 있는것으로 판단, 재생성
        while answer_validation(gpt_answer, testcases) is False:
            print("GPT 답변에 문제가 있습니다.")
            gpt_answer = get_gpt_answer(problem_text, problem_input, problem_output)

        codingSubmission = CodingSubmission(user=username, problem=problem_title, gpt_answer=gpt_answer, user_submission=None, gpt_feedback=None)
        codingSubmission.save() # 정상적 생성 이후 codingSubmission에 저장

    response_data = {
        "message" : "GPT의 답변입니다",
        "answer" : gpt_answer,
    }
    return JsonResponse(response_data)

def useranswer_view(request):
    if request.method == "POST": 
        body = json.loads(request.body)
        username = body.get("id")
        pid = body.get("pid")
        user_submission = body.get("answer")
        problem_info = CodingProblem.objects.get(id=pid) #pid를 통해 전체 문제를 불러온다
        problem_title = problem_info.title
        problem_content = problem_info.content_problem + '\n입력 : ' + problem_info.content_input + '\n 출력: ' + problem_info.content_output

        testcases = CodingTestCase.objects.get(problem = problem_title) #해당 문제의 테스트 케이스를 가져옴
        
        #사용자의 답변이 정확한지 확인
        if answer_validation(problem_content, user_submission, testcases):
            gpt_feedback = get_feedback(problem_content, user_submission)
            codingSubmission = CodingSubmission.objects.get(user=username, problem=problem_title)
            codingSubmission.user_submission = user_submission
            codingSubmission.gpt_feedback = gpt_feedback
            codingSubmission.save() #답변이 정답일 시 사용자의 답변과 피드백을 저장

            response_data = {
                "message": "정답입니다!",
                "isPass" : True,
                "feedback" : gpt_feedback,
            }
        else:
            response_data = {
                "message": "틀렸습니다!",
                "isPass" : False,
                "feedback" : None,
            }  #정답이 아닐 시 저장하지 않음
        return JsonResponse(response_data)
    