# -*- coding: utf-8 -*-
"""ai project - product image generator.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1wo-vBAJ7WrB-RiDVbyMUNdZi_NPILM_Z
"""

pip install torch torchvision diffusers transformers transparent-background

# Import required modules
import os
import torch
import shutil
from PIL import ImageOps
from diffusers import DiffusionPipeline
from diffusers.utils import load_image
from transparent_background import Remover
from google.colab import files
from IPython.display import display, Image

# Setting up the model - using yahoo background generation (open source)
MODEL_NAME = "yahoo-inc/photo-background-generation"
MODEL_CACHE = "model-cache"
device = "cuda" if torch.cuda.is_available() else "cpu"
float_datatype = torch.float16 if device == "cuda" else torch.float32

pipe = DiffusionPipeline.from_pretrained(
    MODEL_NAME,
    cache_dir=MODEL_CACHE,
    torch_dtype=float_datatype,
    custom_pipeline=MODEL_NAME,
).to(device)

# Function that use for modify the image and utility

def resize_with_padding(img, expected_size=(1024, 1024)):
    img.thumbnail(expected_size)
    delta_width = expected_size[0] - img.size[0]
    delta_height = expected_size[1] - img.size[1]
    padding = (
        delta_width // 2,
        delta_height // 2,
        delta_width - delta_width // 2,
        delta_height - delta_height // 2,
    )
    return ImageOps.expand(img, padding)

def generate_image(prompt, negative_prompt, image_path, num_outputs=1, steps=30, seed=None, scale=1.0):
    if seed is None:
        seed = int.from_bytes(os.urandom(3), "big")
    print(f"Using seed: {seed}")

    generator = torch.Generator(device=device).manual_seed(seed)

    img = load_image(image_path).convert("RGB")
    img = resize_with_padding(img)

    remover = Remover(mode="base")
    fg_mask = remover.process(img, type="map")
    mask = ImageOps.invert(fg_mask)

    with torch.autocast(device):
        output = pipe(
            prompt=[prompt] * num_outputs,
            negative_prompt=[negative_prompt] * num_outputs,
            generator=generator,
            num_inference_steps=steps,
            controlnet_conditioning_scale=scale,
            guess_mode=False,
            image=img,
            mask_image=mask,
            control_image=mask,
        )

    result_paths = []
    for i, im in enumerate(output.images):
        output_path = f"output_{i}.png"
        im.save(output_path)
        result_paths.append(output_path)

    return result_paths

# Upload Image to System for Generation (This we need to use main image that we want to add background)
image_path = "path/to/your/local/image.jpg" 

# Prompting
#negative value is the value that you dont want to see in the image or generated into it.
prompt = (
    "A minimal and elegant skincare product placed on a clean, modern desk, "
    "studio lighting, soft shadows, high-resolution product photography, "
    "professional background, pastel blue aesthetic, luxurious branding vibe, "
    "shallow depth of field, perfect for e-commerce"
)

negative_prompt = "3d, cgi, render, bad quality, normal quality"
num_outputs = 1
num_inference_steps = 30
seed = None  # or set to a number like 123
scale = 1.0

# Start generate new image with background
results = generate_image(
    prompt=prompt,
    negative_prompt=negative_prompt,
    image_path=image_path,
    num_outputs=num_outputs,
    steps=num_inference_steps,
    seed=seed,
    scale=scale,
)



from PIL import Image
# from IPython.display import display, Image as IPyImage


# Load the original product image and resize it
original = resize_with_padding(load_image(image_path).convert("RGBA"))

# Load the AI-generated background
generated = Image.open(results[0]).convert("RGBA")

# Recreate the foreground mask (product only)
remover = Remover(mode="base")
fg_mask = remover.process(original.convert("RGB"), type="map").convert("L")

# Create an image with only the product (and original text/logo), transparent background
product_only = Image.composite(original, Image.new("RGBA", original.size), fg_mask)

# Paste the product back onto the generated background
final_image = Image.alpha_composite(generated, product_only)

# Save and display final result
final_path = "final_result.png"
final_image.save(final_path)
# display(IPyImage(filename=final_path))
final_image.show()
