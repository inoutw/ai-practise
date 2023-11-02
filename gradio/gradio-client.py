from gradio_client import Client

client = Client("abidlabs/whisper") 
client.predict("audio_sample.wav")  
