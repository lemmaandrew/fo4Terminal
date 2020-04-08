"""Solves the hacking mini-game in Fallout 4"""
import json
import re
import warnings
from collections import defaultdict

import numpy as np
import pyautogui
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageGrab, ImageOps


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
warnings.filterwarnings('ignore')

with open('words.json') as f:
    WORDS = json.load(f)


def locate_carrot(img: Image) -> tuple:
    """Locates the '>' that is next to words in the input field of the terminal"""
    allcarrots = list(pyautogui.locateAll(Image.open('carrotonly.png'), img, confidence=0.75))
    carrot = max(allcarrots, key=lambda x: x.left + x.top)
    return (carrot.left + 13, \
        carrot.top - 10, \
        carrot.left + carrot.width + 300, \
        carrot.top + carrot.height + 5)


def capture_carrot(img: Image) -> Image:
    """Creates an image with the screen region of locate_carrot"""
    imgarr = np.array(img, dtype=np.uint8)
    carrot = list(locate_carrot(img))
    return Image.fromarray(imgarr[carrot[1]:carrot[3], carrot[0]:carrot[2]])


def fix_screen(img: Image, tolerance: int=10) -> Image:
    """Prepares an image for reading with pytesseract"""
    img = img.convert('L')
    med = img.filter(ImageFilter.MedianFilter())
    enhanced = ImageEnhance.Contrast(med).enhance(2)
    imgarr = np.array(enhanced, dtype=np.uint8)
    imgarr[np.all(imgarr < tolerance, axis=-1)] = 0
    imgarr[np.all(imgarr >= tolerance, axis=-1)] = 255
    img = Image.fromarray(imgarr)
    return ImageOps.invert(ImageEnhance.Contrast(img).enhance(2))


def word_search(region, wordlen: int) -> set:
    """Mouse over each word in the terminal while this is active then press Ctrl-C in the windows terminal to return the found words"""
    words = set()
    try:
        while True:
            try:
                txt = pytesseract.image_to_string(fix_screen(ImageGrab.grab(region)), lang='eng')
                txt = re.match(r'[a-zA-Z]{' + str(wordlen) + '}', txt)[0].upper()
                if txt in words or txt not in WORDS[str(wordlen)]:
                    continue
                print(txt)
                words.add(txt)
            except TypeError:
                continue
    except KeyboardInterrupt:
        return words


def likeness(word1: str, word2: str) -> int:
    """returns how many times each word has the same letter at each index"""
    s = 0
    for idx, letter in enumerate(word1):
        s += letter == word2[idx]
    return s


def suggest_click(words: set) -> str:
    """suggests which word to click based on the lowest average likeness between words"""
    def likeness_chart(word):
        chart = defaultdict(int)
        for i in range(len(word)):
            for j in words:
                chart[i] += likeness(word, j) == i
        return np.average(list(chart.values()))
    minw = min(words, key=likeness_chart)
    print(f'Click on: {minw}, score: {likeness_chart(minw)}')
    return minw


def guess(words: set, word: str, similarity: int) -> None:
    """given a word with a known likeness, removes all words that don't have the same likeness with that word"""
    for word2 in words.copy():
        if likeness(word, word2) != similarity:
            words.remove(word2)
    return None


if __name__ == "__main__":
    while True:
        input("MAKE SURE YOU'RE IN THE TERMINAL SCREEN AND THAT '>' ISN'T SELECTED")
        wordlength = int(input('Length of words: '))
        print('Starting...            ')
        print('Press Ctrl-C when all words have been cached')
        box = locate_carrot(ImageGrab.grab((0, 0, 1920, 1080)))
        cache = word_search(box, wordlength)
        while True:
            clickhere = suggest_click(cache)
            try:
                sim = input(f'What is the likeness of "{clickhere}"? ("done" to finish): ')
                guess(cache, clickhere, int(sim))
            except ValueError as e:
                if sim == 'done':
                    print('\n\n\n')
                    break
