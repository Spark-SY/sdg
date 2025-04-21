""" Operators for data augment.
"""
import random
from typing import override
import json
import requests
import ast
import re
import pandas as pd
import os

from .operator import Meta
from .operator import Operator, Field
from ..storage.dataset import DataType
from ..task.task_type import TaskType
from playwright.sync_api import sync_playwright  # 同步API更简洁

 # Generate random hexadecimal color codes
def random_hex_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

class EChartMutationOperator(Operator):
    """EChartsStyleMutationOperator is an operator that mutates ECharts code styles.
    It can be used for code augmentation tasks.
    """
    def __init__(self, **kwargs):

        self.mutation_prob = kwargs.get('mutation_prob', 0.7)
        self.mutation_range = kwargs.get('mutation_range', 0.5)
        self.non_core_fields = ['animation', 'backgroundColor']

    @classmethod
    @override
    def accept(cls, data_type, task_type) -> bool:
        if data_type == DataType.ECHARTS and task_type == TaskType.AUGMENTATION:
            return True
        return False
    
    @classmethod
    @override
    def get_config(cls) -> list[Field]:

        return [

            Field('mutation_prob', Field.FieldType.NUMBER,
                'Mutation probability of configuration parameters', 0.7),
            Field('mutation_range', Field.FieldType.NUMBER,
                'Mutation range of configuration parameters', 0.5),    
            
        ]
    
    @classmethod
    @override
    def get_meta(cls) -> Meta:
        return Meta(
            name='EChartsMutationOperator',
            description='Mutates ECharts code styles by adjusting parameters , structure transformation and adding/removing non-core items.'
        )
    
    @override
    def execute(self, dataset) -> None:
        
        df = pd.read_csv(dataset.meta_path)
        code_dir = [dir for dir in dataset.dirs if dir.data_type == DataType.ECHARTS][0]
        code_files = df[DataType.ECHARTS.value].tolist()
        
        for index, file_name in enumerate(code_files):

            file_path = os.path.join(code_dir.data_path, file_name)
            with open(file_path,'rb') as f:
                code = f.read().decode('utf-8')
            print(code)
            start = code.find("{")
            end = code.rfind("}")
            echarts_config = json.loads(code[start:end+1])

            try:
                echarts_config = self.mutate_echarts_option(echarts_config)
                echarts_config = self.transform_echart_equal(echarts_config)
                # echarts_config = self.mutate_non_core_items(echarts_config)
            except Exception as e:
                print(f"变异过程异常: {e}")
                # 异常时至少保留参数变异结果

            # Convert to JSON string and ensure normal display of Chinese characters
            echarts_mutation_json = self.convert_to_js(echarts_config)


            parent_dir = os.path.dirname(code_dir.data_path)
            img_dir_path = os.path.join(parent_dir, "images")
            if not os.path.exists(img_dir_path):
                os.mkdir(img_dir_path)
            mutation_img_path = os.path.join(img_dir_path, file_name[:-3]+".jpg")

            # store json
            with open(file_path, 'wb') as f:
                f.write(echarts_mutation_json.encode('utf-8'))
            # store image
            with open(mutation_img_path, 'wb') as f:
                f.write(self.generate_echarts_jpg(echarts_mutation_json))

            
    '''
    tool: randomly adjust value
    '''
    @staticmethod
    def mutate_value(value, mutation_prob,mutation_range):
        """
        以一定概率对数值进行加或减mutation_range的操作
        """
        if isinstance(value, (int, float)) and random.random() < mutation_prob:
            factor = 1 + (random.uniform(-mutation_range, mutation_range))
            print(factor)
            return value * factor
        return value

    '''
    Randomly adjust echart option (colors and size)
    '''
    def mutate_echarts_option(self, config:dict) -> dict:

        mutation_prob = self.mutation_prob
        mutation_range = self.mutation_range

        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('#') and len(value) == 7:
                    # 检查是否为十六进制颜色代码，是，则有一定几率修改
                    if random.random() < mutation_prob:
                        config[key] = random_hex_color()
                        print("改变了颜色")
                        print(config[key])
                elif isinstance(value, str) and key == 'color':
                    # 检查是否为十六进制颜色代码，是，则有一定几率修改
                    if random.random() < mutation_prob:
                        config[key] = random_hex_color()
                        print("改变了颜色")
                        print(config[key])
                elif isinstance(value, int) and key == 'fontSize':
                    print(value)
                    config[key] = self.mutate_value(value, mutation_prob, mutation_range)
                elif isinstance(value, (dict, list)):
                    # 递归处理嵌套的字典或列表
                    if isinstance(value, dict):
                        config[key] = self.mutate_echarts_option( value)
                    elif isinstance(value, list) and key != 'data':  #TODO 是否不改变数据点的值？
                        config[key] = [self.mutate_echarts_option( item) if isinstance(item, (dict, list)) else self.mutate_value(item, mutation_prob, mutation_range) for item in value]
        elif isinstance(config, list):
            config = [self.mutate_echarts_option(item) if isinstance(item, (dict, list)) else self.mutate_value(item, mutation_prob, mutation_range) for item in config]
        return config        
       

    '''
    Randomly perform equivalent transformations on options
    '''
    def transform_echart_equal(self, config:dict) -> dict:

        mutation_prob = self.mutation_prob

        # 改变列表中元素的顺序
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, (dict, list)):
                    if isinstance(value, dict):
                        config[key] = self.transform_echart_equal(value)
                    elif isinstance(value, list) and key != 'data':
                        if random.random() < mutation_prob:
                            random.shuffle(value)
                        config[key] = [self.transform_echart_equal(item) if isinstance(item, (dict, list)) else item for item in value]
        elif isinstance(config, list):
            if random.random() < mutation_prob:
                random.shuffle(data)
            config = [self.transform_echart_equal(item) if isinstance(item, (dict, list)) else item for item in config]
        return config
        
    '''
    Randomly add or remove non core configuration items
    '''
    def mutate_non_core_items(self, config: dict) -> dict:
        for field in self.non_core_fields:
            if (random.random() < self.mutation_prob): 
                if field in config:
                    del config[field]
                else:
                    if field == 'animation':
                        config[field] = random.choice([True, False])
                    elif field == 'backgroundColor':
                        config[field] = random_hex_color()
        return config
    

    '''
    读取.js文件，转换为python字典
    '''
    @staticmethod
    def read_js_to_dict(file_content_bytes):
        try:
            file_content_str = file_content_bytes.decode('utf-8')

            # ====== 字符串保护 ======
            strings = []
            def hide_strings(match):
                strings.append(match.group(1))
                return f'__STR_{len(strings)-1}__'
                
            file_content_str = re.sub(
                r'("(?:\\"|[^"])*"|\'(?:\\\'|[^\'])*\')',
                hide_strings,
                file_content_str,
                flags=re.DOTALL
            )
            # ====== 移除注释 ======
            # 移除单行注释
            file_content_str = re.sub(r'//.*', '', file_content_str)
            # 移除多行注释
            file_content_str = re.sub(r'/\*.*?\*/', '', file_content_str, flags=re.DOTALL)


            # ====== 核心转换 ======
            file_content_str = re.sub(r'//.*|/\*.*?\*/', '', file_content_str, flags=re.DOTALL)
            file_content_str = re.sub(r'([{,])\s*([a-zA-Z_$][\w$]*)\s*:', r'\1"\2":', file_content_str, flags=re.MULTILINE)
            file_content_str = re.sub(r',(\s*[}\]])', r'\1', file_content_str)

            # ====== 恢复字符串 ======
            def restore_strings(match):
                return strings[int(match.group(1))]
            file_content_str = re.sub(r'__STR_(\d+)__', restore_strings, file_content_str)

            # ====== 精准定位对象 ======
            # 优先匹配 option = { ... } 结构
            start = -1
            option_pattern = re.compile(r'\boption\s*=\s*({)', re.IGNORECASE)
            if (match := option_pattern.search(file_content_str)):
                start = match.start(1)
            else:
                start = file_content_str.find('{')
            
            if start == -1:
                raise ValueError("未找到对象起始位置")

            # ====== 带字符串状态跟踪的栈匹配 ======
            stack = []
            end = -1
            in_string = False
            escape = False
            # print("将要处理字符串")
            # print(file_content_str[start:])
            for i, c in enumerate(file_content_str[start:], start=start):
                if c == '"' and not escape:
                    in_string = not in_string
                escape = (c == '\\' and not escape)
                
                if not in_string:
                    if c == '{':
                        stack.append(c)
                    elif c == '}':
                        if stack:
                            stack.pop()
                            if not stack:
                                end = i + 1
                                break
            
            if end == -1 or end <= start:
                raise ValueError(f"对象结束位置异常 start:{start} end:{end}")

            json_str = file_content_str[start:end]

            # ====== 最终处理 ======
            json_str = json_str.replace("'", '"')
            json_str = json_str.replace('undefined', 'null')
            json_str = re.sub(r'\bInfinity\b', '1e999', json_str)
            json_str = re.sub(r'\bNaN\b', '"NaN"', json_str)

            return json.loads(json_str)
        
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}\n错误上下文: {json_str[e.pos-30:e.pos+30]}")
            return None
        except Exception as e:
            print(f"处理失败: {str(e)}")
            return None
    
    '''
    python字典转换为.js文件内容
    '''
    @staticmethod
    def convert_to_js(config):
        json_str = json.dumps(config, indent=2, ensure_ascii=False)
        js_content = f"option = {json_str};"
        return js_content
    
    
    @staticmethod
    def generate_echarts_jpg(echarts_option):
        start = echarts_option.find("{")
        end = echarts_option.rfind("}")
        echarts_option_json = echarts_option[start:end+1]

        # 设置页面内容
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
        </head>
        <body>
            <div id="chart" style="width:1200px;height:800px;"></div>
            <script>
                // Playwright适配方案
                document.addEventListener('DOMContentLoaded', () => {{
                    const chart = echarts.init(document.getElementById('chart'));
                    chart.setOption({echarts_option_json});
                    chart.on('rendered', () => {{
                        document.title = 'RENDER_DONE';  // 保持标题标记
                    }});
                }});
            </script>
        </body>
        </html>
        '''
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-web-security',  # 禁用同源策略
                    '--ignore-certificate-errors'  # 忽略证书错误
                ]
            )
            page = browser.new_page()

            try:
                # 加载页面内容
                page.set_content(html_content)
                
                # 双重等待策略
                page.wait_for_selector('#chart canvas', timeout=60_000)  # 等待Canvas渲染
                page.wait_for_function('''() => {
                    return document.title === 'RENDER_DONE' &&
                        document.querySelector('#chart canvas').clientWidth > 0
                }''', timeout=100_000)  # 等待渲染标记
                
                # 先检测canvas元素是否存在
                page.wait_for_selector('#chart canvas', state='attached', timeout=10_000)
                # 再检测渲染完成标志
                page.wait_for_function('document.title === "RENDER_DONE"', timeout=10_000)
                # 最后添加2秒保险延迟（针对复杂渲染场景）
                page.wait_for_timeout(2000)  # 等同于 time.sleep(2)

                # 截图配置
                chart_div = page.locator('#chart')
                # 存储到指定路径
                # chart_div.screenshot(
                #     path='api_result/tongyi.jpg',
                #     type='jpeg',
                #     quality=95
                # )
                screenshot_bytes = chart_div.screenshot(
                type='jpeg',
                quality=95
                )
                browser.close()
                print("✅ 成功生成 jpeg")
                return screenshot_bytes
            except Exception as e:
                print(f"❌ 生成失败: {str(e)}")
                # 生成调试文件
                with open('error_debug.html', 'w') as f:
                    f.write(html_content)
                print("已生成 error_debug.html 供手动调试")
                
            finally:
                browser.close()
