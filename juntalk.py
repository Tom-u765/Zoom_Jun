# https://zenn.dev/lovegorira/articles/7f9d0060860a43
from __future__ import division

class Get_log():
    def __init__(self):
        import logging

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        logger = logging.getLogger(__name__)

        # ロガーを取得する
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)  # 出力レベルを設定

        # ハンドラー1を生成する
        h1 = logging.StreamHandler()
        h1.setLevel(logging.DEBUG)  # 出力レベルを設定

        # ハンドラー2を生成する
        h2 = logging.FileHandler('sample.log')
        h2.setLevel(logging.ERROR)  # 出力レベルを設定

        # フォーマッタを生成する
        fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # ハンドラーにフォーマッターを設定する
        h1.setFormatter(fmt)
        h2.setFormatter(fmt)

        # ロガーにハンドラーを設定する
        logger.addHandler(h1)
        logger.addHandler(h2)

        # ログ出力を行う
        logger.debug("degubログを出力")
        logger.info("infoログを出力")
        logger.warning("warnログを出力")
        logger.error("errorログを出力")
######################################################################################


import re
import sys
from google.cloud import speech
import pyaudio
from six.moves import queue


import time
from playsound import playsound

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'Zoom_Jun_Key.json'


# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer)

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

def listen_print_loop(responses):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue
            print("a")
        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue
            print("b")
        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = " " * (num_chars_printed - len(transcript))
        print("c")

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)
            print("d")
        else:
            print(transcript + overwrite_chars)
            # print(type(transcript + overwrite_chars))
            text = transcript + overwrite_chars
            print(f'transcript:{transcript + overwrite_chars}')
            dict = {"kokomae": "kokomae-out.wav", "hazure": "ハズレ.m4a", "sing":"daich-out.wav"}
            if "クリアできますか" in text:
                jun_sound_path = dict["kokomae"]
                time.sleep(1)
                print("OK!!")
                playsound(jun_sound_path)

            elif any(map(text.__contains__, ("はずれ", "ハズレ", "外れ"))):
                jun_sound_path = dict["hazure"]
                time.sleep(1)
                print("Bad")
                playsound(jun_sound_path)

            elif "歌って" in text:
                jun_sound_path = dict["sing"]
                time.sleep(1)
                print("Sing!!")
                playsound(jun_sound_path)
            print("e")
            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|終了)\b", transcript, re.I):
                print("Exiting..")
                break

            num_chars_printed = 0

def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = "ja-JP"  # a BCP-47 language tag
    print(0)
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code
    )
    print(1)
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )
    print(2)
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )
        print(3)
        responses = client.streaming_recognize(streaming_config, requests)
        print(4)
        # Now, put the transcription responses to use.
        listen_print_loop(responses)


if __name__ == "__main__":
    print("--main--")
    Get_log()
    main()
