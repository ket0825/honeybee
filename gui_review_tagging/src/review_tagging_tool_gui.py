import tkinter.messagebox as msgbox
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import json

# custom_widget
from custom_widget.custom_checkbutton import CustomCheckbutton

data_len = 0
current_index = 0
topic_entries = []
topic_frames = []
our_topics = []
file_path = ""

topic_candidates = ["만족도","제품만족도", "가격", "서비스만족도", "발송", "배송","환불","포장","AS","수리","환불","교환","문의",
                    "키","키감","소리","키압","통울림","키캡","키축","스테빌라이저","윤활",
                    "디자인","색상","재질","백라이트","외형","키보드각인",
                    "휴대성","무게","사이즈",
                    "제품구성","파우치","거치대","키스킨","건전지","설명서","키캡리무버","키보드커버","케이블",
                    "제품품질","마감","내구성",
                    "성능","배터리","수명","호환성","지연율","소비전력",
                    "편의성","손목","키배열","키보드높이",
                    "연결방식","동글","블루투스","유선",
                    "기능","다중페어링","접이식","래피드 트리거",
                    ]


def on_keyrelease(event, topic_combobox):
    # 입력된 값 가져오기
    value = event.widget.get()
    # 입력된 값으로 시작하는 항목들로 콤보박스 업데이트
    if value == '':
        topic_combobox['values'] = topic_candidates
    else:
        data = []
        for item in topic_candidates:
            if value in item:
                data.append(item)
        topic_combobox['values'] = data


def open_json_file():
    global current_index, data, file_path, our_topics, data_len
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])

    if file_path:
        if our_topics and not msgbox.askokcancel('저장 확인', "저장하셔서 다음 것으로 넘어가신다면 확인을 누르세요.\n아니라면 취소를 하고 먼저 저장해주세요."):
            return           
        
        path_text.config(state='normal')  # 편집 가능하게 변경
        path_text.delete(1.0, tk.END)    
        path_text.insert(tk.END, file_path) 
        path_text.config(state='disabled') # 넣었으니 편집 불가능.

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        current_index = 0
        data_len = len(data)
        our_topics = [0]*data_len
        for idx, datum in enumerate(data):
            if datum.get('our_topics'):
                our_topics[idx] = datum['our_topics']
            else:
                our_topics[idx] = [{'text': "", "topic": "", "topic_score":2, 'start_pos': 0, 'end_pos': 0, 'positive_yn': True, 'sentiment_scale':2}]
            
                
        display_content(data[current_index])
    else:
        data = None
        file_path = None

def modify_page_index():
    global current_index, data_len 
    page_index_lbl.config(text=f"{current_index+1} / {len(data)}")        

def display_content(content_data):
    global current_index, topic_entries, our_topics, topic_frames
    scrolled_text.config(state='normal')
    scrolled_text.delete('1.0', tk.END)
    scrolled_text.insert(tk.END, content_data['content'])
    scrolled_text.config(state='disabled')
    modify_page_index()
    # 기존 topic entry 삭제
    for entry in topic_entries:
        for widget in entry:
            widget.destroy()
    for topic_frame in topic_frames:
        topic_frame.destroy()
    topic_entries = []
    topic_frames = []

    # topic entry 새로 생성
    for topic_data in our_topics[current_index]:
        topic_entry = []
        new_frame = create_new_topic_frame()
        new_frame.pack(pady=5)
        topic_frames.append(new_frame)

        topic_text = tk.Text(new_frame, height=2, width=30)
        topic_text.config(font=('Times New Roman', 12))
        topic_text.insert(tk.END, topic_data['text'])
        topic_text.pack(side=tk.LEFT, padx=10)
        topic_entry.append(topic_text)

        topic_combobox = ttk.Combobox(new_frame, values=topic_candidates, state="normal")
        topic_combobox.bind('<MouseWheel>', lambda event: 'break')        
        topic_combobox.set(topic_data['topic'])
        # 콤보박스에 키 이벤트 바인딩
        topic_combobox.bind('<KeyRelease>', lambda e: on_keyrelease(e, topic_combobox))
        topic_combobox.pack(side=tk.LEFT, padx=10)
        topic_entry.append(topic_combobox)
        
        topic_score = ttk.Combobox(new_frame, width=2, values=[str(i) for i in range(1, 6)], state="readonly")
        topic_score.bind('<MouseWheel>', lambda event: 'break')
        topic_score.set(topic_data['topic_score'])
        topic_score.pack(side=tk.LEFT, padx=10)
        topic_entry.append(topic_score)

        positivte_yn_checkbtn = CustomCheckbutton(new_frame, text="Y/N", width=3)        
        positivte_yn_checkbtn.set(topic_data['positive_yn'])
        positivte_yn_checkbtn.pack(side=tk.LEFT, padx=10)
        topic_entry.append(positivte_yn_checkbtn)


        sentiment_scale_combobox = ttk.Combobox(new_frame, width=2, values=[str(i) for i in range(1, 4)], state="readonly")
        sentiment_scale_combobox.bind('<MouseWheel>', lambda event: 'break')
        sentiment_scale_combobox.set(str(topic_data['sentiment_scale']))
        sentiment_scale_combobox.pack(side=tk.LEFT, padx=10)
        topic_entry.append(sentiment_scale_combobox)

        topic_entries.append(topic_entry)

