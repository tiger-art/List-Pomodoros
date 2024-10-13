import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
import os
import json
import datetime
import pygame  # 导入 pygame
from plyer import notification
import pystray
from PIL import Image, ImageDraw

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄钟计时器")
        
        self.tasks = []  # 存储任务
        self.current_task_index = -1  # 当前任务的索引
        self.timer_running = False  # 计时器是否在运行
        self.timer_id = None  # 用于存储计时器的ID，以便取消计时器
        self.sound_file = "ding.mp3"  # 默认音乐文件
        self.data_directory = "data"  # 默认数据目录
        self.minimize_to_tray = True  # 是否最小化到系统托盘，默认勾选
        self.mini_mode = False  # 是否处于迷你模式
        self.history = {}  # 存储历史记录
        
        # 初始化 pygame 混音器
        pygame.mixer.init()
        
        # 任务列表框
        self.task_frame = tk.Frame(root)
        self.task_frame.grid(row=0, column=0, sticky="nsew")
        
        self.task_listbox = tk.Listbox(self.task_frame, width=50, height=10, selectmode=tk.SINGLE)
        self.task_listbox.grid(row=0, column=0, pady=10, padx=5, sticky="nsew")
        self.task_listbox.bind('<Button-1>', self.on_click)  # 绑定鼠标单击事件
        self.task_listbox.bind('<B1-Motion>', self.on_drag)  # 绑定鼠标拖动事件
        self.task_listbox.bind('<Double-1>', self.rename_task)
        
        # 按钮框架
        self.button_frame = tk.Frame(root)
        self.button_frame.grid(row=0, column=1, sticky="nsew")
        
        # 按钮
        self.start_button = tk.Button(self.button_frame, text="开始", command=self.start_timer)
        self.start_button.grid(row=0, column=0, pady=5, padx=5, sticky="ew")
        
        self.stop_button = tk.Button(self.button_frame, text="停止", command=self.stop_timer)
        self.stop_button.grid(row=1, column=0, pady=5, padx=5, sticky="ew")
        
        self.stop_music_button = tk.Button(self.button_frame, text="停止音乐", command=self.stop_sound, state=tk.DISABLED)
        self.stop_music_button.grid(row=2, column=0, pady=5, padx=5, sticky="ew")
        
        # 移动“迷你模式”按钮到“停止音乐”按钮下方
        self.mini_mode_button = tk.Button(self.button_frame, text="迷你模式", command=self.toggle_mini_mode)
        self.mini_mode_button.grid(row=3, column=0, pady=5, padx=5, sticky="ew")
        
        # 状态标签
        self.status_label = tk.Label(self.button_frame, text="", justify=tk.LEFT)
        self.status_label.grid(row=4, column=0, pady=10, sticky="ew")

        # 任务操作按钮
        self.task_buttons_frame = tk.Frame(self.task_frame)
        self.task_buttons_frame.grid(row=1, column=0, sticky="ew")
        
        self.add_task_button = tk.Button(self.task_buttons_frame, text="添加任务", command=self.add_task)
        self.add_task_button.grid(row=0, column=0, pady=5, padx=5, sticky="ew")
        
        self.delete_task_button = tk.Button(self.task_buttons_frame, text="删除任务", command=self.delete_task)
        self.delete_task_button.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        
        self.color_button = tk.Button(self.task_buttons_frame, text="颜色", command=self.set_task_color)
        self.color_button.grid(row=0, column=2, pady=5, padx=5, sticky="ew")
        
        # 移动按钮位置
        self.history_button = tk.Button(self.task_buttons_frame, text="历史记录", command=self.view_history)
        self.history_button.grid(row=0, column=3, pady=5, padx=5, sticky="ew")
        
        self.settings_button = tk.Button(self.task_buttons_frame, text="设置", command=self.open_settings)
        self.settings_button.grid(row=0, column=4, pady=5, padx=5, sticky="ew")
        
        # 创建“当前任务+剩余时间”标签并放置在右下角
        self.current_task_label = tk.Label(self.button_frame, text="", justify=tk.LEFT)
        self.current_task_label.grid(row=5, column=0, pady=5, padx=5, sticky="se")

        # 加载设置
        self.load_settings()
        
        # 加载任务
        self.load_tasks()
        
        # 加载历史记录
        self.load_history()

        # 设置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 创建迷你模式窗口
        self.create_mini_mode_window()

    def create_mini_mode_window(self):
        self.mini_window = tk.Toplevel(self.root)
        self.mini_window.title("迷你模式")
        self.mini_window.geometry("420x35")  # 调整迷你窗口大小
        self.mini_window.overrideredirect(True)  # 移除窗口边框
        self.mini_window.attributes('-topmost', True)  # 置顶
        self.mini_window.configure(bg='white')
        
        # 小窗口内的控件
        self.mini_start_button = tk.Button(self.mini_window, text="开始", command=self.start_timer, bg='white')
        self.mini_start_button.pack(side=tk.LEFT, padx=5)
        
        self.mini_stop_button = tk.Button(self.mini_window, text="停止", command=self.stop_timer, bg='white')
        self.mini_stop_button.pack(side=tk.LEFT, padx=5)
        
        self.mini_stop_music_button = tk.Button(self.mini_window, text="停止音乐", command=self.stop_sound, state=tk.DISABLED, bg='white')
        self.mini_stop_music_button.pack(side=tk.LEFT, padx=5)
        
        self.mini_status_label = tk.Label(self.mini_window, text="", bg='white')
        self.mini_status_label.pack(side=tk.LEFT, padx=5)
        
        # 新增按钮
        self.mini_minimize_button = tk.Button(self.mini_window, text="最小化", command=self.minimize_to_tray, bg='white')
        self.mini_minimize_button.pack(side=tk.RIGHT, padx=5)
        
        self.mini_maximize_button = tk.Button(self.mini_window, text="放大", command=self.restore_main_window, bg='white')
        self.mini_maximize_button.pack(side=tk.RIGHT, padx=5)
        
        self.mini_close_button = tk.Button(self.mini_window, text="关闭", command=self.quit_application, bg='white')
        self.mini_close_button.pack(side=tk.RIGHT, padx=5)
        
        # 隐藏迷你窗口
        self.mini_window.withdraw()
        
        # 使迷你窗口可移动
        self.mini_window.bind("<ButtonPress-1>", self.start_move)
        self.mini_window.bind("<ButtonRelease-1>", self.stop_move)
        self.mini_window.bind("<B1-Motion>", self.do_move)
        
        self.move_flag = False
        self.x = 0
        self.y = 0

    def start_move(self, event):
        self.move_flag = True
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.move_flag = False

    def do_move(self, event):
        if self.move_flag:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.mini_window.winfo_x() + deltax
            y = self.mini_window.winfo_y() + deltay
            self.mini_window.geometry(f"+{x}+{y}")

    def toggle_mini_mode(self):
        if self.mini_mode:
            self.mini_window.withdraw()
            self.mini_mode = False
            self.root.deiconify()
        else:
            self.mini_window.deiconify()
            self.mini_window.lift()
            self.mini_mode = True
            self.root.withdraw()

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

    def on_click(self, event):
        self.drag_start_index = self.task_listbox.nearest(event.y)

    def on_drag(self, event):
        index = self.task_listbox.nearest(event.y)
        if index >= 0 and index != self.drag_start_index:
            self.drag_end_index = index
            self.swap_tasks(self.drag_start_index, self.drag_end_index)
            self.update_task_listbox()
            self.drag_start_index = self.drag_end_index

    def swap_tasks(self, index1, index2):
        self.tasks[index1], self.tasks[index2] = self.tasks[index2], self.tasks[index1]

    def start_timer(self):
        if not self.tasks:
            messagebox.showwarning("警告", "没有任务可以开始。")
            return
        if not self.timer_running:
            self.timer_running = True
            self.stop_music_button.config(state=tk.DISABLED)
            self.mini_stop_music_button.config(state=tk.DISABLED)
            self.run_next_task()

    def stop_timer(self):
        if self.timer_running:
            self.timer_running = False
            if self.timer_id is not None:
                self.root.after_cancel(self.timer_id)  # 取消计时器
                self.timer_id = None
            self.current_task_label.config(text="计时器已停止。")
            self.mini_status_label.config(text="计时器已停止。")
            self.stop_sound()  # 停止音乐
            self.stop_music_button.config(state=tk.DISABLED)  # 禁用停止音乐按钮
            self.mini_stop_music_button.config(state=tk.DISABLED)  # 禁用迷你模式停止音乐按钮

    def run_next_task(self):
        if self.current_task_index + 1 < len(self.tasks):
            self.current_task_index += 1
            task = self.tasks[self.current_task_index]
            self.current_task_label.config(text=f"当前任务: {task['name']}\n剩余时间: {task['remaining'] // 60}:{task['remaining'] % 60:02d}")
            self.mini_status_label.config(text=f"当前任务: {task['name']}\n剩余时间: {task['remaining'] // 60}:{task['remaining'] % 60:02d}")
            self.countdown(task['remaining'])
            self.highlight_current_task()
        else:
            self.all_tasks_completed()

    def all_tasks_completed(self):
        response = messagebox.askyesno("提示", "所有任务已完成！是否要重复任务？")
        if response:
            self.reset_tasks()
            self.current_task_label.config(text="所有任务已重置，\n点击开始以重新开始。")
            self.mini_status_label.config(text="所有任务已重置，\n点击开始以重新开始。")
            self.start_button.config(state=tk.NORMAL)  # 使“开始”按钮可用
        else:
            self.timer_running = False
            self.current_task_label.config(text="所有任务已完成。")
            self.mini_status_label.config(text="所有任务已完成。")
            # 更新历史记录
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            completed_tasks = [f"{task['name']} ({task['time']}分钟)" for task in self.tasks]
            self.history[now] = completed_tasks
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
            self.current_task_label.config(text=f"已完成: {task['name']}")
            self.mini_status_label.config(text=f"已完成: {task['name']}")
            self.play_sound()
            self.show_notification()
        else:
            mins, secs = divmod(task['remaining'], 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            self.current_task_label.config(text=f"当前任务: {task['name']}\n剩余时间: {timeformat}")
            self.mini_status_label.config(text=f"当前任务: {task['name']}\n剩余时间: {timeformat}")
            task['remaining'] -= 1
            self.timer_id = self.root.after(1000, self.countdown)

    def play_sound(self):
        try:
            # 加载音乐文件
            pygame.mixer.music.load(self.sound_file)
            # 播放音乐
            pygame.mixer.music.play()
        except Exception as e:
            print(f"无法播放声音文件: {e}")

    def stop_sound(self):
        try:
            # 停止 pygame 混音器中的音乐
            pygame.mixer.music.stop()
            self.stop_music_button.config(state=tk.DISABLED)  # 禁用停止音乐按钮
            self.mini_stop_music_button.config(state=tk.DISABLED)  # 禁用迷你模式停止音乐按钮
            self.stop_timer()  # 停止当前任务
        except Exception as e:
            print(f"无法停止声音: {e}")

    def show_notification(self):
        task_name = self.tasks[self.current_task_index]['name']
        try:
            notification.notify(
                title="番茄钟计时器",
                message=f'任务 "{task_name}" 完成',
                app_icon=None,
                timeout=10
            )
            self.stop_music_button.config(state=tk.NORMAL)
            self.mini_stop_music_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Error showing notification: {e}")

    def load_settings(self):
        if not os.path.exists(self.data_directory):
            os.makedirs(self.data_directory)
        settings_path = os.path.join(self.data_directory, "settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, "r") as file:
                settings = json.load(file)
                self.sound_file = settings.get("sound_file", self.sound_file)
                self.minimize_to_tray = settings.get("minimize_to_tray", self.minimize_to_tray)

    def save_settings(self):
        settings_path = os.path.join(self.data_directory, "settings.json")
        with open(settings_path, "w") as file:
            json.dump({
                "sound_file": self.sound_file,
                "minimize_to_tray": self.minimize_to_tray
            }, file)

    def load_tasks(self):
        tasks_path = os.path.join(self.data_directory, "tasks.json")
        if os.path.exists(tasks_path):
            with open(tasks_path, "r") as file:
                self.tasks = json.load(file)
                self.update_task_listbox()

    def save_tasks(self):
        tasks_path = os.path.join(self.data_directory, "tasks.json")
        with open(tasks_path, "w") as file:
            json.dump(self.tasks, file)

    def load_history(self):
        history_path = os.path.join(self.data_directory, "history.json")
        if os.path.exists(history_path):
            with open(history_path, "r") as file:
                try:
                    loaded_history = json.load(file)
                    if isinstance(loaded_history, dict):
                        self.history = loaded_history
                    else:
                        print("历史记录文件格式不正确，已重置。")
                        self.history = {}
                except json.JSONDecodeError:
                    print("历史记录文件损坏，已重置。")
                    self.history = {}

    def save_history(self):
        history_path = os.path.join(self.data_directory, "history.json")
        with open(history_path, "w") as file:
            json.dump(self.history, file)

    def view_history(self):
        history_text = "\n".join([f"{k}: {v}" for k, v in self.history.items()])
        messagebox.showinfo("历史记录", history_text)

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")

        # 自定义音乐
        def choose_sound_file():
            sound_file = filedialog.askopenfilename(title="选择声音文件", filetypes=[("Audio files", "*.mp3 *.wav")])
            if sound_file:
                self.sound_file = sound_file
                self.save_settings()
                messagebox.showinfo("提示", "声音文件设置成功。")

        sound_button = tk.Button(settings_window, text="选择声音文件", command=choose_sound_file)
        sound_button.pack(pady=5, padx=5)

        # 最小化到系统托盘
        def toggle_minimize_to_tray():
            self.minimize_to_tray = minimize_to_tray_var.get()
            self.save_settings()

        minimize_to_tray_var = tk.BooleanVar(value=False)
        minimize_to_tray_checkbutton = tk.Checkbutton(settings_window, text="最小化到系统托盘", variable=minimize_to_tray_var, command=toggle_minimize_to_tray)
        minimize_to_tray_checkbutton.pack(pady=5, padx=5)

        # 导入数据
        def import_data():
            data_file = filedialog.askopenfilename(title="导入数据文件", filetypes=[("JSON files", "*.json")])
            if data_file:
                with open(data_file, "r") as file:
                    imported_data = json.load(file)
                    self.tasks = imported_data.get("tasks", [])
                    self.history = imported_data.get("history", {})
                    self.sound_file = imported_data.get("sound_file", "ding.mp3")
                    self.minimize_to_tray = imported_data.get("minimize_to_tray", False)
                    self.update_task_listbox()
                    self.save_settings()
                    messagebox.showinfo("提示", "数据导入成功。")

        import_button = tk.Button(settings_window, text="导入数据", command=import_data)
        import_button.pack(pady=5, padx=5)

        # 导出数据
        def export_data():
            data_file = filedialog.asksaveasfilename(title="导出数据文件", filetypes=[("JSON files", "*.json")], defaultextension=".json")
            if data_file:
                data_to_export = {
                    "tasks": self.tasks,
                    "history": self.history,
                    "sound_file": self.sound_file,
                    "minimize_to_tray": self.minimize_to_tray
                }
                with open(data_file, "w") as file:
                    json.dump(data_to_export, file)
                messagebox.showinfo("提示", "数据导出成功。")

        export_button = tk.Button(settings_window, text="导出数据", command=export_data)
        export_button.pack(pady=5, padx=5)

    def on_close(self):
        if self.minimize_to_tray:
            self.root.withdraw()
            self.create_tray_icon()
        else:
            self.root.destroy()

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.text((10, 25), "P", fill=(0, 0, 0))
        menu = (pystray.MenuItem('显示', self.restore_window),
                pystray.MenuItem('退出', self.quit_application))
        icon = pystray.Icon("pomodoro", image, "番茄钟计时器", menu)
        icon.run()

    def restore_window(self):
        self.root.deiconify()
        self.tray_icon.stop()

    def quit_application(self):
        self.root.quit()
        self.tray_icon.stop()

    def minimize_to_tray(self):
        self.mini_window.withdraw()
        self.create_tray_icon()

    def restore_main_window(self):
        self.mini_window.withdraw()
        self.root.deiconify()
        self.mini_mode = False

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()