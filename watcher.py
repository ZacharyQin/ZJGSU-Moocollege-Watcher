#!/usr/bin/python
#coding: utf-8
import requests,time,json
import urllib,random
from multiprocessing.dummy import Pool

#登陆相关
def login(username, password):
  url1 = "/nodeapi/3.0.1/student/system/login"
  payload = {
    "username": username,
    "password": password,
    "type": "account",
    "rememberMe": False
  }
  r = s.post(host + url1, json=payload)
  login_data = r.json()['data']
  if login_data!=None:
    name = login_data['realname'].encode('utf-8')
    token = login_data['token']
    s.cookies.set(
      'realname-student-zjedu',
      "%22" + urllib.quote(name) + "%22",
      domain='zjedu.moocollege.com',
      path='/')
    s.cookies.set(
      'token-student-zjedu',
      "%22" + urllib.quote(token) + "%22",
      domain='zjedu.moocollege.com',
      path='/')
    s.cookies.set(
      'avatar-student-zjedu', 'null', domain='zjedu.moocollege.com', path='/')
    return True
  else:
    return False

#获取列表
def get_list(course_id):
  url1 = "/nodeapi/3.0.1/student/system/checkLogin"
  r = s.post(host + url1)
  url2 = "/nodeapi/3.0.1/student/course/getDetail"
  r = s.post(host + url2, json={"id": course_id})
  #获取未看列表
  url3 = "/nodeapi/3.0.1/student/course/plan/list"
  r = s.post(host + url3, json={"courseId": course_id})
  avaliable_plan = r.json()
  unwatched_unit = []
  for chapter_data in avaliable_plan['data']:
    for section_data in chapter_data['data']:
      for unit_data in section_data['data']:
        if unit_data['status'] != 2:
          unwatched_unit.append({
            'unit_id': unit_data['unitId'],
            'type': unit_data['type']
          })
  return unwatched_unit

#上传进度
def upload_rate(unit_id, time, course_id="30002903"):
  url1 = "/nodeapi/3.0.1/student/course/uploadLearnRate"
  r = s.post(
    host + url1,
    json={"unitId": unit_id,
          "courseId": course_id,
          "playPosition": time})
  if r.json()['code'] != 20000:
    return False
  else:
    return True


def watch_video(unit_id):
  global video_count
  global course_id
  # 获取一些id
  url1 = "/nodeapi/3.0.1/teacher/course/plan/unit/getDetail"
  r = s.post(host + url1, {"unitId": unit_id})
  video_id = r.json()['data']['data']['videoId']
  courseware_id = r.json()['data']['data']['coursewareId']

  # 获取题目列表
  url2 = '/nodeapi/3.0.1/student/course/plan/getVideoTest'
  r = s.post(host + url2, json={"coursewareId": courseware_id})
  test_data = r.json()['data']
  if test_data['testList'] != []:
      video_test_time = test_data['testList']
      question_id = {}
      for i in video_test_time:
          question_id[str(i)] = test_data['qsData'][str(i)][0]['id']
  else:
      video_test_time = []
  print video_test_time

  # 获取视频地址
  url3 = "/nodeapi/3.0.1/common/ccPlayer/getInfo"
  r = s.post(host + url3, json={"id": video_id})
  video_source = r.json()['data']['sources'][1]
  # 获取视频
  # s.get(video_source)
  url4 = "/nodeapi/3.0.1/student/course/plan/videoTestBatch"

  # 下面开始传看视频的进度
  print "正在看第" + str(video_count) + "个视频"
  ctime = 0
  flag = upload_rate(unit_id, ctime,course_id)
  upload_rate(unit_id, ctime,course_id)
  pointer = 0
  # 检查是否有题目
  if video_test_time != []:
      # 有题目
      # 检查是否合法
      while flag:
          # 判断下个20s是否有题目
          if int(video_test_time[pointer])>ctime and int(video_test_time[pointer]) <= ctime + 20:
              #答题
              time.sleep(int(video_test_time[pointer])-ctime)

              s.post(host + url4,json={
                      "coursewareId": courseware_id,
                      "questionId": question_id[video_test_time[pointer]]})
              print "第" + video_test_time[pointer] + "s答题"
              #发答题时刻进度
              flag = upload_rate(unit_id, video_test_time[pointer],course_id)
              upload_rate(unit_id, video_test_time[pointer],course_id)
              #发例行进度
              time.sleep(ctime + 20 - int(video_test_time[pointer]))
              ctime += 20
              flag = upload_rate(unit_id, ctime,course_id)
              upload_rate(unit_id, ctime,course_id)
              pointer+=1 if pointer<(len(video_test_time)-1) else 0
          else:
              time.sleep(20)
              ctime += 20
              flag = upload_rate(unit_id, ctime,course_id)
              upload_rate(unit_id, ctime,course_id)
          print "已看" + str('%02d'%(ctime/60))+':'+str('%02d'%(ctime%60))+' or '+str(ctime)+'秒'
  else:
      # 无题目
      while flag:
          time.sleep(20)
          ctime += 20
          flag = upload_rate(unit_id, ctime,course_id)
          upload_rate(unit_id, ctime,course_id)
          print "已看" + str('%02d'%(ctime/60))+':'+str('%02d'%(ctime
          %60))+' or '+str(ctime)+'秒'
  flag=True
  ctime-=20
  while flag:
      ctime += 1
      flag = upload_rate(unit_id, ctime,course_id)
  print "超时，回退至第" + str(ctime) + "s"
  upload_rate(unit_id, ctime,course_id)
  video_count += 1