def save_json_file():
    global current_index, data, file_path, topic_entries, our_topics, data_len
    try:
        if data and file_path:
            save_to_our_topics()
             # clean our_topics
            for idx, our_topic in enumerate(our_topics):
                our_topics[idx] = [dict_topic for dict_topic in our_topics[idx] 
                                  if (dict_topic['start_pos'] != -1 
                                      and dict_topic['end_pos'] != -1 
                                      and dict_topic['text'] != "" 
                                      and dict_topic['topic'] != "")
                                      ]                
                
            for idx, datum in enumerate(data):
                datum['our_topics'] = our_topics[idx]
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            msgbox.showinfo("저장성공",  "성공적으로 저장되었습니다!")
        else:
            msgbox.showerror("에러","데이터가 없습니다. 저장에 실패했어요")
    except Exception as e:
        print(f"[ERROR] {e}")
        msgbox.showerror("에러","파일 경로나 데이터가 없습니다")


def next_content():
    global current_index, data, topic_entries, our_topics, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요.")
        return
    
    save_to_our_topics()

    if current_index+1 == len(data):
        msgbox.showwarning("주의", "현재 페이지가 마지막입니다")
        return
    current_index+=1
    display_content(data[current_index])

def previous_content():
    global current_index, data, topic_entries, our_topics, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요.")
        return
    
    save_to_our_topics()

    if current_index == 0:
        msgbox.showwarning("주의", "현재 페이지가 처음입니다")
        return
    current_index-=1
    display_content(data[current_index])

def add_topic():
    global topic_entries, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요.")
        return

    topic_entry = []
    new_frame = create_new_topic_frame()
    new_frame.pack(pady=10)
    topic_frames.append(new_frame)

    topic_text = tk.Text(new_frame, height=2, width=30)
    topic_text.config(font=('Times New Roman', 12))
    topic_text.pack(side=tk.LEFT, padx=10)
    topic_entry.append(topic_text)

    topic_combobox = ttk.Combobox(new_frame, values=topic_candidates, state="normal")
    topic_combobox.bind('<MouseWheel>', lambda event: 'break')
    topic_combobox.bind('<KeyRelease>', lambda e: on_keyrelease(e, topic_combobox))
    topic_combobox.pack(side=tk.LEFT, padx=10)
    topic_entry.append(topic_combobox)

    topic_score = ttk.Combobox(new_frame, width=2, values=[str(i) for i in range(1, 6)], state="readonly")
    topic_score.bind('<MouseWheel>', lambda event: 'break')
    topic_score.current(1)
    topic_score.pack(side=tk.LEFT, padx=10)
    topic_entry.append(topic_score)

    positivte_yn_checkbtn = CustomCheckbutton(new_frame, text="Y/N", width=3)    
    positivte_yn_checkbtn.set(True)
    positivte_yn_checkbtn.pack(side=tk.LEFT, padx=10)
    topic_entry.append(positivte_yn_checkbtn)

    sentiment_scale_combobox = ttk.Combobox(new_frame, width=2, values=[str(i) for i in range(1, 4)], state="readonly")
    sentiment_scale_combobox.bind('<MouseWheel>', lambda event: 'break')
    sentiment_scale_combobox.current(1)
    sentiment_scale_combobox.pack(side=tk.LEFT, padx=10)
    topic_entry.append(sentiment_scale_combobox)

    topic_entries.append(topic_entry)

def delete_last_topic():
    global topic_entries, file_path
    
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요.")
        return
    for widget in topic_entries[-1]:        
        widget.destroy()
    
    topic_entries.pop()

    topic_frames[-1].destroy()
    topic_frames.pop()


def create_new_topic_frame():
    return tk.Frame(inner_frame)

