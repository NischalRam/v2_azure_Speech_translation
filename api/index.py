import os
import requests
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- NEW: Define absolute paths for templates and static folders ---
# This ensures Flask can find the files when deployed on Vercel.
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_folder = os.path.join(APP_ROOT, 'templates')
static_folder = os.path.join(APP_ROOT, 'static')

# --- UPDATED: Pass the folder paths to the Flask app ---
app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)


# --- Configuration & Language Dictionaries ---

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION")

if not all([AZURE_SPEECH_KEY, AZURE_SPEECH_REGION]):
    # This will help debug in Vercel logs if keys are missing
    raise ValueError("Azure Speech Key or Region is not set in the environment variables.")

# --- Language Dictionaries (No changes below this line) ---

SOURCE_LANGUAGES = {
    "Afrikaans (South Africa)": "af-ZA", "Amharic (Ethiopia)": "am-ET", "Arabic (United Arab Emirates)": "ar-AE",
    "Arabic (Bahrain)": "ar-BH", "Arabic (Algeria)": "ar-DZ", "Arabic (Egypt)": "ar-EG", "Arabic (Israel)": "ar-IL",
    "Arabic (Iraq)": "ar-IQ", "Arabic (Jordan)": "ar-JO", "Arabic (Kuwait)": "ar-KW", "Arabic (Lebanon)": "ar-LB",
    "Arabic (Libya)": "ar-LY", "Arabic (Morocco)": "ar-MA", "Arabic (Oman)": "ar-OM",
    "Arabic (Palestinian Authority)": "ar-PS", "Arabic (Qatar)": "ar-QA", "Arabic (Saudi Arabia)": "ar-SA",
    "Arabic (Syria)": "ar-SY", "Arabic (Tunisia)": "ar-TN", "Arabic (Yemen)": "ar-YE", "Assamese (India)": "as-IN",
    "Azerbaijani (Latin, Azerbaijan)": "az-AZ", "Bulgarian (Bulgaria)": "bg-BG", "Bengali (India)": "bn-IN",
    "Bosnian (Bosnia and Herzegovina)": "bs-BA", "Catalan": "ca-ES", "Czech (Czechia)": "cs-CZ",
    "Welsh (United Kingdom)": "cy-GB", "Danish (Denmark)": "da-DK", "German (Austria)": "de-AT",
    "German (Switzerland)": "de-CH", "German (Germany)": "de-DE", "Greek (Greece)": "el-GR",
    "English (Australia)": "en-AU", "English (Canada)": "en-CA", "English (United Kingdom)": "en-GB",
    "English (Ghana)": "en-GH", "English (Hong Kong SAR)": "en-HK", "English (Ireland)": "en-IE",
    "English (India)": "en-IN", "English (Kenya)": "en-KE", "English (Nigeria)": "en-NG",
    "English (New Zealand)": "en-NZ", "English (Philippines)": "en-PH", "English (Singapore)": "en-SG",
    "English (Tanzania)": "en-TZ", "English (United States)": "en-US", "English (South Africa)": "en-ZA",
    "Spanish (Argentina)": "es-AR", "Spanish (Bolivia)": "es-BO", "Spanish (Chile)": "es-CL",
    "Spanish (Colombia)": "es-CO", "Spanish (Costa Rica)": "es-CR", "Spanish (Cuba)": "es-CU",
    "Spanish (Dominican Republic)": "es-DO", "Spanish (Ecuador)": "es-EC", "Spanish (Spain)": "es-ES",
    "Spanish (Equatorial Guinea)": "es-GQ", "Spanish (Guatemala)": "es-GT", "Spanish (Honduras)": "es-HN",
    "Spanish (Mexico)": "es-MX", "Spanish (Nicaragua)": "es-NI", "Spanish (Panama)": "es-PA",
    "Spanish (Peru)": "es-PE", "Spanish (Puerto Rico)": "es-PR", "Spanish (Paraguay)": "es-PY",
    "Spanish (El Salvador)": "es-SV", "Spanish (United States)": "es-US", "Spanish (Uruguay)": "es-UY",
    "Spanish (Venezuela)": "es-VE", "Estonian (Estonia)": "et-EE", "Basque": "eu-ES", "Persian (Iran)": "fa-IR",
    "Finnish (Finland)": "fi-FI", "Filipino (Philippines)": "fil-PH", "French (Belgium)": "fr-BE",
    "French (Canada)": "fr-CA", "French (Switzerland)": "fr-CH", "French (France)": "fr-FR",
    "Irish (Ireland)": "ga-IE", "Galician": "gl-ES", "Gujarati (India)": "gu-IN", "Hebrew (Israel)": "he-IL",
    "Hindi (India)": "hi-IN", "Croatian (Croatia)": "hr-HR", "Hungarian (Hungary)": "hu-HU",
    "Armenian (Armenia)": "hy-AM", "Indonesian (Indonesia)": "id-ID", "Icelandic (Iceland)": "is-IS",
    "Italian (Switzerland)": "it-CH", "Italian (Italy)": "it-IT", "Japanese (Japan)": "ja-JP",
    "Georgian (Georgia)": "ka-GE", "Kazakh (Kazakhstan)": "kk-KZ", "Khmer (Cambodia)": "km-KH",
    "Kannada (India)": "kn-IN", "Korean (Korea)": "ko-KR", "Lao (Laos)": "lo-LA",
    "Lithuanian (Lithuania)": "lt-LT", "Latvian (Latvia)": "lv-LV", "Macedonian (North Macedonia)": "mk-MK",
    "Malayalam (India)": "ml-IN", "Mongolian (Mongolia)": "mn-MN", "Marathi (India)": "mr-IN",
    "Malay (Malaysia)": "ms-MY", "Maltese (Malta)": "mt-MT", "Burmese (Myanmar)": "my-MM",
    "Norwegian Bokmål (Norway)": "nb-NO", "Nepali (Nepal)": "ne-NP", "Dutch (Belgium)": "nl-BE",
    "Dutch (Netherlands)": "nl-NL", "Odia (India)": "or-IN", "Punjabi (India)": "pa-IN",
    "Polish (Poland)": "pl-PL", "Pashto (Afghanistan)": "ps-AF", "Portuguese (Brazil)": "pt-BR",
    "Portuguese (Portugal)": "pt-PT", "Romanian (Romania)": "ro-RO", "Russian (Russia)": "ru-RU",
    "Sinhala (Sri Lanka)": "si-LK", "Slovak (Slovakia)": "sk-SK", "Slovenian (Slovenia)": "sl-SI",
    "Somali (Somalia)": "so-SO", "Albanian (Albania)": "sq-AL", "Serbian (Cyrillic, Serbia)": "sr-RS",
    "Swedish (Sweden)": "sv-SE", "Kiswahili (Kenya)": "sw-KE", "Kiswahili (Tanzania)": "sw-TZ",
    "Tamil (India)": "ta-IN", "Telugu (India)": "te-IN", "Thai (Thailand)": "th-TH", "Turkish (Türkiye)": "tr-TR",
    "Ukrainian (Ukraine)": "uk-UA", "Urdu (India)": "ur-IN", "Uzbek (Latin, Uzbekistan)": "uz-UZ",
    "Vietnamese (Vietnam)": "vi-VN", "Chinese (Cantonese, Simplified)": "yue-CN",
    "Chinese (Mandarin, Simplified)": "zh-CN", "Chinese (Jilu Mandarin, Simplified)": "zh-CN-shandong",
    "Chinese (Southwestern Mandarin, Simplified)": "zh-CN-sichuan", "Chinese (Cantonese, Traditional)": "zh-HK",
    "Chinese (Taiwanese Mandarin, Traditional)": "zh-TW", "isiZulu (South Africa)": "zu-ZA"
}
TARGET_LANGUAGES = {
    "Afrikaans": "af", "Albanian": "sq", "Amharic": "am", "Arabic": "ar", "Armenian": "hy", "Assamese": "as",
    "Azerbaijani": "az", "Bangla": "bn", "Bosnian (Latin)": "bs", "Bulgarian": "bg",
    "Cantonese (Traditional)": "yue", "Catalan": "ca", "Chinese Simplified": "zh-Hans",
    "Chinese Traditional": "zh-Hant", "Croatian": "hr", "Czech": "cs", "Danish": "da", "Dari": "prs",
    "Dutch": "nl", "English": "en", "Estonian": "et", "Filipino": "fil", "Finnish": "fi", "French": "fr",
    "French (Canada)": "fr-ca", "German": "de", "Greek": "el", "Gujarati": "gu", "Hebrew": "he", "Hindi": "hi",
    "Hungarian": "hu", "Icelandic": "is", "Indonesian": "id", "Irish": "ga", "Italian": "it",
    "Japanese": "ja", "Kannada": "kn", "Kazakh": "kk", "Khmer": "km", "Korean": "ko", "Lao": "lo",
    "Latvian": "lv", "Lithuanian": "lt", "Macedonian": "mk", "Malay": "ms", "Malayalam": "ml", "Maltese": "mt",
    "Marathi": "mr", "Myanmar": "my", "Nepali": "ne", "Norwegian": "nb", "Odia": "or", "Pashto": "ps",
    "Persian": "fa", "Polish": "pl", "Portuguese (Brazil)": "pt", "Portuguese (Portugal)": "pt-pt",
    "Punjabi": "pa", "Romanian": "ro", "Russian": "ru", "Serbian (Cyrillic)": "sr-Cyrl", "Slovak": "sk",
    "Slovenian": "sl", "Somali": "so", "Spanish": "es", "Swahili": "sw", "Swedish": "sv", "Tamil": "ta",
    "Telugu": "te", "Thai": "th", "Tongan": "to", "Turkish": "tr", "Ukrainian": "uk", "Urdu": "ur",
    "Uzbek": "uz", "Vietnamese": "vi", "Welsh": "cy"
}
VOICE_MAP = {
    'af': 'af-ZA-AdriNeural', 'sq': 'sq-AL-AnilaNeural', 'am': 'am-ET-AmehaNeural', 'ar': 'ar-SA-ZariyahNeural',
    'hy': 'hy-AM-AnahitNeural', 'as': 'as-IN-NilakshiNeural', 'az': 'az-AZ-BanuNeural', 'bn': 'bn-IN-TanishaNeural',
    'bs': 'bs-BA-VesnaNeural', 'bg': 'bg-BG-KalinaNeural', 'yue': 'zh-HK-HiuGaaiNeural', 'ca': 'ca-ES-JoanaNeural',
    'zh-Hans': 'zh-CN-XiaoxiaoNeural', 'zh-Hant': 'zh-TW-HsiaoChenNeural', 'hr': 'hr-HR-GabrijelaNeural',
    'cs': 'cs-CZ-VlastaNeural', 'da': 'da-DK-ChristelNeural', 'prs': 'prs-AF-LatifaNeural', 'nl': 'nl-NL-FennaNeural',
    'en': 'en-US-AriaNeural', 'et': 'et-EE-AnuNeural', 'fil': 'fil-PH-BlessicaNeural', 'fi': 'fi-FI-NooraNeural',
    'fr': 'fr-FR-DeniseNeural', 'fr-ca': 'fr-CA-SylvieNeural', 'de': 'de-DE-KatjaNeural', 'el': 'el-GR-AthinaNeural',
    'gu': 'gu-IN-DhwaniNeural', 'he': 'he-IL-HilaNeural', 'hi': 'hi-IN-SwaraNeural', 'hu': 'hu-HU-NoemiNeural',
    'is': 'is-IS-GudrunNeural', 'id': 'id-ID-GadisNeural', 'ga': 'ga-IE-OrlaNeural', 'it': 'it-IT-ElsaNeural',
    'ja': 'ja-JP-NanamiNeural', 'kn': 'kn-IN-SapnaNeural', 'kk': 'kk-KZ-AigulNeural', 'km': 'km-KH-SreymomNeural',
    'ko': 'ko-KR-SunHiNeural', 'lo': 'lo-LA-KeomanyNeural', 'lv': 'lv-LV-EveritaNeural', 'lt': 'lt-LT-OnaNeural',
    'mk': 'mk-MK-MarijaNeural', 'ms': 'ms-MY-YasminNeural', 'ml': 'ml-IN-SobhanaNeural', 'mt': 'mt-MT-GraceNeural',
    'mr': 'mr-IN-AarohiNeural', 'my': 'my-MM-NilarNeural', 'ne': 'ne-NP-SagarikaNeural', 'nb': 'nb-NO-PernilleNeural',
    'or': 'or-IN-AshaNeural', 'ps': 'ps-AF-LatifaNeural', 'fa': 'fa-IR-DilaraNeural', 'pl': 'pl-PL-ZofiaNeural',
    'pt': 'pt-BR-FranciscaNeural', 'pt-pt': 'pt-PT-RaquelNeural', 'pa': 'pa-IN-AseesNeural',
    'ro': 'ro-RO-AlinaNeural', 'ru': 'ru-RU-SvetlanaNeural', 'sr-Cyrl': 'sr-RS-SophieNeural',
    'sk': 'sk-SK-ViktoriaNeural', 'sl': 'sl-SI-PetraNeural', 'so': 'so-SO-UbaxNeural', 'es': 'es-ES-ElviraNeural',
    'sw': 'sw-KE-ZuriNeural', 'sv': 'sv-SE-SofieNeural', 'ta': 'ta-IN-PallaviNeural', 'te': 'te-IN-ShrutiNeural',
    'th': 'th-TH-PremwadeeNeural', 'to': 'to-TO-AnaNeural', 'tr': 'tr-TR-EmelNeural', 'uk': 'uk-UA-PolinaNeural',
    'ur': 'ur-PK-UzmaNeural', 'uz': 'uz-UZ-SardorNeural', 'vi': 'vi-VN-HoaiMyNeural', 'cy': 'cy-GB-NiaNeural'
}

