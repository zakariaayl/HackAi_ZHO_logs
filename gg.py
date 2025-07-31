from pydub import AudioSegment

# Load the MP3 file
# audio = AudioSegment.from_mp3("/content/preter.mp3")

# # Export as WAV
# audio.export("output.wav", format="wav")
import whisper

model = whisper.load_model("small")
result = model.transcribe("audio.wav", language="ar")
print(result["text"])