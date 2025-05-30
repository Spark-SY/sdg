'''Operators for diversity amend.
'''

from typing import override
import openai
import os
import pandas as pd
import random
import base64
from ..config import settings

from .operator import Meta, Operator, Field
from ..storage.dataset import DataType
from ..task.task_type import TaskType

class DiversityAmendOperator(Operator):
    def __init__(self, **kwargs):
        self.api_key = kwargs.get('api_key',"")
        self.model = kwargs.get('model', "gpt-4o")
        self.probability = kwargs.get('probability', 0.5)

    @classmethod
    @override
    def accept(cls, data_type, task_type) -> bool:
        if data_type == DataType.CODE and task_type == TaskType.AUGMENTATION:
            return True
        return False
    
    @classmethod
    @override
    def get_config(cls) -> list[Field]:
        return [
            Field('api-key', Field.FieldType.STRING, 'OpenAI API key', ""),
            Field('model', Field.FieldType.STRING, 'OpenAI model name', "gpt-4o")
        ]
    

    @classmethod
    @override
    def get_meta(cls) -> Meta:
        return Meta(
            name='DiversityxAmendOperator',
            description='Diversity amend.'
        )
    
    @override
    def execute(self, dataset):
        
        # gpt-4o (github版)
        client = openai.OpenAI(
            api_key = self.api_key,
            # base_url = "https://models.inference.ai.azure.com"
            base_url = settings.GPT_URL
        )

        # files
        code_dir = [dir for dir in dataset.dirs if dir.data_type == DataType.CODE][0]
        img_dir = [dir for dir in dataset.dirs if dir.data_type == DataType.IMAGE][0]
        # code_files = ['half_doughnut_chart_1.json','square_pie_chart_1.json']
        df = pd.read_csv(dataset.meta_path)
        code_files = df[DataType.CODE.value].tolist()
        img_files = df[DataType.IMAGE.value].tolist()

        for index, code_file_name in enumerate(code_files):
            
            if pd.isna(code_file_name):
                continue
            
            probability = self.probability
            ran_pro = random.random()
            if (ran_pro < probability):
                print(f"随机{ran_pro}，小于概率{probability}")
                continue

            # get code data
            code_file_path = os.path.join(code_dir.data_path,code_file_name)
            with open(code_file_path, 'rb') as f_code:
                code_data = f_code.read().decode('utf-8')

            # get img data (if exist)
            img_file_name = img_files[index]
            if pd.isna(img_file_name):
                img_data = None
            else:
                img_file_path = os.path.join(img_dir.data_path,img_file_name)
                with open(img_file_path, 'rb') as f_img:
                        img_data = f_img.read()

            new_code_data = self.call_gpt4o(client, code_data,img_data)
            # try:
            #     new_code_data = self.call_gpt4o(client, code_data, 60)
            # except Exception as e:
            #     print(f"调用超时")
            #     # 异常时至少保留参数变异结果
            #     continue

            with open(code_file_path, 'wb') as f:
                f.write(new_code_data.encode('utf-8'))
            

    def call_gpt4o (self, client, code_data, img_data):

        if (img_data is None):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    # {"role": "system", "content": "你是一个熟悉 ECharts 的前端开发专家"},
                    {"role": "user", "content": "以下的echarts配置json代码中的配置项多样性不够，请为其增加合理的配置，完善配置的细节。请只输出json代码，不需要描述与分析。"},
                    {"role": "user", "content": code_data},
                ],
            )
        else :
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    # {"role": "system", "content": "你是一个熟悉 ECharts 的前端开发专家"},
                    {"role": "user", "content": "以下的echarts配置json代码中的配置项多样性不够，请根据给出的图表图像，为其增加合理的配置，完善echarts配置json代码，使图像与配置json代码在细节上更为对应。请只输出json代码，不需要描述与分析。"},
                    {"role": "user", "content": code_data},
                    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(img_data).decode()}}]}
                ],
            )

        response_text = response.choices[0].message.content
        print("收到的结果为：" + response_text)
        start = response_text.find("{")
        end = response_text.rfind("}")
        json_text = response_text[start:end+1]

        return json_text
    
    @staticmethod
    def get_pending_files(csv_path, score_name, file_type):
        # 读取 CSV 文件（处理可能存在的空值）
        df = pd.read_csv(csv_path, na_values=['', ' ', 'NA'], dtype={score_name: float})

        # 筛选 syntax_score < 100 的行（自动排除 NaN 值）
        filtered_df = df[df[score_name] < 100]

        # 提取 code 字段并转换为列表
        code_list = filtered_df[file_type].dropna().tolist()  # 同时过滤 code 列可能的空值

        return code_list