@app.route('/')
def index():
    sorted_source = dict(sorted(SOURCE_LANGUAGES.items()))
    sorted_target = dict(sorted(TARGET_LANGUAGES.items()))
    return render_template('index.html',
                           source_languages=sorted_source,
                           target_languages=sorted_target)

@app.route('/api/get_token')
def get_token():
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    token_url = f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    try:
        response = requests.post(token_url, headers=headers)
        response.raise_for_status()
        return jsonify({'token': response.text, 'region': AZURE_SPEECH_REGION})
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    data = request.get_json()
    text = data.get('text')
    target_lang = data.get('language')
    if not text or not target_lang:
        return jsonify({'error': 'Missing text or language'}), 400
    voice_name = VOICE_MAP.get(target_lang)
    if not voice_name:
        return jsonify({'error': f"No voice available for language code: {target_lang}"}), 400
    synthesis_url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
        'User-Agent': 'FlaskSpeechTranslator'
    }
    ssml_lang = '-'.join(voice_name.split('-')[:2])
    ssml_body = (
        f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{ssml_lang}'>"
        f"<voice name='{voice_name}'>{text}</voice>"
        f"</speak>"
    )
    try:
        response = requests.post(synthesis_url, headers=headers, data=ssml_body.encode('utf-8'))
        response.raise_for_status()
        return response.content, 200, {'Content-Type': 'audio/mpeg'}
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
