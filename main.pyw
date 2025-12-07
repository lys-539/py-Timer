#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正向计时器主程序
Author: Claude Code
Date: 2025-11-03
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import time
import winreg
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates



class TimeCounter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("正向计时器")

        # 初始化变量
        self.is_running = False
        self.start_time = None
        self.pause_time = None
        self.total_paused_time = 0
        self.current_session = None
        self.sessions = []
        self.todos = []
        self.selected_todo_index = None
        self.listbox_to_session_map = {}  # 列表框索引到历史记录索引的映射
        self.todo_changed = False  # 跟踪待办是否被修改

        # 体重记录相关变量
        self.weight_records = []
        self.selected_weight_index = None

        # 闹钟相关变量
        self.alarms = []
        self.selected_alarm_index = None
        self.alarm_changed = False

        # 体重目标相关变量
        self.weight_target = None

        # 加载自定义字体
        self.custom_font = None
        self.load_custom_font()

        # 配置样式
        self.configure_styles()

        # 加载历史记录和待办列表
        self.load_history()
        self.load_todos()
        self.load_weight_records()
        self.load_alarms()
        self.load_weight_target()

        # 加载不透明度设置（必须在setup_window之前调用）
        self.load_opacity_settings()

        # 加载自启动设置
        self.load_autostart_settings()

        # 设置窗口属性（必须在加载设置之后调用）
        self.setup_window()

        # 创建界面
        self.create_widgets()

        # 启动定时器更新
        self.update_timer()

    def load_custom_font(self):
        """加载自定义字体"""
        try:
            # 加载ttf字体文件
            font_path = "HarmonyOS_Sans_SC_Medium.ttf"
            if os.path.exists(font_path):
                # 使用tkinter的字体模块加载字体
                self.custom_font = ("HarmonyOS Sans SC Medium", 10)
                # 注意：tkinter原生不支持直接加载ttf文件，这里使用字体名称
                # 如果字体未安装，可能需要使用其他方法
            else:
                print(f"字体文件 {font_path} 不存在，使用系统默认字体")
                self.custom_font = None
        except Exception as e:
            print(f"加载字体失败: {e}")
            self.custom_font = None

    def configure_styles(self):
        """配置样式"""
        if self.custom_font:
            # 配置按钮样式使用自定义字体
            style = ttk.Style()
            style.configure("Custom.TButton", font=self.custom_font)

    def setup_window(self):
        """设置窗口属性"""
        # 设置窗口大小和位置（使用保存的设置）
        geometry = f"{self.saved_window_geometry['width']}x{self.saved_window_geometry['height']}+{self.saved_window_geometry['x']}+{self.saved_window_geometry['y']}"
        self.root.geometry(geometry)

        # 设置窗口始终置顶
        self.root.attributes('-topmost', self.saved_always_on_top)

        # 设置窗口半透明（Windows系统）
        try:
            self.root.attributes('-alpha', self.saved_opacity)
        except:
            pass  # 如果系统不支持透明度，忽略错误

        # 设置窗口无边框但可拖动
        self.root.overrideredirect(True)

        # 绑定拖动事件
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<ButtonRelease-1>', self.stop_move)
        self.root.bind('<B1-Motion>', self.do_move)

        # 绑定窗口调整大小事件
        self.root.bind('<Motion>', self.on_mouse_move)
        self.root.bind('<Button-1>', self.start_resize, add='+')
        self.root.bind('<B1-Motion>', self.do_resize, add='+')
        self.root.bind('<ButtonRelease-1>', self.stop_resize, add='+')

        # 初始化调整大小状态
        self.resizing = False
        self.resize_edge = None

    def start_move(self, event):
        """开始拖动窗口"""
        # 检查是否在滑块上点击，如果是则不开始窗口拖动
        widget = event.widget
        if widget == self.opacity_slider:
            return

        # 检查是否在可调整大小的边缘，如果是则不开始拖动
        if self.resize_edge:
            return

        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        """停止拖动窗口"""
        self.x = None
        self.y = None
        # 保存设置
        self.save_settings()

    def do_move(self, event):
        """执行窗口拖动"""
        # 检查是否设置了拖动起始坐标
        if not hasattr(self, 'x') or self.x is None:
            return

        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def on_mouse_move(self, event):
        """鼠标移动时检查是否在可调整大小的边缘"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # 定义边缘检测区域（5像素宽）
        edge_size = 5

        # 检查是否在右侧边缘
        if event.x >= width - edge_size and event.x <= width:
            self.root.config(cursor="size_we")
            self.resize_edge = "right"
        # 检查是否在底部边缘
        elif event.y >= height - edge_size and event.y <= height:
            self.root.config(cursor="size_ns")
            self.resize_edge = "bottom"
        # 检查是否在右下角
        elif (event.x >= width - edge_size and event.x <= width and
              event.y >= height - edge_size and event.y <= height):
            self.root.config(cursor="size_nw_se")
            self.resize_edge = "bottom_right"
        else:
            self.root.config(cursor="")
            self.resize_edge = None

    def start_resize(self, event):
        """开始调整窗口大小"""
        if self.resize_edge:
            self.resizing = True
            self.resize_start_x = event.x_root
            self.resize_start_y = event.y_root
            self.resize_start_width = self.root.winfo_width()
            self.resize_start_height = self.root.winfo_height()

    def do_resize(self, event):
        """执行窗口大小调整"""
        if self.resizing and self.resize_edge:
            delta_x = event.x_root - self.resize_start_x
            delta_y = event.y_root - self.resize_start_y

            new_width = self.resize_start_width
            new_height = self.resize_start_height

            if self.resize_edge in ["right", "bottom_right"]:
                new_width = max(400, self.resize_start_width + delta_x)  # 最小宽度400

            if self.resize_edge in ["bottom", "bottom_right"]:
                new_height = max(300, self.resize_start_height + delta_y)  # 最小高度300

            self.root.geometry(f"{new_width}x{new_height}")

    def stop_resize(self, event):
        """停止调整窗口大小"""
        self.resizing = False
        self.resize_edge = None
        # 保存设置
        self.save_settings()

    def create_widgets(self):
        """创建界面组件"""
        # 主框架 - 左中右三栏
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧计时器区域
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 时间显示
        self.time_label = ttk.Label(
            left_frame,
            text="00:00:00",
            font=("HarmonyOS Sans SC Medium", 24, "bold") if self.custom_font else ("Arial", 24, "bold")
            #font=("Arial", 24, "bold")
        )
        self.time_label.pack(pady=10)

        # 当前时间显示
        self.current_time_label = ttk.Label(
            left_frame,
            text="",
            font=("HarmonyOS Sans SC Medium", 10) if self.custom_font else ("Arial", 10)
        )
        self.current_time_label.pack(pady=(0, 10))

        # 控制按钮框架
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(pady=10)

        # 控制按钮
        self.start_button = ttk.Button(
            button_frame,
            text="开始",
            command=self.start_timer,
            style="Custom.TButton" if self.custom_font else None
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(
            button_frame,
            text="暂停",
            command=self.pause_timer,
            state=tk.DISABLED,
            style="Custom.TButton" if self.custom_font else None
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="停止",
            command=self.stop_timer,
            state=tk.DISABLED,
            style="Custom.TButton" if self.custom_font else None
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 关闭按钮
        close_button = ttk.Button(
            left_frame,
            text="关闭",
            command=self.close_app,
            style="Custom.TButton" if self.custom_font else None
        )
        close_button.pack(pady=5)

        # 不透明度控制框架
        opacity_frame = ttk.Frame(left_frame)
        opacity_frame.pack(fill=tk.X, pady=10)

        # 不透明度标签
        opacity_label = ttk.Label(opacity_frame, text="不透明度:")
        if self.custom_font:
            opacity_label.configure(font=self.custom_font)
        opacity_label.pack(anchor=tk.W)

        # 不透明度控制行（滑块和输入框在同一行）
        opacity_row_frame = ttk.Frame(opacity_frame)
        opacity_row_frame.pack(fill=tk.X, pady=(5, 0))

        # 滑块占据大部分空间
        self.opacity_var = tk.DoubleVar(value=self.saved_opacity)  # 使用保存的设置
        opacity_slider = ttk.Scale(
            opacity_row_frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.opacity_var,
            command=self.on_opacity_change
        )
        opacity_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # 存储滑块引用
        self.opacity_slider = opacity_slider

        # 输入框和标签（在滑块右侧）
        self.opacity_entry_var = tk.StringVar(value=str(int(self.saved_opacity * 100)))
        opacity_entry = ttk.Entry(
            opacity_row_frame,
            textvariable=self.opacity_entry_var,
            width=5
        )
        if self.custom_font:
            opacity_entry.configure(font=self.custom_font)
        opacity_entry.pack(side=tk.LEFT, padx=(0, 5))

        # 百分比标签
        percent_label = ttk.Label(opacity_row_frame, text="%")
        if self.custom_font:
            percent_label.configure(font=self.custom_font)
        percent_label.pack(side=tk.LEFT)

        # 绑定输入框事件
        opacity_entry.bind('<Return>', self.on_opacity_entry_change)
        opacity_entry.bind('<FocusOut>', self.on_opacity_entry_change)

        # 窗口置顶复选框
        self.always_on_top_var = tk.BooleanVar(value=self.saved_always_on_top)
        always_on_top_checkbox = ttk.Checkbutton(
            left_frame,
            text="窗口置顶",
            variable=self.always_on_top_var,
            command=self.on_always_on_top_change
        )
        always_on_top_checkbox.pack(anchor=tk.W, pady=(10, 0))

        # 开机自启动复选框
        self.autostart_var = tk.BooleanVar(value=self.autostart_enabled)
        autostart_checkbox = ttk.Checkbutton(
            left_frame,
            text="开机自启动",
            variable=self.autostart_var,
            command=self.on_autostart_change
        )
        autostart_checkbox.pack(anchor=tk.W, pady=(10, 0))

        # 历史记录标签
        history_label = ttk.Label(left_frame, text="历史记录:")
        if self.custom_font:
            history_label.configure(font=self.custom_font)
        history_label.pack(anchor=tk.W, pady=(0, 5))

        # 历史记录列表
        self.create_history_list(left_frame)

        # 中间待办列表区域
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 5))

        # 闹钟功能
        self.create_alarm_section(middle_frame)

        # 待办列表
        self.create_todo_list(middle_frame)

        # 右侧体重记录区域
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 体重记录
        self.create_weight_tracking(right_frame)

    def create_history_list(self, parent):
        """创建历史记录列表"""
        # 创建框架
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建列表框
        self.history_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=8,
            selectbackground='white',  # 选中时背景为白色
            selectforeground='black',  # 选中时文字为黑色
            highlightthickness=0,      # 去除高亮边框
            activestyle='underline'    # 激活时显示下划线
        )
        if self.custom_font:
            self.history_listbox.configure(font=self.custom_font)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_listbox.yview)

        # 绑定右键菜单
        self.history_listbox.bind("<Button-3>", self.show_context_menu)

        # 更新历史记录显示
        self.update_history_display()

    def create_alarm_section(self, parent):
        """创建闹钟功能区域"""
        # 闹钟标题
        alarm_title_label = ttk.Label(parent, text="闹钟")
        if self.custom_font:
            alarm_title_label.configure(font=self.custom_font)
        alarm_title_label.pack(anchor=tk.W, pady=(0, 5))

        # 闹钟列表框架
        alarm_list_frame = ttk.Frame(parent, height=80)
        alarm_list_frame.pack(fill=tk.X, pady=(0, 10))
        alarm_list_frame.pack_propagate(False)  # 防止框架收缩

        # 闹钟列表滚动条
        alarm_scrollbar = ttk.Scrollbar(alarm_list_frame)
        alarm_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 闹钟列表框
        self.alarm_listbox = tk.Listbox(
            alarm_list_frame,
            yscrollcommand=alarm_scrollbar.set,
            height=4,
            selectbackground='white',  # 选中时背景为白色
            selectforeground='black',  # 选中时文字为黑色
            highlightthickness=0,      # 去除高亮边框
            activestyle='underline'    # 激活时显示下划线
        )
        if self.custom_font:
            self.alarm_listbox.configure(font=self.custom_font)
        self.alarm_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alarm_scrollbar.config(command=self.alarm_listbox.yview)

        # 绑定闹钟列表事件
        self.alarm_listbox.bind("<Button-1>", self.on_alarm_select)
        self.alarm_listbox.bind("<Button-3>", self.show_alarm_context_menu)

        # 闹钟操作按钮框架
        alarm_button_frame = ttk.Frame(parent)
        alarm_button_frame.pack(fill=tk.X, pady=5)

        # 添加闹钟按钮
        add_alarm_button = ttk.Button(
            alarm_button_frame,
            text="添加闹钟",
            command=self.add_alarm,
            style="Custom.TButton" if self.custom_font else None
        )
        add_alarm_button.pack(side=tk.LEFT, padx=2)

        # 删除闹钟按钮（初始禁用）
        self.delete_alarm_button = ttk.Button(
            alarm_button_frame,
            text="删除闹钟",
            command=self.delete_alarm,
            state=tk.DISABLED,
            style="Custom.TButton" if self.custom_font else None
        )
        self.delete_alarm_button.pack(side=tk.LEFT, padx=2)

        # 闹钟编辑分区
        self.create_alarm_edit_area(parent)

        # 更新闹钟显示
        self.update_alarm_display()

    def create_alarm_edit_area(self, parent):
        """创建闹钟编辑分区"""
        # 编辑分区标题
        edit_title_label = ttk.Label(parent, text="编辑闹钟")
        if self.custom_font:
            edit_title_label.configure(font=self.custom_font)
        edit_title_label.pack(anchor=tk.W, pady=(10, 5))

        # 编辑分区框架
        edit_frame = ttk.Frame(parent)
        edit_frame.pack(fill=tk.X, pady=5)

        # 时间标签和输入框
        time_label = ttk.Label(edit_frame, text="时间:")
        if self.custom_font:
            time_label.configure(font=self.custom_font)
        time_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.alarm_time_entry = ttk.Entry(edit_frame, width=15)
        if self.custom_font:
            self.alarm_time_entry.configure(font=self.custom_font)
        self.alarm_time_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.alarm_time_entry.insert(0, datetime.now().strftime('%H:%M'))
        self.alarm_time_entry.bind('<KeyRelease>', self.on_alarm_content_change)

        # 重复标签和选择框
        repeat_label = ttk.Label(edit_frame, text="重复:")
        if self.custom_font:
            repeat_label.configure(font=self.custom_font)
        repeat_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.alarm_repeat_var = tk.StringVar(value="不重复")
        repeat_combo = ttk.Combobox(edit_frame, textvariable=self.alarm_repeat_var,
                                   values=["不重复", "每天", "工作日", "周末"], state="readonly", width=10)
        if self.custom_font:
            repeat_combo.configure(font=self.custom_font)
        repeat_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        repeat_combo.bind('<<ComboboxSelected>>', self.on_alarm_content_change)

        # 标签标签和输入框
        label_label = ttk.Label(edit_frame, text="标签:")
        if self.custom_font:
            label_label.configure(font=self.custom_font)
        label_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.alarm_label_entry = ttk.Entry(edit_frame, width=30)
        if self.custom_font:
            self.alarm_label_entry.configure(font=self.custom_font)
        self.alarm_label_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W+tk.E, padx=(0, 5), pady=(5, 0))
        self.alarm_label_entry.insert(0, "闹钟")
        self.alarm_label_entry.bind('<KeyRelease>', self.on_alarm_content_change)

        # 启用状态复选框
        self.alarm_enabled_var = tk.BooleanVar(value=True)
        alarm_enabled_checkbox = ttk.Checkbutton(
            edit_frame,
            text="启用闹钟",
            variable=self.alarm_enabled_var,
            command=self.on_alarm_content_change
        )
        alarm_enabled_checkbox.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=(0, 5), pady=(5, 0))

        # 保存和取消按钮框架
        edit_button_frame = ttk.Frame(edit_frame)
        edit_button_frame.grid(row=3, column=0, columnspan=4, sticky=tk.W+tk.E, pady=(10, 0))

        # 保存按钮（初始禁用）
        self.save_alarm_button = ttk.Button(
            edit_button_frame,
            text="保存",
            command=self.save_alarm,
            state=tk.DISABLED,
            style="Custom.TButton" if self.custom_font else None
        )
        self.save_alarm_button.pack(side=tk.LEFT, padx=(0, 5))

        # 取消按钮
        cancel_alarm_button = ttk.Button(
            edit_button_frame,
            text="取消",
            command=self.cancel_alarm_edit,
            style="Custom.TButton" if self.custom_font else None
        )
        cancel_alarm_button.pack(side=tk.LEFT)

        # 配置网格权重
        edit_frame.columnconfigure(1, weight=1)
        edit_frame.columnconfigure(3, weight=1)

    def create_todo_list(self, parent):
        """创建待办列表"""
        # 待办列表标题
        todo_title_label = ttk.Label(parent, text="待办事项")
        if self.custom_font:
            todo_title_label.configure(font=self.custom_font)
        todo_title_label.pack(anchor=tk.W, pady=(0, 5))

        # 待办列表框架
        todo_list_frame = ttk.Frame(parent)
        todo_list_frame.pack(fill=tk.BOTH, expand=True)

        # 待办列表滚动条
        todo_scrollbar = ttk.Scrollbar(todo_list_frame)
        todo_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 待办列表框
        self.todo_listbox = tk.Listbox(
            todo_list_frame,
            yscrollcommand=todo_scrollbar.set,
            height=8,
            selectbackground='white',  # 选中时背景为白色
            selectforeground='black',  # 选中时文字为黑色
            highlightthickness=0,      # 去除高亮边框
            activestyle='underline'    # 激活时显示下划线
        )
        if self.custom_font:
            self.todo_listbox.configure(font=self.custom_font)
        self.todo_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        todo_scrollbar.config(command=self.todo_listbox.yview)

        # 绑定待办列表事件
        self.todo_listbox.bind("<Button-1>", self.on_todo_select)
        self.todo_listbox.bind("<Button-3>", self.show_todo_context_menu)

        # 待办操作按钮框架
        todo_button_frame = ttk.Frame(parent)
        todo_button_frame.pack(fill=tk.X, pady=5)

        # 添加待办按钮
        add_todo_button = ttk.Button(
            todo_button_frame,
            text="添加待办",
            command=self.add_empty_todo,
            style="Custom.TButton" if self.custom_font else None
        )
        add_todo_button.pack(side=tk.LEFT, padx=2)

        # 删除待办按钮（初始禁用）
        self.delete_todo_button = ttk.Button(
            todo_button_frame,
            text="删除待办",
            command=self.delete_todo,
            state=tk.DISABLED,
            style="Custom.TButton" if self.custom_font else None
        )
        self.delete_todo_button.pack(side=tk.LEFT, padx=2)

        # 待办编辑分区
        self.create_todo_edit_area(parent)

        # 更新待办列表显示
        self.update_todo_display()

    def create_weight_tracking(self, parent):
        """创建体重记录区域"""
        # 体重记录标题
        weight_title_label = ttk.Label(parent, text="每日体重记录")
        if self.custom_font:
            weight_title_label.configure(font=self.custom_font)
        weight_title_label.pack(anchor=tk.W, pady=(0, 5))

        # 体重目标设置
        self.create_weight_target_section(parent)

    def create_weight_target_section(self, parent):
        """创建体重目标设置区域"""
        # 目标设置框架
        target_frame = ttk.Frame(parent)
        target_frame.pack(fill=tk.X, pady=(0, 10))

        # 目标标签
        target_label = ttk.Label(target_frame, text="目标体重:")
        if self.custom_font:
            target_label.configure(font=self.custom_font)
        target_label.pack(side=tk.LEFT, padx=(0, 5))

        # 目标输入框
        self.weight_target_var = tk.StringVar()
        self.weight_target_entry = ttk.Entry(
            target_frame,
            textvariable=self.weight_target_var,
            width=8
        )
        if self.custom_font:
            self.weight_target_entry.configure(font=self.custom_font)
        self.weight_target_entry.pack(side=tk.LEFT, padx=(0, 5))

        # 单位标签
        unit_label = ttk.Label(target_frame, text="kg")
        if self.custom_font:
            unit_label.configure(font=self.custom_font)
        unit_label.pack(side=tk.LEFT, padx=(0, 10))

        # 设置目标按钮
        set_target_button = ttk.Button(
            target_frame,
            text="设置目标",
            command=self.set_weight_target,
            style="Custom.TButton" if self.custom_font else None
        )
        set_target_button.pack(side=tk.LEFT, padx=(0, 5))

        # 清除目标按钮
        clear_target_button = ttk.Button(
            target_frame,
            text="清除目标",
            command=self.clear_weight_target,
            style="Custom.TButton" if self.custom_font else None
        )
        clear_target_button.pack(side=tk.LEFT)

        # 显示当前目标
        self.target_display_label = ttk.Label(target_frame, text="")
        if self.custom_font:
            self.target_display_label.configure(font=self.custom_font)
        self.target_display_label.pack(side=tk.RIGHT)

        # 更新目标显示
        self.update_target_display()

        # 体重图表区域
        self.create_weight_chart(parent)

        # 体重记录列表框架
        weight_list_frame = ttk.Frame(parent)
        weight_list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 体重记录列表滚动条
        weight_scrollbar = ttk.Scrollbar(weight_list_frame)
        weight_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 体重记录列表框
        self.weight_listbox = tk.Listbox(
            weight_list_frame,
            yscrollcommand=weight_scrollbar.set,
            height=8,
            selectbackground='white',  # 选中时背景为白色
            selectforeground='black',  # 选中时文字为黑色
            highlightthickness=0,      # 去除高亮边框
            activestyle='underline'    # 激活时显示下划线
        )
        if self.custom_font:
            self.weight_listbox.configure(font=self.custom_font)
        self.weight_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        weight_scrollbar.config(command=self.weight_listbox.yview)

        # 绑定体重记录列表事件
        self.weight_listbox.bind("<Button-1>", self.on_weight_select)
        self.weight_listbox.bind("<Button-3>", self.show_weight_context_menu)

        # 体重记录操作按钮框架
        weight_button_frame = ttk.Frame(parent)
        weight_button_frame.pack(fill=tk.X, pady=5)

        # 添加体重记录按钮
        add_weight_button = ttk.Button(
            weight_button_frame,
            text="添加记录",
            command=self.add_weight_record,
            style="Custom.TButton" if self.custom_font else None
        )
        add_weight_button.pack(side=tk.LEFT, padx=2)

        # 删除体重记录按钮（初始禁用）
        self.delete_weight_button = ttk.Button(
            weight_button_frame,
            text="删除记录",
            command=self.delete_weight_record,
            state=tk.DISABLED,
            style="Custom.TButton" if self.custom_font else None
        )
        self.delete_weight_button.pack(side=tk.LEFT, padx=2)

        # 体重记录编辑分区
        self.create_weight_edit_area(parent)

        # 更新体重记录显示
        self.update_weight_display()

    def create_weight_chart(self, parent):
        """创建体重图表"""
        # 图表框架
        chart_frame = ttk.Frame(parent, height=150)
        chart_frame.pack(fill=tk.X, pady=(0, 10))
        chart_frame.pack_propagate(False)  # 防止框架收缩

        # 创建matplotlib图表
        self.weight_fig, self.weight_ax = plt.subplots(figsize=(5, 2), dpi=80)
        self.weight_fig.patch.set_alpha(0)  # 设置图表背景透明
        self.weight_ax.patch.set_alpha(0)   # 设置坐标轴背景透明

        # 创建图表画布
        self.weight_canvas = FigureCanvasTkAgg(self.weight_fig, chart_frame)
        self.weight_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 初始化图表
        self.update_weight_chart()

    def create_weight_edit_area(self, parent):
        """创建体重记录编辑分区"""
        # 编辑分区标题
        edit_title_label = ttk.Label(parent, text="编辑体重记录")
        if self.custom_font:
            edit_title_label.configure(font=self.custom_font)
        edit_title_label.pack(anchor=tk.W, pady=(10, 5))

        # 编辑分区框架
        edit_frame = ttk.Frame(parent)
        edit_frame.pack(fill=tk.X, pady=5)

        # 日期标签和输入框
        date_label = ttk.Label(edit_frame, text="日期:")
        if self.custom_font:
            date_label.configure(font=self.custom_font)
        date_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.weight_date_entry = ttk.Entry(edit_frame, width=15)
        if self.custom_font:
            self.weight_date_entry.configure(font=self.custom_font)
        self.weight_date_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.weight_date_entry.insert(0, datetime.now().strftime('%Y.%m.%d'))
        self.weight_date_entry.bind('<KeyRelease>', self.on_weight_content_change)

        # 体重标签和输入框
        weight_label = ttk.Label(edit_frame, text="体重(kg):")
        if self.custom_font:
            weight_label.configure(font=self.custom_font)
        weight_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.weight_value_entry = ttk.Entry(edit_frame, width=10)
        if self.custom_font:
            self.weight_value_entry.configure(font=self.custom_font)
        self.weight_value_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        self.weight_value_entry.bind('<KeyRelease>', self.on_weight_content_change)

        # 备注标签和输入框
        note_label = ttk.Label(edit_frame, text="备注:")
        if self.custom_font:
            note_label.configure(font=self.custom_font)
        note_label.grid(row=1, column=0, sticky=tk.W+tk.N, padx=(0, 5), pady=(5, 0))
        self.weight_note_entry = ttk.Entry(edit_frame, width=30)
        if self.custom_font:
            self.weight_note_entry.configure(font=self.custom_font)
        self.weight_note_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W+tk.E, padx=(0, 5), pady=(5, 0))
        self.weight_note_entry.bind('<KeyRelease>', self.on_weight_content_change)

        # 保存和取消按钮框架
        edit_button_frame = ttk.Frame(edit_frame)
        edit_button_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W+tk.E, pady=(10, 0))

        # 保存按钮（初始禁用）
        self.save_weight_button = ttk.Button(
            edit_button_frame,
            text="保存",
            command=self.save_weight_record,
            state=tk.DISABLED,
            style="Custom.TButton" if self.custom_font else None
        )
        self.save_weight_button.pack(side=tk.LEFT, padx=(0, 5))

        # 取消按钮
        cancel_weight_button = ttk.Button(
            edit_button_frame,
            text="取消",
            command=self.cancel_weight_edit,
            style="Custom.TButton" if self.custom_font else None
        )
        cancel_weight_button.pack(side=tk.LEFT)

        # 配置网格权重
        edit_frame.columnconfigure(1, weight=1)
        edit_frame.columnconfigure(3, weight=1)

    def create_todo_edit_area(self, parent):
        """创建待办编辑分区"""
        # 编辑分区标题
        edit_title_label = ttk.Label(parent, text="编辑待办")
        if self.custom_font:
            edit_title_label.configure(font=self.custom_font)
        edit_title_label.pack(anchor=tk.W, pady=(10, 5))

        # 编辑分区框架
        edit_frame = ttk.Frame(parent)
        edit_frame.pack(fill=tk.X, pady=5)

        # 标题标签和输入框
        title_label = ttk.Label(edit_frame, text="标题:")
        if self.custom_font:
            title_label.configure(font=self.custom_font)
        title_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.todo_title_entry = ttk.Entry(edit_frame, width=30)
        if self.custom_font:
            self.todo_title_entry.configure(font=self.custom_font)
        self.todo_title_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, 5))
        self.todo_title_entry.bind('<KeyRelease>', self.on_todo_content_change)

        # 描述标签和文本框
        desc_label = ttk.Label(edit_frame, text="描述:")
        if self.custom_font:
            desc_label.configure(font=self.custom_font)
        desc_label.grid(row=1, column=0, sticky=tk.W+tk.N, padx=(0, 5), pady=(5, 0))
        self.todo_desc_text = tk.Text(edit_frame, width=30, height=4)
        if self.custom_font:
            self.todo_desc_text.configure(font=self.custom_font)
        self.todo_desc_text.grid(row=1, column=1, sticky=tk.W+tk.E+tk.N+tk.S, padx=(0, 5), pady=(5, 0))
        self.todo_desc_text.bind('<KeyRelease>', self.on_todo_content_change)

        # 优先级标签和选择框
        priority_label = ttk.Label(edit_frame, text="优先级:")
        if self.custom_font:
            priority_label.configure(font=self.custom_font)
        priority_label.grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.todo_priority_var = tk.StringVar(value="中")
        priority_combo = ttk.Combobox(edit_frame, textvariable=self.todo_priority_var,
                                     values=["低", "中", "高"], state="readonly", width=10)
        if self.custom_font:
            priority_combo.configure(font=self.custom_font)
        priority_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        priority_combo.bind('<<ComboboxSelected>>', self.on_todo_content_change)

        # 状态标签和选择框
        status_label = ttk.Label(edit_frame, text="状态:")
        if self.custom_font:
            status_label.configure(font=self.custom_font)
        status_label.grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.todo_status_var = tk.StringVar(value="待办")
        status_combo = ttk.Combobox(edit_frame, textvariable=self.todo_status_var,
                                   values=["待办", "进行中", "已完成"], state="readonly", width=10)
        if self.custom_font:
            status_combo.configure(font=self.custom_font)
        status_combo.grid(row=3, column=1, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        status_combo.bind('<<ComboboxSelected>>', self.on_todo_content_change)

        # 保存和取消按钮框架
        edit_button_frame = ttk.Frame(edit_frame)
        edit_button_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(10, 0))

        # 保存按钮（初始禁用）
        self.save_todo_button = ttk.Button(
            edit_button_frame,
            text="保存",
            command=self.save_todo,
            state=tk.DISABLED,
            style="Custom.TButton" if self.custom_font else None
        )
        self.save_todo_button.pack(side=tk.LEFT, padx=(0, 5))

        # 取消按钮
        cancel_todo_button = ttk.Button(
            edit_button_frame,
            text="取消",
            command=self.cancel_todo_edit,
            style="Custom.TButton" if self.custom_font else None
        )
        cancel_todo_button.pack(side=tk.LEFT)

        # 配置网格权重
        edit_frame.columnconfigure(1, weight=1)
        edit_frame.rowconfigure(1, weight=1)

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 获取点击位置的项目
        listbox_index = self.history_listbox.nearest(event.y)
        if listbox_index >= 0:
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(listbox_index)

            # 获取实际的历史记录索引
            session_index = self.listbox_to_session_map.get(listbox_index)
            if session_index is not None:
                # 创建菜单
                context_menu = tk.Menu(self.root, tearoff=0)
                context_menu.add_command(
                    label="重命名",
                    command=lambda: self.rename_session(session_index)
                )
                context_menu.add_separator()
                context_menu.add_command(
                    label="删除",
                    command=lambda: self.delete_session(session_index)
                )

                # 显示菜单
                context_menu.post(event.x_root, event.y_root)

    def rename_session(self, index):
        """重命名计时段落"""
        if 0 <= index < len(self.sessions):
            session = self.sessions[index]
            new_name = simpledialog.askstring(
                "重命名",
                "输入新的段落名称:",
                initialvalue=session.get('name', f'段落 {index+1}')
            )
            if new_name:
                session['name'] = new_name
                self.save_history()
                self.update_history_display()

    def delete_session(self, index):
        """删除计时段落"""
        if 0 <= index < len(self.sessions):
            if messagebox.askyesno("确认删除", "确定要删除这个计时段落吗？"):
                self.sessions.pop(index)
                self.save_history()
                self.update_history_display()

    def start_timer(self):
        """开始计时"""
        if not self.is_running:
            self.is_running = True
            if self.pause_time:
                # 从暂停状态恢复
                self.total_paused_time += time.time() - self.pause_time
                self.pause_time = None
            else:
                # 新的计时开始
                self.start_time = time.time()
                self.total_paused_time = 0

            # 更新按钮状态
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)

    def pause_timer(self):
        """暂停计时"""
        if self.is_running:
            self.is_running = False
            self.pause_time = time.time()

            # 更新按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)

    def stop_timer(self):
        """停止计时并保存记录"""
        if self.start_time:
            # 计算总时间
            end_time = time.time()
            if self.pause_time:
                total_time = self.pause_time - self.start_time - self.total_paused_time
            else:
                total_time = end_time - self.start_time - self.total_paused_time

            # 创建新的计时段落
            session = {
                'name': f'段落 {len(self.sessions) + 1}',
                'start_time': datetime.fromtimestamp(self.start_time).strftime('%Y.%m.%d %H:%M:%S'),
                'duration': total_time,
                'end_time': datetime.fromtimestamp(end_time).strftime('%Y.%m.%d %H:%M:%S')
            }

            self.sessions.append(session)
            self.save_history()
            self.update_history_display()

        # 重置计时器
        self.is_running = False
        self.start_time = None
        self.pause_time = None
        self.total_paused_time = 0

        # 更新按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

        # 重置时间显示
        self.time_label.config(text="00:00:00")

    def update_timer(self):
        """更新计时器显示"""
        if self.is_running and self.start_time:
            current_time = time.time()
            elapsed_time = current_time - self.start_time - self.total_paused_time

            # 格式化时间显示
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)

            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.time_label.config(text=time_str)

        # 更新当前时间显示
        self.update_current_time()

        # 每秒更新一次
        self.root.after(1000, self.update_timer)

    def update_current_time(self):
        """更新当前时间显示"""
        current_time = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        self.current_time_label.config(text=current_time)

    def update_history_display(self):
        """更新历史记录显示"""
        self.history_listbox.delete(0, tk.END)

        # 创建列表框索引到实际历史记录索引的映射
        self.listbox_to_session_map = {}

        last_date = None
        listbox_index = 0
        session_index = len(self.sessions) - 1  # 从最后一个开始，因为reversed

        for session in reversed(self.sessions):  # 最新的显示在最上面
            duration = session['duration']
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)

            # 提取时间部分（移除年月日）
            start_time = session['start_time'][-8:-3]
            end_time = session['end_time'][-8:-3]

            # 提取日期部分用于比较
            current_date = session['start_time'][:10]  # 格式: YYYY.MM.DD

            # 如果日期变化，添加分隔行
            if current_date != last_date:
                if last_date is not None:
                    # 添加空行作为分隔
                    self.history_listbox.insert(tk.END, "")
                    listbox_index += 1
                # 添加日期标识行
                date_display = f" --- {current_date} ---"
                self.history_listbox.insert(tk.END, date_display)
                listbox_index += 1
                last_date = current_date

            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            name_str = session['name']
            display_text = f" {start_time} - {end_time} | {time_str} | {name_str}"
            self.history_listbox.insert(tk.END, display_text)

            # 记录映射关系
            self.listbox_to_session_map[listbox_index] = session_index
            listbox_index += 1
            session_index -= 1

    def save_history(self):
        """保存历史记录到文件"""
        try:
            history_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'timer_history.json')
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def load_history(self):
        """从文件加载历史记录"""
        try:
            history_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'timer_history.json')
            if os.path.exists(history_path):
                with open(history_path, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self.sessions = []

    def on_opacity_change(self, value):
        """滑块改变不透明度"""
        opacity = float(value)
        try:
            self.root.attributes('-alpha', opacity)
            # 同步更新输入框显示（百分比形式）
            self.opacity_entry_var.set(str(int(opacity * 100)))
            # 自动保存设置
            self.save_settings()
        except:
            pass  # 如果系统不支持透明度，忽略错误

    def on_opacity_entry_change(self, event):
        """输入框改变不透明度"""
        try:
            # 获取输入框的值并转换为0-100的整数
            opacity_percent = int(self.opacity_entry_var.get())
            # 限制在1-100范围内
            opacity_percent = max(1, min(100, opacity_percent))

            # 转换为0.0-1.0的小数
            opacity = opacity_percent / 100.0

            # 更新窗口透明度
            self.root.attributes('-alpha', opacity)

            # 同步更新滑块
            self.opacity_var.set(opacity)

            # 更新输入框显示（确保显示正确的值）
            self.opacity_entry_var.set(str(opacity_percent))
            # 自动保存设置
            self.save_settings()
        except ValueError:
            # 如果输入不是有效数字，恢复之前的值
            current_opacity = self.opacity_var.get()
            self.opacity_entry_var.set(str(int(current_opacity * 100)))


    def close_app(self):
        """关闭应用"""
        # 如果正在计时，先停止
        if self.is_running:
            self.stop_timer()
        self.root.quit()

    def on_todo_content_change(self, event=None):
        """待办内容改变时启用保存按钮"""
        self.save_todo_button.config(state=tk.NORMAL)

    def on_always_on_top_change(self):
        """窗口置顶复选框改变事件"""
        enabled = self.always_on_top_var.get()
        try:
            self.root.attributes('-topmost', enabled)
            # 保存设置
            self.save_settings()
        except Exception as e:
            messagebox.showerror("错误", f"设置窗口置顶失败: {e}")
            # 恢复复选框状态
            self.always_on_top_var.set(not enabled)

    def on_autostart_change(self):
        """自启动复选框改变事件"""
        enabled = self.autostart_var.get()
        try:
            if enabled:
                self.enable_autostart()
            else:
                self.disable_autostart()
            # 保存设置
            self.save_settings()
        except Exception as e:
            messagebox.showerror("错误", f"设置自启动失败: {e}")
            # 恢复复选框状态
            self.autostart_var.set(not enabled)

    def enable_autostart(self):
        """启用开机自启动"""
        try:
            # 获取当前脚本的完整路径
            script_path = os.path.abspath(__file__)

            # 打开注册表键
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )

            # 设置注册表值
            winreg.SetValueEx(key, "TimeCounter", 0, winreg.REG_SZ, script_path)
            winreg.CloseKey(key)

        except Exception as e:
            raise Exception(f"无法启用自启动: {e}")

    def disable_autostart(self):
        """禁用开机自启动"""
        try:
            # 打开注册表键
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )

            # 删除注册表值
            try:
                winreg.DeleteValue(key, "TimeCounter")
            except FileNotFoundError:
                # 如果值不存在，忽略错误
                pass

            winreg.CloseKey(key)

        except Exception as e:
            raise Exception(f"无法禁用自启动: {e}")

    def check_autostart_status(self):
        """检查当前自启动状态"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )

            try:
                value, _ = winreg.QueryValueEx(key, "TimeCounter")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False

        except Exception:
            return False

    # 待办列表相关方法
    def on_todo_select(self, event):
        """待办项选择事件"""
        index = self.todo_listbox.nearest(event.y)
        if index >= 0:
            self.selected_todo_index = index
            self.load_todo_to_edit(index)
            # 启用删除按钮
            self.delete_todo_button.config(state=tk.NORMAL)

    def show_todo_context_menu(self, event):
        """显示待办右键菜单"""
        index = self.todo_listbox.nearest(event.y)
        if index >= 0:
            self.todo_listbox.selection_clear(0, tk.END)
            self.todo_listbox.selection_set(index)
            self.selected_todo_index = index

            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(
                label="编辑",
                command=lambda: self.load_todo_to_edit(index)
            )
            context_menu.add_separator()
            context_menu.add_command(
                label="删除",
                command=lambda: self.delete_todo()
            )
            context_menu.post(event.x_root, event.y_root)

    def add_empty_todo(self):
        """在列表中添加空待办"""
        # 创建空的待办项
        empty_todo = {
            'title': '新待办事项',
            'description': '',
            'priority': '中',
            'status': '待办',
            'created_time': datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
            'updated_time': datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        }

        # 添加到列表
        self.todos.append(empty_todo)
        self.save_todos()
        self.update_todo_display()

        # 选中新添加的待办项
        self.selected_todo_index = len(self.todos) - 1
        self.todo_listbox.selection_clear(0, tk.END)
        self.todo_listbox.selection_set(self.selected_todo_index)
        self.load_todo_to_edit(self.selected_todo_index)

        # 启用删除按钮
        self.delete_todo_button.config(state=tk.NORMAL)

    def add_todo(self):
        """添加新待办"""
        self.selected_todo_index = None
        self.clear_todo_edit()

    def delete_todo(self):
        """删除选中的待办"""
        if self.selected_todo_index is not None:
            if messagebox.askyesno("确认删除", "确定要删除这个待办事项吗？"):
                self.todos.pop(self.selected_todo_index)
                self.selected_todo_index = None
                self.save_todos()
                self.update_todo_display()
                self.clear_todo_edit()
                # 禁用删除按钮
                self.delete_todo_button.config(state=tk.DISABLED)

    def load_todo_to_edit(self, index):
        """加载待办到编辑区域"""
        if 0 <= index < len(self.todos):
            todo = self.todos[index]
            self.todo_title_entry.delete(0, tk.END)
            self.todo_title_entry.insert(0, todo.get('title', ''))

            self.todo_desc_text.delete(1.0, tk.END)
            self.todo_desc_text.insert(1.0, todo.get('description', ''))

            self.todo_priority_var.set(todo.get('priority', '中'))
            self.todo_status_var.set(todo.get('status', '待办'))
            # 加载时禁用保存按钮，等待用户修改
            self.save_todo_button.config(state=tk.DISABLED)

    def save_todo(self):
        """保存待办"""
        title = self.todo_title_entry.get().strip()
        if not title:
            messagebox.showwarning("警告", "请输入待办标题")
            return

        description = self.todo_desc_text.get(1.0, tk.END).strip()
        priority = self.todo_priority_var.get()
        status = self.todo_status_var.get()

        todo_data = {
            'title': title,
            'description': description,
            'priority': priority,
            'status': status,
            'created_time': datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
            'updated_time': datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        }

        if self.selected_todo_index is not None:
            # 更新现有待办
            self.todos[self.selected_todo_index] = todo_data
        else:
            # 添加新待办
            self.todos.append(todo_data)

        self.save_todos()
        self.update_todo_display()
        self.clear_todo_edit()
        self.selected_todo_index = None
        # 禁用保存按钮
        self.save_todo_button.config(state=tk.DISABLED)

    def cancel_todo_edit(self):
        """取消待办编辑 - 清空待办栏并取消选中"""
        self.clear_todo_edit()
        self.selected_todo_index = None
        # 取消列表选中
        self.todo_listbox.selection_clear(0, tk.END)
        # 禁用删除按钮
        self.delete_todo_button.config(state=tk.DISABLED)
        # 禁用保存按钮
        self.save_todo_button.config(state=tk.DISABLED)

    def clear_todo_edit(self):
        """清空待办编辑区域"""
        self.todo_title_entry.delete(0, tk.END)
        self.todo_desc_text.delete(1.0, tk.END)
        self.todo_priority_var.set("中")
        self.todo_status_var.set("待办")

    def update_todo_display(self):
        """更新待办列表显示"""
        self.todo_listbox.delete(0, tk.END)

        for todo in self.todos:
            priority_symbol = {"低": "⚪", "中": "🟡", "高": "🔴"}.get(todo.get('priority', '中'), "⚪")
            status_symbol = {"待办": "📝", "进行中": "🔄", "已完成": "✅"}.get(todo.get('status', '待办'), "📝")

            display_text = f"{priority_symbol} {status_symbol} {todo['title']}"
            self.todo_listbox.insert(tk.END, display_text)

    def save_todos(self):
        """保存待办列表到文件"""
        try:
            todo_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'todo_list.json')
            with open(todo_path, 'w', encoding='utf-8') as f:
                json.dump(self.todos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存待办列表失败: {e}")

    def load_todos(self):
        """从文件加载待办列表"""
        try:
            todo_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'todo_list.json')
            if os.path.exists(todo_path):
                with open(todo_path, 'r', encoding='utf-8') as f:
                    self.todos = json.load(f)
        except Exception as e:
            print(f"加载待办列表失败: {e}")
            self.todos = []

    def save_settings(self):
        """保存所有设置到文件"""
        try:
            # 获取当前窗口位置和大小
            geometry = self.root.geometry()
            # 解析geometry字符串 "widthxheight+x+y"
            parts = geometry.split('+')
            size_parts = parts[0].split('x')
            width = int(size_parts[0])
            height = int(size_parts[1])
            x = int(parts[1])
            y = int(parts[2])

            settings = {
                'opacity': self.opacity_var.get(),
                'autostart': self.autostart_var.get(),
                'always_on_top': self.always_on_top_var.get(),
                'window_geometry': {
                    'width': width,
                    'height': height,
                    'x': x,
                    'y': y
                }
            }
            settings_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")

    def load_opacity_settings(self):
        """从文件加载不透明度设置"""
        try:
            settings_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # 在创建滑块之前存储设置
                    self.saved_opacity = settings.get('opacity', 0.8)
                    # 加载窗口置顶设置
                    self.saved_always_on_top = settings.get('always_on_top', True)
                    # 加载窗口几何设置
                    self.saved_window_geometry = settings.get('window_geometry', {
                        'width': 700,
                        'height': 500,
                        'x': 100,
                        'y': 100
                    })
            else:
                self.saved_opacity = 0.8
                self.saved_always_on_top = True
                self.saved_window_geometry = {
                    'width': 700,
                    'height': 500,
                    'x': 100,
                    'y': 100
                }
        except Exception as e:
            print(f"加载设置失败: {e}")
            self.saved_opacity = 0.8
            self.saved_always_on_top = True
            self.saved_window_geometry = {
                'width': 700,
                'height': 500,
                'x': 100,
                'y': 100
            }

    def load_autostart_settings(self):
        """加载自启动设置"""
        try:
            # 首先检查注册表状态
            registry_status = self.check_autostart_status()

            # 然后检查设置文件
            file_status = False
            settings_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    file_status = settings.get('autostart', False)

            # 如果注册表和文件状态不一致，以注册表为准
            if registry_status != file_status:
                # 更新文件设置
                self.autostart_enabled = registry_status
                self.save_settings()
            else:
                self.autostart_enabled = file_status

        except Exception as e:
            print(f"加载自启动设置失败: {e}")
            self.autostart_enabled = False

    # 体重记录相关方法
    def on_weight_select(self, event):
        """体重记录选择事件"""
        index = self.weight_listbox.nearest(event.y)
        if index >= 0:
            self.selected_weight_index = index
            self.load_weight_to_edit(index)
            # 启用删除按钮
            self.delete_weight_button.config(state=tk.NORMAL)

    def show_weight_context_menu(self, event):
        """显示体重记录右键菜单"""
        index = self.weight_listbox.nearest(event.y)
        if index >= 0:
            self.weight_listbox.selection_clear(0, tk.END)
            self.weight_listbox.selection_set(index)
            self.selected_weight_index = index

            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(
                label="编辑",
                command=lambda: self.load_weight_to_edit(index)
            )
            context_menu.add_separator()
            context_menu.add_command(
                label="删除",
                command=lambda: self.delete_weight_record()
            )
            context_menu.post(event.x_root, event.y_root)

    def add_weight_record(self):
        """添加体重记录"""
        # 清空编辑区域
        self.clear_weight_edit()
        # 设置默认日期为今天
        self.weight_date_entry.delete(0, tk.END)
        self.weight_date_entry.insert(0, datetime.now().strftime('%Y.%m.%d'))
        # 取消选中
        self.selected_weight_index = None
        self.weight_listbox.selection_clear(0, tk.END)
        # 禁用删除按钮
        self.delete_weight_button.config(state=tk.DISABLED)

    def delete_weight_record(self):
        """删除选中的体重记录"""
        if self.selected_weight_index is not None:
            if messagebox.askyesno("确认删除", "确定要删除这个体重记录吗？"):
                self.weight_records.pop(self.selected_weight_index)
                self.selected_weight_index = None
                self.save_weight_records()
                self.update_weight_display()
                self.clear_weight_edit()
                # 禁用删除按钮
                self.delete_weight_button.config(state=tk.DISABLED)

    def load_weight_to_edit(self, index):
        """加载体重记录到编辑区域"""
        if 0 <= index < len(self.weight_records):
            weight_record = self.weight_records[index]
            self.weight_date_entry.delete(0, tk.END)
            self.weight_date_entry.insert(0, weight_record.get('date', ''))

            self.weight_value_entry.delete(0, tk.END)
            self.weight_value_entry.insert(0, str(weight_record.get('weight', '')))

            self.weight_note_entry.delete(0, tk.END)
            self.weight_note_entry.insert(0, weight_record.get('note', ''))
            # 加载时禁用保存按钮，等待用户修改
            self.save_weight_button.config(state=tk.DISABLED)

    def save_weight_record(self):
        """保存体重记录"""
        date = self.weight_date_entry.get().strip()
        weight_str = self.weight_value_entry.get().strip()
        note = self.weight_note_entry.get().strip()

        # 验证输入
        if not date:
            messagebox.showwarning("警告", "请输入日期")
            return

        if not weight_str:
            messagebox.showwarning("警告", "请输入体重")
            return

        try:
            weight = float(weight_str)
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的体重数值")
            return

        # 创建体重记录数据
        weight_data = {
            'date': date,
            'weight': weight,
            'note': note,
            'created_time': datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
            'updated_time': datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        }

        if self.selected_weight_index is not None:
            # 更新现有记录
            self.weight_records[self.selected_weight_index] = weight_data
        else:
            # 添加新记录
            self.weight_records.append(weight_data)

        self.save_weight_records()
        self.update_weight_display()
        self.clear_weight_edit()
        self.selected_weight_index = None
        # 禁用保存按钮
        self.save_weight_button.config(state=tk.DISABLED)

    def cancel_weight_edit(self):
        """取消体重记录编辑"""
        self.clear_weight_edit()
        self.selected_weight_index = None
        # 取消列表选中
        self.weight_listbox.selection_clear(0, tk.END)
        # 禁用删除按钮
        self.delete_weight_button.config(state=tk.DISABLED)
        # 禁用保存按钮
        self.save_weight_button.config(state=tk.DISABLED)

    def clear_weight_edit(self):
        """清空体重记录编辑区域"""
        self.weight_date_entry.delete(0, tk.END)
        self.weight_value_entry.delete(0, tk.END)
        self.weight_note_entry.delete(0, tk.END)

    def on_weight_content_change(self, event=None):
        """体重记录内容改变时启用保存按钮"""
        self.save_weight_button.config(state=tk.NORMAL)

    def update_weight_display(self):
        """更新体重记录显示"""
        self.weight_listbox.delete(0, tk.END)

        # 按日期排序记录（最新的在前面）
        sorted_records = sorted(self.weight_records,
                               key=lambda x: datetime.strptime(x['date'], '%Y.%m.%d'),
                               reverse=True)

        for record in sorted_records:
            date = record['date']
            weight = record['weight']
            note = record.get('note', '')

            if note:
                display_text = f"{date} | {weight}kg | {note}"
            else:
                display_text = f"{date} | {weight}kg"

            self.weight_listbox.insert(tk.END, display_text)

    def update_weight_chart(self):
        """更新体重图表"""
        self.weight_ax.clear()

        # 设置中文字体
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass

        if not self.weight_records:
            # 如果没有数据，显示提示信息
            self.weight_ax.text(0.5, 0.5, 'No weight data',
                              horizontalalignment='center', verticalalignment='center',
                              transform=self.weight_ax.transAxes, fontsize=12)
            self.weight_ax.set_xlim(0, 1)
            self.weight_ax.set_ylim(0, 1)
            self.weight_ax.set_xticks([])
            self.weight_ax.set_yticks([])
        else:
            # 按日期排序记录
            sorted_records = sorted(self.weight_records,
                                   key=lambda x: datetime.strptime(x['date'], '%Y.%m.%d'))

            dates = [datetime.strptime(record['date'], '%Y.%m.%d') for record in sorted_records]
            weights = [record['weight'] for record in sorted_records]

            # 绘制折线图
            self.weight_ax.plot(dates, weights, 'o-', linewidth=2, markersize=4)

            # 如果有体重目标，绘制目标线
            if self.weight_target is not None:
                # 获取日期范围
                min_date = min(dates)
                max_date = max(dates)

                # 绘制贯穿首尾的红色横线
                self.weight_ax.axhline(y=self.weight_target, color='red', linestyle='--', linewidth=2, alpha=0.7)

                # 在目标线旁边添加标签
                self.weight_ax.text(max_date, self.weight_target, f' 目标: {self.weight_target}kg',
                                  color='red', verticalalignment='center', fontsize=10)

            # 设置图表样式
            self.weight_ax.set_xlabel('Date')
            self.weight_ax.set_ylabel('Weight (kg)')
            self.weight_ax.grid(True, alpha=0.3)

            # 格式化日期显示
            self.weight_ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%d'))
            self.weight_ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

            # 自动调整布局
            self.weight_fig.tight_layout()

        # 更新画布
        self.weight_canvas.draw()

    def save_weight_records(self):
        """保存体重记录到文件"""
        try:
            weight_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'weight_records.json')
            with open(weight_path, 'w', encoding='utf-8') as f:
                json.dump(self.weight_records, f, ensure_ascii=False, indent=2)
            # 更新图表
            self.update_weight_chart()
        except Exception as e:
            print(f"保存体重记录失败: {e}")

    def load_weight_records(self):
        """从文件加载体重记录"""
        try:
            weight_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'weight_records.json')
            if os.path.exists(weight_path):
                with open(weight_path, 'r', encoding='utf-8') as f:
                    self.weight_records = json.load(f)
        except Exception as e:
            print(f"加载体重记录失败: {e}")
            self.weight_records = []

    def run(self):
        """运行应用"""
        # 启动闹钟检查
        self.check_alarms()
        self.root.mainloop()

    # 体重目标相关方法
    def set_weight_target(self):
        """设置体重目标"""
        target_str = self.weight_target_var.get().strip()
        if not target_str:
            messagebox.showwarning("警告", "请输入目标体重")
            return

        try:
            target = float(target_str)
            if target <= 0:
                messagebox.showwarning("警告", "请输入有效的体重数值")
                return

            self.weight_target = target
            self.save_weight_target()
            self.update_target_display()
            self.update_weight_chart()
            messagebox.showinfo("成功", f"体重目标已设置为 {target}kg")

        except ValueError:
            messagebox.showwarning("警告", "请输入有效的体重数值")

    def clear_weight_target(self):
        """清除体重目标"""
        if messagebox.askyesno("确认清除", "确定要清除体重目标吗？"):
            self.weight_target = None
            self.save_weight_target()
            self.update_target_display()
            self.update_weight_chart()
            self.weight_target_var.set("")

    def update_target_display(self):
        """更新目标显示"""
        if self.weight_target is not None:
            self.target_display_label.config(text=f"当前目标: {self.weight_target}kg")
        else:
            self.target_display_label.config(text="未设置目标")

    def save_weight_target(self):
        """保存体重目标到文件"""
        try:
            target_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'weight_target.json')
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump({'target': self.weight_target}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存体重目标失败: {e}")

    def load_weight_target(self):
        """从文件加载体重目标"""
        try:
            target_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'weight_target.json')
            if os.path.exists(target_path):
                with open(target_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.weight_target = data.get('target')
        except Exception as e:
            print(f"加载体重目标失败: {e}")
            self.weight_target = None

    # 闹钟相关方法
    def on_alarm_select(self, event):
        """闹钟项选择事件"""
        index = self.alarm_listbox.nearest(event.y)
        if index >= 0:
            self.selected_alarm_index = index
            self.load_alarm_to_edit(index)
            # 启用删除按钮
            self.delete_alarm_button.config(state=tk.NORMAL)

    def show_alarm_context_menu(self, event):
        """显示闹钟右键菜单"""
        index = self.alarm_listbox.nearest(event.y)
        if index >= 0:
            self.alarm_listbox.selection_clear(0, tk.END)
            self.alarm_listbox.selection_set(index)
            self.selected_alarm_index = index

            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(
                label="编辑",
                command=lambda: self.load_alarm_to_edit(index)
            )
            context_menu.add_separator()
            context_menu.add_command(
                label="删除",
                command=lambda: self.delete_alarm()
            )
            context_menu.post(event.x_root, event.y_root)

    def add_alarm(self):
        """添加闹钟"""
        # 清空编辑区域
        self.clear_alarm_edit()
        # 设置默认时间为当前时间
        self.alarm_time_entry.delete(0, tk.END)
        self.alarm_time_entry.insert(0, datetime.now().strftime('%H:%M'))
        # 取消选中
        self.selected_alarm_index = None
        self.alarm_listbox.selection_clear(0, tk.END)
        # 禁用删除按钮
        self.delete_alarm_button.config(state=tk.DISABLED)

    def delete_alarm(self):
        """删除选中的闹钟"""
        if self.selected_alarm_index is not None:
            if messagebox.askyesno("确认删除", "确定要删除这个闹钟吗？"):
                self.alarms.pop(self.selected_alarm_index)
                self.selected_alarm_index = None
                self.save_alarms()
                self.update_alarm_display()
                self.clear_alarm_edit()
                # 禁用删除按钮
                self.delete_alarm_button.config(state=tk.DISABLED)

    def load_alarm_to_edit(self, index):
        """加载闹钟到编辑区域"""
        if 0 <= index < len(self.alarms):
            alarm = self.alarms[index]
            self.alarm_time_entry.delete(0, tk.END)
            self.alarm_time_entry.insert(0, alarm.get('time', ''))

            self.alarm_repeat_var.set(alarm.get('repeat', '不重复'))
            self.alarm_label_entry.delete(0, tk.END)
            self.alarm_label_entry.insert(0, alarm.get('label', '闹钟'))
            self.alarm_enabled_var.set(alarm.get('enabled', True))
            # 加载时禁用保存按钮，等待用户修改
            self.save_alarm_button.config(state=tk.DISABLED)

    def save_alarm(self):
        """保存闹钟"""
        time_str = self.alarm_time_entry.get().strip()
        repeat = self.alarm_repeat_var.get()
        label = self.alarm_label_entry.get().strip()
        enabled = self.alarm_enabled_var.get()

        # 验证输入
        if not time_str:
            messagebox.showwarning("警告", "请输入时间")
            return

        if not label:
            messagebox.showwarning("警告", "请输入标签")
            return

        # 验证时间格式
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的时间格式 (HH:MM)")
            return

        # 创建闹钟数据
        alarm_data = {
            'time': time_str,
            'repeat': repeat,
            'label': label,
            'enabled': enabled,
            'created_time': datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
            'updated_time': datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        }

        if self.selected_alarm_index is not None:
            # 更新现有闹钟
            self.alarms[self.selected_alarm_index] = alarm_data
        else:
            # 添加新闹钟
            self.alarms.append(alarm_data)

        self.save_alarms()
        self.update_alarm_display()
        self.clear_alarm_edit()
        self.selected_alarm_index = None
        # 禁用保存按钮
        self.save_alarm_button.config(state=tk.DISABLED)

    def cancel_alarm_edit(self):
        """取消闹钟编辑"""
        self.clear_alarm_edit()
        self.selected_alarm_index = None
        # 取消列表选中
        self.alarm_listbox.selection_clear(0, tk.END)
        # 禁用删除按钮
        self.delete_alarm_button.config(state=tk.DISABLED)
        # 禁用保存按钮
        self.save_alarm_button.config(state=tk.DISABLED)

    def clear_alarm_edit(self):
        """清空闹钟编辑区域"""
        self.alarm_time_entry.delete(0, tk.END)
        self.alarm_time_entry.insert(0, datetime.now().strftime('%H:%M'))
        self.alarm_repeat_var.set("不重复")
        self.alarm_label_entry.delete(0, tk.END)
        self.alarm_label_entry.insert(0, "闹钟")
        self.alarm_enabled_var.set(True)

    def on_alarm_content_change(self, event=None):
        """闹钟内容改变时启用保存按钮"""
        self.save_alarm_button.config(state=tk.NORMAL)

    def update_alarm_display(self):
        """更新闹钟显示"""
        self.alarm_listbox.delete(0, tk.END)

        for alarm in self.alarms:
            time_str = alarm['time']
            label = alarm['label']
            enabled = alarm.get('enabled', True)
            repeat = alarm.get('repeat', '不重复')

            status_symbol = "🔔" if enabled else "🔕"
            repeat_symbol = {"不重复": "", "每天": "🔄", "工作日": "📅", "周末": "🏖️"}.get(repeat, "")

            display_text = f"{status_symbol} {time_str} {repeat_symbol} {label}"
            self.alarm_listbox.insert(tk.END, display_text)

    def save_alarms(self):
        """保存闹钟列表到文件"""
        try:
            alarm_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'alarms.json')
            with open(alarm_path, 'w', encoding='utf-8') as f:
                json.dump(self.alarms, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存闹钟列表失败: {e}")

    def load_alarms(self):
        """从文件加载闹钟列表"""
        try:
            alarm_path = os.path.join(os.path.expanduser('~'), 'LuisAPP', 'TimeCounter', 'alarms.json')
            if os.path.exists(alarm_path):
                with open(alarm_path, 'r', encoding='utf-8') as f:
                    self.alarms = json.load(f)
        except Exception as e:
            print(f"加载闹钟列表失败: {e}")
            self.alarms = []

    def check_alarms(self):
        """检查闹钟是否触发"""
        current_time = datetime.now().strftime('%H:%M')
        current_weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday

        for alarm in self.alarms:
            if not alarm.get('enabled', True):
                continue

            alarm_time = alarm['time']
            repeat = alarm.get('repeat', '不重复')

            # 检查时间是否匹配
            if alarm_time == current_time:
                # 检查重复设置
                should_ring = False
                if repeat == "不重复":
                    should_ring = True
                elif repeat == "每天":
                    should_ring = True
                elif repeat == "工作日" and current_weekday < 5:  # 周一到周五
                    should_ring = True
                elif repeat == "周末" and current_weekday >= 5:  # 周六和周日
                    should_ring = True

                if should_ring:
                    self.trigger_alarm(alarm)

        # 每分钟检查一次
        self.root.after(60000, self.check_alarms)

    def trigger_alarm(self, alarm):
        """触发闹钟"""
        messagebox.showinfo("闹钟", f"{alarm['time']} - {alarm['label']}")
        # 如果是不重复的闹钟，触发后禁用
        if alarm.get('repeat', '不重复') == "不重复":
            alarm['enabled'] = False
            self.save_alarms()
            self.update_alarm_display()


if __name__ == "__main__":
    app = TimeCounter()
    app.run()