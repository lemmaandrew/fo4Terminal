from collections import defaultdict
from PIL import Image, ImageEnhance, ImageFilter, ImageGrab, ImageOps
import numpy as np
import pyautogui
import pytesseract
import re
import time
import warnings


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
warnings.filterwarnings('ignore')

def locateCarrot(img: Image) -> tuple:
    """Locates the '>' that is next to words in the input field of the terminal"""
    allcarrots = list(pyautogui.locateAll(Image.open('carrotonly.png'), img, confidence=0.75))
    carrot = max(allcarrots, key=lambda x: x.left + x.top)
    return (carrot.left + 13, \
        carrot.top - 10, \
        carrot.left + carrot.width + 300, \
        carrot.top + carrot.height + 5)


def captureCarrot(img: Image) -> Image:
    """Creates an image with the screen region of locateCarrot"""
    imgarr = np.array(img, dtype=np.uint8)
    carrot = list(locateCarrot(img))
    return Image.fromarray(imgarr[carrot[1]:carrot[3], carrot[0]:carrot[2]])


def fixScreen(img: Image) -> Image:
    """Prepares an image for reading with pytesseract"""
    med = img.filter(ImageFilter.MedianFilter())
    enhanced = ImageEnhance.Contrast(med).enhance(2)
    imgarr = np.array(enhanced, dtype=np.uint8)
    #imgarr[imgarr < 70] = 0
    mask0 = np.less(np.divide(imgarr[:, :, 1], imgarr[:, :, 0]), 20)
    mask2 = np.less(np.divide(imgarr[:, :, 1], imgarr[:, :, 2]), 20)
    imgarr[mask0 & mask2] = 0
    #not black -> white
    #imgarr[np.not_equal.reduce(imgarr != 0, axis=-1)] = 255
    return Image.fromarray(imgarr).convert('LA')


def wordSearch(region, wordlen: int) -> set:
    """Mouse over each word in the terminal while this is active then press Ctrl-C in the windows terminal to return the found words"""
    words = set()
    try:
        while True:
            try:
                txt = pytesseract.image_to_string(fixScreen(ImageGrab.grab(region)), lang='eng')
                txt = re.match(r'[a-zA-Z]{' + str(wordlen) + '}', txt)[0].upper()
                if len(txt) != wordlen or txt in words:
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
        for i in range(len(word1)):
            s += word1[i] == word2[i]
        return s


def suggestClick(words: set) -> str:
    """suggests which word to click based on the lowest average likeness between words"""
    def likenessChart(word):
        chart = defaultdict(int)
        for i in range(len(word)):
            for j in words:
                chart[i] += likeness(word, j) == i
        return np.average(list(chart.values()))
    
    minw = min(words, key=likenessChart)
    print(f'Click on: {minw}, score: {likenessChart(minw)}')
    return minw


def guess(words: set, word: str, similarity: int) -> None:
    """given a word with a known likeness, removes all words that don't have the same likeness with that word"""
    for word2 in words.copy():
        if likeness(word, word2) != similarity:
            words.remove(word2)
    return None


if __name__ == "__main__":
    input("MAKE SURE YOU'RE IN THE TERMINAL SCREEN AND THAT '>' ISN'T SELECTED")
    wordlength = int(input('Length of words: '))
    print('Starting...            ')
    print('Press Ctrl-C when all words have been cached')
    box = locateCarrot(ImageGrab.grab((0, 0, 1920, 1080)))
    cache = wordSearch(box, wordlength)
    while True:
        clickhere = suggestClick(cache)
        sim = int(input(f'What is the likeness of "{clickhere}"? '))
        guess(cache, clickhere, sim)
