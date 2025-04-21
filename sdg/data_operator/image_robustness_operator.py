import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import override
from .operator import Meta, Operator, Field
from ..storage.dataset import DataType
from ..task.task_type import TaskType
import io
import pandas as pd
import os

class ImageRobustnessEnhancer(Operator):
    """ImageRobustnessEnhancer is an operator that enhances the robustness of images
    by adding random interference elements and text descriptions.

    Attributes:
        add_watermark: Whether to add a semi-transparent watermark.
        add_noise: Whether to add noise to the image.
        add_text: Whether to add text descriptions around the image.
    """

    def __init__(self, **kwargs):
        self.add_watermark: bool = kwargs.get('add_watermark', True)
        self.watermark_count: int = kwargs.get('water_count', 25)
        self.add_noise: bool = kwargs.get('add_noise', True)
        self.add_text: bool = kwargs.get('add_text', True)
        self.text_count: int = kwargs.get('text_count', 15)
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
            Field('add_watermark', Field.FieldType.BOOL,
                  'Add a semi-transparent watermark to the image.', True),
            Field('watermark_count', Field.FieldType.NUMBER,
                  'The number of watermark.', 25),
            Field('add_noise', Field.FieldType.BOOL,
                  'Add noise to the image.', True),
            Field('add_text', Field.FieldType.BOOL,
                  'Add text descriptions around the image.', True),
            Field('text_count', Field.FieldType.NUMBER,
                  'The number of text.', 15)
        ]

    @classmethod
    @override
    def get_meta(cls) -> Meta:
        return Meta(
            name='ImageRobustnessEnhancer',
            description='Enhances the robustness of images by adding random interference elements and text descriptions.'
        )

    @override
    def execute(self, dataset) -> None:

        df = pd.read_csv(dataset.meta_path)
        img_dir = [dir for dir in dataset.dirs if dir.data_type == DataType.IMAGE][0]
        img_files = df[DataType.IMAGE.value].tolist()

        for img_name in img_files:
            if not img_name :
                continue
            file_path = os.path.join(img_dir.data_path, img_name)
            with open(file_path, 'rb') as f:
                img_data = f.read()
            # 将字节数据转换为 BytesIO 对象
            img_byte_arr = io.BytesIO(img_data)
            with Image.open(img_byte_arr) as img:
                if self.add_watermark:
                    img = self._add_watermark(img)
                if self.add_noise:
                    img = self._add_noise(img)
                if self.add_text:
                    img = self._add_text(img)

                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()

                with open(file_path, 'wb') as f:
                    f.write(img_byte_arr)


    def _add_watermark(self, img):
        watermark = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        font = ImageFont.load_default()
        # print(f"当前使用的字体: {font}")  
        text = "Sample Watermark"

        # 水印数量
        num_watermarks = self.watermark_count  
        # 随机生成颜色，这里固定了透明度是128（0是完全透明，255是完全不透明）
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        color = (r, g, b, 128)
        

        for _ in range(num_watermarks):
            # 使用 textbbox 方法计算文本的边界框
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            text_width = right - left
            text_height = bottom - top
            
            x = random.randint(0, img.width - text_width)
            y = random.randint(0, img.height - text_height)

            draw.text((x, y), text, font=font, fill=color)
       
        watermarked = Image.alpha_composite(img.convert('RGBA'), watermark)
        return watermarked.convert('RGB')

    def _add_noise(self, img):
        # 生成与原始图片尺寸和模式相同的噪声图片
        noise = Image.effect_noise(img.size, 100).convert(img.mode)
        noisy_img = Image.blend(img, noise, 0.1)
        return noisy_img

    def _add_text(self, img):
        texts = ["This is a related description.", "Another description here."]
        text = random.choice(texts)
        new_width = img.width + 200
        new_height = img.height + 200
        new_img = Image.new('RGB', (new_width, new_height), (255, 255, 255))
        new_img.paste(img, (100, 100))
        draw = ImageDraw.Draw(new_img)
        font = ImageFont.load_default()
        
        # 文本数量
        num_text = self.text_count

        for _ in range(num_text):
            # # 使用 textbbox 方法计算文本的边界框
            # left, top, right, bottom = draw.textbbox((0,0), text, font=font)
            # text_width = right - left
            # text_height = bottom - top
        
            # 随机选择文本位置
            # x = random.randint(0, new_width - text_width)
            # y = random.randint(0, new_height - text_height)

            x = random.randint(0, new_width - 100)
            y1 = random.randint(0, 85)
            y2 = random.randint(new_height-85, new_height)
            y = random.choice([y1, y2])
            # 随机生成颜色
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            color = (r, g, b)

            draw.text((x, y), text, font=font, fill=color)

        return new_img

    # def _add_text(self, img):
    #     texts = ["This is a related description.", "Another description here."]
    #     text = random.choice(texts)
    #     new_width = img.width + 200
    #     new_height = img.height + 200
    #     new_img = Image.new('RGB', (new_width, new_height), (255, 255, 255))
    #     new_img.paste(img, (100, 100))
    #     draw = ImageDraw.Draw(new_img)
    #     font = ImageFont.load_default()
    #     x = random.randint(0, new_width - 100)
    #     y = random.randint(0, 50)
    #     draw.text((x, y), text, font=font, fill=(0, 0, 0))
    #     return new_img