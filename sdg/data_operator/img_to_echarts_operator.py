""" Operator for echarts converting
"""

from typing import override
import openai
import os
import base64
import pandas as pd

from .operator import Meta, Operator, Field
from ..storage.dataset import DataType
from ..task.task_type import TaskType

class ImgToEchartsOperator(Operator):
    """ImgToEchartsOperator is an operator that converts an image dataset to an ECharts code dataset."""

    def __init__(self, **kwargs):
        self.api_key = kwargs.get('api_key',"")
        self.model = kwargs.get('model', "gpt-4o")

    @classmethod
    @override
    def accept(cls, data_type, task_type) -> bool:
        if data_type == DataType.IMAGE and task_type == TaskType.AUGMENTATION:
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
            name='ImgToEchartsOperator',
            description='Converts an image dataset to an ECharts code dataset.'
        )
    
    @override
    def execute(self, dataset):
        
        # gpt-4o (github版)
        client = openai.OpenAI(
            api_key = self.api_key,
            base_url = "https://models.inference.ai.azure.com"
        )

        # files
        df = pd.read_csv(dataset.meta_path)
        img_dir = [dir for dir in dataset.dirs if dir.data_type == DataType.IMAGE][0]
        code_dir = [dir for dir in dataset.dirs if dir.data_type == DataType.ECHARTS][0]
        img_files = df[DataType.IMAGE.value].tolist()
        code_files = df[DataType.ECHARTS.value].tolist()

        # process
        for index, img_file_name in enumerate(img_files):
            print("img_file : " + img_file_name)
            # For images without corresponding echarts code files
            code_file_name = os.path.splitext(img_file_name)[0]+'.js'
            print("code_file : " + code_file_name)
            if not self.check_file_existence(code_file_name, code_files):
                # Generate echarts code files
                img_file_path = os.path.join(img_dir.data_path, img_file_name)
                with open(img_file_path,'rb+') as image_f :
                    image=image_f.read()

                answer_content = self.call_gpt4o(client, image)
                if not answer_content :
                    print('调用api获取数据失败')
                else :
                    code_file_path = os.path.join(code_dir.data_path, code_file_name)
                    
                    with open(code_file_path, 'wb') as code_f:
                        code_f.write(answer_content.encode('utf-8'))
                
                # modify csv file
                df.at[index, DataType.ECHARTS.value] = code_file_name

        # save the modified csv
        df.to_csv(dataset.meta_path, index=False)

    

    def call_gpt4o (self, client, img_data):

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                # {"role": "system", "content": "你是一个熟悉 ECharts 的前端开发专家"},
                {"role": "user", "content": "Compose the ECharts code to achieve the same design and content as this chart screenshot.\n\n## Cautions\n- Write the json with ECharts directly. No html in the code.\n- Make sure the rendered chart looks exactly the same as the given image.\n- DO NOT miss the legend if it is in the image.\n- Just output the json code without description and analysis.\n\nLet's begin!\n"},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(img_data).decode()}}]}
            ]
        )

        response_text = response.choices[0].message.content
        # print("收到的结果为：" + response_text)
        start = response_text.find("{")
        end = response_text.rfind("}")
        js_text = "option=" + response_text[start:end+1]

        return js_text
    
    @staticmethod
    def check_file_existence(file, file_array):
        return file in file_array