def watch_pdf(unit_id):
  global pdf_count
  global course_id
  # 获取一些id
  url1 = "/nodeapi/3.0.1/teacher/course/plan/unit/getDetail"
  r = s.post(host + url1, {"unitId": unit_id})
  file_url = r.json()['data']['data']['fileUrl']
  # 获取文件地址
  url2 = "/nodeapi/3.0.1/common/access/getAccessUrl"
  r = s.post(host + url2, json={"name": file_url, "inline": True})
  url3 = r.json()['data']
  # 获取文件
  print "已看第" + str(pdf_count) + "个pdf"
  # 上传进度
  upload_rate(unit_id, 0,course_id)
  pdf_count += 1

def watch(i):
  global video_count
  global pdf_count
  if i['type'] == 1:
    watch_video(i['unit_id'])
    video_count+=1
  elif i['type'] == 3:
    watch_pdf(i['unit_id'])
    pdf_count+=1

if __name__ == '__main__':
  #初始化session
  s = requests.Session()
  s.headers = {
    'Accept-Encoding':
    'gzip, deflate',
    'Accept-Language':
    'zh-Hans-CN,zh-Hans;q=0.8,en-GB;q=0.5,en;q=0.3',
    'User-Agent':
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
    'Connection':
    'keep-alive',
    'Host':
    'student.zjedu.moocollege.com',
    'Origin':
    'http://student.zjedu.moocollege.com'
  }
  r = s.get(host)
  host = "http://student.zjedu.moocollege.com"
  video_count = 1
  pdf_count = 1
  
  s_time=time.time()
  course_id='30002903' #课程id号，抓包可得
  userlist=[]
  with open('users.json','r') as f:
    userlist=json.load(f)
  for i in userlist:
    username=i['username']
    password=i['password']
    print 'now:'+username
    if login(username,password):
      print '登陆成功'
    else:
      print '登陆失败'
    unwatched_unit = get_list(course_id)
    pool_num=len(unwatched_unit)
    if pool_num>0:
      pool = Pool(pool_num)
      res = pool.map(watch, unwatched_unit)
      pool.close()
      pool.join()
    e_time=time.time()
    print 'done！耗时'+ str('%.2f'%(e_time-s_time))+'s'
    time.sleep(random.randint(10,30))
