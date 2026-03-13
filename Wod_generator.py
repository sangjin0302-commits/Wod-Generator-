import streamlit as st
import anthropic
import json
import random

st.set_page_config(page_title="WOD Generator", page_icon="🏋️", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;600&display=swap');
.stApp { background-color: #070d1a; }
h1 { font-family: 'Bebas Neue', monospace; color: #ef4444 !important; font-size: 3rem; letter-spacing: 0.1em; }
</style>
""", unsafe_allow_html=True)

MOVEMENTS = {
    "squat":     {"label":"스쿼트",     "levels":["Overhead Squat","Front Squat","Back Squat","Air Squat"],               "muscles":["대퇴사두","둔근","햄스트링"],  "weights":{"M":[95,75,95,None],      "F":[65,55,65,None]}},
    "press":     {"label":"프레스",     "levels":["Push Jerk","Push Press","Shoulder Press"],                             "muscles":["어깨","삼두"],                 "weights":{"M":[135,95,75],          "F":[95,65,55]}},
    "deadlift":  {"label":"데드리프트", "levels":["Deadlift","Sumo Deadlift High Pull","Medicine-Ball Clean"],            "muscles":["햄스트링","둔근","허리"],      "weights":{"M":[225,75,20],          "F":[155,55,14]}},
    "situp":     {"label":"싯업",       "levels":["GHD Sit-up","AB Mat Sit-up"],                                         "muscles":["복근","고관절굴근"],           "weights":{"M":[None,None],          "F":[None,None]}},
    "pushup":    {"label":"푸시업",     "levels":["Ring Dip","Push-up","Knee Push-up"],                                   "muscles":["가슴","어깨","삼두"],          "weights":{"M":[None,None,None],     "F":[None,None,None]}},
    "boxjump":   {"label":"박스점프",   "levels":['Burpee Box Jump Over (48/40")','Burpee Box Jump (24/20")','Box Jump','Box Step-up'], "muscles":["대퇴사두","둔근","종아리"], "weights":{"M":[None,None,None,None],"F":[None,None,None,None]}},
    "burpee":    {"label":"버피",       "levels":["Bar Touch Burpee","Burpee"],                                           "muscles":["전신","어깨","가슴"],          "weights":{"M":[None,None],          "F":[None,None]}},
    "handstand": {"label":"핸드스탠드", "levels":["Handstand Walk","Handstand Push-up","Pike Push-up"],                   "muscles":["어깨","삼두"],                 "weights":{"M":[None,None,None],     "F":[None,None,None]}},
    "gymnastic": {"label":"체조",       "levels":["Ring Muscle-up","Bar Muscle-up","Chest to Bar","Pull-up","Ring Row"],  "muscles":["광배근","이두"],               "weights":{"M":[None,None,None,None,None],"F":[None,None,None,None,None]}},
    "t2b":       {"label":"T2B",        "levels":["Toes to Bar","Knees to Elbow","Hanging Knee Raise"],                   "muscles":["복근","광배근","고관절굴근"],   "weights":{"M":[None,None,None],     "F":[None,None,None]}},
    "clean":     {"label":"클린",       "levels":["Clean & Jerk","Squat Clean","Power Clean","Hang Power Clean"],         "muscles":["전신","대퇴사두","승모근"],     "weights":{"M":[185,155,135,115],    "F":[125,105,95,75]}},
    "lunge":     {"label":"런지",       "levels":["Overhead Walking Lunge","DB Front-rack Lunge","Lunge"],                "muscles":["대퇴사두","둔근","햄스트링"],   "weights":{"M":[45,50,None],         "F":[25,35,None]}},
    "snatch":    {"label":"스내치",     "levels":["Squat Snatch","Power Snatch","Hang Power Snatch"],                     "muscles":["전신","어깨","승모근"],         "weights":{"M":[135,115,95],         "F":[95,75,65]}},
    "thruster":  {"label":"스러스터",   "levels":["Thruster","DB Thruster"],                                              "muscles":["대퇴사두","어깨","둔근"],       "weights":{"M":[95,50],              "F":[65,35]}},
    "wallball":  {"label":"월볼",       "levels":["Wall Ball (20/14 lb)","Wall Ball (14/10 lb)"],                         "muscles":["대퇴사두","어깨","둔근"],       "weights":{"M":[20,14],              "F":[14,10]}},
    "kettlebell":{"label":"케틀벨",     "levels":["AKBS (American KB Swing)","RKBS (Russian KB Swing)"],                  "muscles":["둔근","햄스트링","어깨"],       "weights":{"M":[53,53],              "F":[35,35]}},
    "ropeclimb": {"label":"로프클라임", "levels":["Rope Climb (15 ft)","Rope Climb (10 ft)","Rope Pull (lying)"],         "muscles":["광배근","이두","코어"],         "weights":{"M":[None,None,None],     "F":[None,None,None]}},
    "run":       {"label":"달리기",     "levels":["Run 400m","Run 200m","Run 100m"],                                      "muscles":["종아리","햄스트링","전신"],     "weights":{"M":[None,None,None],     "F":[None,None,None]}},
    "row":       {"label":"로잉",       "levels":["Rowing 500m","Rowing 250m"],                                           "muscles":["광배근","햄스트링","전신"],     "weights":{"M":[None,None],          "F":[None,None]}},
    "bike":      {"label":"바이크",     "levels":["Bike 1000m","Bike 500m"],                                              "muscles":["대퇴사두","종아리","전신"],     "weights":{"M":[None,None],          "F":[None,None]}},
}

LEVEL_INDEX = {"RXD": 0, "A": 1, "B": 2, "C": 3}
WOD_TYPES = ["For Time", "AMRAP", "EMOM", "Death by", "For Load", "Tabata", "네임드 와드"]
LEVELS = ["RXD", "A", "B", "C"]
TIME_OPTIONS = [10, 15, 20, 30]
ROUNDS_OPT = [3, 4, 5, 6, 7]
BODY_REGIONS = ["상체", "코어", "하체", "전신"]

RAW_WODS = [
# GIRLS
["Amanda","Girls","For Time","9-7-5",None,"크로스핏 대표 벤치마크","9-7-5 For Time\nSquat Snatches (135/95 lb)\nRing Muscle-ups",[["Squat Snatch",["전신","어깨","승모근"],9,135,95],["Ring Muscle-up",["광배근","이두","가슴"],9,None,None]],"최고난도. 스내치+링머슬업. 목표 8~15분."],
["Angie","Girls","For Time",None,None,"크로스핏 최초 벤치마크 (2003)","For Time\n100 Pull-ups\n100 Push-ups\n100 Sit-ups\n100 Air Squats",[["Pull-up",["광배근","이두"],100,None,None],["Push-up",["가슴","어깨","삼두"],100,None,None],["Sit-up",["복근","고관절굴근"],100,None,None],["Air Squat",["대퇴사두","둔근"],100,None,None]],"총 400회 바디웨이트. 목표 15~25분."],
["Annie","Girls","For Time","50-40-30-20-10",None,"크로스핏 대표 벤치마크","50-40-30-20-10 For Time\nDouble Unders\nSit-ups",[["Double Under",["종아리","전신"],50,None,None],["AB Mat Sit-up",["복근","고관절굴근"],50,None,None]],"줄넘기+싯업 점감. 총 150+150회. 목표 10분 이내."],
["Barbara","Girls","For Time",5,None,"크로스핏 최초 벤치마크 (2003)","5 Rounds For Time\n20 Pull-ups / 30 Push-ups / 40 Sit-ups / 50 Air Squats",[["Pull-up",["광배근","이두"],20,None,None],["Push-up",["가슴","어깨","삼두"],30,None,None],["Sit-up",["복근","고관절굴근"],40,None,None],["Air Squat",["대퇴사두","둔근"],50,None,None]],"라운드 사이 3분 휴식. 총 700회. 목표 20~30분(휴식 제외)."],
["Badger","Girls","For Time",3,None,"크로스핏 대표 벤치마크","3 Rounds For Time\n30 Squat Cleans (95/65 lb)\n30 Pull-ups\n800m Run",[["Squat Clean",["전신","대퇴사두","승모근"],30,95,65],["Pull-up",["광배근","이두"],30,None,None],["Run 400m",["종아리","햄스트링","전신"],None,None,None]],"총 90 클린+90 풀업+2.4km 달리기. 40~60분 소요."],
["Chelsea","Girls","EMOM",None,30,"크로스핏 최초 벤치마크 (2003)","EMOM 30 Minutes\n5 Pull-ups / 10 Push-ups / 15 Air Squats",[["Pull-up",["광배근","이두"],5,None,None],["Push-up",["가슴","어깨","삼두"],10,None,None],["Air Squat",["대퇴사두","둔근"],15,None,None]],"30분 EMOM. Cindy와 동일 동작이지만 시간 강제."],
["Cindy","Girls","AMRAP",None,20,"크로스핏 대표 벤치마크","20 min AMRAP\n5 Pull-ups / 10 Push-ups / 15 Air Squats",[["Pull-up",["광배근","이두"],5,None,None],["Push-up",["가슴","어깨","삼두"],10,None,None],["Air Squat",["대퇴사두","둔근"],15,None,None]],"Good: 남 20R+, 여 15R+."],
["Diane","Girls","For Time","21-15-9",None,"크로스핏 대표 벤치마크","21-15-9 For Time\nDeadlifts (225/155 lb)\nHandstand Push-ups",[["Deadlift",["햄스트링","둔근","허리"],21,225,155],["Handstand Push-up",["어깨","삼두"],21,None,None]],"데드리프트+HSPU. 목표 5~8분."],
["Elizabeth","Girls","For Time","21-15-9",None,"크로스핏 대표 벤치마크 (2003)","21-15-9 For Time\nSquat Cleans (135/95 lb)\nRing Dips",[["Squat Clean",["전신","대퇴사두","승모근"],21,135,95],["Ring Dip",["가슴","어깨","삼두"],21,None,None]],"클린+링딥. 목표 7~12분."],
["Eva","Girls","For Time",5,None,"크로스핏 대표 벤치마크","5 Rounds For Time\n800m Run\n30 KB Swings (70/53 lb)\n30 Pull-ups",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],30,70,53],["Pull-up",["광배근","이두"],30,None,None]],"총 4km 달리기+150 KB+150 풀업. 60~90분 소요."],
["Fran","Girls","For Time","21-15-9",None,"크로스핏 대표 벤치마크","21-15-9 For Time\nThrusters (95/65 lb)\nPull-ups",[["Thruster",["대퇴사두","어깨","둔근"],21,95,65],["Pull-up",["광배근","이두"],21,None,None]],"크로스핏 대표 벤치마크. 엘리트 2분대, 일반 5~10분."],
["Grace","Girls","For Time",None,None,"크로스핏 대표 벤치마크","For Time\n30 Clean & Jerks (135/95 lb)",[["Clean & Jerk",["전신","어깨","대퇴사두"],30,135,95]],"단일 올림픽 리프팅 30회. 엘리트 1~2분대."],
["Gwen","Girls","For Load",None,None,"크로스핏 대표 벤치마크","For Load (15-10-5)\nClean & Jerks (Touch-and-Go)",[["Clean & Jerk",["전신","어깨","대퇴사두"],15,135,95]],"15-10-5 터치앤고 클린앤저크. 각 세트 최대 중량으로 진행."],
["Helen","Girls","For Time",3,None,"크로스핏 대표 벤치마크","3 Rounds For Time\n400m Run\n21 KB Swings (53/35 lb)\n12 Pull-ups",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],21,53,35],["Pull-up",["광배근","이두"],12,None,None]],"달리기→KB→풀업 교차. 목표 9~12분."],
["Isabel","Girls","For Time",None,None,"크로스핏 대표 벤치마크","For Time\n30 Snatches (135/95 lb)",[["Power Snatch",["전신","어깨","승모근"],30,135,95]],"Grace의 스내치 버전. 목표 2~5분."],
["Jackie","Girls","For Time",None,None,"크로스핏 대표 벤치마크","For Time\n1000m Row\n50 Thrusters (45/35 lb)\n30 Pull-ups",[["Rowing 500m",["광배근","햄스트링","전신"],None,None,None],["Thruster",["대퇴사두","어깨","둔근"],50,45,35],["Pull-up",["광배근","이두"],30,None,None]],"로잉→스러스터→풀업. 목표 10~15분."],
["Karen","Girls","For Time",None,None,"크로스핏 대표 벤치마크","For Time\n150 Wall Ball Shots (20/14 lb)",[["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],150,20,14]],"단일 월볼 150회. 목표 8~15분."],
["Kelly","Girls","For Time",5,None,"크로스핏 대표 벤치마크","5 Rounds For Time\n400m Run\n30 Box Jumps (24/20 in)\n30 Wall Ball Shots (20/14 lb)",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Box Jump",["대퇴사두","둔근","종아리"],30,None,None],["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],30,20,14]],"하체 지구력 극한. 목표 35~50분."],
["Linda","Girls","For Time","10-9-8-7-6-5-4-3-2-1",None,"크로스핏 '3 Bars of Death'","10-9-8-7-6-5-4-3-2-1 For Time\nDeadlifts / Bench Press / Cleans",[["Deadlift",["햄스트링","둔근","허리"],10,225,155],["Bench Press",["가슴","어깨","삼두"],10,175,115],["Power Clean",["전신","대퇴사두","승모근"],10,135,95]],"체중 기준 3바벨. 총 165회. 목표 20~30분."],
["Lynne","Girls","For Load",5,None,"크로스핏 대표 벤치마크","5 Rounds Max Reps\nBench Press (body weight)\nPull-ups",[["Bench Press",["가슴","어깨","삼두"],None,None,None],["Pull-up",["광배근","이두"],None,None,None]],"5라운드 최대랩. 벤치프레스+풀업 총합이 점수."],
["Mary","Girls","AMRAP",None,20,"크로스핏 대표 벤치마크","20 min AMRAP\n5 Handstand Push-ups\n10 Pistol Squats\n15 Pull-ups",[["Handstand Push-up",["어깨","삼두"],5,None,None],["Pistol Squat",["대퇴사두","둔근","코어"],10,None,None],["Pull-up",["광배근","이두"],15,None,None]],"고난도 체조 AMRAP. Good: 10R+."],
["Nancy","Girls","For Time",5,None,"크로스핏 대표 벤치마크","5 Rounds For Time\n400m Run\n15 Overhead Squats (95/65 lb)",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Overhead Squat",["대퇴사두","어깨","코어"],15,95,65]],"심폐 소진 후 OHS 기술. 목표 15~20분."],
["Nicole","Girls","AMRAP",None,20,"크로스핏 대표 벤치마크","20 min AMRAP\n400m Run\nMax Pull-ups",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Pull-up",["광배근","이두"],None,None,None]],"달리기 후 풀업 최대랩. 총 달리기×풀업 합계가 점수."],
["Nasty Girls","Girls","For Time",3,None,"크로스핏 대표 벤치마크","3 Rounds For Time\n50 Air Squats\n7 Ring Muscle-ups\n10 Hang Power Cleans (135/95 lb)",[["Air Squat",["대퇴사두","둔근"],50,None,None],["Ring Muscle-up",["광배근","이두","가슴"],7,None,None],["Hang Power Clean",["전신","승모근"],10,135,95]],"스쿼트+머슬업+클린 3라운드. 목표 15~25분."],
["Ingrid","Girls","For Time",3,None,"크로스핏 대표 벤치마크","3 Rounds For Time\n30 KB Swings (53/35)\n20 OHS (45/35)\n10 L-Pull-ups",[["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],30,53,35],["Overhead Squat",["대퇴사두","어깨","코어"],20,45,35],["Pull-up",["광배근","이두"],10,None,None]],"KB+OHS+L풀업 3라운드. 코어 안정성 집중."],
["Kalsu","Girls","For Time",None,None,"크로스핏 대표 벤치마크 (영웅 와드 경계)","For Time\n100 Thrusters (135/95 lb)\nEvery minute: 5 Burpees",[["Thruster",["대퇴사두","어깨","둔근"],100,135,95],["Burpee",["전신","가슴"],5,None,None]],"매 분 버피 5개. 역대 최악 와드 중 하나."],
["Wittman","Girls","For Time",7,None,"크로스핏 대표 벤치마크","7 Rounds For Time\n15 KB Swings (53/35)\n15 Power Cleans (95/65)\n15 Box Jumps (24/20)",[["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],15,53,35],["Power Clean",["전신","대퇴사두","승모근"],15,95,65],["Box Jump",["대퇴사두","둔근","종아리"],15,None,None]],"3종 × 7라운드. 총 315회. 목표 30~45분."],
# HERO
["Arnie","Hero","For Time",None,None,"Cpl. Jesse A. Ainsworth 추모","For Time\n21 Turkish Get-ups / 50 KB Swings / 21 OHS\n50 Pull-ups / 21 Thruster / 50 Sit-ups / 21 Ring Dips",[["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],50,53,35],["Overhead Squat",["대퇴사두","어깨","코어"],21,95,65],["Pull-up",["광배근","이두"],50,None,None],["Thruster",["대퇴사두","어깨","둔근"],21,95,65],["AB Mat Sit-up",["복근","고관절굴근"],50,None,None],["Ring Dip",["가슴","어깨","삼두"],21,None,None]],"다종목 Hero WOD. 60분+ 소요."],
["Badger","Hero","For Time",3,None,"Chief Petty Officer Mark Carter 추모 (2009, 이라크)","3 Rounds For Time\n30 Squat Cleans (95/65)\n30 Pull-ups\n800m Run",[["Squat Clean",["전신","대퇴사두","승모근"],30,95,65],["Pull-up",["광배근","이두"],30,None,None],["Run 400m",["종아리","햄스트링","전신"],None,None,None]],"총 90 클린+90 풀업+2.4km 달리기. 40~60분."],
["Boat","Hero","For Time",None,None,"Chief Warrant Officer 2 Brian J. Luce 추모","For Time\n1000m Row\n50 HSPU\n1000m Row\n50 HSPU",[["Rowing 500m",["광배근","햄스트링","전신"],None,None,None],["Handstand Push-up",["어깨","삼두"],50,None,None]],"로잉+HSPU 2세트. 어깨 극한 테스트."],
["Bull","Hero","For Time",3,None,"Sgt. James D. Bull 추모 (2006, 이라크)","3 Rounds For Time\n20 Box Jumps (24/20)\n20 KB Swings (53/35)\n20 Pull-ups",[["Box Jump",["대퇴사두","둔근","종아리"],20,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],20,53,35],["Pull-up",["광배근","이두"],20,None,None]],"박스점프+KB+풀업 3라운드. 목표 15~22분."],
["Caesar","Hero","For Time",None,None,"Sgt. 1st Class Ramon E. Caesar Jr. 추모 (2008, 아프가니스탄)","For Time\n6 Rounds: 6 DL / 7 HPC / 8 Thruster / 10 T2B",[["Deadlift",["햄스트링","둔근","허리"],6,225,155],["Hang Power Clean",["전신","승모근"],7,135,95],["Thruster",["대퇴사두","어깨","둔근"],8,95,65],["Toes to Bar",["복근","광배근","고관절굴근"],10,None,None]],"4종 동작 6라운드 바벨 집중 Hero WOD."],
["Chad","Hero","For Load",None,None,"Navy SEAL Chad Wilkinson 추모","For Time\n1,000 Box Step-ups (45 lb ruck, 20 in box)",[["Box Step-up",["대퇴사두","둔근","햄스트링"],1000,None,None]],"1,000회 스텝업. 45lb 배낭. 역대 가장 긴 Hero WOD. 4~8시간 소요."],
["Danny","Hero","AMRAP",None,20,"Sgt. Daniel J. Crabtree 추모 (2006, 이라크)","20 min AMRAP\n30 Box Jumps (24/20)\n20 Push Press (115/75)\n10 Pull-ups",[["Box Jump",["대퇴사두","둔근","종아리"],30,None,None],["Push Press",["어깨","삼두"],20,115,75],["Pull-up",["광배근","이두"],10,None,None]],"3종 AMRAP. Good: 8라운드+."],
["DT","Hero","For Time",5,None,"USAF Staff Sgt. Timothy P. Davis 추모 (2009, 아프가니스탄)","5 Rounds For Time\n12 Deadlifts (155/105)\n9 Hang Power Cleans (155/105)\n6 Push Jerks (155/105)",[["Deadlift",["햄스트링","둔근","허리"],12,155,105],["Hang Power Clean",["전신","승모근"],9,155,105],["Push Jerk",["어깨","삼두"],6,155,105]],"바벨 내려놓지 않는 콤플렉스. 그립 지구력 테스트."],
["Glen","Hero","For Time",None,None,"Army Staff Sgt. Glenn Watkins 추모","For Time\n30 C&J (205/145) / 1mile run / 10 Rope Climbs\n1mile run / 30 C&J",[["Clean & Jerk",["전신","어깨","대퇴사두"],30,205,145],["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Rope Climb (15 ft)",["광배근","이두","코어"],10,None,None]],"초고중량 클린앤저크+달리기+로프클라임. 극한 난이도."],
["Griff","Hero","For Time",None,None,"Sgt. Joshua P. Haifley 추모 (2009, 이라크)","For Time\n800m Run / 400m Run (backward)\n800m Run / 400m Run (backward)",[["Run 400m",["종아리","햄스트링","전신"],None,None,None]],"전진+후진 달리기 반복. 총 2.4km."],
["Hansen","Hero","For Time",5,None,"Chief Petty Officer Stephen Bass 추모","5 Rounds For Time\n30 KB Swings (53/35)\n30 Burpees\n30 GHD Sit-ups",[["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],30,53,35],["Burpee",["전신","가슴"],30,None,None],["GHD Sit-up",["복근","고관절굴근"],30,None,None]],"총 450회. 코어+전신 지구력 극한. 50~70분 소요."],
["Hollywood","Hero","For Time",6,None,"Lt. Col. Marc Stratton 추모 (2008, 이라크)","6 Rounds For Time\n25 Air Squats / 7 Ring Dips / 35 Sit-ups",[["Air Squat",["대퇴사두","둔근"],25,None,None],["Ring Dip",["가슴","어깨","삼두"],7,None,None],["AB Mat Sit-up",["복근","고관절굴근"],35,None,None]],"총 150 스쿼트+42 링딥+210 싯업. 목표 25~35분."],
["Jack","Hero","AMRAP",None,20,"Staff Sgt. Jack Martin III 추모 (2009, 아프가니스탄)","20 min AMRAP\n10 Push Press (115/85)\n10 KB Swings (53/35)\n10 Box Jumps (24/20)",[["Push Press",["어깨","삼두"],10,115,85],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],10,53,35],["Box Jump",["대퇴사두","둔근","종아리"],10,None,None]],"접근하기 쉬운 Hero WOD. Good: 20R+."],
["JT","Hero","For Time",None,None,"Petty Officer 1st Class Jeff Taylor 추모 (2006, 아프가니스탄)","For Time\n21-15-9\nHandstand Push-ups / Ring Dips / Push-ups",[["Handstand Push-up",["어깨","삼두"],21,None,None],["Ring Dip",["가슴","어깨","삼두"],21,None,None],["Push-up",["가슴","어깨","삼두"],21,None,None]],"21-15-9 상체 밀기 3종. 어깨+삼두 극한. 목표 15~25분."],
["Josh","Hero","For Time",None,None,"Staff Sgt. Joshua Hager 추모 (2007, 이라크)","For Time\n21 OHS / 42 Pull-ups\n15 OHS / 30 Pull-ups\n9 OHS / 18 Pull-ups",[["Overhead Squat",["대퇴사두","어깨","코어"],21,95,65],["Pull-up",["광배근","이두"],42,None,None]],"OHS+풀업 21-42/15-30/9-18 구조. 어깨 안정성 극한."],
["Kalsu","Hero","For Time",None,None,"1st Lt. Robert James Kalsu 추모 (1970, 베트남)","For Time\n100 Thrusters (135/95)\n+ Every minute: 5 Burpees",[["Thruster",["대퇴사두","어깨","둔근"],100,135,95],["Burpee",["전신","가슴"],5,None,None]],"매 분 버피 5개 강제. 역대 최악의 와드. 60분+ 소요."],
["Keeler","Hero","For Time",None,None,"SSgt. Michael J. Kelley 추모","For Time\n5 Rounds:\n20 Pull-ups / 20 KB Swings / 20 Box Jumps / 20 DU",[["Pull-up",["광배근","이두"],20,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],20,53,35],["Box Jump",["대퇴사두","둔근","종아리"],20,None,None],["Double Under",["종아리","전신"],20,None,None]],"4종 × 5라운드. 목표 25~40분."],
["Klepto","Hero","For Time",None,None,"Petty Officer 2nd Class David Robert Toshimitsu 추모","5 Rounds For Time\n10 Pull-ups / 15 KB Swings / 20 Box Jumps",[["Pull-up",["광배근","이두"],10,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],15,53,35],["Box Jump",["대퇴사두","둔근","종아리"],20,None,None]],"3종 5라운드. 목표 18~28분."],
["Luce","Hero","AMRAP",None,20,"Chief Warrant Officer 2 Brian J. Luce 추모 (2009, 아프가니스탄)","20 min AMRAP\n6 Burpees / 10 Thrusters (45/35) / 24 DU",[["Burpee",["전신","가슴"],6,None,None],["Thruster",["대퇴사두","어깨","둔근"],10,45,35],["Double Under",["종아리","전신"],24,None,None]],"3종 20분 AMRAP. 접근하기 쉬운 Hero WOD."],
["Loredo","Hero","For Time",6,None,"Staff Sgt. Edwardo Loredo 추모 (2010, 아프가니스탄)","6 Rounds For Time\n24 Air Squats / 24 Push-ups / 24 Walking Lunges / 400m Run",[["Air Squat",["대퇴사두","둔근"],24,None,None],["Push-up",["가슴","어깨","삼두"],24,None,None],["Walking Lunge",["대퇴사두","둔근","햄스트링"],24,None,None],["Run 400m",["종아리","햄스트링","전신"],None,None,None]],"총 432회 바디웨이트+2.4km 달리기. 목표 25~40분."],
["Lumberjack 20","Hero","For Time",None,None,"포트후드 테러 희생 크로스피터 4인 추모 (2009)","For Time\n20 DL / 400m / 20 KBS / 400m / 20 OHS / 400m\n20 Burpees / 400m / 20 C2B / 400m / 20 BJ / 400m / 20 DB SC / 400m",[["Deadlift",["햄스트링","둔근","허리"],20,275,185],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],20,70,53],["Overhead Squat",["대퇴사두","어깨","코어"],20,115,80],["Burpee",["전신","가슴"],20,None,None],["Chest to Bar",["광배근","이두"],20,None,None],["Box Jump",["대퇴사두","둔근","종아리"],20,None,None]],"7종 × 20회 + 각 400m 달리기. 40~60분 소요."],
["Manion","Hero","For Time",7,None,"1st Lt. Travis Manion 추모 (2007, 이라크)","7 Rounds For Time\n400m Run\n29 Back Squats (135/95)",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Back Squat",["대퇴사두","둔근","햄스트링"],29,135,95]],"7라운드=7월, 29=29세. 총 203 스쿼트+2.8km 달리기."],
["McGhee","Hero","AMRAP",None,30,"Cpl. Ryan C. McGhee 추모 (2009, 이라크)","30 min AMRAP\n5 Deadlifts (275/185)\n13 Push-ups\n9 Box Jumps (24/20)",[["Deadlift",["햄스트링","둔근","허리"],5,275,185],["Push-up",["가슴","어깨","삼두"],13,None,None],["Box Jump",["대퇴사두","둔근","종아리"],9,None,None]],"30분 AMRAP. 중량 DL 관건. Good: 12R+."],
["Michael","Hero","For Time",3,None,"Navy Lt. Michael McGreevy 추모 (2005, 아프가니스탄)","3 Rounds For Time\n800m Run / 50 Back Extensions / 50 Sit-ups",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Back Extension",["허리","둔근","햄스트링"],50,None,None],["AB Mat Sit-up",["복근","고관절굴근"],50,None,None]],"달리기+백익스텐션+싯업. 코어 전·후면 균형."],
["Millan","Hero","For Time",4,None,"Sgt. Jason D. Millan 추모 (2007, 이라크)","4 Rounds For Time\n20 Thrusters / 20 Pull-ups / 20 KB Swings / 20 Sit-ups / 400m Run",[["Thruster",["대퇴사두","어깨","둔근"],20,45,35],["Pull-up",["광배근","이두"],20,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],20,35,26],["AB Mat Sit-up",["복근","고관절굴근"],20,None,None],["Run 400m",["종아리","햄스트링","전신"],None,None,None]],"5종 4라운드. 목표 30~45분."],
["Mr. Joshua","Hero","For Time",5,None,"SO1 Joshua Thomas Harris 추모 (2008, 아프가니스탄)","5 Rounds For Time\n400m Run / 30 GHD Sit-ups / 15 Deadlifts (250/175)",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["GHD Sit-up",["복근","고관절굴근"],30,None,None],["Deadlift",["햄스트링","둔근","허리"],15,250,175]],"달리기+GHD+DL. 후면사슬·코어·심폐 고볼륨."],
["Murph","Hero","For Time",None,None,"Lt. Michael P. Murphy 추모 (2005, 아프가니스탄)","For Time (20/14 lb Vest)\n1 Mile Run / 100 Pull-ups / 200 Push-ups / 300 Air Squats / 1 Mile Run",[["Run (1 mile)",["전신","종아리"],None,None,None],["Pull-up",["광배근","이두"],100,None,None],["Push-up",["가슴","어깨","삼두"],200,None,None],["Air Squat",["대퇴사두","둔근"],300,None,None]],"Navy SEAL Murphy의 'Body Armor' WOD. 600 바디웨이트+2마일."],
["Nate","Hero","AMRAP",None,20,"Navy SEAL Chief Nate Hardy 추모 (2008, 이라크)","20 min AMRAP\n2 Ring Muscle-ups / 4 Handstand Push-ups / 8 KB Swings (70/53)",[["Ring Muscle-up",["광배근","이두","가슴"],2,None,None],["Handstand Push-up",["어깨","삼두"],4,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],8,70,53]],"고기술 AMRAP. 링머슬업이 관건. Good: 8R+."],
["Nick","Hero","For Time",None,None,"Cpl. Nicholas J. Xiarhos 추모 (2009, 아프가니스탄)","For Time\n10 Rounds:\n10 DB Push Press / 10 DB Box Step-ups / 1 Rope Climb (15 ft)",[["Push Press",["어깨","삼두"],10,80,50],["Box Step-up",["대퇴사두","둔근","햄스트링"],10,None,None],["Rope Climb (15 ft)",["광배근","이두","코어"],1,None,None]],"덤벨+스텝업+로프클라임 10라운드. 목표 25~40분."],
["OPT","Hero","For Time",None,None,"크로스핏 대표 Hero WOD (James FitzGerald 헌정)","For Time\n21-15-9\nClean (135/95) / Ring Dip",[["Squat Clean",["전신","대퇴사두","승모근"],21,135,95],["Ring Dip",["가슴","어깨","삼두"],21,None,None]],"21-15-9 클린+링딥. Elizabeth와 유사하지만 링딥 버전."],
["Oscar","Hero","For Time",None,None,"Sgt. 1st Class Oscar Vargas 추모 (2012)","For Time\n5 Rounds:\n5 Power Snatches (135/95) / 10 OHS (135/95) / 5 Bar Muscle-ups",[["Power Snatch",["전신","어깨","승모근"],5,135,95],["Overhead Squat",["대퇴사두","어깨","코어"],10,135,95],["Bar Muscle-up",["광배근","이두","가슴"],5,None,None]],"스내치+OHS+바머슬업. 고기술 Hero WOD. 목표 15~25분."],
["Pheezy","Hero","AMRAP",None,20,"USMC Sgt. Travis L. Pfister 추모 (2010, 아프가니스탄)","20 min AMRAP\n5 Ring Muscle-ups / 10 Thrusters (95/65) / 10 Toes-to-Bars",[["Ring Muscle-up",["광배근","이두","가슴"],5,None,None],["Thruster",["대퇴사두","어깨","둔근"],10,95,65],["Toes to Bar",["복근","광배근","고관절굴근"],10,None,None]],"머슬업+스러스터+T2B. 고강도 AMRAP."],
["Randy","Hero","For Time",None,None,"LAPD Officer Randy Simmons 추모 (2008)","For Time\n75 Power Snatches (75/55)",[["Power Snatch",["전신","어깨","승모근"],75,75,55]],"단일 동작 75회. 그립+어깨+후면사슬 지구력. 목표 5~10분."],
["Ryan","Hero","For Time",5,None,"Cpl. Ryan Reyes 추모 (2008, 아프가니스탄)","5 Rounds For Time\n7 Ring Muscle-ups / 21 Burpees",[["Ring Muscle-up",["광배근","이두","가슴"],7,None,None],["Burpee",["전신","가슴"],21,None,None]],"총 35 머슬업+105 버피. 전신 파워+심폐 극한."],
["Ship","Hero","For Time",None,None,"크로스핏 Hero WOD","For Time\n10 Rounds:\n10 Deadlifts (275/185) / 10 Burpee Box Jumps (24/20)",[["Deadlift",["햄스트링","둔근","허리"],10,275,185],["Burpee",["전신","가슴"],10,None,None]],"고중량 데드리프트+버피박스점프 10라운드."],
["Small","Hero","For Time",3,None,"Marine Gunnery Sgt. Aaron Kenefick 추모 (2009)","3 Rounds For Time\n3 Rope Climbs (15 ft) / 10 Thrusters (135/95) / 21 KB Swings (70/53)",[["Rope Climb (15 ft)",["광배근","이두","코어"],3,None,None],["Thruster",["대퇴사두","어깨","둔근"],10,135,95],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],21,70,53]],"로프클라임+스러스터+KB 3라운드. 목표 20~35분."],
["The Seven","Hero","For Time",7,None,"카우스트 기지 CIA 요원 7인 추모 (2009, 아프가니스탄)","7 Rounds For Time\n7 HSPU / 7 Thrusters / 7 KTE / 7 DL / 7 Burpees / 7 KBS / 7 Pull-ups",[["Handstand Push-up",["어깨","삼두"],7,None,None],["Thruster",["대퇴사두","어깨","둔근"],7,135,95],["Knees to Elbow",["복근","광배근"],7,None,None],["Deadlift",["햄스트링","둔근","허리"],7,245,165],["Burpee",["전신","가슴"],7,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],7,70,53],["Pull-up",["광배근","이두"],7,None,None]],"7×7×7×7. 전신 모든 패턴. 최난이도 Hero WOD."],
["Tommy V","Hero","For Time",None,None,"SO1 Thomas J. Valentine 추모 (2008)","For Time\n21 Thrusters (115/75) / 12 Rope Climbs\n15 Thrusters / 9 Rope Climbs\n9 Thrusters / 6 Rope Climbs",[["Thruster",["대퇴사두","어깨","둔근"],21,115,75],["Rope Climb (15 ft)",["광배근","이두","코어"],12,None,None]],"21-15-9 스러스터+12-9-6 로프클라임. 총 45+27회."],
["TJ","Hero","For Time",5,None,"Lance Cpl. T.J. Antuna 추모 (2004, 이라크)","5 Rounds For Time\n10 Hang Snatches (75/55) / 15 Push-ups / 20 Sit-ups / 25 Air Squats",[["Hang Power Snatch",["전신","어깨","승모근"],10,75,55],["Push-up",["가슴","어깨","삼두"],15,None,None],["AB Mat Sit-up",["복근","고관절굴근"],20,None,None],["Air Squat",["대퇴사두","둔근"],25,None,None]],"4종 5라운드. 목표 20~30분."],
["Tiffiny","Hero","For Time",5,None,"Marine SSgt. Tiffiny Kretz 추모 (2009)","5 Rounds For Time\n35 DB Deadlifts (35/25) / 25 Box Jumps (20 in) / 15 Push-ups",[["Deadlift",["햄스트링","둔근","허리"],35,70,50],["Box Jump",["대퇴사두","둔근","종아리"],25,None,None],["Push-up",["가슴","어깨","삼두"],15,None,None]],"DB 데드리프트+박스점프+푸시업 5라운드."],
["Tucker","Hero","AMRAP",None,25,"Army Ranger Scott Tucker 추모 (2008, 아프가니스탄)","25 min AMRAP\n10 DB Hammer Curl / 10 DB Tricep Extension / 200m Run",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Pull-up",["광배근","이두"],10,None,None],["Push-up",["가슴","어깨","삼두"],10,None,None]],"팔 집중 AMRAP+달리기."],
["Whitten","Hero","For Time",5,None,"Capt. Dan Whitten 추모 (2010, 아프가니스탄)","5 Rounds For Time\n22 KB Swings (1.5 pood) / 22 Box Jumps (24 in) / 400m Run",[["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],22,53,35],["Box Jump",["대퇴사두","둔근","종아리"],22,None,None],["Run 400m",["종아리","햄스트링","전신"],None,None,None]],"22=Whitten 부대 번호. 3종 5라운드. 목표 25~40분."],
["Wrath","Hero","AMRAP",None,20,"SSgt. Kevin Dupont 추모","20 min AMRAP\n10 Pull-ups / 10 Push-ups / 10 Sit-ups / 10 Squats",[["Pull-up",["광배근","이두"],10,None,None],["Push-up",["가슴","어깨","삼두"],10,None,None],["AB Mat Sit-up",["복근","고관절굴근"],10,None,None],["Air Squat",["대퇴사두","둔근"],10,None,None]],"4종 바디웨이트 AMRAP. 입문하기 쉬운 Hero WOD."],
["Zeus","Hero","For Time",None,None,"크로스핏 Hero WOD","For Time\n30 Wall Ball / 30 SDHP / 30 Box Jumps / 30 Push Press / 30 Row Cal",[["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],30,20,14],["Sumo Deadlift High Pull",["햄스트링","어깨","승모근"],30,75,55],["Box Jump",["대퇴사두","둔근","종아리"],30,None,None],["Push Press",["어깨","삼두"],30,75,55],["Rowing 500m",["광배근","햄스트링","전신"],None,None,None]],"5종 각 30회. CrossFit Filthy Fifty 간소화 버전."],
["Zembiec","Hero","For Time",4,None,"Maj. Douglas A. Zembiec 추모 (2007, 이라크)","4 Rounds For Time\n400m Run / 10 Deadlifts (225/155) / 50 Push-ups / 10 Pull-ups",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Deadlift",["햄스트링","둔근","허리"],10,225,155],["Push-up",["가슴","어깨","삼두"],50,None,None],["Pull-up",["광배근","이두"],10,None,None]],"달리기+DL+푸시업+풀업 4라운드."],
["Lodin","Hero","For Time",None,None,"Petty Officer 2nd Class Marc Lee 추모 (2006, 이라크)","For Time\n30 HSPU / 40 Pull-ups / 50 KB Swings / 60 Sit-ups / 70 Burpees",[["Handstand Push-up",["어깨","삼두"],30,None,None],["Pull-up",["광배근","이두"],40,None,None],["AKBS (American KB Swing)",["둔근","햄스트링","어깨"],50,53,35],["AB Mat Sit-up",["복근","고관절굴근"],60,None,None],["Burpee",["전신","가슴"],70,None,None]],"5종 점증 구조. 총 250회. 목표 30~50분."],
# OPEN
["11.1","Open","AMRAP",None,10,"CrossFit Open 2011 - WOD 1","10 min AMRAP\n30 Double Unders\n15 Power Snatches (75/55)",[["Double Under",["종아리","전신"],30,None,None],["Power Snatch",["전신","어깨","승모근"],15,75,55]],"오픈 역사 첫 번째 공식 WOD. Top 5%: 9R+."],
["11.2","Open","AMRAP",None,15,"CrossFit Open 2011 - WOD 2","15 min AMRAP\n9 DL (155/100) / 12 Push-ups / 15 Box Jumps (24/20)",[["Deadlift",["햄스트링","둔근","허리"],9,155,100],["Push-up",["가슴","어깨","삼두"],12,None,None],["Box Jump",["대퇴사두","둔근","종아리"],15,None,None]],"3종 15분 AMRAP."],
["11.3","Open","AMRAP",None,5,"CrossFit Open 2011 - WOD 3","5 min AMRAP\n165 lb Squat Clean & Jerk",[["Clean & Jerk",["전신","어깨","대퇴사두"],None,165,110]],"5분 단일 동작 최대랩. 165lb 클린앤저크."],
["11.4","Open","For Time","10",None,"CrossFit Open 2011 - WOD 4","For Time (10-min cap)\n60 Burpees / 30 OHS (120/90) / 10 Muscle-ups",[["Burpee",["전신","가슴"],60,None,None],["Overhead Squat",["대퇴사두","어깨","코어"],30,120,90],["Ring Muscle-up",["광배근","이두","가슴"],10,None,None]],"버피→OHS→머슬업 타임캡. 머슬업까지 간 선수 극소수."],
["11.5","Open","AMRAP",None,20,"CrossFit Open 2011 - WOD 5","20 min AMRAP\n5 Power Cleans (145/100) / 10 T2B / 15 Wall Balls",[["Power Clean",["전신","대퇴사두","승모근"],5,145,100],["Toes to Bar",["복근","광배근","고관절굴근"],10,None,None],["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],15,20,14]],"클린+T2B+월볼 20분 AMRAP. 오픈 최초 T2B 등장."],
["11.6","Open","For Time","21-18-15-12-9-6-3",None,"CrossFit Open 2011 - WOD 6","21-18-15-12-9-6-3 For Time\nThrusters (100/65) / Burpees",[["Thruster",["대퇴사두","어깨","둔근"],21,100,65],["Burpee",["전신","가슴"],21,None,None]],"총 84+84회. 가장 고통스러운 오픈 와드. 2016년 재등장."],
["12.1","Open","AMRAP",None,7,"CrossFit Open 2012 - WOD 1","7 min AMRAP\nBurpees",[["Burpee",["전신","가슴"],None,None,None]],"7분 버피 단일 동작 최대랩. 엘리트 120+회."],
["12.2","Open","AMRAP",None,10,"CrossFit Open 2012 - WOD 2","10 min AMRAP\n스내치 점증 무게 (75→135→165→210 lb)",[["Power Snatch",["전신","어깨","승모근"],30,75,45]],"점증 무게 스내치 10분."],
["12.3","Open","AMRAP",None,18,"CrossFit Open 2012 - WOD 3","18 min AMRAP\n15 Box Jumps / 12 Push Press (115/75) / 9 T2B",[["Box Jump",["대퇴사두","둔근","종아리"],15,None,None],["Push Press",["어깨","삼두"],12,115,75],["Toes to Bar",["복근","광배근","고관절굴근"],9,None,None]],"3종 18분 AMRAP."],
["12.4","Open","AMRAP",None,12,"CrossFit Open 2012 - WOD 4","12 min AMRAP\n150 Wall Balls / 90 DU / 30 Ring Muscle-ups",[["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],150,20,14],["Double Under",["종아리","전신"],90,None,None],["Ring Muscle-up",["광배근","이두","가슴"],30,None,None]],"'The 150 Wall Ball' 전설. 머슬업까지 간 선수 극소수."],
["12.5","Open","For Time","21-15-9",None,"CrossFit Open 2012 - WOD 5","21-15-9 For Time\nThrusters (100/65) / Chest-to-Bar Pull-ups",[["Thruster",["대퇴사두","어깨","둔근"],21,100,65],["Chest to Bar",["광배근","이두"],21,None,None]],"Fran 헤비 버전. C2B 풀업+무거운 스러스터."],
["13.1","Open","AMRAP",None,17,"CrossFit Open 2013 - WOD 1","17 min AMRAP\n40 Burpees / 30 Snatches (점증)",[["Burpee",["전신","가슴"],40,None,None],["Power Snatch",["전신","어깨","승모근"],30,75,45]],"버피+스내치 점증. 버피 페이스 유지가 핵심."],
["13.2","Open","AMRAP",None,10,"CrossFit Open 2013 - WOD 2","10 min AMRAP\n5 S2O (115/75) / 10 DL / 15 Box Jumps",[["Push Press",["어깨","삼두"],5,115,75],["Deadlift",["햄스트링","둔근","허리"],10,115,75],["Box Jump",["대퇴사두","둔근","종아리"],15,None,None]],"S2O+DL+박스점프 10분 AMRAP."],
["13.3","Open","AMRAP",None,12,"CrossFit Open 2013 - WOD 3 (12.4 재등장)","12 min AMRAP\n150 Wall Balls / 90 DU / 30 Ring Muscle-ups",[["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],150,20,14],["Double Under",["종아리","전신"],90,None,None],["Ring Muscle-up",["광배근","이두","가슴"],30,None,None]],"12.4와 동일. 전년도 대비 성장 측정."],
["13.4","Open","AMRAP",None,7,"CrossFit Open 2013 - WOD 4","7 min AMRAP\n3 C&J / 3 T2B (+3 each round)",[["Clean & Jerk",["전신","어깨","대퇴사두"],3,135,95],["Toes to Bar",["복근","광배근","고관절굴근"],3,None,None]],"클린앤저크+T2B 점증 구조 7분."],
["13.5","Open","For Time","21-18-15-12-9-6-3",None,"CrossFit Open 2013 - WOD 5","4 min AMRAP (연장)\n15 Thrusters (100/65) / 15 C2B",[["Thruster",["대퇴사두","어깨","둔근"],15,100,65],["Chest to Bar",["광배근","이두"],15,None,None]],"스러스터+C2B 무제한 연장 포맷."],
["14.1","Open","AMRAP",None,10,"CrossFit Open 2014 - WOD 1 (11.1 재등장)","10 min AMRAP\n30 DU / 15 Power Snatches (75/55)",[["Double Under",["종아리","전신"],30,None,None],["Power Snatch",["전신","어깨","승모근"],15,75,55]],"11.1과 동일. 3년 성장 측정용."],
["14.2","Open","AMRAP",None,3,"CrossFit Open 2014 - WOD 2","Every 3 min: 2 OHS + 2 C2B (점증)",[["Overhead Squat",["대퇴사두","어깨","코어"],2,95,65],["Chest to Bar",["광배근","이두"],2,None,None]],"OHS+C2B 점증. 3분 창 안에 완료 못하면 종료."],
["14.3","Open","For Time",None,8,"CrossFit Open 2014 - WOD 3","8 min AMRAP\n10 DL (점증 무게) + 15 Box Jumps",[["Deadlift",["햄스트링","둔근","허리"],10,135,95],["Box Jump",["대퇴사두","둔근","종아리"],15,None,None]],"DL 점증 무게+박스점프. 8분 타임캡."],
["14.4","Open","AMRAP",None,14,"CrossFit Open 2014 - WOD 4","14 min AMRAP\n60 Cal Row / 50 T2B / 40 Wall Balls / 30 Cleans / 20 Ring Muscle-ups",[["Rowing 500m",["광배근","햄스트링","전신"],None,None,None],["Toes to Bar",["복근","광배근","고관절굴근"],50,None,None],["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],40,20,14],["Power Clean",["전신","대퇴사두","승모근"],30,135,95],["Ring Muscle-up",["광배근","이두","가슴"],20,None,None]],"5종 사다리. 전설적 오픈 와드."],
["14.5","Open","For Time","21-18-15-12-9-6-3",None,"CrossFit Open 2014 - WOD 5 (11.6 재등장)","21-18-15-12-9-6-3 For Time\nThrusters (95/65) / Burpees",[["Thruster",["대퇴사두","어깨","둔근"],21,95,65],["Burpee",["전신","가슴"],21,None,None]],"11.6 재등장. 역대 가장 고통스러운 오픈 마지막 WOD."],
["15.1","Open","AMRAP",None,9,"CrossFit Open 2015 - WOD 1","9 min AMRAP\n15 T2B / 10 DL (115/75) / 5 Snatches (115/75)",[["Toes to Bar",["복근","광배근","고관절굴근"],15,None,None],["Deadlift",["햄스트링","둔근","허리"],10,115,75],["Power Snatch",["전신","어깨","승모근"],5,115,75]],"T2B+DL+스내치. 동일 바벨 무게 3동작."],
["15.2","Open","AMRAP",None,None,"CrossFit Open 2015 - WOD 2 (14.2 재등장)","Every 3 min: 2 OHS + 2 C2B (점증)",[["Overhead Squat",["대퇴사두","어깨","코어"],2,95,65],["Chest to Bar",["광배근","이두"],2,None,None]],"14.2 재등장. OHS+C2B 점증 3분 창."],
["15.3","Open","AMRAP",None,14,"CrossFit Open 2015 - WOD 3","14 min AMRAP\n7 Muscle-ups / 50 Wall Balls / 100 DU",[["Ring Muscle-up",["광배근","이두","가슴"],7,None,None],["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],50,20,14],["Double Under",["종아리","전신"],100,None,None]],"머슬업+월볼+더블언더. 고기술 고볼륨 AMRAP."],
["15.4","Open","AMRAP",None,8,"CrossFit Open 2015 - WOD 4","8 min: HSPU + Clean (185/125, 점증)",[["Handstand Push-up",["어깨","삼두"],3,None,None],["Squat Clean",["전신","대퇴사두","승모근"],3,185,125]],"HSPU+고중량 클린 교대 점증."],
["15.5","Open","For Time","27-21-15-9",None,"CrossFit Open 2015 - WOD 5","27-21-15-9 For Time\nRow (Cal) / Thrusters (95/65)",[["Rowing 500m",["광배근","햄스트링","전신"],None,None,None],["Thruster",["대퇴사두","어깨","둔근"],27,95,65]],"로잉+스러스터 점감. 총 72 Cal+72 스러스터."],
["16.1","Open","AMRAP",None,20,"CrossFit Open 2016 - WOD 1","20 min AMRAP\n25ft OWL (95/65) / 8 Bar Muscle-ups",[["Overhead Walking Lunge",["대퇴사두","둔근","어깨"],None,95,65],["Bar Muscle-up",["광배근","이두","가슴"],8,None,None]],"런지+바머슬업 교대 20분."],
["16.2","Open","AMRAP",None,4,"CrossFit Open 2016 - WOD 2","25 T2B / 50 DU / 15 Squat Cleans (135/85, 4분 창)",[["Toes to Bar",["복근","광배근","고관절굴근"],25,None,None],["Double Under",["종아리","전신"],50,None,None],["Squat Clean",["전신","대퇴사두","승모근"],15,135,85]],"T2B+DU+스쿼트클린. 4분 창 포맷."],
["16.3","Open","AMRAP",None,7,"CrossFit Open 2016 - WOD 3","7 min AMRAP\n10 Power Snatches (75/55) / 3 Bar Muscle-ups",[["Power Snatch",["전신","어깨","승모근"],10,75,55],["Bar Muscle-up",["광배근","이두","가슴"],3,None,None]],"파워스내치+바머슬업 7분."],
["16.4","Open","For Time",None,13,"CrossFit Open 2016 - WOD 4","13 min\n55 DL / 55 Wall Balls / 55 Cal Row / 55 HSPU",[["Deadlift",["햄스트링","둔근","허리"],55,225,155],["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],55,20,14],["Rowing 500m",["광배근","햄스트링","전신"],None,None,None],["Handstand Push-up",["어깨","삼두"],55,None,None]],"4종 각 55회. 고볼륨 타임캡."],
["16.5","Open","For Time","21-18-15-12-9-6-3",None,"CrossFit Open 2016 - WOD 5 (11.6 재등장)","21-18-15-12-9-6-3 For Time\nThrusters (95/65) / Bar-facing Burpees",[["Thruster",["대퇴사두","어깨","둔근"],21,95,65],["Burpee",["전신","가슴"],21,None,None]],"11.6의 재등장. 역대 최악의 마지막 와드 중 하나."],
["17.1","Open","AMRAP",None,20,"CrossFit Open 2017 - WOD 1","20 min AMRAP\n10 DB Snatches (50/35) / 15 Burpee Box Jump Overs",[["Power Snatch",["전신","어깨","승모근"],10,50,35],["Burpee",["전신","가슴"],15,None,None]],"덤벨 스내치+버피박스점프오버. 덤벨 오픈의 시작."],
["17.2","Open","AMRAP",None,12,"CrossFit Open 2017 - WOD 2","12 min AMRAP\n2 DB Lunges / 4 DB Hang C&J / 6 Burpees (+2/+2 each)",[["Walking Lunge",["대퇴사두","둔근","햄스트링"],2,None,None],["Clean & Jerk",["전신","어깨","대퇴사두"],4,100,70],["Burpee",["전신","가슴"],6,None,None]],"DB+버피 점증 12분 AMRAP."],
["17.3","Open","AMRAP",None,8,"CrossFit Open 2017 - WOD 3","8 min AMRAP\n6 C2B / 6 Squat Snatches (95/65, 점증 무게)",[["Chest to Bar",["광배근","이두"],6,None,None],["Squat Snatch",["전신","어깨","승모근"],6,95,65]],"C2B+스쿼트스내치 점증 무게 8분 창 포맷."],
["17.4","Open","For Time",None,13,"CrossFit Open 2017 - WOD 4 (16.4 재등장)","13 min\n55 DL / 55 Wall Balls / 55 Cal Row / 55 HSPU",[["Deadlift",["햄스트링","둔근","허리"],55,225,155],["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],55,20,14],["Rowing 500m",["광배근","햄스트링","전신"],None,None,None],["Handstand Push-up",["어깨","삼두"],55,None,None]],"16.4 재등장. 4종 각 55회 타임캡."],
["17.5","Open","For Time","10",None,"CrossFit Open 2017 - WOD 5","10 Rounds For Time\n9 Thrusters (95/65) / 35 DU",[["Thruster",["대퇴사두","어깨","둔근"],9,95,65],["Double Under",["종아리","전신"],35,None,None]],"총 90 스러스터+350 더블언더."],
["18.1","Open","AMRAP",None,20,"CrossFit Open 2018 - WOD 1","20 min AMRAP\n8 T2B / 10 DB Hang C&J (50/35) / 14 Cal Row",[["Toes to Bar",["복근","광배근","고관절굴근"],8,None,None],["Hang Power Clean",["전신","승모근"],10,50,35],["Rowing 500m",["광배근","햄스트링","전신"],None,None,None]],"덤벨 크린앤저크+T2B+로잉 20분."],
["18.2","Open","For Time","1-2-3-4-5-6-7-8-9-10",None,"CrossFit Open 2018 - WOD 2","1-10 DB Squats + Burpees → max Clean (275/185)",[["Air Squat",["대퇴사두","둔근"],10,50,35],["Burpee",["전신","가슴"],10,None,None],["Squat Clean",["전신","대퇴사두","승모근"],None,275,185]],"DB스쿼트+버피 점증 후 남은 시간에 클린 최대랩."],
["18.3","Open","AMRAP",None,14,"CrossFit Open 2018 - WOD 3","14 min AMRAP\n100 DU / 20 OHS (115/80) / 12 Ring Muscle-ups / 200ft HS Walk",[["Double Under",["종아리","전신"],100,None,None],["Overhead Squat",["대퇴사두","어깨","코어"],20,115,80],["Ring Muscle-up",["광배근","이두","가슴"],12,None,None],["Handstand Walk",["어깨","삼두","코어"],None,None,None]],"DU→OHS→머슬업→핸드스탠드워크 사다리. 극고난도."],
["18.4","Open","For Time",None,9,"CrossFit Open 2018 - WOD 4","9 min\n21 DL + 21 HSPU / 15+15 / 9+9 / Max Strict HSPU",[["Deadlift",["햄스트링","둔근","허리"],21,225,155],["Handstand Push-up",["어깨","삼두"],21,None,None]],"데드리프트+HSPU 21-15-9."],
["18.5","Open","AMRAP",None,7,"CrossFit Open 2018 - WOD 5","7 min AMRAP\n3 Thrusters (100/65) / 3 C2B (점증)",[["Thruster",["대퇴사두","어깨","둔근"],3,100,65],["Chest to Bar",["광배근","이두"],3,None,None]],"스러스터+C2B 점증 7분."],
["19.1","Open","AMRAP",None,15,"CrossFit Open 2019 - WOD 1","15 min AMRAP\n19 Wall Balls (20/14) / 19 Cal Row",[["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],19,20,14],["Rowing 500m",["광배근","햄스트링","전신"],None,None,None]],"월볼+로잉 단순 2종. 페이스 유지가 전부."],
["19.2","Open","AMRAP",None,8,"CrossFit Open 2019 - WOD 2 (16.2 재등장)","8 min AMRAP\n25 T2B / 50 DU / 15 Squat Cleans (135/85)",[["Toes to Bar",["복근","광배근","고관절굴근"],25,None,None],["Double Under",["종아리","전신"],50,None,None],["Squat Clean",["전신","대퇴사두","승모근"],15,135,85]],"T2B+DU+스쿼트클린 8분 창."],
["19.3","Open","For Time",None,10,"CrossFit Open 2019 - WOD 3","200ft DB OH Lunges / 50 DB Box Step-ups / 50 Strict HSPU / 200ft HS Walk",[["Overhead Walking Lunge",["대퇴사두","둔근","어깨"],None,50,35],["Box Step-up",["대퇴사두","둔근","햄스트링"],50,None,None],["Handstand Push-up",["어깨","삼두"],50,None,None],["Handstand Walk",["어깨","삼두","코어"],None,None,None]],"DB 런지→스텝업→HSPU→핸드스탠드워크."],
["19.4","Open","For Time","3",None,"CrossFit Open 2019 - WOD 4","3 min AMRAP: 10 Pistols / 10 Bar Muscle-ups / 10 Hang C&J (95/65)",[["Pistol Squat",["대퇴사두","둔근","코어"],10,None,None],["Bar Muscle-up",["광배근","이두","가슴"],10,None,None],["Hang Power Clean",["전신","승모근"],10,95,65]],"피스톨스쿼트+바머슬업+행파워클린. 3분 창."],
["19.5","Open","For Time","33",None,"CrossFit Open 2019 - WOD 5","33 Thrusters / 33 C2B / 33 DU / 33 Thrusters (점증) / 33 BMU / 33 DU...",[["Thruster",["대퇴사두","어깨","둔근"],33,95,65],["Chest to Bar",["광배근","이두"],33,None,None],["Double Under",["종아리","전신"],33,None,None],["Bar Muscle-up",["광배근","이두","가슴"],33,None,None]],"스러스터 점증+C2B/BMU."],
["20.1","Open","For Time","10",None,"CrossFit Open 2020 - WOD 1","10 Rounds For Time (10-min cap)\n8 GTO (65/45) / 10 Bar-facing Burpees",[["Power Snatch",["전신","어깨","승모근"],8,65,45],["Burpee",["전신","가슴"],10,None,None]],"총 80 GTO+100 버피. 타임캡 10분."],
["20.2","Open","AMRAP",None,20,"CrossFit Open 2020 - WOD 2","20 min AMRAP\n4 DB Thrusters (50/35) / 6 T2B / 24 DU",[["Thruster",["대퇴사두","어깨","둔근"],4,100,70],["Toes to Bar",["복근","광배근","고관절굴근"],6,None,None],["Double Under",["종아리","전신"],24,None,None]],"DB스러스터+T2B+DU 20분 AMRAP."],
["20.3","Open","For Time",None,9,"CrossFit Open 2020 - WOD 3 (18.4 재등장+연장)","21 DL / 21 HSPU / 15+15 / 9+9 → 연장 포맷",[["Deadlift",["햄스트링","둔근","허리"],21,225,155],["Handstand Push-up",["어깨","삼두"],21,None,None]],"18.4 재등장+연장 포맷."],
["20.4","Open","For Time",None,20,"CrossFit Open 2020 - WOD 4","30 Box Jump Overs + C&J 점증 무게 (5단계)",[["Box Jump",["대퇴사두","둔근","종아리"],30,None,None],["Clean & Jerk",["전신","어깨","대퇴사두"],15,95,65]],"BJO+C&J 점증 무게. 총 150 박스점프오버."],
["20.5","Open","AMRAP",None,None,"CrossFit Open 2020 - WOD 5","40 Ring Muscle-ups / 40-cal Bike / 40 Handstand Push-ups",[["Ring Muscle-up",["광배근","이두","가슴"],40,None,None],["Bike 1000m",["대퇴사두","종아리","전신"],None,None,None],["Handstand Push-up",["어깨","삼두"],40,None,None]],"링머슬업+바이크+HSPU. 완주자 극소수."],
["21.1","Open","AMRAP",None,15,"CrossFit Open 2021 - WOD 1","15 min AMRAP\n1 Wall Walk / 10 DB Snatches (점증)",[["Handstand Push-up",["어깨","삼두","코어"],1,None,None],["Power Snatch",["전신","어깨","승모근"],10,50,35]],"월워크+DB스내치 점증. 어깨 누적 피로."],
["21.2","Open","AMRAP",None,20,"CrossFit Open 2021 - WOD 2","20 min AMRAP\n95 DU / 5 Squat Snatches (점증)",[["Double Under",["종아리","전신"],95,None,None],["Squat Snatch",["전신","어깨","승모근"],5,65,45]],"DU+스쿼트스내치. 무게 점증 포맷 20분."],
["21.3","Open","For Time","10",None,"CrossFit Open 2021 - WOD 3 & 4","For Time (10-min cap)\n10 FS / 10 C2B / 10 T2B / 10 SC (×5 rounds)",[["Front Squat",["대퇴사두","둔근","코어"],10,135,85],["Chest to Bar",["광배근","이두"],10,None,None],["Toes to Bar",["복근","광배근","고관절굴근"],10,None,None],["Squat Clean",["전신","대퇴사두","승모근"],10,135,85]],"4종 5라운드 10분 타임캡."],
["22.1","Open","AMRAP",None,15,"CrossFit Open 2022 - WOD 1","15 min AMRAP\n3 Wall Walks / 12 DB Snatches (50/35) / 15 Box Jump Overs",[["Handstand Push-up",["어깨","삼두","코어"],3,None,None],["Power Snatch",["전신","어깨","승모근"],12,50,35],["Box Jump",["대퇴사두","둔근","종아리"],15,None,None]],"월워크+DB스내치+박스점프오버 15분 AMRAP."],
["22.2","Open","For Time","1-2-3-10-9-8-1",None,"CrossFit Open 2022 - WOD 2","For Time (10-min cap)\n1-10-1 DL (225/155) / Bar-facing Burpees",[["Deadlift",["햄스트링","둔근","허리"],10,225,155],["Burpee",["전신","가슴"],10,None,None]],"총 100 DL+100 버피. 다이아몬드 랩스킴. 완주자 1%."],
["22.3","Open","For Time",None,12,"CrossFit Open 2022 - WOD 3","12 min\nGHD Sit-ups + Thrusters (21-18-15-12-9-6-3)",[["GHD Sit-up",["복근","고관절굴근"],21,None,None],["Thruster",["대퇴사두","어깨","둔근"],21,95,65]],"GHD싯업+스러스터 점감."],
["23.1","Open","AMRAP",None,14,"CrossFit Open 2023 - WOD 1 (14.4 재등장)","14 min AMRAP\n60 Cal Row / 50 T2B / 40 Wall Balls / 30 Cleans / 20 Ring Muscle-ups",[["Rowing 500m",["광배근","햄스트링","전신"],None,None,None],["Toes to Bar",["복근","광배근","고관절굴근"],50,None,None],["Wall Ball (20/14 lb)",["대퇴사두","어깨","둔근"],40,20,14],["Power Clean",["전신","대퇴사두","승모근"],30,135,95],["Ring Muscle-up",["광배근","이두","가슴"],20,None,None]],"14.4 재등장. 9년 성장 측정."],
["23.2","Open","For Time",None,20,"CrossFit Open 2023 - WOD 2","For Time (20-min cap)\n1000m Row / 50 Burpee Box Jump Overs / 1000m Row",[["Rowing 500m",["광배근","햄스트링","전신"],None,None,None],["Burpee",["전신","대퇴사두","둔근"],50,None,None]],"로잉-BBJO-로잉 샌드위치. 20분 타임캡."],
["23.3","Open","For Time",None,None,"CrossFit Open 2023 - WOD 3","For Time\n5 Thrusters (점증) / 10 C2B / 5 Thrusters / 10 BMU...",[["Thruster",["대퇴사두","어깨","둔근"],5,95,65],["Chest to Bar",["광배근","이두"],10,None,None],["Bar Muscle-up",["광배근","이두","가슴"],10,None,None]],"스러스터 점증+C2B/BMU. 오픈 최종 WOD."],
["24.1","Open","AMRAP",None,15,"CrossFit Open 2024 - WOD 1","15 min AMRAP\n3 Lateral Burpees / 3 DB Hang C2OH (50/35) / 30ft Lunge (+3 each)",[["Burpee",["전신","가슴"],3,None,None],["Hang Power Clean",["전신","승모근"],3,50,35],["Walking Lunge",["대퇴사두","둔근","햄스트링"],None,None,None]],"버피+DB 크린오버헤드+런지 점증."],
["24.2","Open","For Time",None,20,"CrossFit Open 2024 - WOD 2","20-min cap\n4 DL / 6 Burpee Box Jumps / 8 HPC / 10 Box Jump Overs",[["Deadlift",["햄스트링","둔근","허리"],4,185,125],["Burpee",["전신","가슴"],6,None,None],["Hang Power Clean",["전신","승모근"],8,185,125],["Box Jump",["대퇴사두","둔근","종아리"],10,None,None]],"DL+버피박스점프+HPC+박스점프오버 반복."],
["24.3","Open","For Time",None,25,"CrossFit Open 2024 - WOD 3","25-min cap\n5 Strict Pull-ups / 10 Push-ups / 15 Air Squats / 25 DU...",[["Pull-up",["광배근","이두"],5,None,None],["Push-up",["가슴","어깨","삼두"],10,None,None],["Air Squat",["대퇴사두","둔근"],15,None,None],["Double Under",["종아리","전신"],25,None,None]],"Cindy+DU 구조. 모든 레벨 접근 가능."],
["25.1","Open","AMRAP",None,15,"CrossFit Open 2025 - WOD 1","15 min AMRAP\n3 Lateral Burpees / 3 DB Hang C2OH / 30ft Lunge (+3 each)",[["Burpee",["전신","가슴"],3,None,None],["Hang Power Clean",["전신","승모근"],3,50,35],["Walking Lunge",["대퇴사두","둔근","햄스트링"],None,None,None]],"2025 오픈 첫 번째. 24.1과 유사 점증 구조."],
["25.2","Open","For Time",None,15,"CrossFit Open 2025 - WOD 2","For Time (15-min cap)\n21 Thrusters / 21 C2B / 15 Thrusters / 15 BMU / 9 Thrusters / 9 BMU",[["Thruster",["대퇴사두","어깨","둔근"],21,95,65],["Chest to Bar",["광배근","이두"],21,None,None],["Bar Muscle-up",["광배근","이두","가슴"],9,None,None]],"스러스터 점증+풀업/머슬업 21-15-9 구조."],
["25.3","Open","For Time",None,20,"CrossFit Open 2025 - WOD 3","For Time (20-min cap)\n400m Run / 21 KB Snatches / 400m / 18 KB Snatches...",[["Run 400m",["종아리","햄스트링","전신"],None,None,None],["Power Snatch",["전신","어깨","승모근"],21,53,35]],"달리기+KB스내치 점감 구조. 2025 오픈 마지막."],
]

NAMED_WODS = []
for row in RAW_WODS:
    name, cat, wtype, rounds, time, tribute, desc, mv_raw, note = row
    movements = [{"name": m[0], "muscles": m[1], "reps": m[2], "wM": m[3], "wF": m[4]} for m in mv_raw]
    NAMED_WODS.append({"name": name, "cat": cat, "type": wtype, "rounds": rounds, "time": time,
                        "tribute": tribute, "desc": desc, "movements": movements, "note": note})

def get_movement_for_level(cat, level):
    c = MOVEMENTS[cat]
    idx = min(LEVEL_INDEX.get(level, 0), len(c["levels"]) - 1)
    return {"name": c["levels"][idx], "weight_M": c["weights"]["M"][idx],
            "weight_F": c["weights"]["F"][idx], "muscles": c["muscles"], "category": cat}

def format_weight(wM, wF):
    if wM is not None and wF is not None:
        return f"♂ {wM} lbs · ♀ {wF} lbs"
    return ""

def generate_with_ai(wod_type, level, time_val, target_regions, rounds):
    avail = []
    for cat, info in MOVEMENTS.items():
        idx = min(LEVEL_INDEX.get(level, 0), len(info["levels"]) - 1)
        avail.append(f'"{cat}":{info["levels"][idx]}|근육:{",".join(info["muscles"])}|M:{info["weights"]["M"][idx] or "없음"}/F:{info["weights"]["F"][idx] or "없음"}')
    ref = []
    for w in NAMED_WODS[:10]:
        mvs = "+".join([f'{m["reps"]}×{m["name"]}' if m["reps"] else m["name"] for m in w["movements"]])
        ref.append(f'{w["name"]}({w["type"]}): {mvs}')
    region_str = "전신 균형" if "전신" in target_regions else f'{"+".join(target_regions)} 집중'
    is_fl = wod_type == "For Load"; is_tab = wod_type == "Tabata"; is_db = wod_type == "Death by"; is_ft = wod_type == "For Time"
    mc = 2 if (is_db or is_tab) else 1 if is_fl else 3 if wod_type == "EMOM" else random.randint(3, 5)
    tg = ("동작1개 reps=null 최대중량" if is_fl else "동작1~2개 reps=null 20s/10s×8" if is_tab else
          "[0]=고정(reps설정) [1]=증가(reps=1)" if is_db else
          f"{rounds}R 동작{mc}개 라운드당9~21개" if is_ft else f"{time_val}분 동작3개 5~10개")
    level_guide = ("올림픽리프팅가능" if level == "RXD" else "중간난이도" if level == "A" else "기본위주" if level == "B" else "바디웨이트만")
    prompt = f"""크로스핏 전문 코치. JSON만 응답(코드블록없이).
타입:{wod_type}|레벨:{level}|부위:{region_str}|{tg}
참고 와드:\n{chr(10).join(ref)}
동작:\n{chr(10).join(avail)}
원칙:같은주동근연속금지|{level_guide}
{{"movements":[{{"category":"키","reps":숫자또는null}}],"rationale":"한국어 2문장"}}"""
    client = anthropic.Anthropic()
    response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=600,
                                       messages=[{"role": "user", "content": prompt}])
    text = response.content[0].text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(text)
    movements = []
    for m in parsed["movements"]:
        mv = get_movement_for_level(m["category"], level)
        mv["reps"] = m.get("reps")
        movements.append(mv)
    muscles = list(set(sum([m["muscles"] for m in movements], [])))
    return {"movements": movements, "muscles": muscles, "wodType": wod_type,
            "level": level, "time": time_val, "rounds": rounds, "rationale": parsed.get("rationale", "")}

def render_wod(wod, named_info=None):
    st.markdown("---")
    if named_info:
        st.markdown(f"### 🏆 {named_info['name']} `{named_info['cat']}`")
        st.caption(named_info["tribute"])
        st.code(named_info["desc"], language=None)
    else:
        type_emoji = {"For Time": "⏱️", "AMRAP": "🔄", "EMOM": "📟", "Tabata": "⚡", "For Load": "🏋️", "Death by": "💀"}.get(wod["wodType"], "💪")
        label = wod["wodType"]
        if wod.get("time"): label += f" · {wod['time']}분"
        if wod.get("rounds"): label += f" · {wod['rounds']}R"
        st.markdown(f"### {type_emoji} {label}  `{wod.get('level','')}`")
    st.markdown("#### 동작")
    for m in wod["movements"]:
        reps_str = f"**{m['reps']}회** " if m.get("reps") else "**MAX** " if wod.get("wodType") == "For Load" else ""
        weight_str = format_weight(m.get("weight_M") or m.get("wM"), m.get("weight_F") or m.get("wF"))
        st.markdown(f"- {reps_str}{m['name']}" + (f"  _{weight_str}_" if weight_str else ""))
    st.markdown("#### 🎯 목표 근육")
    st.write(" · ".join(wod["muscles"]))
    if wod.get("rationale"):
        with st.expander("📋 AI 설계 근거 / 와드 소개"): st.write(wod["rationale"])
    if named_info and named_info.get("note"):
        with st.expander("📝 코치 노트"): st.write(named_info["note"])

girls_n = sum(1 for w in NAMED_WODS if w['cat'] == 'Girls')
hero_n  = sum(1 for w in NAMED_WODS if w['cat'] == 'Hero')
open_n  = sum(1 for w in NAMED_WODS if w['cat'] == 'Open')

st.markdown("<h1 style='text-align:center'>WOD GENERATOR</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;color:#475569;font-family:monospace;font-size:12px'>Girls {girls_n} · Hero {hero_n} · Open {open_n} · 총 {len(NAMED_WODS)}개 내장</p>", unsafe_allow_html=True)

mode = st.radio("모드", ["🤖 AI 자동 생성", "✏️ 직접 선택", "📋 네임드 와드"], horizontal=True, label_visibility="collapsed")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    if "네임드" in mode:
        wod_type = "네임드 와드"; st.selectbox("와드 타입", ["네임드 와드"], disabled=True)
    else:
        wod_type = st.selectbox("와드 타입", [t for t in WOD_TYPES if t != "네임드 와드"])
with col2:
    level = st.select_slider("레벨", options=LEVELS, value="RXD", disabled=("네임드" in mode))

if "AI" in mode:
    col3, col4 = st.columns(2)
    with col3:
        time_val = st.select_slider("시간 (분)", options=TIME_OPTIONS, value=15, disabled=(wod_type in ["Tabata", "For Load"]))
        rounds = st.select_slider("라운드 수", options=ROUNDS_OPT, value=5) if wod_type == "For Time" else None
    with col4:
        target_regions = st.multiselect("목표 부위", BODY_REGIONS, default=["전신"]) or ["전신"]
    if st.button("🤖 AI WOD 생성", type="primary", use_container_width=True):
        with st.spinner("Claude가 WOD를 설계하고 있습니다..."):
            try:
                wod = generate_with_ai(wod_type, level, time_val, target_regions, rounds)
                render_wod(wod)
            except Exception as e:
                st.error(f"AI 생성 실패: {e}")

elif "직접" in mode:
    cat_labels = {cat: info["label"] for cat, info in MOVEMENTS.items()}
    selected_cats = st.multiselect("동작 카테고리 선택", options=list(cat_labels.keys()), format_func=lambda x: cat_labels[x])
    reps_dict = {}
    if selected_cats:
        st.markdown("#### 랩수 설정 (0 = 랜덤)")
        rep_cols = st.columns(min(len(selected_cats), 4))
        for i, cat in enumerate(selected_cats):
            with rep_cols[i % 4]:
                reps_dict[cat] = st.number_input(cat_labels[cat], min_value=0, max_value=50, value=0, key=f"rep_{cat}")
    rounds = st.select_slider("라운드 수", options=ROUNDS_OPT, value=5, key="manual_rounds") if wod_type == "For Time" else None
    if st.button("✅ WOD 빌드", type="primary", use_container_width=True, disabled=not selected_cats):
        REPS = [5, 7, 9, 10, 12, 15, 21]
        is_fl = wod_type == "For Load"; is_tab = wod_type == "Tabata"
        movements = []
        for cat in selected_cats:
            mv = get_movement_for_level(cat, level)
            mv["reps"] = None if (is_fl or is_tab) else (reps_dict.get(cat) or random.choice(REPS))
            movements.append(mv)
        muscles = list(set(sum([m["muscles"] for m in movements], [])))
        render_wod({"movements": movements, "muscles": muscles, "wodType": wod_type,
                    "level": level, "time": None, "rounds": rounds, "rationale": None})

elif "네임드" in mode:
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        cat_filter = st.radio("카테고리", ["전체", "Girls", "Hero", "Open"])
    with col_f2:
        search = st.text_input("🔍 와드 검색", placeholder="이름 검색...")
    filtered = [w for w in NAMED_WODS
                if (cat_filter == "전체" or w["cat"] == cat_filter)
                and (search == "" or search.lower() in w["name"].lower())]
    if not filtered:
        st.warning("검색 결과가 없습니다.")
    else:
        st.caption(f"{len(filtered)}개 표시")
        wod_names = [f"{w['name']} ({w['cat']})" for w in filtered]
        selected = st.selectbox("와드 선택", wod_names)
        selected_wod = filtered[wod_names.index(selected)]
        st.info(f"**{selected_wod['tribute']}**")
        st.code(selected_wod["desc"], language=None)
        if st.button("📋 와드 불러오기", type="primary", use_container_width=True):
            movements = [{"name": m["name"], "muscles": m["muscles"], "reps": m["reps"],
                          "weight_M": m.get("wM"), "weight_F": m.get("wF")} for m in selected_wod["movements"]]
            muscles = list(set(sum([m["muscles"] for m in movements], [])))
            render_wod({"movements": movements, "muscles": muscles, "wodType": selected_wod["type"],
                        "level": None, "time": selected_wod.get("time"), "rounds": selected_wod.get("rounds"),
                        "rationale": selected_wod.get("note")}, named_info=selected_wod)

st.markdown("---")
st.caption("⚠️ RXD 시도 전 반드시 전문 트레이너와 상담하세요")