def save_to_our_topics():
    global current_index, data, topic_entries, our_topics
    if len(topic_entries) > len(our_topics[current_index]):
        for _ in range(len(topic_entries)-len(our_topics[current_index])): # 추가된 topic만큼 더해줌
            our_topics[current_index].append({'text': "", "topic": "", 'start_pos': 0, 'end_pos': 0, 'positive_yn': "", 'sentiment_scale':5})

    for topic_idx, topic_entry in enumerate(topic_entries):        
        for widget_order, widget in enumerate(topic_entry):
            if widget_order == 0:
                # 얘만 text. rstrip으로 끝의 줄바꿈 제거.
                our_topics[current_index][topic_idx]['text'] = widget.get('1.0', tk.END).rstrip() 
                target_str = our_topics[current_index][topic_idx]['text'].strip()
                our_topics[current_index][topic_idx]['start_pos'] = data[current_index]['content'].find(target_str)
                our_topics[current_index][topic_idx]['end_pos'] = data[current_index]['content'].find(target_str) + len(target_str)+1 if data[current_index]['content'].find(target_str) > -1 else -1
            elif widget_order == 1:
                our_topics[current_index][topic_idx]['topic'] = widget.get()
            elif widget_order == 2:
                our_topics[current_index][topic_idx]['topic_score'] = int(widget.get())
            elif widget_order == 3:
                our_topics[current_index][topic_idx]['positive_yn'] = "Y" if widget.get() else "N"
                
            elif widget_order == 4:
                our_topics[current_index][topic_idx]['sentiment_scale'] = int(widget.get())


root = tk.Tk()
root.geometry("850x700")
root.resizable(True, True)
root.title("Review Tagging Editor")

# 경로 프레임.
path_frame = tk.Frame(root)
path_frame.pack(pady=10)

# 경로 레이블.
path_lbl = tk.Label(path_frame, text='Path: ')
path_lbl.config(font=('Times New Roman', 12))
path_lbl.pack(side=tk.LEFT, pady=10, padx=5)

# 경로 텍스트.
path_text = tk.Text(path_frame, state='disabled', height=2, width=80)
path_text.config(font=('Times New Roman', 12))
path_text.pack(fill=tk.BOTH, pady=10)

# 버튼 프레임
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

# ScrolledText 프레임
text_frame = tk.Frame(root)
text_frame.pack(fill=tk.BOTH, expand=True)

# 'Open' 버튼
open_btn = tk.Button(btn_frame, text="Open", command=open_json_file)
open_btn.pack(side=tk.LEFT, padx=10)

# 'Save' 버튼
save_btn = tk.Button(btn_frame, text="Save", command=save_json_file)
save_btn.pack(side=tk.LEFT, padx=10)

# 'Next' 버튼
next_btn = tk.Button(btn_frame, text="Next", command=next_content)
next_btn.pack(side=tk.LEFT, padx=10)

# 'Previous' 버튼
prev_btn = tk.Button(btn_frame, text="Previous", command=previous_content)
prev_btn.pack(side=tk.LEFT, padx=10)

# ScrolledText 위젯
scrolled_text = scrolledtext.ScrolledText(text_frame, width=80, height=20)
scrolled_text.config(font=('Times New Roman', 14))
scrolled_text.pack(fill=tk.BOTH, expand=True)

# topic frame
topic_frame = tk.Frame(root)
topic_frame.pack(fill=tk.BOTH, expand=True)

# Scrollbar 생성
topic_scroll = tk.Scrollbar(topic_frame)
topic_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# Canvas 생성
topic_canvas = tk.Canvas(topic_frame, yscrollcommand=topic_scroll.set)
topic_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Scrollbar 구현
topic_scroll.config(command=topic_canvas.yview)

# Canvas 내부에 Frame 생성
inner_frame = tk.Frame(topic_canvas)
topic_canvas.create_window((0, 0), window=inner_frame, anchor='nw')

# 스크롤 영역 업데이트
inner_frame.bind('<Configure>', lambda event: topic_canvas.configure(scrollregion=topic_canvas.bbox('all')))

# 마우스 호버 이벤트 바인딩
topic_canvas.bind('<Enter>', lambda event: topic_canvas.focus_set())
topic_canvas.bind('<Leave>', lambda event: topic_canvas.master.focus_set())

# 마우스 휠 이벤트 처리
def on_mouse_wheel(event):
    topic_canvas.yview_scroll(-1 * (event.delta // 120), "units")

topic_canvas.bind_all('<MouseWheel>', on_mouse_wheel)

# topic label.
topic_lbl = tk.Label(topic_frame, text="    Text    //    topic    //   \n topic score  //  감성 긍정 Y/N  // \n 감성의 강도")
topic_lbl.config(font=('Times New Roman', 14))
topic_lbl.pack(side=tk.TOP, pady=5)

# 'Add Topic' 버튼
add_topic_btn = tk.Button(topic_frame, text="Add Topic", command=add_topic)
add_topic_btn.pack(side=tk.LEFT, padx=10)

# 'Delete Last Topic' 버튼
delete_topic_btn = tk.Button(topic_frame, text="Delete Last Topic", command=delete_last_topic)
delete_topic_btn.pack(side=tk.LEFT, padx=8)

# 페이지 index frame.
page_index_frame = tk.Frame(topic_frame)
page_index_frame.pack(side=tk.BOTTOM, pady=5)

# 페이지 index label.
page_index_lbl = tk.Label(page_index_frame)
page_index_lbl.config(font=('Times New Roman', 14))
page_index_lbl.pack(fill=tk.BOTH)


root.mainloop()