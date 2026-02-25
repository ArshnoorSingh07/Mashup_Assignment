import sys
import os
import zipfile
import smtplib
from email.message import EmailMessage
from pytubefix import YouTube, Search
from moviepy import AudioFileClip, concatenate_audioclips

SENDER_EMAIL = "arshnoorsingh.05@gmail.com"
APP_PASSWORD = "dlhhovirseqiakxn"


def create_mashup(singer_name, num_videos, duration, output_file, receiver_email):
    print("Starting Mashup Creation...")

    video_files = []
    search = Search(singer_name + " songs")

    for i, vid in enumerate(search.results[:num_videos]):
        try:
            yt = YouTube(vid.watch_url)
            stream = yt.streams.filter(only_audio=True).first()
            filename = f"video_{i}.mp4"
            stream.download(filename=filename)
            video_files.append(filename)
            print(f"Downloaded {i+1}")
        except:
            continue

    audio_files = []
    for i, video in enumerate(video_files):
        clip = AudioFileClip(video)
        audio_name = f"audio_{i}.mp3"
        clip.write_audiofile(audio_name, logger=None)
        clip.close()
        os.remove(video)
        audio_files.append(audio_name)

    cut_files = []
    for i, audio in enumerate(audio_files):
        clip = AudioFileClip(audio)
        cut_clip = clip.subclipped(0, duration)
        cut_name = f"cut_{i}.mp3"
        cut_clip.write_audiofile(cut_name, logger=None)
        clip.close()
        cut_clip.close()
        os.remove(audio)
        cut_files.append(cut_name)

    clips = [AudioFileClip(f) for f in cut_files]
    final = concatenate_audioclips(clips)
    final.write_audiofile(output_file, logger=None)

    for c in clips:
        c.close()

    for f in cut_files:
        os.remove(f)

    zip_filename = "mashup.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write(output_file)

    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Mashup File"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg.set_content("Mashup attached.")

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

        print("Email sent successfully")

    except Exception as e:
        print("Email failed:", e)


if __name__ == "__main__":

    if len(sys.argv) != 6:
        print('Usage: python 102317161.py "SingerName" <NoOfVideos> <Duration> <OutputFile> <ReceiverEmail>')
        sys.exit(1)

    singer_name = sys.argv[1]
    num_videos = int(sys.argv[2])
    duration = int(sys.argv[3])
    output_file = sys.argv[4]
    receiver_email = sys.argv[5]

    if num_videos <= 10:
        print("Number of videos must be > 10")
        sys.exit(1)

    if duration <= 20:
        print("Duration must be > 20 seconds")
        sys.exit(1)

    create_mashup(singer_name, num_videos, duration, output_file, receiver_email)