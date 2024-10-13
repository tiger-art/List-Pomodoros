import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
import subprocess
import os
import json
import datetime
import dbus
from dbus.mainloop.glib import DBusGMainLoop

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄钟计时器")
        self.tasks = []  # 存储任务
        self.current_task_index = -1  # 当前任务的索引
        self.timer_running = False  # 计时器是否在运行
        self.notification_id = None  # 通知的ID
        self.sound_process = None  # 播放声音的进程
        self.timer_id = None  # 用于存储计时器的ID，以便取消计时器
        self.history = {}  # 存储任务历史记录
        self.sound_file = os.path.abspath("ding.mp3")  # 使用绝对路径
        self.data_directory = "data"  # 默认数据目录
        self.mini_mode = False  # 是否处于迷你模式
        self._offset_x = 0  # 鼠标按下时的X偏移量
        self._offset_y = 0  # 鼠标按下时的Y偏移量

        # 任务列表框
        self.task_frame = tk.Frame(root)
        self.task_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.task_listbox = tk.Listbox(self.task_frame, width=50, height=10, selectmode=tk.SINGLE)
        self.task_listbox.pack(side=tk.TOP, pady=10, padx=5)
        self.task_listbox.bind('<Button-1>', self.on_click)  # 绑定鼠标单击事件
        self.task_listbox.bind('<B1-Motion>', self.on_drag)  # 绑定鼠标拖动事件
        self.task_listbox.bind('<Double-1>', self.rename_task)

        # 右侧框架
        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮框架
        self.button_frame = tk.Frame(self.right_frame)
        self.button_frame.pack(side=tk.TOP, fill=tk.Y, pady=5, padx=5)

        # 按钮
        self.start_button = tk.Button(self.button_frame, text="开始", command=self.start_timer)
        self.start_button.pack(pady=5, padx=5, anchor=tk.N)
        self.stop_button = tk.Button(self.button_frame, text="停止", command=self.stop_timer)
        self.stop_button.pack(pady=5, padx=5, anchor=tk.N)
        self.stop_music_button = tk.Button(self.button_frame, text="停止音乐", command=self.stop_sound, state=tk.DISABLED)
        self.stop_music_button.pack(pady=5, padx=5, anchor=tk.N)
        self.mini_mode_button = tk.Button(self.button_frame, text="迷你模式", command=self.toggle_mini_mode)
        self.mini_mode_button.pack(pady=5, padx=5, anchor=tk.N)

        # 任务操作按钮
        self.task_buttons_frame = tk.Frame(self.task_frame)
        self.task_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.add_task_button = tk.Button(self.task_buttons_frame, text="添加任务", command=self.add_task)
        self.add_task_button.pack(side=tk.LEFT, pady=5, padx=5)
        self.delete_task_button = tk.Button(self.task_buttons_frame, text="删除任务", command=self.delete_task)
        self.delete_task_button.pack(side=tk.LEFT, pady=5, padx=5)
        self.color_button = tk.Button(self.task_buttons_frame, text="颜色", command=self.set_task_color)
        self.color_button.pack(side=tk.LEFT, pady=5, padx=5)
        self.history_button = tk.Button(self.task_buttons_frame, text="历史记录", command=self.view_history)
        self.history_button.pack(side=tk.LEFT, pady=5, padx=5)
        self.settings_button = tk.Button(self.task_buttons_frame, text="设置", command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, pady=5, padx=5)

        # 剩余时间标签
        self.status_label = tk.Label(self.right_frame, text="", justify=tk.RIGHT, anchor=tk.SE)
        self.status_label.pack(side=tk.BOTTOM, anchor=tk.SE, pady=5, padx=5)

        # 初始化D-Bus连接
        DBusGMainLoop(set_as_default=True)  # 设置默认的主循环
        try:
            self.bus = dbus.SessionBus()
            self.notify = self.bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
            self.notify_interface = dbus.Interface(self.notify, 'org.freedesktop.Notifications')
            self.notify_interface.connect_to_signal('ActionInvoked', self.on_action_invoked)
            print("D-Bus connection initialized successfully.")
        except Exception as e:
            print(f"Error initializing D-Bus connection: {e}")

        # 加载设置
        self.load_settings()

        # 加载任务
        self.load_tasks()

        # 加载历史记录
        self.load_history()

    def toggle_mini_mode(self):
        if self.mini_mode:
            self.mini_window.destroy()
            self.mini_mode = False
            self.root.deiconify()  # 显示主窗口
        else:
            self.root.withdraw()  # 隐藏主窗口
            self.create_mini_mode_window()
            self.mini_mode = True

    def create_mini_mode_window(self):
        self.mini_window = tk.Toplevel(self.root)
        self.mini_window.overrideredirect(True)  # 隐藏标题栏
        self.mini_window.attributes('-topmost', True)  # 始终在最前面
        self.mini_window.attributes('-alpha', 0.7)  # 设置透明度
        self.mini_window.geometry("500x40+100+100")  # 修改了初始尺寸和位置
        self.mini_window.resizable(False, False)  # 禁用调整大小

        self.mini_frame = tk.Frame(self.mini_window, bg='white')
        self.mini_frame.pack(fill=tk.BOTH, expand=True)

        # 功能按钮横排
        self.mini_start_button = tk.Button(self.mini_frame, text="开始", command=self.start_timer, bg='white')
        self.mini_start_button.pack(side=tk.LEFT, padx=5)
        self.mini_stop_button = tk.Button(self.mini_frame, text="停止", command=self.stop_timer, bg='white')
        self.mini_stop_button.pack(side=tk.LEFT, padx=5)
        self.mini_stop_music_button = tk.Button(self.mini_frame, text="停止音乐", command=self.stop_sound, state=tk.DISABLED, bg='white')
        self.mini_stop_music_button.pack(side=tk.LEFT, padx=5)
        self.mini_status_label = tk.Label(self.mini_frame, text="", bg='white')
        self.mini_status_label.pack(side=tk.LEFT, padx=5)
        self.mini_close_button = tk.Button(self.mini_frame, text="关闭", command=self.mini_window.destroy, bg='white')
        self.mini_close_button.pack(side=tk.RIGHT, padx=5)
        self.mini_maximize_button = tk.Button(self.mini_frame, text="放大", command=self.toggle_mini_mode, bg='white')
        self.mini_maximize_button.pack(side=tk.RIGHT, padx=5)
        self.mini_minimize_button = tk.Button(self.mini_frame, text="最小化", command=self.minimize_main_window, bg='white')
        self.mini_minimize_button.pack(side=tk.RIGHT, padx=5)

        self.mini_window.bind("<B1-Motion>", self.move_window)
        self.mini_window.bind("<Button-1>", self.on_click)  # 绑定鼠标单击事件

        self.update_mini_status_label()

    def move_window(self, event):
        x = self.mini_window.winfo_pointerx() - self._offset_x
        y = self.mini_window.winfo_pointery() - self._offset_y
        self.mini_window.geometry(f"+{x}+{y}")

    def on_click(self, event):
        self._offset_x = event.x_root - self.mini_window.winfo_x()
        self._offset_y = event.y_root - self.mini_window.winfo_y()

    def on_drag(self, event):
        index = self.task_listbox.nearest(event.y)
        if index >= 0 and index != self.drag_start_index:
            self.drag_end_index = index
            self.swap_tasks(self.drag_start_index, self.drag_end_index)
            self.update_task_listbox()
            self.drag_start_index = self.drag_end_index

    def update_mini_status_label(self):
        if self.mini_mode:
            task = self.tasks[self.current_task_index] if self.current_task_index >= 0 else {}
            remaining_time = task.get('remaining', 0)
            mins, secs = divmod(remaining_time, 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            self.mini_status_label.config(text=f"正在执行: {task.get('name', '')}\n剩余时间: {timeformat}")
            self.mini_window.after(1000, self.update_mini_status_label)

    def add_task(self):
        task_name = simpledialog.askstring("输入", "任务名称:")
        if not task_name:
            return
        task_time = simpledialog.askinteger("输入", "时间（分钟）:", minvalue=1)
        if task_time is None:
            return
        self.tasks.append({"name": task_name, "time": task_time, "remaining": task_time * 60, "color": "black"})
        self.update_task_listbox()
        self.save_tasks()

    def delete_task(self):
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("警告", "未选择要删除的任务。")
            return
        del self.tasks[selected_index[0]]
        self.update_task_listbox()
        self.save_tasks()

    def set_task_color(self):
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("警告", "未选择要设置颜色的任务。")
            return
        colors = [("浅红色", "lightcoral"), ("黑色", "black")]
        color_choice = simpledialog.askstring("选择颜色", "选择任务字体颜色:\n1. 浅红色\n2. 黑色")
        if color_choice == "1":
            self.tasks[selected_index[0]]["color"] = "lightcoral"
        elif color_choice == "2":
            self.tasks[selected_index[0]]["color"] = "black"
        else:
            return
        self.update_task_listbox()
        self.save_tasks()

    def rename_task(self, event):
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            return
        old_task = self.tasks[selected_index[0]]
        new_task_name = simpledialog.askstring("输入", "新的任务名称:", initialvalue=old_task['name'])
        if not new_task_name or new_task_name == old_task['name']:
            return
        self.tasks[selected_index[0]]['name'] = new_task_name
        self.update_task_listbox()
        self.save_tasks()

    def update_task_listbox(self):
        self.task_listbox.delete(0, tk.END)
        for task in self.tasks:
            color = task.get("color", "black")
            self.task_listbox.insert(tk.END, f"{task['name']} - {task['time']} 分钟")
            self.task_listbox.itemconfig(tk.END, fg=color)
        self.highlight_current_task()

    def highlight_current_task(self):
        for i in range(len(self.tasks)):
            bg_color = '#ADD8E6' if i == self.current_task_index else 'white'
            self.task_listbox.itemconfig(i, {'bg': bg_color})

    def start_timer(self):
        if not self.tasks:
            messagebox.showwarning("警告", "没有任务可以开始。")
            return
        if not self.timer_running:
            self.timer_running = True
            self.stop_music_button.config(state=tk.NORMAL)
            if self.mini_mode:
                self.mini_stop_music_button.config(state=tk.NORMAL)
            self.run_next_task()

    def run_next_task(self):
        if self.current_task_index + 1 < len(self.tasks):
            self.current_task_index += 1
            task = self.tasks[self.current_task_index]
            self.status_label.config(text=f"正在执行: {task['name']}\n剩余时间: {task['remaining'] // 60}:{task['remaining'] % 60:02d}")
            self.countdown(task['remaining'])
            self.highlight_current_task()
            self.update_mini_status_label()
        else:
            self.all_tasks_completed()

    def all_tasks_completed(self):
        response = messagebox.askyesno("提示", "所有任务已完成！是否要重复任务？")
        if response:
            self.reset_tasks()
            self.status_label.config(text="所有任务已重置，\n点击开始以重新开始。")
            self.start_button.config(state=tk.NORMAL)  # 使“开始”按钮可用
        else:
            self.timer_running = False
            self.status_label.config(text="所有任务已完成。")
            self.save_history()

    def reset_tasks(self):
        for task in self.tasks:
            task['remaining'] = task['time'] * 60
        self.current_task_index = -1
        self.timer_running = False  # 重置计时器状态
        self.update_task_listbox()

    def countdown(self, remaining=None):
        if not self.timer_running:
            return
        task = self.tasks[self.current_task_index]
        if remaining is not None:
            task['remaining'] = remaining
        if task['remaining'] <= 0:
            self.status_label.config(text=f"已完成: {task['name']}")
            self.play_sound()
            self.show_notification()
        else:
            mins, secs = divmod(task['remaining'], 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            self.status_label.config(text=f"正在执行: {task['name']}\n剩余时间: {timeformat}")
            task['remaining'] -= 1
            self.timer_id = self.root.after(1000, self.countdown)
            self.update_mini_status_label()

    def stop_timer(self):
        if self.timer_running:
            self.timer_running = False
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
            self.timer_id = None
            self.status_label.config(text="计时器已停止。")
            self.update_mini_status_label()
            self.stop_sound()  # 停止音乐

    def play_sound(self):
        if not os.path.exists(self.sound_file):
            print(f"音乐文件未找到: {self.sound_file}")
            return
        try:
            print(f"Playing sound: {self.sound_file}")
            self.sound_process = subprocess.Popen(['mpg123', self.sound_file])
        except FileNotFoundError:
            print("mpg123 未找到。请确保已安装 mpg123。")
        except Exception as e:
            print(f"播放声音时发生错误: {e}")

    def stop_sound(self):
        if self.sound_process:
            self.sound_process.terminate()
            self.sound_process = None
            self.stop_music_button.config(state=tk.DISABLED)
            if self.mini_mode:
                self.mini_stop_music_button.config(state=tk.DISABLED)
            self.stop_timer()  # 停止计时器

    def show_notification(self):
        if self.notification_id:
            self.notify_interface.CloseNotification(self.notification_id)
        notification = {
            'app_name': 'Pomodoro Timer',
            'replaces_id': 0,
            'app_icon': '',
            'summary': '番茄钟',
            'body': '任务完成！',
            'actions': ['default', '默认操作'],
            'hints': {},
            'expire_timeout': 5000
        }
        self.notification_id = self.notify_interface.Notify(
            'Pomodoro Timer', 0, '', '番茄钟', '任务完成！', ['default', '默认操作'], {}, 5000
        )

    def on_action_invoked(self, notification_id, action):
        print(f"Action invoked: {action} for notification {notification_id}")

    def save_history(self):
        history_file = os.path.join(self.data_directory, "history.json")
        os.makedirs(self.data_directory, exist_ok=True)
        today = datetime.date.today().isoformat()
        if today not in self.history:
            self.history[today] = []
        for task in self.tasks:
            if task['remaining'] == 0:
                self.history[today].append({
                    "name": task["name"],
                    "time": task["time"]
                })
        with open(history_file, "w") as f:
            json.dump(self.history, f, indent=4)

    def load_history(self):
        history_file = os.path.join(self.data_directory, "history.json")
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                self.history = json.load(f)

    def view_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("任务历史记录")
        tree = ttk.Treeview(history_window, columns=("date", "task", "time"), show="headings")
        tree.heading("date", text="日期")
        tree.heading("task", text="任务")
        tree.heading("time", text="时间（分钟）")
        tree.pack(fill=tk.BOTH, expand=True)
        for date, tasks in self.history.items():
            for task in tasks:
                tree.insert("", tk.END, values=(date, task["name"], task["time"]))

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        tk.Label(settings_window, text="选择音乐文件:").pack(pady=5, padx=5)
        tk.Button(settings_window, text="浏览", command=self.choose_sound_file).pack(pady=5, padx=5)
        tk.Label(settings_window, text="选择数据保存目录:").pack(pady=5, padx=5)
        tk.Button(settings_window, text="浏览", command=self.choose_data_directory).pack(pady=5, padx=5)
        tk.Label(settings_window, text="导出数据:").pack(pady=5, padx=5)
        tk.Button(settings_window, text="导出", command=self.export_data).pack(pady=5, padx=5)
        tk.Label(settings_window, text="导入数据:").pack(pady=5, padx=5)
        tk.Button(settings_window, text="导入", command=self.import_data).pack(pady=5, padx=5)
        tk.Label(settings_window, text=f"当前音乐文件: {self.sound_file}").pack(pady=5, padx=5)
        tk.Label(settings_window, text=f"当前数据保存目录: {self.data_directory}").pack(pady=5, padx=5)

    def choose_sound_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Music files", "*.mp3 *.wav *.ogg")])
        if file_path:
            self.sound_file = file_path
            messagebox.showinfo("信息", f"已选择音乐文件: {self.sound_file}")
            self.save_settings()

    def choose_data_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.data_directory = directory
            messagebox.showinfo("信息", f"已选择数据保存目录: {self.data_directory}")
            self.save_settings()

    def save_settings(self):
        settings_file = os.path.join(self.data_directory, "settings.json")
        os.makedirs(self.data_directory, exist_ok=True)
        settings = {
            "sound_file": self.sound_file,
            "data_directory": self.data_directory
        }
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=4)

    def load_settings(self):
        settings_file = os.path.join(self.data_directory, "settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                settings = json.load(f)
                self.sound_file = settings.get("sound_file", "ding.mp3")
                self.data_directory = settings.get("data_directory", "data")

    def load_tasks(self):
        tasks_file = os.path.join(self.data_directory, "tasks.json")
        if os.path.exists(tasks_file):
            with open(tasks_file, "r") as f:
                self.tasks = json.load(f)
            self.update_task_listbox()

    def save_tasks(self):
        tasks_file = os.path.join(self.data_directory, "tasks.json")
        os.makedirs(self.data_directory, exist_ok=True)
        with open(tasks_file, "w") as f:
            json.dump(self.tasks, f, indent=4)

    def export_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            data = {
                "tasks": self.tasks,
                "history": self.history,
                "settings": {
                    "sound_file": self.sound_file,
                    "data_directory": self.data_directory
                }
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("信息", "数据已成功导出。")

    def import_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as f:
                data = json.load(f)
                self.tasks = data.get("tasks", [])
                self.history = data.get("history", {})
                settings = data.get("settings", {})
                self.sound_file = settings.get("sound_file", "ding.mp3")
                self.data_directory = settings.get("data_directory", "data")
            self.update_task_listbox()
            self.save_settings()
            messagebox.showinfo("信息", "数据已成功导入。")

    def minimize_main_window(self):
        self.root.iconify()

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()