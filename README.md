# video-generator

-  Download the video-generator.py file and move it into a directory (for example on your desktop/video-generator/video-generator.py)
-  You need to install latest python version https://www.python.org/downloads/
-  Then open a console (powershell) and navigate to the directory of the video-generator.py
    - Run following command to install these packages:
      - pip install openai requests Pillow moviepy boto3
-  Register on openai https://openai.com/ and create your API key
-  Paste your API key into the video-generator.py file instead of the placeholder "OPENAI-API-KEY"
-  Register on aws (amazon) https://signin.aws.amazon.com/ and sign in to the console on the platform
-  Now create an AWS Polly API key and insert it into the video-generator.py file instead of the placeholder "AWS_ACCESS_KEY" and "AWS_SECRET_KEY" (ATTENTION: There are 2 sections, where you need to paste the API key, in line 91,92 and also in line 167, 168)
-  Thats it! You are ready to create your first shorts video! Just save the file and then run the python tool with this command:
  - py video-generator.py


!! If there are any issues, please write me a comment on the YouTube video !!
