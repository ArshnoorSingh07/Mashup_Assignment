import os
import zipfile
import smtplib
import streamlit as st
from email.message import EmailMessage
from pytubefix import YouTube, Search
from moviepy import AudioFileClip, concatenate_audioclips

SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]


def create_mashup(singer_name, num_videos, duration):
    video_files = []
    search = Search(singer_name + " songs")

    for i, vid in enumerate(search.results[:num_videos]):
        try:
            yt = YouTube(vid.watch_url)
            stream = yt.streams.filter(only_audio=True).first()
            filename = f"video_{i}.mp4"
            stream.download(filename=filename)
            video_files.append(filename)
        except:
            continue

    audio_files = []
    for i, video in enumerate(video_files):
        try:
            clip = AudioFileClip(video)
            audio_name = f"audio_{i}.mp3"
            clip.write_audiofile(audio_name, logger=None)
            clip.close()
            os.remove(video)
            audio_files.append(audio_name)
        except:
            pass

    cut_files = []
    for i, audio in enumerate(audio_files):
        try:
            clip = AudioFileClip(audio)
            cut_clip = clip.subclipped(0, duration)
            cut_name = f"cut_{i}.mp3"
            cut_clip.write_audiofile(cut_name, logger=None)
            clip.close()
            cut_clip.close()
            os.remove(audio)
            cut_files.append(cut_name)
        except:
            pass

    clips = []
    for f in cut_files:
        try:
            clip = AudioFileClip(f)
            clip = clip.with_fps(44100).with_channels(2)
            if clip.duration > 1:
                clips.append(clip)
        except:
            pass

    if len(clips) == 0:
        raise ValueError("No valid audio clips")

    final = concatenate_audioclips(clips)
    output_file = "output.mp3"
    final.write_audiofile(output_file, logger=None)

    for c in clips:
        c.close()
    for f in cut_files:
        try:
            os.remove(f)
        except:
            pass

    zip_filename = "mashup.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write(output_file)

    return zip_filename


def send_email(zip_filename, receiver_email):
    msg = EmailMessage()
    msg["Subject"] = "Your Mashup File"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg.set_content("Mashup attached")

    with open(zip_filename, "rb") as f:
        file_data = f.read()

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="zip",
        filename=zip_filename
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)


st.title("YouTube Mashup Generator")

singer = st.text_input("Singer name")
num_videos = st.number_input("Number of videos (>10)", min_value=11, step=1)
duration = st.number_input("Clip duration seconds (>20)", min_value=21, step=1)
email = st.text_input("Receiver email")

if st.button("Create Mashup"):
    if singer and email:
        try:
            with st.spinner("Processing... this can take 2-5 minutes"):
                zip_file = create_mashup(singer, num_videos, duration)
                send_email(zip_file, email)

            st.success("Mashup created and sent to email")

            with open(zip_file, "rb") as f:
                st.download_button("Download ZIP", f, file_name="mashup.zip")

        except Exception as e:
            st.error("Error occurred while creating mashup")
            st.exception(e)