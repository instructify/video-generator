import openai
import re
import requests
import os
import datetime
import boto3
import io
import textwrap
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.editor import concatenate_videoclips
from moviepy.editor import *


def generate_text(prompt, api_key):
    openai.api_key = api_key
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response["choices"][0]["text"]

def save_text_to_file(text, directory):
    with open(f"{directory}/text/output.txt", "w") as f:
        f.write(text)

def separate_text_into_sentences(text):
    return re.split(r"(?<!\d\.\s)(?<=[.!?])\s", text)

def generate_image(prompt, api_key):
    print(f"\nCreating openai image for prompt: {prompt}")
    openai.api_key = api_key
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    return response["data"][0]["url"]

def save_image(url, path, sentence, offset=400, zoom_factor=1.2):

    if url.startswith("http"):
        response = requests.get(url)
        image = Image.open(io.BytesIO(response.content))

    else:
        image = Image.open(url)

    width, height = image.size
    new_width, new_height = 1080, 1920
    ratio = min(new_width/width, new_height/height)
    width, height = int(width * ratio * zoom_factor), int(height * ratio * zoom_factor)
    image = image.resize((width, height), Image.ANTIALIAS)
    new_image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    new_image.paste(image, ((1080 - width) // 2, (1920 - height) // 2))
    draw = ImageDraw.Draw(new_image)
    font = ImageFont.truetype("arialbd.ttf", 72)
    lines = textwrap.wrap(sentence, width=int(1080 / font.getsize("a")[0]))
    line_heights = [font.getsize(line)[1] for line in lines]
    total_height = sum(line_heights) + 10 * len(lines)
    y = int((1920 - total_height) / 2) + offset
    for i, line in enumerate(lines): 
        w, h = draw.textsize(line, font=font)
        x = int((1080 - w) / 2)
        y_ = y + sum(line_heights[:i])

        if any(val == line for val in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.']):
            font_size = 150
        else:
            font_size = 72
            background_height = h + 0
            background_width = w + 30
            background_box = Image.new("RGBA", (background_width, background_height), (48, 48, 48, 230))
            x_ = int((1080 - background_width) / 2)
            y__ = y_ + h - background_height
            new_image.alpha_composite(background_box, (x_, y__))
              
        font = ImageFont.truetype("arialbd.ttf", size=font_size)
        draw.text((x, y_), line, fill=(255, 255, 255), font=font)

    new_image.save(path, format="PNG")

def generate_speech(sentences, directory):
    polly = boto3.client("polly", region_name='eu-west-1',
                        aws_access_key_id="AWS_ACCESS_KEY",
                        aws_secret_access_key="AWS_SECRET_KEY")

    for i, sentence in enumerate(sentences):
        try:
            response = polly.synthesize_speech(Text=sentence, OutputFormat="mp3", Engine='neural', VoiceId="Matthew")
        except (BotoCoreError, ClientError) as error:
            print(f"Failed to synthesize speech: {error}")
            return
        if "AudioStream" in response:
            with open(f"{directory}/audio/output_{i + 1}.mp3", "wb") as f:
                f.write(response["AudioStream"].read())

def generate_video(directory, sentences, output_name):
    audio_files = [f"{directory}/audio/output_{i + 1}.mp3" for i in range(len(sentences))]
    images = [f"{directory}/images/image_{i + 1}.jpg" for i in range(len(sentences))]
    audio_clips = [AudioFileClip(audio_file) for audio_file in audio_files]
    image_clips = [ImageClip(image).set_duration(audio_clip.duration) for image, audio_clip in zip(images, audio_clips)]
    
    final_video = concatenate_videoclips(image_clips)
    final_video = final_video.set_audio(concatenate_audioclips(audio_clips))
    try:
        final_video.write_videofile(f"{directory}/video/{output_name}.mp4", fps=24)
    except IndexError:
        print("\nVideo generation complete with an ERROR!")

def print_progress(current, total, status):
    bar_length = 60
    filled_length = int(bar_length * current / total)
    bar = "=" * filled_length + "-" * (bar_length - filled_length)
    print(f"\r[{bar}] {current}/{total} {status}", end="")
    if current == total:
        print("\n")


if __name__ == "__main__":
    api_key = "OPENAI-API-KEY"
    topic = input("Please enter your topic: ")
    prompt = f"write {topic}"

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    directory = f"data/{timestamp}"

    os.makedirs(directory, exist_ok=True)
    os.makedirs(f"{directory}/text", exist_ok=True)
    os.makedirs(f"{directory}/images", exist_ok=True)
    os.makedirs(f"{directory}/audio", exist_ok=True)
    os.makedirs(f"{directory}/video", exist_ok=True)

    result = generate_text(prompt, api_key)
    print("Result:")
    print(result + "\n")
    output_name = topic
    save_text_to_file(result, directory)
    sentences = separate_text_into_sentences(result)
    sentences = [string.strip() for string in sentences]
    strings_to_remove = ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.']
    sentences_openai = [x for x in sentences if not any(x.startswith(s) for s in strings_to_remove)]
    # generate images
    image_urls = [generate_image(sentence, api_key) for sentence in sentences_openai]
    
    default_image_url = 'image.png'
   
    if len(image_urls) < len(sentences):
        num_defaults = len(sentences) - len(image_urls)
        default_images = [default_image_url] * num_defaults
        image_urls = [url for pair in zip(default_images, image_urls) for url in pair]
    
    #print(image_urls)

    for i, (sentence, image_url) in enumerate(zip(sentences, image_urls)):
        image_path = f"{directory}/images/image_{i + 1}.jpg"
        save_image(image_url, image_path, sentence)
        print_progress(i + 1, len(sentences), "Saving images")

        polly = boto3.client("polly", region_name='eu-west-1',
                        aws_access_key_id="AWS_ACCESS_KEY",
                        aws_secret_access_key="AWS_SECRET_KEY")

        try:
            response = polly.synthesize_speech(Text=sentence, OutputFormat="mp3", Engine='neural', VoiceId="Matthew")
        except (BotoCoreError, ClientError) as error:
            print(f"Failed to synthesize speech: {error}")
            #return
        if "AudioStream" in response:
            with open(f"{directory}/audio/output_{i + 1}.mp3", "wb") as f:
                f.write(response["AudioStream"].read())
            #print(f"\nAudio was created for sentence: {sentence}")

    generate_video(directory, sentences, output_name)
    print("\nVideo generation complete!")
    print(f"\nVideo output path: {directory}/video/{output_name}.mp4")